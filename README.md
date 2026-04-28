# NYC MTA Bus Reliability Tracker

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![DuckDB](https://img.shields.io/badge/DuckDB-0.9.2-FFF000?style=flat&logo=duckdb&logoColor=black)](https://duckdb.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![pytest](https://img.shields.io/badge/Tests-40%20passing-2ECC71?style=flat&logo=pytest&logoColor=white)](tests/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

> A real-time data engineering pipeline that automatically collects, processes, and analyzes NYC MTA bus performance — detecting delays, ghost buses, and bus bunching across 4 major routes.

---

## Key Findings
*8 days of continuous data collection — 926,551 arrivals analyzed*

| Metric | Value |
|--------|-------|
| System on-time rate | **64.6%** |
| Ghost buses per day | **45 detected** |
| Worst bunching route | **Q58 — 664 events/day (Critical)** |
| Worst stop avg delay | **+16.5 min (Palmetto St/Myrtle Av, Q58)** |
| False positive reduction | **88% (342 events → 40 after 3-layer filter)** |
| Total arrivals analyzed | **926,551+** |

---

## Architecture

```
MTA Bus Time API (SIRI)
        │
        ▼  every 60 seconds
┌─────────────────────┐
│   Ingestion Layer   │  ingestion/ingest.py
│   Python + requests │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   DuckDB Writer     │  mta_bus.db
│  raw_bus_snapshots  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Transform Layer    │  transforms/transform.py
│  · Delay calc       │
│  · Ghost detect     │
│  · Bunch detect     │
└──────────┬──────────┘
           │ atomic copy
           ▼
┌─────────────────────┐     ┌──────────────────────┐
│   DuckDB Writer     │────▶│    Read Replica       │
│   bus_arrivals      │     │  mta_bus_reader.db    │
│   ghost_buses       │     │  dashboard reads here │
│   bunching_events   │     └──────────┬───────────┘
└─────────────────────┘                │
                                       ▼
                            ┌──────────────────────┐
                            │  Streamlit Dashboard  │
                            │  5 interactive pages  │
                            │  localhost:8501       │
                            └──────────────────────┘
```

---

## What We Detect

### Ghost Buses
A bus appears in the MTA app with a promised arrival time then vanishes before reaching the stop — leaving riders stranded with zero warning.

**Detection logic:** Track vehicle presence across API polls. Flag vehicles that disappear while still more than 500m from their promised stop, with a gap of more than 10 minutes.

> Initial count: **15,648 events** (obviously wrong) → After fixing algorithm: **45 credible detections per day**

### Bus Bunching
When buses cluster together instead of staying evenly spaced. You wait 20 minutes then 3 buses arrive at once.

**Detection logic:** Haversine formula calculates great-circle distance between all vehicle pairs on same route and direction. Three quality filters applied:

1. **Direction filter** — same DirectionRef only (eliminates opposite-direction false positives)
2. **Distance filter** — 50m to 500m range (below 50m = GPS noise, above 500m = not bunching)
3. **Duplicate filter** — same pair counted once per 5-minute window

> Initial count: **342 events** → After 3-layer filter: **40 real events** (88% reduction)

### Schedule Delays
Delay in minutes = `expected_arrival - aimed_arrival` from the MTA API, classified into 5 categories: Early, On Time, Slightly Late, Late, Very Late (20+ min).

---

## Dashboard Pages

| Page | What It Shows |
|------|--------------|
| **Overview** | KPI cards, route grades A-F, delay distribution |
| **Ghost Bus Tracker** | Live incidents with vehicle ID, vanish time, distance |
| **Bus Bunching** | Severity bars (Critical/High/Medium/Low), hourly chart |
| **Route Analysis** | Best time to ride, top 5 worst stops, route comparison |
| **Live Map** | Real-time bus positions with colored route markers |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.11 | All pipeline components |
| Database | DuckDB 0.9.2 | Zero-config analytical storage |
| Ingestion | requests + schedule | MTA API polling every 60s |
| Transform | Pandas | Data cleaning and detection |
| Dashboard | Streamlit 1.28 | 5-page web application |
| Charts | Plotly 5.17 | Interactive visualizations |
| Maps | Folium 0.14 | Live GPS bus positions |
| Containers | Docker + Compose | One-command deployment |
| Testing | pytest + pytest-cov | 40 tests, 76% coverage |
| Orchestration | Apache Airflow | Production DAG (Linux/cloud) |
| Logging | Loguru | Structured pipeline logs |

---

## Quick Start with Docker

**Requirements:** Docker Desktop installed

```bash
# 1. Clone repository
git clone https://github.com/Malav4217/MTA.git
cd MTA

# 2. Add your MTA API key
echo "MTA_API_KEY=your_key_here" > .env

# 3. Start everything
docker-compose up -d

# 4. Open dashboard
# http://localhost:8501
```

That's it. The pipeline starts collecting data immediately. Dashboard updates every 60 seconds.

### Get an MTA API Key (free)
1. Visit [bustime.mta.info](http://bustime.mta.info)
2. Click "Developer Resources"
3. Register for a free API key

---

## Local Development Setup

```bash
# Clone and enter directory
git clone https://github.com/Malav4217/MTA.git
cd MTA

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your MTA API key

# Initialize database
python database/schema.py

# Terminal 1 — Run pipeline
python pipeline.py

# Terminal 2 — Run dashboard
streamlit run dashboard/app.py
```

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_data_quality.py -v
pytest tests/test_detection.py -v
```

**Expected output:**
```
tests/test_api.py::TestMTAAPI::test_api_returns_200 PASSED
tests/test_data_quality.py::TestRawDataQuality::test_coordinates_within_nyc_bounds PASSED
tests/test_detection.py::TestHaversineFormula::test_known_distance PASSED
tests/test_pipeline.py::TestReadReplica::test_reader_db_exists PASSED
... 36 more tests ...
======== 40 passed, 1 skipped in 2.66s ========
```

| Test File | Tests | Validates |
|-----------|-------|-----------|
| test_api.py | 5 | MTA API connectivity and response format |
| test_data_quality.py | 8 | Data completeness, ranges, GPS bounds |
| test_detection.py | 11 | Ghost bus and bunching detection logic |
| test_pipeline.py | 11 | Schema, read replica, configuration |

---

## Docker Commands

```bash
# Check container status
docker-compose ps

# Watch pipeline logs live
docker-compose logs -f pipeline

# Watch dashboard logs
docker-compose logs -f dashboard

# Restart pipeline only
docker-compose restart pipeline

# Stop everything
docker-compose down

# Fresh start (deletes all data)
docker-compose down -v

# Rebuild after code changes
docker-compose up --build -d
```

---

## Project Structure

```
MTA/
├── pipeline.py               # Master orchestration (60s loop)
├── config.py                 # API keys, routes, constants
├── requirements.txt          # Dependencies
├── docker-compose.yml        # Container orchestration
├── Dockerfile.pipeline       # Pipeline container
├── Dockerfile.dashboard      # Dashboard container
├── pytest.ini                # Test configuration
│
├── ingestion/
│   └── ingest.py             # MTA API polling
│
├── transforms/
│   └── transform.py          # Delay calc + detection algorithms
│
├── database/
│   ├── schema.py             # Table creation (auto-runs on start)
│   ├── connection.py         # Safe query + retry logic
│   ├── replica.py            # Read replica pattern
│   └── add_indexes.py        # Performance indexes
│
├── dashboard/
│   ├── app.py                # Main router (~30 lines)
│   ├── components/
│   │   ├── sidebar.py        # Navigation + pipeline status
│   │   ├── cards.py          # KPI cards, grade cards, UI
│   │   └── charts.py         # Chart builder functions
│   └── views/
│       ├── overview.py       # Overview page
│       ├── ghost_buses.py    # Ghost Bus Tracker page
│       ├── bunching.py       # Bus Bunching page
│       ├── route_analysis.py # Route Analysis page
│       └── live_map.py       # Live Map page
│
├── airflow/
│   └── dags/
│       └── mta_pipeline_dag.py  # Production Airflow DAG
│
└── tests/
    ├── conftest.py           # Shared fixtures
    ├── test_api.py           # API connectivity tests
    ├── test_data_quality.py  # Data validation tests
    ├── test_detection.py     # Algorithm correctness tests
    └── test_pipeline.py      # Integration tests
```

---

## Airflow DAG (Production)

The pipeline is designed for Apache Airflow deployment with a 4-task DAG:

```
ingest_mta_data → transform_data → update_read_replica → health_check
```

Each task has automatic retry logic with exponential backoff. The DAG file is at `airflow/dags/mta_pipeline_dag.py` and deploys directly to:
- **AWS MWAA** (Managed Airflow)
- **Google Cloud Composer**
- Any Linux server running Airflow

For local development on Windows, `pipeline.py` uses the `schedule` library as a fallback.

---

## Data Quality Engineering

One of the most important aspects of this project was questioning our own numbers.

### Ghost Bus Investigation
| Stage | Count | Action |
|-------|-------|--------|
| Initial algorithm | 15,648/day | Obviously wrong — investigated |
| Root cause found | — | Counting snapshots not completions |
| Fixed algorithm | 45/day | Credible and defensible |
| Test written | — | Prevents regression forever |

### Bunching Investigation
| Stage | Count | Filter Applied |
|-------|-------|---------------|
| Initial detection | 342 | No filters |
| After direction filter | 114 | Same DirectionRef only |
| After 50m minimum | 60 | Eliminates GPS noise |
| After duplicate filter | 40 | 5-minute window per pair |
| **Total reduction** | **88%** | **3-layer quality framework** |

---

## Route Performance Summary

| Route | On-Time % | Grade | Bunching Severity |
|-------|-----------|-------|-------------------|
| BX12 (Bronx) | 68.4% | B | Low (19 events) |
| M15 (Manhattan) | 67.7% | B | High (87 events) |
| B46 (Brooklyn) | 55.5% | C | Critical (156 events) |
| Q58 (Queens) | 37.2% | D | Critical (664 events) |

**Worst stop:** Palmetto St/Myrtle Av on Q58 — **+16.5 min average delay** across **23,728 observations**

---

## Key Engineering Decisions

**Why DuckDB over PostgreSQL?**
Zero configuration, no server process, file-based, excellent Pandas integration, and fast analytical queries. Perfect for a solo data engineering project.

**Why the read replica pattern?**
DuckDB allows only one writer at a time. The dashboard and pipeline both need database access simultaneously. Atomic file copy (shutil.copy2 + os.replace) creates a reader replica with zero downtime — the same pattern as PostgreSQL streaming replication, in 20 lines of Python.

**Why 3-layer bunching filter?**
Initial detection showed 342 events. Investigation revealed three separate false positive sources: opposite-direction buses, GPS noise at 8-26m, and duplicate pair counting. Each filter addressed one root cause specifically.

---

## License

MIT License — see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- MTA Bus Time API for providing free real-time transit data
- DuckDB team for the excellent embedded analytical database
- Streamlit team for making Python dashboards fast to build

---

*Built as a data engineering portfolio project demonstrating real-time pipeline development, data quality engineering, and production-ready containerization.*
