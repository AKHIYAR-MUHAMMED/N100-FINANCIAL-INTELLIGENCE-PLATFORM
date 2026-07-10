# Sprint 1: Data Ingestion, Quality Foundation & Dashboard (Days 01 – 07)

This repository contains the foundation for **Epic 01: Data Ingestion & ETL** and the **Dashboard Foundation** of the Nifty 100 Analytics project. It includes the setup, normalisation engine, 16 Data Quality (DQ) validation checks, a 14-table SQLite database schema, a custom ratio calculator, automatic data quality reporting, and an interactive dark-themed web dashboard served via a local API.

---

## 📂 Project Structure

```text
nifty100/
├── data/
│   ├── raw/                 # Staging area for raw incoming Excel sheets (12 files)
│   └── processed/           # Normalized, staged CSV files
├── db/
│   └── schema.sql           # SQLite schema defining 14 tables
├── notebooks/
│   └── exploratory_queries.sql # 10 SQL queries for data verification & audits
├── output/
│   ├── load_audit.csv       # Audit log for processed/loaded files
│   ├── validation_failures.csv # Logs for DQ rule warnings and rejections
│   └── report.md            # Auto-generated markdown DQ report
├── src/
│   ├── dashboard/
│   │   └── index.html       # Dark-themed glassmorphism HTML dashboard
│   ├── etl/
│   │   ├── loader.py        # Orchestrator & transactional database loader
│   │   ├── normaliser.py    # Year and ticker cleaning functions
│   │   ├── ratios.py        # ROE, Debt-to-Equity, PE, and PB ratios calculator
│   │   └── validator.py     # SchemaValidator containing 16 DQ rules
│   ├── api_server.py        # API server hosting static dashboard & data endpoints
│   ├── database.py          # SQLite connections & schema initializer
│   ├── report.py            # Script generating the markdown audit report
│   └── __init__.py
├── tests/
│   └── etl/
│       ├── test_database.py # Database constraint checks and migration tests
│       ├── test_loader.py   # Full ETL pipeline integration tests
│       ├── test_normaliser.py # Year and ticker cleaning unit tests
│       └── test_validator.py # 16 DQ validation engine rules unit tests
├── .env.example             # Configuration template
├── .flake8                  # Style configuration rules
├── Makefile                 # Automated developer commands
└── requirements.txt         # Project library dependencies
```

---

## 🛠️ Sprint Deliverables (Day 01 – Day 07)

### Day 01: Environment Setup
- Established standard folder paths (`data/raw`, `data/processed`, `db`, `src/etl`, `tests/etl`, `notebooks`).
- Configured virtual environment dependencies inside `.venv/`.
- Setup `.env` configuration file mapping `DB_PATH=data/db/nifty100.db`.

### Day 02: Excel Loader & Normaliser
- **Ticker Normalisation**: Converts ticker strings to uppercase, strips whitespace, and removes exchange suffixes (e.g. `.NS`, `.BO`, `.BSE`, `.NSE`). Converts whole floats (e.g., `12345.0`) to standard string representations.
- **Year Normalisation**: Converts any string, numeric, or datetime year value into a 4-digit integer. Converts 2-digit years to 4-digit using a pivot boundary of `50` (years `< 50` map to `20XX`, `>= 50` map to `19XX`).

### Day 03: Schema Validator (16 DQ Rules)
Validates incoming worksheets against 16 distinct rules. Rule severity divides into:
- **CRITICAL** (Drops/Rejects the row to preserve transactional database integrity):
  - `DQ-01`: Duplicate primary keys (e.g. duplicates in companies or duplicate ticker/date in prices).
  - `DQ-02`: Null primary key values or invalid date/year formats.
  - `DQ-03`: Foreign Key referential integrity (refers to ticker that exists in companies master).
  - `DQ-09`: Negative stock prices (open, high, low, close must be positive).
- **WARNING** (Logs the failure but permits row insertion to the database):
  - `DQ-04`: Balance Sheet balance discrepancy (warns if assets != liabilities + equity, or discrepancy is $\ge 1\%$).
  - `DQ-05`: OPM cross-check (warns if OPM reported differs from operating profit / sales by $> 5\%$).
  - `DQ-06`: Sales/Revenue positive check (warns if revenue $\le 0$).
  - `DQ-07`: Cash flow reconciliation (warns if ending cash != beginning cash + net change).
  - `DQ-08`: Abnormal tax rate (warns if calculated tax rate is not between 0% and 100%).
  - `DQ-09`: Dividend cap check (warns if dividend per share value is $> 500$).
  - `DQ-10`: Website URL validation (checks format of company website).
  - `DQ-11`: EPS sign check (checks if EPS sign matches Net Income sign).
  - `DQ-12`: Ticker exchange suffix validation (validates .NS, .BO, .BSE, .NSE suffixes).
  - `DQ-13`: Stock price coverage and ratio leverage boundary checks.
  - `DQ-14`: Positive trading volume.
  - `DQ-15`: Stock price consistency (High is maximum, Low is minimum).
  - `DQ-16`: Logical profit ordering (Gross Profit $\ge$ Operating Profit $\ge$ Net Income).

