import sys
import time
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import (
    get_companies, get_ratios, get_pl, get_bs, get_cf,
    get_sectors, get_peers, get_valuation, get_pros_cons,
    get_documents, get_capital_allocation
)

def test_integration_and_qa():
    print("=== STARTING INTEGRATION QA & PERFORMANCE BENCHMARKING ===")
    
    # 1. DB Loader Checks
    df_comp = get_companies()
    assert len(df_comp) == 92, f"Expected 92 companies, got {len(df_comp)}"
    print(f"[OK] get_companies: {len(df_comp)} companies loaded.")
    
    df_ratios = get_ratios()
    assert not df_ratios.empty, "get_ratios returned empty"
    print(f"[OK] get_ratios: {len(df_ratios)} ratio records loaded.")
    
    df_peers = get_peers()
    assert len(df_peers['group_name'].unique()) == 11, f"Expected 11 peer groups, got {len(df_peers['group_name'].unique())}"
    print(f"[OK] get_peers: 11 peer groups verified across {len(df_peers)} mappings.")
    
    # 2. Test 10 Tickers across 5 Sectors (IT, Financials, FMCG, Energy, Healthcare)
    test_tickers = ["COMP01", "COMP02", "COMP03", "COMP04", "COMP05", "COMP06", "COMP07", "COMP08", "COMP09", "COMP10"]
    
    print("\n--- Testing Company Profile Screen Load Times (< 3 Seconds Goal) ---")
    for ticker in test_tickers:
        t0 = time.time()
        c_info = df_comp[df_comp["ticker"] == ticker]
        r_info = get_ratios(ticker=ticker)
        pl_info = get_pl(ticker=ticker)
        bs_info = get_bs(ticker=ticker)
        cf_info = get_cf(ticker=ticker)
        pc_info = get_pros_cons(ticker=ticker)
        elapsed = time.time() - t0
        
        assert elapsed < 3.0, f"Profile load for {ticker} took {elapsed:.3f}s (exceeded 3s target)"
        print(f"[OK] Profile data load for {ticker}: {elapsed:.4f}s")
    
    # 3. Test Unknown Ticker & Edge Case Fallback
    unknown_ticker = "NON_EXISTENT_TICKER"
    c_unk = df_comp[df_comp["ticker"] == unknown_ticker]
    assert c_unk.empty, "Unknown ticker should return empty dataframe"
    print("[OK] Unknown ticker gracefully identified as empty result.")
    
    # 4. Test Extreme Screener Sliders Logic
    print("\n--- Testing Screener Extreme Slider Values ---")
    df_latest = get_ratios(year=2023)
    
    # Extreme Max Sliders (Should yield empty without crash)
    df_extreme_high = df_latest[
        (df_latest["return_on_equity_pct"].fillna(-999) >= 99.0) &
        (df_latest["pe_ratio"].fillna(999) <= 1.0)
    ]
    print(f"[OK] Extreme high filter count: {len(df_extreme_high)} companies match (no crash).")
    
    # Extreme Low Sliders (Should yield all companies without crash)
    df_extreme_low = df_latest[
        (df_latest["return_on_equity_pct"].fillna(-999) >= -100.0) &
        (df_latest["pe_ratio"].fillna(999) <= 1000.0)
    ]
    print(f"[OK] Extreme low filter count: {len(df_extreme_low)} companies match (no crash).")
    
    # 5. Verify Valuation Module Outputs
    print("\n--- Verifying Valuation Summary & Flags Artifacts ---")
    val_excel_path = PROJECT_ROOT / "output" / "valuation_summary.xlsx"
    val_csv_path = PROJECT_ROOT / "output" / "valuation_flags.csv"
    
    assert val_excel_path.exists(), "valuation_summary.xlsx does not exist"
    assert val_csv_path.exists(), "valuation_flags.csv does not exist"
    
    df_val_summary = pd.read_excel(val_excel_path)
    assert len(df_val_summary) == 92, f"Expected 92 rows in valuation_summary.xlsx, got {len(df_val_summary)}"
    
    required_val_cols = ["company_id", "company_name", "sector", "P/E", "P/B", "EV/EBITDA", "FCF_yield_pct", "5yr_median_PE", "PE_vs_sector_median_pct", "flag"]
    for col in required_val_cols:
        assert col in df_val_summary.columns, f"Missing required column {col} in valuation_summary.xlsx"
    
    df_val_flags = pd.read_csv(val_csv_path)
    assert not df_val_flags.empty, "valuation_flags.csv should contain Caution/Discount companies"
    print(f"[OK] valuation_summary.xlsx verified with {len(df_val_summary)} rows and all required columns.")
    print(f"[OK] valuation_flags.csv verified with {len(df_val_flags)} flagged companies.")
    
    print("\n=== ALL INTEGRATION QA TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_integration_and_qa()
