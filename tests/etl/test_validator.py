import pandas as pd
import pytest

from src.etl.validator import SchemaValidator


@pytest.fixture
def companies_data():
    return pd.DataFrame(
        {
            "ticker": ["TCS", "RELIANCE", "INFY"],
            "name": ["Tata Consultancy Services", "Reliance Industries", "Infosys"],
        }
    )


def test_validate_companies_success():
    validator = SchemaValidator()
    df = pd.DataFrame({"ticker": ["TCS", "RELIANCE"]})
    validator.validate_companies(df, "companies.csv")
    assert len(validator.failures) == 0
    assert not validator.has_critical_failures()


def test_validate_companies_duplicates_and_nulls():
    validator = SchemaValidator()
    df = pd.DataFrame({"ticker": ["TCS", "TCS", None, "  "]})
    validator.validate_companies(df, "companies.csv")

    failures = validator.failures
    assert len(failures) == 4
    assert all(f.severity == "CRITICAL" for f in failures)

    rule_ids = [f.rule_id for f in failures]
    assert "DQ-01" in rule_ids
    assert "DQ-02" in rule_ids


def test_validate_relationships_fk():
    companies_df = pd.DataFrame({"ticker": ["TCS", "RELIANCE"]})
    financials_df = pd.DataFrame({"ticker": ["TCS", "INFY", "RELIANCE", None]})

    # Financial FK validation (DQ-03)
    validator = SchemaValidator()
    validator.validate_relationships(
        financials_df, companies_df, "pnl.csv", is_prices=False
    )
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-03"
    assert validator.failures[0].invalid_value == "INFY"
    assert validator.failures[0].severity == "CRITICAL"

    # Prices FK validation (DQ-04)
    validator2 = SchemaValidator()
    validator2.validate_relationships(
        financials_df, companies_df, "prices.csv", is_prices=True
    )
    assert len(validator2.failures) == 1
    assert validator2.failures[0].rule_id == "DQ-04"
    assert validator2.failures[0].invalid_value == "INFY"


def test_validate_prices_all_rules():
    validator = SchemaValidator()

    # DQ-05: Duplicate PK
    # DQ-06: Null PK
    # DQ-08: Invalid date
    # DQ-09: Non-positive prices
    # DQ-14: Negative volume (Warning)
    # DQ-15: Inconsistent open/high/low/close (Warning)
    prices_df = pd.DataFrame(
        {
            "ticker": ["TCS", "TCS", None, "RELIANCE", "INFY", "INFY"],
            "date": [
                "2026-07-08",
                "2026-07-08",
                "2026-07-08",
                "invalid-date",
                "2026-07-08",
                "2026-07-08",
            ],
            "open": [100.0, 100.0, 50.0, 150.0, -10.0, 100.0],
            "high": [120.0, 120.0, 60.0, 160.0, 120.0, 90.0],
            "low": [90.0, 90.0, 40.0, 140.0, 80.0, 95.0],
            "close": [110.0, 110.0, 55.0, 155.0, 110.0, 100.0],
            "volume": [1000, 1000, 500, 2000, -5, 1500],
        }
    )

    validator.validate_prices(prices_df, "prices.csv")
    failures = validator.failures
    assert len(failures) > 0

    rule_ids = [f.rule_id for f in failures]
    assert "DQ-05" in rule_ids
    assert "DQ-06" in rule_ids
    assert "DQ-08" in rule_ids
    assert "DQ-09" in rule_ids
    assert "DQ-14" in rule_ids
    assert "DQ-15" in rule_ids


def test_validate_financials_pnl():
    validator = SchemaValidator()

    # DQ-07: Duplicate ticker, year
    # DQ-08: Year out of bounds (1999)
    # DQ-10: Non-positive sales (Warning)
    # DQ-11: Out of bounds OPM (Warning)
    # DQ-16: Inconsistent gross_profit >= operating_profit >= net_income (Warning)
    pnl_df = pd.DataFrame(
        {
            "ticker": ["TCS", "TCS", "RELIANCE", "INFY", "INFY"],
            "year": [2026, 2026, 1999, 2025, 2025],
            "sales": [1000.0, 1000.0, -50.0, 800.0, 800.0],
            "opm": [0.25, 0.25, 0.15, 1.5, 0.20],
            "gross_profit": [500.0, 500.0, 200.0, 400.0, 300.0],
            "operating_profit": [300.0, 300.0, 150.0, 250.0, 320.0],
            "net_income": [200.0, 200.0, 100.0, 180.0, 150.0],
        }
    )

    validator.validate_financials(pnl_df, "pnl.xlsx", "pnl")
    failures = validator.failures
    assert len(failures) > 0

    rule_ids = [f.rule_id for f in failures]
    assert "DQ-07" in rule_ids
    assert "DQ-08" in rule_ids
    assert "DQ-10" in rule_ids
    assert "DQ-11" in rule_ids
    assert "DQ-16" in rule_ids


def test_validate_financials_bs():
    validator = SchemaValidator()

    # DQ-12: Assets != Liabilities + Equity (Warning)
    bs_df = pd.DataFrame(
        {
            "ticker": ["TCS", "RELIANCE"],
            "year": [2026, 2026],
            "total_assets": [1000.0, 1500.0],
            "total_liabilities": [400.0, 500.0],
            "total_equity": [600.0, 800.0],
        }
    )

    validator.validate_financials(bs_df, "bs.xlsx", "bs")
    failures = validator.failures
    assert len(failures) == 1
    assert failures[0].rule_id == "DQ-12"
    assert failures[0].severity == "WARNING"


def test_validate_financials_cf():
    validator = SchemaValidator()

    # DQ-13: Ending Cash != Beginning Cash + Net Cash Flow (Warning)
    cf_df = pd.DataFrame(
        {
            "ticker": ["TCS", "RELIANCE"],
            "year": [2026, 2026],
            "beginning_cash": [100.0, 200.0],
            "ending_cash": [150.0, 220.0],
            "net_cash_flow": [50.0, 50.0],
        }
    )

    validator.validate_financials(cf_df, "cf.xlsx", "cf")
    failures = validator.failures
    assert len(failures) == 1
    assert failures[0].rule_id == "DQ-13"
    assert failures[0].severity == "WARNING"


def test_save_failures_csv(tmp_path):
    validator = SchemaValidator()
    validator.log_failure(
        "TCS", "companies.csv", 1, "DQ-01", "CRITICAL", "ticker", "TCS", "Duplicate"
    )

    out_file = tmp_path / "failures.csv"
    validator.save_failures(out_file)

    assert out_file.is_file()
    df = pd.read_csv(out_file)
    assert len(df) == 1
    assert df.loc[0, "company_ticker"] == "TCS"
    assert df.loc[0, "severity"] == "CRITICAL"
