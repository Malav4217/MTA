import schedule
import time
import duckdb
from loguru import logger
from config import DB_FILE
from ingestion.ingest import ingestion_job
from transforms.transform import transform_job
from database.replica import update_replica

def pipeline():
    logger.info("Running pipeline...")
    ingestion_job()
    transform_job()
    update_replica()
    logger.info("Pipeline complete")

def archive_old_data():
    """Archive snapshots older than 7 days"""
    con = duckdb.connect(DB_FILE)
    deleted = con.execute("""
        DELETE FROM raw_bus_snapshots 
        WHERE captured_at < NOW() - INTERVAL '7 days'
    """).rowcount
    logger.info(f"Archived {deleted} old snapshots")
    con.close()

# Run every 60 seconds
schedule.every(60).seconds.do(pipeline)

# Archive old data daily at 03:00 AM
schedule.every().day.at("03:00").do(archive_old_data)

if __name__ == "__main__":
    pipeline()  # run immediately on start
    while True:
        schedule.run_pending()
        time.sleep(1)