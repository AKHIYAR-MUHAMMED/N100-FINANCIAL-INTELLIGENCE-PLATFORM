import os
import sqlite3
import pytest
from src.db_optimizer import (
    ensure_database_indexes,
    benchmark_query_execution,
)


def test_ensure_database_indexes_on_memory_db(tmp_path):
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE companies (ticker TEXT, sector_name TEXT);")
    conn.execute("CREATE TABLE financial_ratios (ticker TEXT, year INTEGER);")
    conn.execute("CREATE TABLE profitandloss (ticker TEXT, year INTEGER);")
    conn.execute("CREATE TABLE balancesheet (ticker TEXT, year INTEGER);")
    conn.execute("CREATE TABLE cashflow (ticker TEXT, year INTEGER);")
    conn.commit()
    conn.close()

    result = ensure_database_indexes(str(db_file))
    assert result["status"] == "success"
    assert len(result["created_indexes"]) >= 1

    # Second run should report already existing
    result2 = ensure_database_indexes(str(db_file))
    assert len(result2["existing_indexes"]) >= 1


def test_benchmark_query_execution(tmp_path):
    db_file = tmp_path / "test_bench.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE test_table (id INTEGER, val TEXT);")
    for i in range(50):
        conn.execute("INSERT INTO test_table VALUES (?, ?);", (i, f"val_{i}"))
    conn.commit()
    conn.close()

    avg_ms = benchmark_query_execution(str(db_file), "SELECT * FROM test_table WHERE id > 10;", iterations=5)
    assert avg_ms >= 0.0
