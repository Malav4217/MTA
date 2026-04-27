"""
Ingests real-time MTA bus data and saves it to DuckDB.
"""
import time
import requests
import pandas as pd
import duckdb
import schedule
from loguru import logger
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import MTA_API_KEY, VEHICLE_MONITORING_URL, TRACKED_ROUTES, DB_FILE, DATA_COLLECTION_INTERVAL_SECONDS

def fetch_bus_data(route):
    """
    Fetches real-time bus data for a specific route from the MTA Bus Time API.

    Args:
        route (str): The bus route to fetch data for.

    Returns:
        list: A list of vehicle activity dictionaries, or an empty list if the request fails.
    """
    params = {
        'key': MTA_API_KEY,
        'LineRef': route,
        'VehicleMonitoringDetailLevel': 'calls'
    }
    try:
        response = requests.get(VEHICLE_MONITORING_URL, params=params, timeout=15)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        
        if data.get('Siri', {}).get('ServiceDelivery', {}).get('VehicleMonitoringDelivery', [{}])[0].get('VehicleActivity'):
            return data['Siri']['ServiceDelivery']['VehicleMonitoringDelivery'][0]['VehicleActivity']
        else:
            logger.warning(f"No vehicle activity found for route {route}.")
            return []

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for route {route}: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching data for route {route}: {e}")
        return []

# def process_data(vehicle_activities, captured_at):
#     """
#     Processes the raw API response into a structured pandas DataFrame.

#     Args:
#         vehicle_activities (list): List of vehicle activity dictionaries from the API.
#         captured_at (datetime): The timestamp when the data was captured.

#     Returns:
#         pd.DataFrame: A DataFrame with the structured bus data.
#     """
#     records = []
#     for activity in vehicle_activities:
#         journey = activity.get('MonitoredVehicleJourney', {})
#         if not journey:
#             continue

#         onward_call = journey.get('OnwardCalls', {}).get('OnwardCall', [{}])[0]
        
#         records.append({
#             'snapshot_id': hash(f"{journey.get('VehicleRef')}{captured_at}"),
#             'captured_at': captured_at,
#             'vehicle_id': journey.get('VehicleRef'),
#             'route': journey.get('LineRef'),
#             'direction': journey.get('DirectionRef'),
#             'latitude': journey.get('VehicleLocation', {}).get('Latitude'),
#             'longitude': journey.get('VehicleLocation', {}).get('Longitude'),
#             'next_stop_id': onward_call.get('StopPointRef'),
#             'next_stop_name': onward_call.get('StopPointName'),
#             'aimed_arrival': onward_call.get('AimedArrivalTime'),
#             'expected_arrival': onward_call.get('ExpectedArrivalTime'),
#             'distance_to_stop': onward_call.get('Extensions', {}).get('Distances', {}).get('DistanceFromCall')
#         })
    
#     return pd.DataFrame(records)

def process_data(vehicle_activities, captured_at):
    """
    Processes the raw API response into a structured pandas DataFrame.

    Args:
        vehicle_activities (list): List of vehicle activity dictionaries from the API.
        captured_at (datetime): The timestamp when the data was captured.

    Returns:
        pd.DataFrame: A DataFrame with the structured bus data.
    """
    records = []
    for activity in vehicle_activities:
        journey = activity.get('MonitoredVehicleJourney', {})
        if not journey:
            continue

        monitored_call = journey.get('MonitoredCall', {})
        distances = monitored_call.get('Extensions', {}).get('Distances', {})

        records.append({
            'snapshot_id':      hash(f"{journey.get('VehicleRef')}{captured_at}"),
            'captured_at':      captured_at,
            'vehicle_id':       journey.get('VehicleRef'),
            'route':            journey.get('LineRef'),
            'direction':        journey.get('DirectionRef'),
            'latitude':         journey.get('VehicleLocation', {}).get('Latitude'),
            'longitude':        journey.get('VehicleLocation', {}).get('Longitude'),
            'next_stop_id':     monitored_call.get('StopPointRef'),      
            'next_stop_name':   monitored_call.get('StopPointName'),     
            'aimed_arrival':    monitored_call.get('AimedArrivalTime'),   
            'expected_arrival': monitored_call.get('ExpectedArrivalTime') 
                                or monitored_call.get('AimedArrivalTime'),
            'distance_to_stop': distances.get('DistanceFromCall'),     
        })

    return pd.DataFrame(records)

def save_to_duckdb(df):
    """
    Saves the DataFrame to the 'raw_bus_snapshots' table in DuckDB.

    Args:
        df (pd.DataFrame): The DataFrame to save.
    """
    if df.empty:
        logger.info("No data to save.")
        return
        
    try:
        con = duckdb.connect(DB_FILE)
        con.register('df_temp', df)
        con.execute('INSERT INTO raw_bus_snapshots SELECT * FROM df_temp')
        con.close()
        logger.info(f"Successfully saved {len(df)} records to 'raw_bus_snapshots'.")
    except Exception as e:
        logger.error(f"Error saving data to DuckDB: {e}")

def ingestion_job():
    """
    The main job to be scheduled. Fetches, processes, and saves data for all tracked routes.
    """
    logger.info("Starting ingestion job...")
    captured_at = datetime.now()
    all_data = []

    for route in TRACKED_ROUTES:
        logger.info(f"Fetching data for route: {route}")
        vehicle_activities = fetch_bus_data(route)
        if vehicle_activities:
            df = process_data(vehicle_activities, captured_at)
            all_data.append(df)
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        save_to_duckdb(combined_df)
    
    logger.info("Ingestion job finished.")

if __name__ == "__main__":
    logger.add("ingestion.log", rotation="1 day")
    
    # Run once immediately
    ingestion_job()

    # Schedule the job
    schedule.every(DATA_COLLECTION_INTERVAL_SECONDS).seconds.do(ingestion_job)
    logger.info(f"Scheduled ingestion job to run every {DATA_COLLECTION_INTERVAL_SECONDS} seconds.")

    while True:
        schedule.run_pending()
        time.sleep(1)
