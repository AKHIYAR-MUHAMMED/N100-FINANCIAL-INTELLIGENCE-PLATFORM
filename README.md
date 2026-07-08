# Sprint 1: Data Ingestion & ETL - Day 01: Environment Setup

This repository contains the foundation code for **Epic 01: Data Ingestion & ETL** of the Nifty 100 Analytics project. 

Day 01 focuses on establishing a professional development environment, compiling dependencies, configuring environments, and setting up automated developer targets.

---

## 📂 Project Structure

The project structure is organized as follows:
```text
nifty100/
├── data/
│   ├── raw/             # Staging area for raw incoming Excel sheets
│   └── processed/       # Cleaned and normalized CSVs ready for SQLite
├── src/                 # Application source package
│   └── __init__.py
├── tests/               # Unit testing suite
├── logs/                # Rotated run logs
├── .env.example         # Template for environment configuration
├── .gitignore           # Git ignore definitions
├── Makefile             # Automation target commands
└── requirements.txt     # List of 20 project library dependencies
```

---

## 🛠️ Requirements & Libraries

The environment uses 20 Python packages categorized across:
* **Data Processing:** `pandas`, `numpy`, `openpyxl`, `xlrd` (Excel read/write support)
* **Databases:** `sqlalchemy`
* **Configuration:** `python-dotenv`, `pyyaml`
* **Code Quality & Checks:** `black`, `isort`, `flake8`, `mypy`, `pydantic`
* **Testing:** `pytest`, `pytest-cov`
* **CLI/Logging:** `tqdm`, `colorama`, `requests`
* **Reporting & Visualizations:** `jinja2`, `matplotlib`, `seaborn`

---

## 🚀 Local Setup Instructions

Follow these steps to set up the development environment locally:

### 1. Create Directories and Virtual Environment
Create the necessary folder structure and initialize the Python virtual environment (`venv`):
```bash
python -m venv venv
```

### 2. Activate the Environment
* **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **Windows (Git Bash/CMD):**
  ```bash
  source venv/Scripts/activate
  ```
* **Linux/macOS:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies
Install all 20 libraries inside the active virtual environment:
```bash
pip install -r requirements.txt
```

### 4. Setup Local Configurations
Copy the template `.env.example` file to create your active `.env` configuration file:
```bash
cp .env.example .env
```

---

## ⚙️ Automated Developer Commands (Makefile)

A `Makefile` is configured in the root directory for automated task execution:

| Command | Action |
| --- | --- |
| `make setup` | Automatically generates local folder paths and initializes the `venv` virtual environment. |
| `make install` | Installs all Python dependencies listed in `requirements.txt`. |
| `make format` | Runs `black` formatting and sorts imports using `isort` across `src` and `tests`. |
| `make lint` | Performs style auditing using `flake8` and static type checking using `mypy`. |
| `make test` | Runs the test suite via `pytest` and logs code coverage. |
| `make clean` | Purges Python caches (`__pycache__`), environment file locks, test databases, and local test coverage metrics. |
