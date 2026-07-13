# Nifty 100 Analytics & Financial Intelligence Platform

This repository contains a full-stack, data-driven financial analysis pipeline for Nifty 100 stocks. The project is split into two completed sprints: **Sprint 1 (Data Ingestion & Quality Foundation)** and **Sprint 2 (Financial Ratio Engine)**. It processes raw financial statements and stock price history for 92 companies across all available years, stores them in SQLite, computes 50+ KPIs, handles complex edge cases, and logs data quality and formula anomalies.

---

## 📂 Project Structure

```text
nifty100/
├── data/
│   ├── raw/                 # Staging area for raw incoming Excel sheets (12 files)
│   └── processed/           # Normalized, staged CSV files
├── db/
│   └── schema.sql           # SQLite schema defining 14 tables (updated for Sprint 2)
├── notebooks/
│   └── exploratory_queries.sql # 10 SQL queries for data verification & audits
├── output/
│   ├── load_audit.csv       # Audit log for processed/loaded files
│   ├── validation_failures.csv # Logs for DQ rule warnings and rejections
│   ├── capital_allocation.csv # 8-pattern Capital Allocation classifier output (Sprint 2)
│   ├── ratio_edge_cases.log # Edge case logging for ratio variances (Sprint 2)
│   └── report.md            # Auto-generated markdown DQ report
├── src/
│   ├── analytics/           # KPI calculations library (Sprint 2)
│   │   ├── cagr.py          # CAGR engine with 6 edge cases
│   │   ├── cashflow_kpis.py # FCF, CFO Quality, CapEx Intensity, Allocation patterns
│   │   └── ratios.py        # Profitability, Leverage, and Efficiency ratios
│   ├── dashboard/
│   │   └── index.html       # Dark-themed glassmorphism HTML dashboard
│   ├── etl/
│   │   ├── loader.py        # Orchestrator & transactional database loader
│   │   ├── normaliser.py    # Year and ticker cleaning functions
│   │   ├── ratios.py        # Ratio engine pipeline orchestrator
│   │   └── validator.py     # SchemaValidator containing 16 DQ rules
│   ├── api_server.py        # API server hosting static dashboard & data endpoints
│   ├── database.py          # SQLite connections & schema initializer
│   ├── report.py            # Script generating the markdown audit report
│   └── __init__.py
├── tests/
│   ├── etl/
│   │   ├── test_database.py # Database constraint checks and migration tests
│   │   ├── test_loader.py   # Full ETL pipeline integration tests
│   │   ├── test_normaliser.py # Year and ticker cleaning unit tests
│   │   └── test_validator.py # 16 DQ validation engine rules unit tests
│   └── kpi/
│       └── test_kpi_formulas.py # 32 KPI formula unit tests (Sprint 2)
├── .env.example             # Configuration template
├── .flake8                  # Style configuration rules
├── Makefile                 # Automated developer commands
└── requirements.txt         # Project library dependencies
```

---

## 🛠️ Sprint Deliverables

### Sprint 1: Data Ingestion & Quality Foundation (Days 01 – 07)
- **Excel Ingestion & Normalisation**: Standardized incoming Excel sheets, performing ticker suffix cleanups and year-standardization using a pivot-boundary of 50.
- **Schema Validator**: Built 16 distinct Data Quality rules checking primary keys, foreign keys, logical ordering of profits, and out-of-bound variables.
- **SQLite Database Ingestion**: Configured schema in `db/schema.sql` and loaded all processed tables into SQLite.
- **HTML Dashboard & API Server**: Built a dark-themed glassmorphism web interface showing company listings, DQ failures, and sector breakdowns via a local API.

### Sprint 2: Financial Ratio Engine (Days 08 – 14)
- **Profitability Ratios (Day 08)**:
  - Net Profit Margin (`net_profit / sales * 100`).
  - Operating Profit Margin (`operating_profit / sales * 100`), verified against raw OPM field (logs variance > 1%).
  - Return on Equity (`net_profit / (equity_capital + reserves) * 100`).
  - Return on Capital Employed (`EBIT / (equity + reserves + borrowings) * 100`). Uses dynamic sector-relative benchmarks for the `Financials` broad sector.
  - Return on Assets (`net_profit / total_assets * 100`).
- **Leverage & Efficiency Ratios (Day 09)**:
  - Debt-to-Equity (`borrowings / (equity + reserves)`). Adds a `high_leverage_flag` if D/E > 5 for non-Financials.
  - Interest Coverage Ratio (`(operating_profit + other_income) / interest`). Returns `None` and labels as `Debt Free` if interest is 0. Adds warning flag if ICR < 1.5.
  - Net Debt (`borrowings - investments` using `ending_cash` as liquid asset proxy).
  - Asset Turnover (`sales / total_assets`).
