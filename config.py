import os
from dotenv import load_dotenv
from datetime import date

load_dotenv()

# API Configuration
MTA_API_KEY = os.getenv('MTA_API_KEY')
VEHICLE_MONITORING_URL = (
    "http://bustime.mta.info/api/siri/"
    "vehicle-monitoring.json"
)

# Routes to track
TRACKED_ROUTES = ['M15', 'BX12', 'B46', 'Q58']

# Pipeline settings
DATA_COLLECTION_INTERVAL_SECONDS = 60
HAVERSINE_DISTANCE_THRESHOLD_METERS = 500
DELAY_THRESHOLD_MINUTES = 5
EARLY_THRESHOLD_MINUTES = -2

# ─── Smart Database Detection ────────────────────────
# Priority order:
# 1. Explicit env var DB_FILE (Docker sets this)
# 2. Full database exists locally → use full DB
# 3. Reader replica exists locally → use reader
# 4. Sample database → use sample (Streamlit Cloud)

def get_db_file():
    # Docker or explicit override
    if os.getenv('DB_FILE'):
        return os.getenv('DB_FILE')

    # Full local database exists (you running locally)
    if os.path.exists('mta_bus.db'):
        return 'mta_bus.db'

    # Reader replica exists
    if os.path.exists('mta_bus_reader.db'):
        return 'mta_bus_reader.db'

    # Streamlit Cloud — use sample
    if os.path.exists('mta_sample.db'):
        return 'mta_sample.db'

    # Default fallback
    return 'mta_bus.db'


DB_FILE = get_db_file()
READER_DB_FILE = DB_FILE.replace('.db', '_reader.db')

# ─── Smart Date Range Detection ──────────────────────
# If using sample DB → restrict to sample dates
# If using full DB → use today and allow full range

def get_date_config():
    if 'sample' in DB_FILE:
        # Sample database date range
        return {
            'min_date':   date(2026, 4, 18),
            'max_date':   date(2026, 4, 22),
            'start_date': date(2026, 4, 18),
            'end_date':   date(2026, 4, 22),
            'is_sample':  True,
            'label':      'Historical Data (Apr 18-22, 2026)'
        }
    else:
        # Full database — use last 30 days
        today = date.today()
        thirty_days_ago = date(2026, 4, 13)
        return {
            'min_date':   thirty_days_ago,
            'max_date':   today,
            'start_date': thirty_days_ago,
            'end_date':   today,
            'is_sample':  False,
            'label':      'Live Data'
        }

DATE_CONFIG = get_date_config()
