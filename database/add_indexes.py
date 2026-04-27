import sys
sys.path.append('C:/Users/4217m/Desktop/MTA/mta-bus-mvp')
import duckdb
from config import DB_FILE

con = duckdb.connect(DB_FILE)

con.execute("""
    CREATE INDEX IF NOT EXISTS idx_raw_captured_at 
    ON raw_bus_snapshots(captured_at)
""")
con.execute("""
    CREATE INDEX IF NOT EXISTS idx_raw_aimed_arrival 
    ON raw_bus_snapshots(aimed_arrival)
""")
con.execute("""
    CREATE INDEX IF NOT EXISTS idx_arrivals_date 
    ON bus_arrivals(date)
""")
con.execute("""
    CREATE INDEX IF NOT EXISTS idx_arrivals_route 
    ON bus_arrivals(route)
""")
con.execute("""
    CREATE INDEX IF NOT EXISTS idx_bunching_timestamp 
    ON bunching_events(timestamp)
""")

print("All indexes created successfully")
con.close()
