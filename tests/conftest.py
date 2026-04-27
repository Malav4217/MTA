import pytest
import duckdb
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))
from config import DB_FILE


@pytest.fixture(scope="session")
def db_connection():
    """
    Provide read-only database connection
    for all tests in the session.
    Automatically closes after all tests run.
    """
    con = duckdb.connect(DB_FILE, read_only=True)
    yield con
    con.close()


@pytest.fixture(scope="session")
def sample_raw_data(db_connection):
    """
    Fetch sample of raw snapshots for testing.
    Returns DataFrame with recent data.
    """
    return db_connection.execute("""
        SELECT *
        FROM raw_bus_snapshots
        WHERE captured_at >= CURRENT_DATE
        LIMIT 1000
    """).df()


@pytest.fixture(scope="session")
def sample_arrivals(db_connection):
    """
    Fetch sample of processed arrivals.
    Returns DataFrame with today's data.
    """
    return db_connection.execute("""
        SELECT *
        FROM bus_arrivals
        WHERE date >= CURRENT_DATE - 1
        LIMIT 1000
    """).df()


@pytest.fixture(scope="session")
def sample_bunching(db_connection):
    """
    Fetch sample of bunching events.
    """
    return db_connection.execute("""
        SELECT *
        FROM bunching_events
        WHERE CAST(timestamp AS DATE) >= CURRENT_DATE - 1
        LIMIT 500
    """).df()


@pytest.fixture(scope="session")
def sample_ghosts(db_connection):
    """
    Fetch sample of ghost bus detections.
    """
    return db_connection.execute("""
        SELECT *
        FROM ghost_buses
        LIMIT 500
    """).df()