All failures are recorded in the SQLite `validation_failures` table and exported to `output/validation_failures.csv`.

### Day 04: SQLite Database Schema
- Relational schema inside `db/schema.sql` incorporating primary keys, foreign keys with ON DELETE CASCADE, and column boundary constraints (`CHECK`).
- Configured connection handlers enforcing referential integrity with `PRAGMA foreign_keys = ON;`.

### Day 05: Core Schema Refinement & Financial Ratios Calculator
- Extended database schema to 14 tables including placeholder fundamental analysis entities: `analysis`, `documents`, `prosandcons`, `peer_groups`.
- Core financial tables renamed to align with standard terminology: `profitandloss`, `balancesheet`, `cashflow`, and `financial_ratios`.
- Developed [ratios.py](file:///d:/Internship/Bluestocks/TASK2/src/etl/ratios.py) to calculate customised ROE, Debt-to-Equity, PE Ratio, and PB Ratio using financial statements and stock prices, with price fallback logic for non-overlapping years.

### Day 06: Automated Reports & Makefile Integration
- Created [report.py](file:///d:/Internship/Bluestocks/TASK2/src/report.py) to automatically compile database row counts, source file ingestion status, validation failure logs, and integrity validation results into `output/report.md`.
- Staged automation targets inside the `Makefile` (`load`, `ratios`, `report`, `dashboard`, `api`, `clean`).

### Day 07: Dark-Themed Glassmorphic API/Dashboard
- Built [api_server.py](file:///d:/Internship/Bluestocks/TASK2/src/api_server.py) to start a local server at `http://localhost:8000/`.
- Implemented a premium front-end dashboard [index.html](file:///d:/Internship/Bluestocks/TASK2/src/dashboard/index.html) featuring:
  - Real-time data summaries and KPI cards.
  - Interactive sector distribution doughnut chart and row count bar chart (using Chart.js).
  - Searchable companies directory with sector filter logic.
  - Searchable data quality failures logs.

---

## ⚙️ Automated Developer Commands (Makefile)

A `Makefile` is configured in the root directory for automated task execution:

| Command | Action |
| --- | --- |
| `make setup` | Automatically generates local folder paths and initializes the `venv` virtual environment. |
| `make install` | Installs all Python dependencies listed in `requirements.txt`. |
| `make format` | Runs `black` formatting and sorts imports using `isort` across `src` and `tests`. |
| `make lint` | Performs style auditing using `flake8` and static type checking using `mypy`. |
| `make test` | Runs the unit test suite via `pytest` and logs code coverage. |
| `make load` | Runs the ETL ingestion loader to populate the database from the 12 raw Excel files. |
| `make ratios` | Executes the ratios calculator to compute custom PE, PB, ROE, and Debt-to-Equity ratios. |
| `make report` | Generates the markdown Data Quality Audit Report. |
| `make dashboard` / `make api` | Launches the local dashboard web page and API server at `http://localhost:8000`. |
| `make clean` | Purges python caches (`__pycache__`), environment locks, and local test coverage metrics. |

---

## 🚀 Running the Pipeline locally

### 1. Ingestion, Ratios Calculation & Reporting
Run these targets sequentially to completely ingest raw Excel sheets, calculate financial ratios, and compile the data quality report:
```bash
# Ingest Excel sheets into SQLite database
venv/Scripts/python -m src.etl.loader

# Compute PE, PB, ROE, and Debt-to-Equity ratios
venv/Scripts/python -m src.etl.ratios

# Generate the data quality markdown report
venv/Scripts/python -m src.report
```

### 2. Run Test Suite
Run the test cases to verify normalisation, validation checks, database constraint integrity, and database insertion coverage:
```bash
venv/Scripts/python -m pytest tests/ --cov=src
```

### 3. Launch Web Dashboard
Start the local server and open your browser at `http://localhost:8000`:
```bash
venv/Scripts/python -m src.api_server
```
