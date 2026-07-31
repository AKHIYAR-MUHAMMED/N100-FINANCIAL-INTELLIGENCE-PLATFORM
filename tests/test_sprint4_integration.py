import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import pytest
except ImportError:
    pytest = None
import pandas as pd
from pathlib import Path

from src.dashboard.utils.db import (
    get_companies, get_ratios, get_pl, get_bs, get_cf,
    get_sectors, get_peers, get_valuation, get_pros_cons,
    get_documents, get_capital_allocation
)
from src.analytics.valuation import ValuationEngine

def test_all_92_tickers_db_loaders():
    """Verify that all database loader functions work cleanly for all 92 companies."""
    df_companies = get_companies()
    assert len(df_companies) == 92, f"Expected 92 companies, got {len(df_companies)}"
    
    tickers = df_companies["ticker"].tolist()
    
    for ticker in tickers:
        df_r = get_ratios(ticker=ticker)
        df_p = get_pl(ticker=ticker)
        df_b = get_bs(ticker=ticker)
        df_c = get_cf(ticker=ticker)
        df_pc = get_pros_cons(ticker=ticker)
        df_doc = get_documents(ticker=ticker)
        
        # Verify no unhandled crashes for any ticker
        assert isinstance(df_r, pd.DataFrame)
        assert isinstance(df_p, pd.DataFrame)
        assert isinstance(df_b, pd.DataFrame)
        assert isinstance(df_c, pd.DataFrame)

def test_company_profile_load_time():
    """Verify that company profile data loading time is under 3 seconds per ticker."""
    sample_tickers = ["COMP01", "COMP15", "COMP30", "COMP55", "COMP90"]
    
    for ticker in sample_tickers:
        start_time = time.time()
        
        comp_df = get_companies()
        ratios_df = get_ratios(ticker=ticker)
        pl_df = get_pl(ticker=ticker)
        pc_df = get_pros_cons(ticker=ticker)
        
        elapsed = time.time() - start_time
        assert elapsed < 3.0, f"Profile load for {ticker} took {elapsed:.2f}s, exceeding 3s limit!"

def test_screener_extreme_values():
    """Test screener filtering logic with extreme slider values."""
    df_all = get_ratios(year=2023)
    if df_all.empty:
        df_all = get_ratios()
        
    # Minimum extreme criteria
    df_min = df_all[
        (df_all["return_on_equity_pct"].fillna(-999) >= -100.0) &
        (df_all["debt_to_equity"].fillna(999) <= 100.0) &
        (df_all["pe_ratio"].fillna(999) <= 1000.0)
    ]
    assert isinstance(df_min, pd.DataFrame)

    # Maximum extreme criteria (no match)
    df_max = df_all[
        (df_all["return_on_equity_pct"].fillna(-999) >= 999.0) &
        (df_all["pe_ratio"].fillna(999) <= 0.001)
    ]
    assert len(df_max) == 0

def test_valuation_engine_outputs():
    """Verify valuation summary and flags files generation."""
    engine = ValuationEngine()
    df_summary = engine.run_valuation_analysis()
    
    assert len(df_summary) == 92, f"Valuation summary has {len(df_summary)} rows, expected 92"
    
    req_cols = [
        "company_id", "company_name", "sector", "P/E", "P/B",
        "EV/EBITDA", "FCF_yield_pct", "5yr_median_PE",
        "PE_vs_sector_median_pct", "flag"
    ]
    for col in req_cols:
        assert col in df_summary.columns, f"Missing column {col} in valuation summary"

    output_dir = Path(__file__).resolve().parents[1] / "output"
    assert (output_dir / "valuation_summary.xlsx").exists()
    assert (output_dir / "valuation_flags.csv").exists()

if __name__ == "__main__":
    test_all_92_tickers_db_loaders()
    test_company_profile_load_time()
    test_screener_extreme_values()
    test_valuation_engine_outputs()
    print("ALL SPRINT 4 INTEGRATION TESTS PASSED SUCCESSFULLY!")
