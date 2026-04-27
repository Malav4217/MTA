import shutil
import os
import sys
from loguru import logger

sys.path.append(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))
from config import DB_FILE

READER_DB = DB_FILE.replace('.db', '_reader.db')
TEMP_DB   = DB_FILE.replace('.db', '_reader.db.tmp')


def update_replica():
    """
    Safely copy writer DB to reader replica.
    Atomic copy — reader never unavailable.
    """
    try:
        if not os.path.exists(DB_FILE):
            logger.warning(f"Writer DB not found: {DB_FILE}")
            return False

        # Ensure directory exists (needed in Docker)
        db_dir = os.path.dirname(READER_DB)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        # Atomic copy: write to temp then rename
        shutil.copy2(DB_FILE, TEMP_DB)
        os.replace(TEMP_DB, READER_DB)

        size_mb = os.path.getsize(READER_DB) / 1024 / 1024
        logger.info(f"Read replica updated ({size_mb:.1f} MB)")
        return True

    except Exception as e:
        logger.error(f"Replica update failed: {e}")
        if os.path.exists(TEMP_DB):
            try:
                os.remove(TEMP_DB)
            except:
                pass
        return False


def get_reader_db():
    """Return best available DB for reading."""
    if os.path.exists(READER_DB):
        return READER_DB
    logger.warning("Replica not found, using writer DB")
    return DB_FILE
