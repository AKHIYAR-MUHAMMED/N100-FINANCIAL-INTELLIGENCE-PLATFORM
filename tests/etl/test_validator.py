import pandas as pd

from src.etl.validator import SchemaValidator


def test_validate_companies_all_rules():
    validator = SchemaValidator()
    # DQ-01: Duplicate ticker
    # DQ-02: Null ticker
    # DQ-10: Website URL validation
    # DQ-12: Exchange suffix check
    df = pd.DataFrame(
        {
            "ticker": ["TCS", "TCS", None, "INFY.NS", "RELIANCE.XYZ"],
            "name": ["Tata", "Tata", "Null Company", "Infosys", "Reliance"],
            "website": [
                "https://tcs.com",
                "tcs.com",
                "",
                "invalid_url",
                "www.reliance.in",
            ],
        }
    )
    validator.validate_companies(df, "companies.csv")
    failures = validator.failures
    assert len(failures) > 0
    rule_ids = [f.rule_id for f in failures]
    assert "DQ-01" in rule_ids
    assert "DQ-02" in rule_ids
    assert "DQ-10" in rule_ids
    assert "DQ-12" in rule_ids


def test_validate_relationships_fk():
    companies_df = pd.DataFrame({"ticker": ["TCS", "RELIANCE"]})
    financials_df = pd.DataFrame({"ticker": ["TCS", "INFY", "RELIANCE"]})

    # Financial FK validation (DQ-03)
    validator = SchemaValidator()
    validator.validate_relationships(financials_df, companies_df, "profitandloss.csv")
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-03"
    assert validator.failures[0].invalid_value == "INFY"
    assert validator.failures[0].severity == "CRITICAL"


def test_validate_prices_all_rules():
    validator = SchemaValidator()
    # DQ-01: Duplicate PK
    # DQ-02: Null/Invalid date PK
    # DQ-09: Positive prices
    # DQ-13: Coverage check
    # DQ-14: Positive volume
    # DQ-15: Stock price consistency
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
    assert "DQ-01" in rule_ids
    assert "DQ-02" in rule_ids
    assert "DQ-09" in rule_ids
    assert "DQ-13" in rule_ids
    assert "DQ-14" in rule_ids
    assert "DQ-15" in rule_ids


def test_validate_corporate_actions():
    validator = SchemaValidator()
    # DQ-09: Dividend cap
    df = pd.DataFrame(
        {
            "ticker": ["TCS", "RELIANCE"],
            "action_type": ["Dividend", "Dividend"],
            "value": [10.5, 600.0],
        }
    )
    validator.validate_corporate_actions(df, "corp.csv")
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-09"
    assert validator.failures[0].invalid_value == 600.0


def test_validate_financials_pnl():
    validator = SchemaValidator()
    # DQ-01: Duplicate PK
    # DQ-02: Year out of bounds
    # DQ-05: OPM cross-check
    # DQ-06: Positive sales
    # DQ-08: Tax rate check
    # DQ-11: EPS sign check
    # DQ-16: Logical profit order
    pnl_df = pd.DataFrame(
        {
            "ticker": ["TCS", "TCS", "RELIANCE", "INFY", "TCS"],
            "year": [2026, 2026, 1999, 2025, 2025],
            "sales": [1000.0, 1000.0, -50.0, 800.0, 1000.0],
            "operating_profit": [300.0, 300.0, 150.0, 250.0, 300.0],
            "opm": [
                0.30,
                0.30,
                0.15,
                0.90,
                0.30,
            ],  # In INFY op/sales = 250/800 = 0.3125 but opm is 0.90
            "gross_profit": [
                500.0,
                500.0,
                200.0,
                400.0,
                200.0,
            ],  # TCS 2025 GP (200) < OP (300)
            "net_income": [200.0, 200.0, 100.0, -50.0, 150.0],
            "eps": [
                2.0,
                2.0,
                1.0,
                0.5,
                1.5,
            ],  # INFY EPS is positive but Net Income is negative
        }
    )

    validator.validate_financials(pnl_df, "pnl.xlsx", "pnl")
    failures = validator.failures
    assert len(failures) > 0
    rule_ids = [f.rule_id for f in failures]
    assert "DQ-01" in rule_ids
    assert "DQ-02" in rule_ids
    assert "DQ-05" in rule_ids
    assert "DQ-06" in rule_ids
    assert "DQ-08" in rule_ids
    assert "DQ-11" in rule_ids
    assert "DQ-16" in rule_ids


def test_validate_financials_bs():
    validator = SchemaValidator()
    # DQ-04: Balance Sheet equation discrepancy
    bs_df = pd.DataFrame(
        {
            "ticker": ["TCS", "RELIANCE"],
            "year": [2026, 2026],
            "total_assets": [1000.0, 1000.0],
            "total_liabilities": [400.0, 500.0],
            "total_equity": [
                600.0,
                480.0,
            ],  # RELIANCE has 2% discrepancy: (1000 - 980) / 1000 = 0.02
        }
    )
    validator.validate_financials(bs_df, "bs.xlsx", "bs")
    failures = validator.failures
    assert len(failures) == 1
    assert failures[0].rule_id == "DQ-04"
    assert failures[0].severity == "WARNING"


def test_validate_financials_cf():
    validator = SchemaValidator()
    # DQ-07: Cash flow reconciliation discrepancy
    cf_df = pd.DataFrame(
        {
            "ticker": ["TCS", "RELIANCE"],
            "year": [2026, 2026],
            "beginning_cash": [100.0, 200.0],
            "ending_cash": [150.0, 220.0],
            "net_cash_flow": [
                50.0,
                50.0,
            ],  # RELIANCE Ending cash is 220, Start + Net = 250, diff = 30
        }
    )
    validator.validate_financials(cf_df, "cf.xlsx", "cf")
    failures = validator.failures
    assert len(failures) == 1
    assert failures[0].rule_id == "DQ-07"
    assert failures[0].severity == "WARNING"


def test_validate_financials_ratios():
    validator = SchemaValidator()
    # DQ-13: Ratio coverage warnings
    ratios_df = pd.DataFrame(
        {
            "ticker": ["TCS", "RELIANCE"],
            "year": [2026, 2026],
            "pe_ratio": [15.0, 20.0],
            "pb_ratio": [2.5, 3.0],
            "roe": [15.0, 200.0],  # RELIANCE ROE is anomalous
            "debt_to_equity": [0.5, 6.0],  # RELIANCE debt-to-equity is very high
        }
    )
    validator.validate_financials(ratios_df, "ratios.xlsx", "ratios")
    failures = validator.failures
    assert len(failures) == 2
    rule_ids = [f.rule_id for f in failures]
    assert all(r == "DQ-13" for r in rule_ids)


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
