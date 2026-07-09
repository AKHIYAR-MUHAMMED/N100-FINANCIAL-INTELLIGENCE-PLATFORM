import pandas as pd

from src.database import DatabaseManager
from src.etl.loader import ETLLoader


def test_etl_loader_pipeline(tmp_path, monkeypatch):
    # Setup temporary directory structures
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    output_dir = tmp_path / "output"

    raw_dir.mkdir()
    processed_dir.mkdir()
    output_dir.mkdir()

    db_file = tmp_path / "test_nifty100.db"

    # Create mock excel files for ingestion
    # 1. sectors.xlsx
    df_sectors = pd.DataFrame(
        {"sector_name": ["Technology"], "sector_description": ["IT services"]}
    )
    df_sectors.to_excel(raw_dir / "sectors.xlsx", index=False)

    # 2. companies.xlsx
    df_companies = pd.DataFrame(
        {
            "ticker": ["TCS.NS", "  INFY  "],  # Test normalisation
            "name": ["Tata", "Infosys"],
            "sector_name": ["Technology", "Technology"],
            "industry": ["IT", "IT"],
        }
    )
    df_companies.to_excel(raw_dir / "companies.xlsx", index=False)

    # 3. income_statements.xlsx
    df_pnl = pd.DataFrame(
        {
            "ticker": [
                "TCS",
                "INFY",
                "TCS",
            ],  # TCS duplicated year to test duplicate drop
            "year": [2024, 2024, 2024],
            "sales": [100.0, 200.0, 100.0],
            "operating_profit": [15.0, 30.0, 15.0],
            "opm": [0.15, 0.15, 0.15],
            "gross_profit": [40.0, 80.0, 40.0],
            "net_income": [10.0, 20.0, 10.0],
            "eps": [0.1, 0.2, 0.1],
            "shares_outstanding": [100.0, 100.0, 100.0],
        }
    )
    df_pnl.to_excel(raw_dir / "income_statements.xlsx", index=False)

    # 4. stock_prices_core.xlsx
    df_prices = pd.DataFrame(
        {
            "ticker": ["TCS", "INFY"],
            "date": ["2026-07-08", "2026-07-08"],
            "open": [100.0, 200.0],
            "high": [105.0, 205.0],
            "low": [98.0, 198.0],
            "close": [102.0, 202.0],
            "volume": [1000, 2000],
        }
    )
    df_prices.to_excel(raw_dir / "stock_prices_core.xlsx", index=False)

    # Instantiate loader
    loader = ETLLoader(db_path=db_file)

    # Mock loader paths using monkeypatch
    loader.raw_dir = raw_dir
    loader.processed_dir = processed_dir
    loader.output_dir = output_dir

    # Run pipeline
    fk_violations = loader.run_pipeline()

    # Assertions
    assert fk_violations == 0

    # Verify outputs created
    assert (output_dir / "load_audit.csv").is_file()
    assert (output_dir / "validation_failures.csv").is_file()

    # Check database counts
    db_manager = DatabaseManager(db_file)

    sectors_count = db_manager.execute_query("SELECT COUNT(*) as cnt FROM sectors;")[0][
        "cnt"
    ]
    companies_count = db_manager.execute_query(
        "SELECT COUNT(*) as cnt FROM companies;"
    )[0]["cnt"]
    pnl_count = db_manager.execute_query("SELECT COUNT(*) as cnt FROM profitandloss;")[
        0
    ]["cnt"]
    prices_count = db_manager.execute_query(
        "SELECT COUNT(*) as cnt FROM stock_prices;"
    )[0]["cnt"]

    assert sectors_count == 1
    assert companies_count == 2
    assert pnl_count == 2  # The duplicate was dropped!
    assert prices_count == 2