- **CAGR Engine (Day 10)**:
  - Computes 3-year, 5-year, and 10-year windows for Revenue, PAT (net profit), and EPS.
  - Handles 6 edge cases:
    - *Positive to Positive*: Calculates CAGR normally.
    - *Positive to Negative/Zero*: Returns `None` with flag `DECLINE_TO_LOSS`.
    - *Negative to Positive/Zero*: Returns `None` with flag `TURNAROUND`.
    - *Negative to Negative*: Returns `None` with flag `BOTH_NEGATIVE`.
    - *Zero Base*: Returns `None` with flag `ZERO_BASE`.
    - *Insufficient Data*: Returns `None` with flag `INSUFFICIENT`.
- **Cash Flow KPIs & Capital Allocation Classifier (Day 11)**:
  - Free Cash Flow (`operating_activity + investing_activity`).
  - CFO Quality Score (`CFO / PAT` rolling 5-year average), classified into *High Quality*, *Moderate*, or *Accrual Risk*.
  - CapEx Intensity (`abs(investing_activity) / sales * 100`), classified into *Asset Light*, *Moderate*, or *Capital Intensive*.
  - FCF Conversion Rate (`FCF / operating_profit * 100`).
  - **Capital Allocation Sign pattern (CFO, CFI, CFF)**: Classifies company-years into 8 pattern labels: `Reinvestor`, `Shareholder Returns`, `Liquidating Assets`, `Distress Signal`, `Growth Funded by Debt`, `Cash Accumulator`, `Pre-Revenue`, or `Mixed`.
- **SQLite Database Population (Day 12)**:
  - Populates 40+ KPI and CAGR columns in the `financial_ratios` table across **1,276 rows** (exceeding the Sprint 2 DOD of $\ge 1,100$ rows).
- **Edge-Case Logging (Day 13)**:
  - Performs cross-checks for ROE, ROCE, and OPM and logs anomalies with categorization (`formula discrepancy` or `data source issue`) into `output/ratio_edge_cases.log`. Logs specific anomalous cases (such as the TCS ROE anomaly of 0.52%).
- **Verification & Review (Day 14)**:
  - Added 32 KPI formula unit tests. Total test suite counts **113 tests passing successfully (0 failures)**.
  - Validated stock screener query (`ROE > 15% and D/E < 1` on display values) returning exactly **41 matching companies** (within the target range of 15 to 50).

---

## ⚙️ Automated Developer Commands (Makefile)

| Command | Action |
| --- | --- |
| `make setup` | Automatically generates local folder paths and initializes the `venv` virtual environment. |
| `make install` | Installs all Python dependencies listed in `requirements.txt`. |
| `make format` | Runs `black` formatting and sorts imports using `isort` across `src` and `tests`. |
| `make lint` | Performs style auditing using `flake8` and static type checking using `mypy`. |
| `make test` | Runs all 113 unit tests via `pytest` and logs code coverage. |
| `make load` | Runs the ETL ingestion loader to populate the database from the 12 raw Excel files. |
| `make ratios` | Executes the ratios engine to compute PE, PB, ROE, D/E, and all Sprint 2 KPIs. |
| `make report` | Generates the data quality markdown report. |
| `make dashboard` / `make api` | Launches the local dashboard web page and API server at `http://localhost:8000`. |
| `make clean` | Purges python caches (`__pycache__`), environment locks, and local test coverage metrics. |

---

## 🚀 Running the Pipeline locally

### 1. Execute Ingestion, Ratio Engine & Reporting
Run these targets sequentially to completely ingest raw Excel sheets, calculate the financial ratios, and compile reports:
```bash
# Ingest Excel sheets into SQLite database
venv/Scripts/python -m src.etl.loader

# Compute and insert PE, PB, ROE, CAGR, Cash Flow KPIs, and Capital Allocation patterns
venv/Scripts/python -m src.etl.ratios

# Generate the data quality markdown report
venv/Scripts/python -m src.report
```

### 2. Run the full Test Suite
Run the test cases to verify normalisation, validation rules, database constraint integrity, and KPI formulas:
```bash
venv/Scripts/python -m pytest tests/ --cov=src
```

### 3. Launch the Web Dashboard
Start the local server and open your browser at `http://localhost:8000`:
```bash
venv/Scripts/python -m src.api_server
```
