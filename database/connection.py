import duckdb
import time
import sys
import os
from loguru import logger

sys.path.append(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))
from config import DB_FILE

try:
    from database.replica import get_reader_db
    USE_REPLICA = True
except ImportError:
    USE_REPLICA = False


def get_connection(read_only=True, retries=5, delay=0.3):
    """
    Get DuckDB connection with retry on conflict.
    Dashboard always reads from replica.
    Pipeline writes to writer DB directly.
    """
    if read_only:
        from database.replica import get_reader_db
        db_path = get_reader_db()
    else:
        db_path = DB_FILE

    last_error = None
    for attempt in range(retries):
        try:
            return duckdb.connect(db_path, read_only=read_only)
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                logger.warning(
                    f"DB attempt {attempt+1}/{retries} "
                    f"failed on {db_path}: {e}"
                )
                time.sleep(delay)
            else:
                # Last resort: try writer DB directly
                if read_only and db_path != DB_FILE:
                    logger.warning(
                        "Replica failed, trying writer DB"
                    )
                    try:
                        return duckdb.connect(
                            DB_FILE, read_only=True
                        )
                    except Exception as e2:
                        logger.error(
                            f"Writer fallback also failed: {e2}"
                        )
                raise last_error


def safe_query(query, params=None):
    """
    Execute a read-only query safely.
    Always uses reader replica.
    Always closes connection after query.
    Returns DataFrame or None on error.
    """
    con = None
    try:
        con = get_connection(read_only=True)
        if params:
            return con.execute(query, params).df()
        return con.execute(query).df()
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return None
    finally:
        if con:
            try:
                con.close()
            except:
                pass


def safe_write(query, df=None, retries=3):
    """
    Execute a write operation safely.
    Always uses writer DB directly.
    Used by pipeline only — never dashboard.
    """
    for attempt in range(retries):
        con = None
        try:
            con = get_connection(read_only=False)
            if df is not None:
                con.register('write_df', df)
            con.execute(query)
            return True
        except Exception as e:
            logger.warning(
                f"Write attempt {attempt+1} failed: {e}"
            )
            time.sleep(1)
        finally:
            if con:
                try:
                    con.close()
                except:
                    pass
    return False
