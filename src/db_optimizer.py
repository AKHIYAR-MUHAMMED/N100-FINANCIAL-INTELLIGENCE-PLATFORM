"""SQLite Database Performance Optimizer and Query Indexing Utility.

Provides automated index creation, query plan analysis (EXPLAIN QUERY PLAN),
and benchmarking helpers for financial database queries.
"""

from typing import Dict, List, Tuple
import sqlite3
import time
from pathlib import Path


RECOMMENDED_INDEXES: List[Tuple[str, str, str]] = [
    ("idx_companies_sector", "companies", "sector_name"),
    ("idx_financial_ratios_ticker_year", "financial_ratios", "ticker, year"),
    ("idx_profitandloss_ticker_year", "profitandloss", "ticker, year"),
    ("idx_balancesheet_ticker_year", "balancesheet", "ticker, year"),
    ("idx_cashflow_ticker_year", "cashflow", "ticker, year"),
]


def ensure_database_indexes(db_path: str) -> Dict[str, str]:
    """Inspects SQLite database and creates recommended performance indexes if missing."""
    if not Path(db_path).exists():
        return {"status": "error", "message": f"Database {db_path} not found"}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    created = []
    already_exist = []

    # Get existing index names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
    existing_indexes = {row[0] for row in cursor.fetchall()}

    for idx_name, table, cols in RECOMMENDED_INDEXES:
        if idx_name in existing_indexes:
            already_exist.append(idx_name)
        else:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({cols});")
                created.append(idx_name)
            except sqlite3.OperationalError:
                pass

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "created_indexes": created,
        "existing_indexes": already_exist,
    }


def benchmark_query_execution(db_path: str, query: str, iterations: int = 10) -> float:
    """Measures average execution time in milliseconds over specified iterations."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        cursor.execute(query)
        _ = cursor.fetchall()
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)

    conn.close()
    return round(sum(times) / len(times), 3)
