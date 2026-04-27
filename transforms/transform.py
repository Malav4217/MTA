"""
Cleans raw bus data, detects delays, ghost buses, and bunching events.
"""
import duckdb
import pandas as pd
from loguru import logger
import numpy as np
import math
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    DB_FILE,
    DELAY_THRESHOLD_MINUTES,
    EARLY_THRESHOLD_MINUTES,
    HAVERSINE_DISTANCE_THRESHOLD_METERS
)

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on Earth using the Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of the first point.
        lat2, lon2: Latitude and longitude of the second point.

    Returns:
        float: Distance in meters.
    """
    R = 6371000  # Earth radius in meters
    
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    
    distance = R * c
    return distance

def clean_and_calculate_delays(con):
    logger.info("Starting delay calculation and data cleaning...")
    
    # Get last processed timestamp from bus_arrivals
    last_processed = con.execute("""
        SELECT MAX(scheduled_arrival) FROM bus_arrivals
    """).fetchone()[0]
    
    # Fetch unprocessed raw snapshots based on time
    if last_processed:
        logger.info(f"Processing snapshots after {last_processed}")
        df = con.execute("""
            SELECT * FROM raw_bus_snapshots
            WHERE aimed_arrival IS NOT NULL
            AND expected_arrival IS NOT NULL
            AND CAST(aimed_arrival AS TIMESTAMP) > CAST(? AS TIMESTAMP)
        """, [str(last_processed)]).df()
    else:
        logger.info("No previous data found - processing all snapshots")
        df = con.execute("""
            SELECT * FROM raw_bus_snapshots
            WHERE aimed_arrival IS NOT NULL
            AND expected_arrival IS NOT NULL
        """).df()
    
    if df.empty:
        logger.info("No new arrivals to process for delays.")
        return
    
    logger.info(f"Found {len(df)} new snapshots to process...")
    
    # Parse timestamps
    df['aimed_arrival'] = pd.to_datetime(df['aimed_arrival'], utc=True)
    df['expected_arrival'] = pd.to_datetime(df['expected_arrival'], utc=True)
    
    # Calculate delay in minutes
    df['delay_minutes'] = (
        (df['expected_arrival'] - df['aimed_arrival'])
        .dt.total_seconds() / 60
    ).round(2)
    
    # Remove bad/outlier data
    df = df[df['delay_minutes'].between(-10, 60)].copy()
    
    if df.empty:
        logger.info("All rows filtered out as bad data.")
        return
    
    # Add derived columns
    df['is_late']      = df['delay_minutes'] > 5
    df['is_early']     = df['delay_minutes'] < -2
    df['is_on_time']   = ~df['is_late'] & ~df['is_early']
    df['date']         = pd.to_datetime(df['captured_at']).dt.date
    df['hour']         = pd.to_datetime(df['captured_at']).dt.hour
    df['day_of_week']  = pd.to_datetime(df['captured_at']).dt.dayofweek
    
    # Rename to match bus_arrivals schema
    df = df.rename(columns={
        'next_stop_id':   'stop_id',
        'next_stop_name': 'stop_name',
        'aimed_arrival':  'scheduled_arrival',
        'expected_arrival': 'actual_arrival',
    })
    
    # Register DataFrame with DuckDB for insertion
    con.register('df', df)

    # Insert into bus_arrivals
    con.execute("""
        INSERT INTO bus_arrivals 
        (vehicle_id, route, stop_id, stop_name, 
         scheduled_arrival, actual_arrival, 
         delay_minutes, is_late, is_early, is_on_time,
         date, hour, day_of_week)
        SELECT 
         vehicle_id, route, stop_id, stop_name,
         scheduled_arrival, actual_arrival,
         delay_minutes, is_late, is_early, is_on_time,
         date, hour, day_of_week
        FROM df
    """)
    
    logger.info(f"✅ Saved {len(df)} new arrivals to bus_arrivals.")


def detect_bunching(con):
    logger.info("Starting bus bunching detection...")
    
    # Only look at snapshots from last 2 minutes (current run)
    df = con.execute("""
        SELECT 
            vehicle_id, route, direction,
            latitude, longitude, captured_at
        FROM raw_bus_snapshots
        WHERE captured_at >= NOW() - INTERVAL '2 minutes'
        AND latitude IS NOT NULL
        AND longitude IS NOT NULL
    """).df()
    
    if df.empty:
        logger.info("No recent snapshots for bunching detection")
        return
    
    import math
    from datetime import datetime
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Get pairs already detected in last 5 minutes
    # to avoid inserting same pair repeatedly
    recent_pairs = con.execute("""
        SELECT vehicle_1_id || '_' || vehicle_2_id as pair_key
        FROM bunching_events
        WHERE timestamp >= NOW() - INTERVAL '5 minutes'
    """).df()
    
    already_seen = set(recent_pairs['pair_key'].tolist()) \
                   if not recent_pairs.empty else set()
    
    bunching_events = []
    
    for (route, direction), group in df.groupby(['route', 'direction']):
        vehicles = group.drop_duplicates('vehicle_id', keep='last')
        vehicle_list = vehicles.to_dict('records')
        
        for i in range(len(vehicle_list)):
            for j in range(i+1, len(vehicle_list)):
                v1 = vehicle_list[i]
                v2 = vehicle_list[j]
                
                dist = haversine(
                    v1['latitude'], v1['longitude'],
                    v2['latitude'], v2['longitude']
                )
                
                # Only real bunching: 50m-500m apart
                if 50 < dist < 500:
                    # Check if this pair was already recorded recently
                    pair_key = '_'.join(sorted([
                        str(v1['vehicle_id']), 
                        str(v2['vehicle_id'])
                    ]))
                    
                    if pair_key not in already_seen:
                        already_seen.add(pair_key)
                        bunching_events.append({
                            'route': route,
                            'direction': str(direction),
                            'vehicle_1_id': v1['vehicle_id'],
                            'vehicle_2_id': v2['vehicle_id'],
                            'distance_between_m': round(dist, 1),
                            'is_bunched': True,
                            'timestamp': datetime.now(),
                            'stop_area': 'N/A'
                        })
    
    if bunching_events:
        # APPEND only — never delete historical data
        events_df = pd.DataFrame(bunching_events)
        con.execute("""
            INSERT INTO bunching_events 
            (route, direction, vehicle_1_id, vehicle_2_id,
             distance_between_m, is_bunched, timestamp, stop_area)
            SELECT route, direction, vehicle_1_id, vehicle_2_id,
                   distance_between_m, is_bunched, timestamp, stop_area
            FROM events_df
        """)
        logger.info(f"Added {len(bunching_events)} new bunching events")
    else:
        logger.info("No new bunching events this run")

def detect_ghost_buses(con):
    """
    Detects ghost buses by grouping snapshots by vehicle and next stop.

    Args:
        con: DuckDB connection object.
    """
    logger.info("Starting ghost bus detection...")
    try:
        # Clear existing ghost buses to start clean using safe TRUNCATE
        try:
            con.execute("TRUNCATE TABLE ghost_buses")
            logger.info("Cleared existing ghost_buses table.")
        except Exception as truncate_error:
            # Fallback: recreate the table if TRUNCATE fails
            logger.warning(f"TRUNCATE failed ({truncate_error}), recreating table...")
            con.execute("DROP TABLE IF EXISTS ghost_buses")
            con.execute("""
                CREATE TABLE ghost_buses (
                    vehicle_id VARCHAR,
                    route VARCHAR,
                    stop_id VARCHAR,
                    last_seen_at TIMESTAMP,
                    expected_arrival TIMESTAMP,
                    distance_at_disappear DOUBLE,
                    is_ghost BOOLEAN,
                    captured_date DATE
                )
            """)

        df = con.execute("SELECT * FROM raw_bus_snapshots").fetchdf()
        if df.empty:
            logger.info("No raw snapshots available for ghost bus detection.")
            return

        df = df.dropna(subset=['vehicle_id', 'next_stop_id', 'distance_to_stop', 'captured_at'])
        if df.empty:
            logger.info("No valid raw snapshot rows for ghost detection.")
            return

        # Ensure captured_at is datetime
        df['captured_at'] = pd.to_datetime(df['captured_at'])

        ghost_records = []
        grouped = df.groupby(['vehicle_id', 'next_stop_id'])

        for (vehicle_id, stop_id), group in grouped:
            group = group.sort_values('captured_at').reset_index(drop=True)
            if len(group) < 1:
                continue

            first_row = group.iloc[0]
            last_row = group.iloc[-1]

            # Condition 2: First snapshot distance > 500m
            if first_row['distance_to_stop'] <= 500:
                continue

            # Condition 3: Never appeared with distance < 50m
            if (group['distance_to_stop'] < 50).any():
                continue

            # Condition 4: Time between first and last > 10 minutes
            time_diff = (last_row['captured_at'] - first_row['captured_at']).total_seconds() / 60
            if time_diff <= 10:
                continue

            # All conditions met, add one ghost event
            ghost_records.append({
                'vehicle_id': vehicle_id,
                'route': first_row.get('route'),
                'stop_id': stop_id,
                'last_seen_at': last_row['captured_at'],
                'expected_arrival': last_row.get('expected_arrival'),
                'distance_at_disappear': last_row['distance_to_stop'],
                'is_ghost': True,
                'captured_date': last_row['captured_at'].date()
            })

        if not ghost_records:
            logger.info("No ghost buses detected.")
            return

        ghosts_df = pd.DataFrame(ghost_records)
        con.register('ghost_buses_temp', ghosts_df)
        con.execute('INSERT INTO ghost_buses SELECT * FROM ghost_buses_temp')
        logger.info(f"Detected and saved {len(ghosts_df)} ghost bus events.")

    except Exception as e:
        logger.error(f"Error in ghost bus detection: {e}")


def transform_job():
    """
    Main transformation job to run all detection logic.
    """
    logger.info("Starting transformation job...")
    try:
        con = duckdb.connect(DB_FILE)
        clean_and_calculate_delays(con)
        detect_bunching(con)
        detect_ghost_buses(con)
        # Ghost bus detection would be added here
        con.close()
        logger.info("Transformation job finished.")
    except Exception as e:
        logger.error(f"Transformation job failed: {e}")

if __name__ == "__main__":
    logger.add("transforms.log", rotation="1 day")
    transform_job()
