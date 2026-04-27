from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
PROJECT_ROOT = "C:/Users/4217m/Desktop/MTA/mta-bus-mvp"
sys.path.insert(0, PROJECT_ROOT)

# ── Default arguments ────────────────────────
default_args = {
    'owner':                     'mta-pipeline',
    'depends_on_past':           False,
    'start_date':                days_ago(1),
    'retries':                   3,
    'retry_delay':               timedelta(seconds=30),
    'retry_exponential_backoff': True,
    'email_on_failure':          False,
    'email_on_retry':            False,
}

# ── DAG definition ───────────────────────────
dag = DAG(
    dag_id='mta_bus_reliability_pipeline',
    default_args=default_args,
    description='Real-time MTA Bus Reliability Pipeline',
    schedule_interval=timedelta(minutes=1),
    catchup=False,
    max_active_runs=1,
    tags=['transit', 'real-time', 'nyc', 'mta'],
)

# ── Task functions ───────────────────────────

def run_ingestion(**context):
    """
    Task 1: Fetch live bus data from MTA API
    and save to raw_bus_snapshots table.
    """
    from ingestion.ingest import ingestion_job
    ingestion_job()
    print(f"Ingestion completed at {datetime.now()}")


def run_transform(**context):
    """
    Task 2: Clean data, calculate delays,
    detect ghost buses and bunching events.
    """
    from transforms.transform import transform_job
    transform_job()
    print(f"Transform completed at {datetime.now()}")


def run_replica_update(**context):
    """
    Task 3: Copy writer DB to reader replica
    so dashboard reads fresh data without
    conflicting with the pipeline writer.
    """
    from database.replica import update_replica
    success = update_replica()
    if not success:
        raise Exception("Replica update failed")
    print(f"Replica updated at {datetime.now()}")


def run_health_check(**context):
    """
    Task 4: Verify pipeline ran correctly
    by checking row counts and data freshness.
    """
    import duckdb
    from config import DB_FILE
    from datetime import datetime

    con = duckdb.connect(DB_FILE, read_only=True)

    # Check 1: Recent snapshots exist
    latest = con.execute("""
        SELECT MAX(captured_at) as latest
        FROM raw_bus_snapshots
    """).fetchone()[0]

    if latest:
        age = (datetime.now() - latest).total_seconds()
        print(f"Latest snapshot: {age:.0f} seconds ago")
        if age > 120:
            raise Exception(
                f"Data is stale: {age:.0f} seconds old"
            )

    # Check 2: Arrivals being processed
    today_count = con.execute("""
        SELECT COUNT(*) FROM bus_arrivals
        WHERE date = CURRENT_DATE
    """).fetchone()[0]

    print(f"Today's arrivals: {today_count:,}")

    # Check 3: All routes have data
    route_counts = con.execute("""
        SELECT route, COUNT(*) as count
        FROM raw_bus_snapshots
        WHERE captured_at >= NOW() - INTERVAL '5 minutes'
        GROUP BY route
    """).df()

    print(f"Active routes: {len(route_counts)}")
    print(route_counts.to_string())

    con.close()
    print("Health check passed!")


# ── Define tasks ─────────────────────────────

ingest_task = PythonOperator(
    task_id='ingest_mta_data',
    python_callable=run_ingestion,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=run_transform,
    dag=dag,
)

replica_task = PythonOperator(
    task_id='update_read_replica',
    python_callable=run_replica_update,
    dag=dag,
)

health_task = PythonOperator(
    task_id='health_check',
    python_callable=run_health_check,
    dag=dag,
)

# ── Task dependencies ────────────────────────
# ingest → transform → update replica → health check
ingest_task >> transform_task >> replica_task >> health_task
