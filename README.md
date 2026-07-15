# Nifty 100 Analytics & Financial Intelligence Platform

This repository contains a full-stack, data-driven financial analysis pipeline for Nifty 100 stocks. The project is split into three completed sprints:
1. **Sprint 1 (Data Ingestion & Quality Foundation)**
2. **Sprint 2 (Financial Ratio Engine)**
3. **Sprint 3 (Stock Screener & Peer/Competitor Analysis)**

It processes raw financial statements and stock price history for 92 companies across all available years, stores them in SQLite, computes 50+ KPIs, runs a custom-configured stock screening engine, ranks companies relative to industry peers, and visualizes financial performance via automatically generated radar charts and a web dashboard.

---

## 📂 Project Structure

```text
nifty100/
├── config/
│   └── screener_config.yaml # Preset filters thresholds & metric mappings
├── data/
│   ├── raw/                 # Staging area for raw incoming Excel sheets (12 files + peer_groups.xlsx)
│   └── processed/           # Normalized, staged CSV files
├── db/
│   └── schema.sql           # SQLite schema defining 15 tables (updated for peer percentiles)
├── notebooks/
│   └── exploratory_queries.sql # SQL queries for database verification & audits
├── output/
│   ├── load_audit.csv       # Audit log for processed/loaded files
│   ├── validation_failures.csv # Logs for DQ rule warnings and rejections
│   ├── capital_allocation.csv # 8-pattern Capital Allocation classifier output (Sprint 2)
│   ├── ratio_edge_cases.log # Edge case logging for ratio variances (Sprint 2)
│   ├── report.md            # Auto-generated markdown DQ report (Sprint 1)
│   ├── screener_output.xlsx # 6-preset Stock Screener output (with conditional colors) (Sprint 3)
│   └── peer_comparison.xlsx # 11-sheet Peer Comparison output (with percentile ranks) (Sprint 3)
├── reports/
│   └── radar_charts/        # 92 Generated radar charts / standalone bar charts (png) (Sprint 3)
├── scripts/
│   └── generate_peer_groups.py # Script to generate peer_groups.xlsx mapping
├── src/
│   ├── analytics/           # Calculation modules library
│   │   ├── cagr.py          # CAGR engine with 6 edge cases (Sprint 2)
│   │   ├── cashflow_kpis.py # FCF, CFO Quality, CapEx Intensity, Allocation patterns (Sprint 2)
│   │   ├── peer.py          # PeerAnalyzer with percentile ranking and radar charts (Sprint 3)
│   │   └── ratios.py        # Profitability, Leverage, and Efficiency ratios (Sprint 2)
│   ├── dashboard/
│   │   └── index.html       # Dark-themed glassmorphism HTML dashboard
│   ├── etl/
│   │   ├── loader.py        # Ingestion orchestrator & transactional DB loader
│   │   ├── normaliser.py    # Year and ticker cleaning functions
│   │   ├── ratios.py        # Ratio engine pipeline orchestrator
│   │   └── validator.py     # SchemaValidator containing 16 DQ rules
│   ├── screener/
│   │   └── engine.py        # Stock Screener engine (Winsorisation, Excel generator) (Sprint 3)
│   ├── api_server.py        # API server hosting static dashboard & data endpoints
│   ├── database.py          # SQLite connections & schema initializer
│   ├── report.py            # Markdown DQ report builder
│   └── __init__.py
├── tests/
│   ├── etl/
│   │   ├── test_database.py # Database constraint checks and migration tests
│   │   ├── test_loader.py   # Full ETL pipeline integration tests
│   │   ├── test_normaliser.py # Year and ticker cleaning unit tests
│   │   └── test_validator.py # 16 DQ validation engine rules unit tests
│   ├── kpi/
│   │   └── test_kpi_formulas.py # 32 KPI formula unit tests (Sprint 2)
│   ├── test_peer.py         # 4 Peer analyzer unit tests (Sprint 3)
│   └── test_screener.py     # 5 Stock screener unit tests (Sprint 3)
├── .env.example             # Configuration template
├── .flake8                  # Style configuration rules
├── Makefile                 # Automated developer commands
└── requirements.txt         # Project library dependencies
```

---

## 🛠️ Sprint Deliverables

### Sprint 1: Data Ingestion & Quality Foundation (Days 01 – 07)
- **Excel Ingestion & Normalisation**: Standardized incoming Excel sheets, performing ticker suffix cleanups (`.NS`, `.BO`) and year-standardization using a pivot-boundary of 50.
- **Schema Validator**: Built 16 distinct Data Quality rules checking primary keys, foreign keys, logical ordering of profits, and out-of-bound variables.
- **SQLite Database Ingestion**: Configured schema in `db/schema.sql` and loaded all processed tables into SQLite.
- **HTML Dashboard & API Server**: Built a dark-themed glassmorphism web interface showing company listings, DQ failures, and sector breakdowns via a local API.

### Sprint 2: Financial Ratio Engine (Days 08 – 14)
- **Profitability Ratios**: NPM, OPM, ROE, ROCE (with dynamic sector benchmarks), and ROA.
- **Leverage & Efficiency Ratios**: Debt-to-Equity (with non-Financials high leverage flags), Interest Coverage Ratio (handling debt-free edge cases and warnings), Net Debt, and Asset Turnover.
- **CAGR Engine**: Computes 3-year, 5-year, and 10-year windows for Revenue, PAT (net profit), and EPS. Handles 6 edge cases (`DECLINE_TO_LOSS`, `TURNAROUND`, `BOTH_NEGATIVE`, `ZERO_BASE`, `INSUFFICIENT`, normal case) and stores CAGR flags.
- **Cash Flow KPIs & Capital Allocation Classifier**: CFO Quality Score (rolling 5-year average), CapEx Intensity, FCF Conversion, and the 8-pattern Capital Allocation classifier (`Reinvestor`, `Shareholder Returns`, `Liquidating Assets`, `Distress Signal`, `Growth Funded by Debt`, `Cash Accumulator`, `Pre-Revenue`, or `Mixed`).
- **Edge-Case Logging**: Logs computed ratio variances (OPM diff > 1%, ROCE/ROE variance > 5%, TCS ROE anomaly) to `output/ratio_edge_cases.log`.

