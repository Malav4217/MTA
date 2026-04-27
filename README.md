# 🚌 NYC MTA Bus Reliability Tracker

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![DuckDB](https://img.shields.io/badge/DuckDB-0.9.2-yellow)](https://duckdb.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-red?logo=streamlit)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-40%20passing-brightgreen)](tests/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> A real-time data engineering pipeline that
> automatically collects, processes, and analyzes
> NYC MTA bus performance data — detecting delays,
> ghost buses, and bus bunching across 4 major routes.

---

## 📊 Key Findings
*(8 days of continuous data collection)*

| Metric | Value |
|--------|-------|
| Total arrivals analyzed | 926,551+ |
| System on-time rate | 64.6% |
| Worst stop avg delay | +16.5 min (Palmetto St/Myrtle Av, Q58) |
| Ghost buses detected | 45 per day |
| Worst bunching route | Q58 — 664 events/day (Critical) |
| False positive reduction | 88% via 3-layer quality filter |

---

## 🏗️ Architecture

```
MTA Bus Time API (SIRI)
        │
        ▼ every 60 seconds
┌───────────────────┐
│  Ingestion Layer  │  ingestion/ingest.py
│  Python + requests│
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│   DuckDB Writer   │  mta_bus.db
│  raw_bus_snapshots│
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Transform Layer   │  transforms/transform.py
│  • Delay calc     │
│  • Ghost detect   │
│  • Bunch detect   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐     ┌──────────────────┐
│  DuckDB Writer    │────▶│  Read Replica    │
│  bus_arrivals     │copy │  mta_bus_reader  │
│  ghost_buses      │     │  (dashboard uses)│
│  bunching_events  │     └────────┬─────────┘
└───────────────────┘              │
                                   ▼
                         ┌──────────────────┐
                         │ Streamlit Dashboard│
                         │  5 interactive    │
                         │  pages — live     │
                         └──────────────────┘
```

---

## 🔍 What We Detect

### 👻 Ghost Buses
A bus that appears in the MTA app with a
promised arrival time but vanishes before
reaching the stop — leaving riders stranded.

**Detection:** Track vehicle presence across
API polls. Flag vehicles that disappear while
still >500m from their promised stop.

### 🚌 Bus Bunching
When buses on the same route cluster together
instead of staying evenly spaced. You wait
20 minutes then 3 buses arrive at once.

**Detection:** Haversine formula calculates
distance between all vehicle pairs on same
route and direction. Flag pairs 50-500m apart.

**3-Layer Quality Filter:**
1. Direction filter — no false positives from
   buses traveling opposite directions
2. Duplicate filter — same pair not counted
   twice within 5-minute window
3. Minimum distance — 50m threshold eliminates
   GPS noise (reduced false positives by 88%)

---

## 🖥️ Dashboard Pages

| Page | What It Shows |
|------|---------------|
| Overview | KPI cards, route grades, delay distribution |
| Ghost Bus Tracker | Incidents with vehicle ID, time, distance |
| Bus Bunching | Severity bars, hourly chart |
| Route Analysis | Best time to ride, worst stops, comparison |
| Live Map | Real-time bus positions with route filter |

---

## ⚙️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Language | Python 3.11 | Everything |
| Database | DuckDB 0.9.2 | Analytical storage |
| Ingestion | requests + schedule | MTA API polling |
| Transform | Pandas | Data cleaning + detection |
| Dashboard | Streamlit | Web application |
| Charts | Plotly | Interactive visualizations |
| Maps | Folium | Live GPS map |
| Containers | Docker + Compose | Deployment |
| Testing | pytest + pytest-cov | 40 tests, 76% coverage |
| Orchestration | Apache Airflow DAG | Production ready |
| Logging | Loguru | Structured pipeline logs |

---

## 🐳 Quick Start with Docker

**Requirements:** Docker Desktop installed

```bash
# 1. Clone repository
git clone https://github.com/yourusername/mta-bus-tracker
cd mta-bus-tracker

# 2. Add your MTA API key
echo "MTA_API_KEY=your_key_here" > .env

# 3. Start everything
docker-compose up -d

# 4. Open dashboard
open http://localhost:8501
```

That's it. Pipeline starts collecting data
immediately. Dashboard updates every 60 seconds.

---

## 💻 Local Development Setup

```bash
# Clone and enter directory
git clone https://github.com/yourusername/mta-bus-tracker
cd mta-bus-tracker

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your MTA API key

# Initialize database
python database/schema.py

# Run pipeline (terminal 1)
python pipeline.py

# Run dashboard (terminal 2)
streamlit run dashboard/app.py
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_data_quality.py -v
pytest tests/test_detection.py -v
pytest tests/test_api.py -v

# Expected: 40 passed, 1 skipped
```

**Test Coverage:**

| Test File | Tests | What It Validates |
|-----------|-------|-------------------|
| test_api.py | 5 | MTA API connectivity |
| test_data_quality.py | 8 | Data completeness and ranges |
| test_detection.py | 11 | Ghost bus and bunching logic |
| test_pipeline.py | 11 | Schema, replica, configuration |

---

## 🐳 Docker Commands

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

## 📁 Project Structure

```
mta-bus-mvp/
├── pipeline.py              # Master orchestration
├── config.py                # Settings and constants
├── requirements.txt         # Dependencies
├── docker-compose.yml       # Container orchestration
├── Dockerfile.pipeline      # Pipeline container
├── Dockerfile.dashboard     # Dashboard container
│
├── ingestion/
│   └── ingest.py           # MTA API polling
│
├── transforms/
│   └── transform.py        # Detection algorithms
│
├── database/
│   ├── schema.py           # Table creation
│   ├── connection.py       # Connection manager
│   ├── replica.py          # Read replica pattern
│   └── add_indexes.py      # Performance indexes
│
├── dashboard/
│   ├── app.py              # Main router (30 lines)
│   ├── components/
│   │   ├── sidebar.py      # Navigation + status
│   │   ├── cards.py        # UI components
│   │   └── charts.py       # Chart builders
│   └── views/
│       ├── overview.py     # Overview page
│       ├── ghost_buses.py  # Ghost Bus page
│       ├── bunching.py     # Bunching page
│       ├── route_analysis.py # Analysis page
│       └── live_map.py     # Live Map page
│
├── airflow/
│   └── dags/
│       └── mta_pipeline_dag.py  # Production DAG
│
└── tests/
    ├── conftest.py          # Shared fixtures
    ├── test_api.py          # API tests
    ├── test_data_quality.py # Data validation
    ├── test_detection.py    # Algorithm tests
    └── test_pipeline.py     # Integration tests
```

---

## 🚀 Production Architecture

The pipeline is designed for Apache Airflow
deployment on Linux/cloud infrastructure.

The DAG (`airflow/dags/mta_pipeline_dag.py`)
defines 4 tasks with automatic retry:

```
ingest_mta_data
      │
      ▼
transform_data
      │
      ▼
update_read_replica
      │
      ▼
health_check
```

Deploy to: AWS MWAA, Google Cloud Composer,
or any Linux server running Airflow.

---

## 📈 Data Quality Approach

Initial ghost bus detection showed 15,648 events.
After investigation we found the algorithm was
counting every raw snapshot instead of tracking
vehicle completion.

Initial bunching detection showed 342 events for B46.
After applying direction filtering, duplicate removal,
and 50m minimum distance threshold — the real count
was 40 (88% false positive reduction).

This iterative quality improvement process is
documented in the test suite which now prevents
these issues from reoccurring.

---

## 🔑 Getting an MTA API Key

1. Visit http://bustime.mta.info
2. Click "Developer Resources"
3. Register for a free API key
4. Add to your .env file

---

## 📄 License

MIT License — see LICENSE file for details.

---

## 🙏 Acknowledgments

- MTA Bus Time API for providing real-time data
- DuckDB team for the excellent analytical database
- Streamlit team for the dashboard framework

---

*Built as a data engineering portfolio project
demonstrating real-time pipeline development,
data quality engineering, and production-ready
containerization.*
