"""
Configuration for the MTA Bus Reliability Tracker MVP.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# MTA API Configuration
MTA_API_KEY = os.getenv('MTA_API_KEY')
VEHICLE_MONITORING_URL = (
    "http://bustime.mta.info/api/siri/"
    "vehicle-monitoring.json"
)
STOP_MONITORING_URL = "http://bustime.mta.info/api/siri/stop-monitoring.json"

# Routes to track
TRACKED_ROUTES = ['M15', 'BX12', 'B46', 'Q58']

# Database - works in both local and Docker
# Docker sets DB_FILE=/app/data/mta_bus.db via environment
# Local falls back to mta_bus.db in project root
DB_FILE = os.getenv(
    'DB_FILE',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mta_bus.db')
)
READER_DB_FILE = DB_FILE.replace('.db', '_reader.db')

# Pipeline settings
DATA_COLLECTION_INTERVAL_SECONDS = 60
HAVERSINE_DISTANCE_THRESHOLD_METERS = 500
DELAY_THRESHOLD_MINUTES = 5
EARLY_THRESHOLD_MINUTES = -2
