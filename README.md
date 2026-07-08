# Sprint 1: Data Ingestion & ETL (Days 01 – 04)

This repository contains the foundation for **Epic 01: Data Ingestion & ETL** of the Nifty 100 Analytics project. It includes the environment setup, ticker/year normalisation engine, 16 Data Quality (DQ) validation checks, and the SQLite database schema design.

---

## 📂 Project Structure

```text
nifty100/
├── data/
│   ├── raw/                 # Staging area for raw incoming Excel sheets
│   └── processed/           # Normalized, staged CSV files
├── db/
│   └── schema.sql           # SQLite migration file defining 10 tables
├── notebooks/
│   └── exploratory_queries.sql # 10 SQL queries for data verification
├── output/
│   ├── load_audit.csv       # Audit log for processed/loaded files
│   └── validation_failures.csv # Logs for DQ rule warnings and rejections
├── src/
│   ├── etl/
│   │   ├── generate_mock_data.py # Realistic mock Excel sheets generator
│   │   ├── loader.py        # Pipeline orchestrator & transactional database loader
│   │   ├── normaliser.py    # Year and ticker cleaning functions
│   │   └── validator.py     # SchemaValidator containing 16 DQ rules
│   ├── database.py          # SQLite connections & schema initializer
│   └── __init__.py
├── tests/
│   └── etl/
│       ├── test_database.py # Database constraint checks and migrations tests
│       ├── test_loader.py   # Full ETL pipeline integration tests
│       ├── test_normaliser.py # Year and ticker cleaning unit tests
│       └── test_validator.py # DQ validation engine rules unit tests
├── .env.example             # Configuration template
├── .flake8                  # Style configuration rules
├── Makefile                 # Automated commands
└── requirements.txt         # Project library dependencies
```

---

## 🛠️ Sprint Deliverables (Day 01 – Day 04)

### Day 01: Environment Setup
- Established directories (`data/raw`, `data/processed`, `db`, `src/etl`, `tests/etl`, `notebooks`).
- Managed virtual environment dependencies inside `.venv/`.
- Configured `.env` environment variables (`DB_PATH=data/db/nifty100.db`).
- Developed automation targets in the `Makefile` (`make setup`, `make install`, `make format`, `make lint`, `make test`, `make clean`).

### Day 02: Excel Loader & Normaliser
Implemented standard cleaning algorithms in `normaliser.py`:
- **Ticker Normalisation**: Converts ticker strings to uppercase, strips whitespace, and removes exchange suffixes (e.g. `.NS`, `.BO`, `.BSE`, `.NSE`). Converts whole floats (e.g., `12345.0`) to standard string representations.
- **Year Normalisation**: Normalises any string, numeric, or datetime year value into a 4-digit integer. Converts 2-digit years to 4-digit using a pivot boundary of `50` (years `< 50` map to `20XX`, `>= 50` map to `19XX`).

### Day 03: Schema Validator (16 DQ Rules)
Validates files against 16 distinct rules in `validator.py`. Rule severity divides into:
- **CRITICAL** (Rejects the row to preserve database transactional integrity):
  - `DQ-01`: Duplicate ticker in companies directory.
  - `DQ-02`: Null ticker in companies directory.
  - `DQ-03`: Financial statements referential integrity (foreign key exists in companies directory).
  - `DQ-04`: Stock prices referential integrity (foreign key exists in companies directory).
  - `DQ-05`: Duplicate stock price records (same ticker and date).
  - `DQ-06`: Null primary key values in stock prices.
  - `DQ-07`: Duplicate financial records (same ticker and year).
  - `DQ-08`: Invalid year format or date boundary constraints.
  - `DQ-09`: Negative stock prices (open, high, low, close must be positive).
- **WARNING** (Logs the failure but permits row insertion):
  - `DQ-10`: Sales/Revenue should be positive (warns if `sales <= 0`).
  - `DQ-11`: Operating Profit Margin (OPM) boundary constraints (warns if `abs(OPM) > 1.0`).
  - `DQ-12`: Balance Sheet balances (warns if `Assets != Liabilities + Equity`).
  - `DQ-13`: Cash Flow reconciles (warns if `Ending Cash != Beginning Cash + Net Cash Flow`).
  - `DQ-14`: Positive trading volume (warns if `volume < 0`).
  - `DQ-15`: Stock price consistency (warns if `High` is not maximum, or `Low` is not minimum).
  - `DQ-16`: Logical profit ordering (warns if `Gross Profit < Operating Profit` or `Operating Profit < Net Income`).

All failures are recorded in the database `validation_failures` table and exported to `output/validation_failures.csv`.

### Day 04: SQLite Database Schema
- Built a 10-table relational schema inside `db/schema.sql` incorporating primary keys, foreign keys, cascade deletes, and column boundary constraints (`CHECK`).
- Configured connection handlers in `database.py` enforcing referential integrity with `PRAGMA foreign_keys = ON;`.
- Implemented tables: `sectors`, `companies`, `income_statements`, `balance_sheets`, `cash_flows`, `stock_prices`, `ratios`, `corporate_actions`, `validation_failures`, and `load_audit`.

---

## ⚙️ Automated Developer Commands (Makefile)

A `Makefile` is configured in the root directory for automated task execution:

| Command | Action |
| --- | --- |
| `make setup` | Automatically generates local folder paths and initializes the `venv` virtual environment. |
| `make install` | Installs all Python dependencies listed in `requirements.txt`. |
| `make format` | Runs `black` formatting and sorts imports using `isort` across `src` and `tests`. |
| `make lint` | Performs style auditing using `flake8` and static type checking using `mypy` (ignoring missing third-party imports). |
| `make test` | Runs the unit test suite via `pytest` and logs code coverage. |
| `make clean` | Purges python caches (`__pycache__`), environment locks, and local test coverage metrics. |

---

## 🚀 Running the Pipeline locally

### 1. Ingestion Execution
Run the orchestrator script to automatically parse raw Excel sheets, normalize years/tickers, apply the 16 DQ rules, and load clean data into SQLite:
```bash
venv/Scripts/python -m src.etl.loader
```

### 2. Run Test Suite
Run the 80 test cases to verify normalisation, validation checks, database constraint integrity, and database insertion coverage:
```bash
venv/Scripts/python -m pytest tests/ --cov=src
```