### Sprint 3: Stock Screener & Peer/Competitor Analysis (Days 15 – 21)
- **Winsorised & Sector-Relative Composite Quality Score**:
  - Computes a dynamic composite quality score (0–100) based on winsorising (clipping outlier metrics to 10th and 90th percentiles inside each sector) and calculating a weighted index:
    - **Profitability (35%)**: ROE (15%), ROCE (10%), NPM (10%)
    - **Cash Flow Metrics (30%)**: 5-Year FCF CAGR (15%), CFO/PAT Ratio (10%), FCF Positive Flag (5%)
    - **Growth & Safety (35%)**: 5-Year Revenue CAGR (10%), 5-Year PAT CAGR (10%), Debt-to-Equity (10%), Interest Coverage Ratio (5%)
- **Stock Screener Presets**:
  - Evaluates 6 configured screeners from `config/screener_config.yaml`:
    1. **Quality Compounder**: High ROE (>15%), low debt (D/E < 1.0), positive cash flows, steady growth.
    2. **Value Pick**: Low valuation (PE < 20, PB < 3), reasonable debt (< 2.0), dividend yield (> 1.0%).
    3. **Growth Accelerator**: High growth (PAT CAGR > 20%, Rev CAGR > 15%), manageable debt (< 2.0).
    4. **Dividend Champion**: High dividend yield (> 2%), sustainable payout ratio (< 80%), positive FCF.
    5. **Debt-Free Blue Chip**: No debt (D/E = 0), strong ROE (> 12%), large scale sales (> 5,000 Cr).
    6. **Turnaround Watch**: Improving sales (3-Yr Rev CAGR > 10%), positive FCF, declining D/E ratio.
  - Generates highly formatted output at `output/screener_output.xlsx` with conditional color formatting (pastel Green for passed filters, pastel Red for failed filters).
- **Peer Percentile Ranking**:
  - Groups 92 companies into distinct peer groups based on sector/industry (e.g. IT Services, Banking, Software & Tech) using `data/raw/peer_groups.xlsx`.
  - Designates a benchmark company for each group.
  - Calculates percentile ranks for 10 metrics within each peer group/year, inverting ranks for D/E (lower is better), and inserts them into `peer_percentiles` SQLite table.
  - Exports an 11-sheet workbook to `output/peer_comparison.xlsx` highlighting benchmark rows in gold and color-coding percentile ranks (Green for >= 75th percentile, Red for <= 25th percentile, Yellow for middle ranges).
- **Radar & Performance Charting**:
  - Automatically generates polar radar charts overlaying each company's percentile scores against its peer group average, saved as `reports/radar_charts/{ticker}_radar.png`.
  - For companies without a peer group (e.g., test cases `COMP85`-`COMP88`), it generates a standalone bar chart comparing its composite score against the overall Nifty 100 average.

---

## ⚙️ Automated Developer Commands (Makefile)

| Command | Action |
| --- | --- |
| `make setup` | Automatically generates local folder paths and initializes the `venv` virtual environment. |
| `make install` | Installs all Python dependencies listed in `requirements.txt`. |
| `make format` | Runs `black` formatting and sorts imports using `isort` across `src` and `tests`. |
| `make lint` | Performs style auditing using `flake8` and static type checking using `mypy`. |
| `make test` | Runs all 122 unit tests via `pytest` and logs code coverage. |
| `make load` | Runs the ETL ingestion loader to populate the database from the raw Excel files. |
| `make ratios` | Executes the ratios engine to compute PE, PB, ROE, D/E, and all Sprint 2 KPIs. |
| `make screener` | Computes winsorised scores and generates the Excel stock screener report. |
| `make peer` | Runs the peer analysis engine, populates percentiles database, and creates radar charts. |
| `make report` | Generates the data quality markdown report. |
| `make dashboard` / `make api` | Launches the local dashboard web page and API server at `http://localhost:8000`. |
| `make clean` | Purges python caches (`__pycache__`), environment locks, and local test coverage metrics. |

---

## 🚀 Running the Pipeline locally

### 1. Execute Ingestion, Calculations, and Screener/Peer Reports
Run these targets sequentially to completely ingest raw Excel sheets, calculate the financial ratios, run the stock screener, rank peers, and generate reports:
```bash
# Ingest Excel sheets into SQLite database
venv/Scripts/python -m src.etl.loader

# Compute and insert PE, PB, ROE, CAGR, Cash Flow KPIs, and Capital Allocation patterns
venv/Scripts/python -m src.etl.ratios

# Execute the Stock Screener Engine (Winsorisation & composite scoring)
venv/Scripts/python -m src.screener.engine

# Execute Peer Analysis Engine (Calculates peer rankings, inserts to DB, and draws radar/bar charts)
venv/Scripts/python -m src.analytics.peer

# Generate the data quality markdown report
venv/Scripts/python -m src.report
```

### 2. Run the full Test Suite
Run all 122 test cases to verify normalisation, validation rules, database constraint integrity, KPI formulas, and screener/peer ranks logic:
```bash
venv/Scripts/python -m pytest tests/ --cov=src
```

### 3. Launch the Web Dashboard
Start the local server and open your browser at `http://localhost:8000`:
```bash
venv/Scripts/python -m src.api_server
```
