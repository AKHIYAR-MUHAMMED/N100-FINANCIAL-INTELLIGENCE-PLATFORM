import sqlite3
import pytest

from src.database import DatabaseManager


@pytest.fixture
def temp_db_manager(tmp_path):
    """Fixture that initializes a DatabaseManager with a temporary database."""
    db_file = tmp_path / "test_nifty100.db"
    manager = DatabaseManager(db_path=db_file)
    manager.initialize_schema()
    return manager


def test_initialize_schema(temp_db_manager):
    """Test that schema tables are successfully created."""
    tables = temp_db_manager.execute_query(
        "SELECT name FROM sqlite_master WHERE type='table';"
    )
    table_names = [row["name"] for row in tables]

    # Verify core tables are present
    assert "companies" in table_names
    assert "sectors" in table_names
    assert "income_statements" in table_names
    assert "balance_sheets" in table_names
    assert "cash_flows" in table_names
    assert "stock_prices" in table_names
    assert "validation_failures" in table_names
    assert "load_audit" in table_names


def test_foreign_key_enforcement(temp_db_manager):
    """Test that FK violations raise sqlite3.IntegrityError."""
    # Attempt to insert a company referencing a non-existent sector
    with pytest.raises(sqlite3.IntegrityError):
        temp_db_manager.execute_update(
            "INSERT INTO companies (ticker, name, sector_name, industry) "
            "VALUES (?, ?, ?, ?);",
            ("TCS", "Tata Consultancy Services", "NON_EXISTENT_SECTOR", "IT"),
        )


def test_foreign_key_success(temp_db_manager):
    """Test that valid foreign keys succeed."""
    # Insert sector first
    temp_db_manager.execute_update(
        "INSERT INTO sectors (sector_name, sector_description) VALUES (?, ?);",
        ("Technology", "IT Services"),
    )
    # Insert company next
    temp_db_manager.execute_update(
        "INSERT INTO companies (ticker, name, sector_name, industry) "
        "VALUES (?, ?, ?, ?);",
        ("TCS", "Tata Consultancy Services", "Technology", "IT Services"),
    )

    # Query back
    rows = temp_db_manager.execute_query(
        "SELECT * FROM companies WHERE ticker = ?;", ("TCS",)
    )
    assert len(rows) == 1
    assert rows[0]["name"] == "Tata Consultancy Services"


def test_check_constraints(temp_db_manager):
    """Test that CHECK constraints (e.g. OPM margin ranges) are enforced."""
    # Insert sector and company
    temp_db_manager.execute_update(
        "INSERT INTO sectors (sector_name) VALUES (?);", ("Technology",)
    )
    temp_db_manager.execute_update(
        "INSERT INTO companies (ticker, name, sector_name) VALUES (?, ?, ?);",
        ("TCS", "Tata", "Technology"),
    )

    # Try inserting P&L with invalid OPM (> 1.0)
    with pytest.raises(sqlite3.IntegrityError):
        temp_db_manager.execute_update(
            "INSERT INTO income_statements (ticker, year, sales, opm) "
            "VALUES (?, ?, ?, ?);",
            ("TCS", 2026, 1000.0, 1.2),  # OPM must be between -1.0 and 1.0
        )


def test_run_fk_check(temp_db_manager):
    """Test that run_fk_check correctly identifies FK issues."""
    # Verify that initially there are 0 violations
    violations = temp_db_manager.run_fk_check()
    assert len(violations) == 0
