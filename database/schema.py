"""
Defines the database schema and creates the tables in DuckDB.
"""
import duckdb
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from loguru import logger

from config import DB_FILE

def create_tables():
    """
    Connects to the DuckDB database and creates the necessary tables if they don't exist.
    """
    try:
        db_dir = os.path.dirname(DB_FILE)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        con = duckdb.connect(DB_FILE)
        logger.info(f"Connected to database {DB_FILE}")

        # Table 1 - raw_bus_snapshots
        con.execute("""
        CREATE TABLE IF NOT EXISTS raw_bus_snapshots (
            snapshot_id BIGINT,
            captured_at TIMESTAMP,
            vehicle_id VARCHAR,
            route VARCHAR,
            direction VARCHAR,
            latitude DOUBLE,
            longitude DOUBLE,
            next_stop_id VARCHAR,
            next_stop_name VARCHAR,
            aimed_arrival TIMESTAMP,
            expected_arrival TIMESTAMP,
            distance_to_stop DOUBLE
        );
        """)
        logger.info("Table 'raw_bus_snapshots' created or already exists.")

        # Table 2 - bus_arrivals
        con.execute("""
        CREATE TABLE IF NOT EXISTS bus_arrivals (
            arrival_id BIGINT,
            vehicle_id VARCHAR,
            route VARCHAR,
            stop_id VARCHAR,
            stop_name VARCHAR,
            scheduled_arrival TIMESTAMP,
            actual_arrival TIMESTAMP,
            delay_minutes INTEGER,
            is_late BOOLEAN,
            is_early BOOLEAN,
            is_on_time BOOLEAN,
            date DATE,
            hour INTEGER,
            day_of_week INTEGER
        );
        """)
        logger.info("Table 'bus_arrivals' created or already exists.")

        # Table 3 - ghost_buses
        con.execute("""
        CREATE TABLE IF NOT EXISTS ghost_buses (
            vehicle_id VARCHAR,
            route VARCHAR,
            stop_id VARCHAR,
            last_seen_at TIMESTAMP,
            expected_arrival TIMESTAMP,
            distance_at_disappear DOUBLE,
            is_ghost BOOLEAN,
            captured_date DATE
        );
        """)
        logger.info("Table 'ghost_buses' created or already exists.")

        # Table 4 - bunching_events
        con.execute("""
        CREATE TABLE IF NOT EXISTS bunching_events (
            route VARCHAR,
            direction VARCHAR,
            vehicle_1_id VARCHAR,
            vehicle_2_id VARCHAR,
            distance_between_m DOUBLE,
            avg_distance DOUBLE,
            is_bunched BOOLEAN,
            "timestamp" TIMESTAMP,
            stop_area VARCHAR
        );
        """)
        logger.info("Table 'bunching_events' created or already exists.")

        # Table 5 - route_reliability
        con.execute("""
        CREATE TABLE IF NOT EXISTS route_reliability (
            route VARCHAR,
            hour_of_day INTEGER,
            day_of_week INTEGER,
            total_arrivals INTEGER,
            on_time_count INTEGER,
            late_count INTEGER,
            on_time_pct DOUBLE,
            avg_delay_minutes DOUBLE,
            max_delay_minutes INTEGER
        );
        """)
        logger.info("Table 'route_reliability' created or already exists.")

        con.close()
        logger.info("Database connection closed.")

    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

if __name__ == "__main__":
    create_tables()
