"""
Simple pipeline runner.
For development use: python pipeline.py
"""
import sys
import os
import schedule
import time
from loguru import logger

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingestion.ingest import ingestion_job
from transforms.transform import transform_job
from database.replica import update_replica


def initialize_database():
    """Create tables if they don't exist. Called once at startup."""
    try:
        from database.schema import create_tables
        create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)


def pipeline():
    """Run one complete pipeline cycle."""
    logger.info("Pipeline starting...")
    try:
        ingestion_job()
        transform_job()
        update_replica()
        logger.info("Pipeline complete")
    except Exception as e:
        logger.error(f"Pipeline error: {e}")


if __name__ == "__main__":
    logger.info("Starting pipeline...")
    initialize_database()

    pipeline()

    schedule.every(60).seconds.do(pipeline)

    while True:
        schedule.run_pending()
        time.sleep(1)
