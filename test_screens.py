import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import (
    get_companies, get_ratios, get_pl, get_bs, get_cf,
    get_sectors, get_peers, get_valuation, get_pros_cons,
    get_documents, get_capital_allocation
)

def test_db_loaders():
    print("Testing db loader functions...")
    
    df_comp = get_companies()
    assert not df_comp.empty, "get_companies returned empty DataFrame"
    print(f"[OK] get_companies: {len(df_comp)} rows")
    
    df_rat = get_ratios()
    assert not df_rat.empty, "get_ratios returned empty DataFrame"
    print(f"[OK] get_ratios: {len(df_rat)} rows")
    
    df_pl = get_pl("COMP01")
    assert not df_pl.empty, "get_pl returned empty DataFrame for COMP01"
    print(f"[OK] get_pl(COMP01): {len(df_pl)} rows")
    
    df_bs = get_bs("COMP01")
    assert not df_bs.empty, "get_bs returned empty DataFrame for COMP01"
    print(f"[OK] get_bs(COMP01): {len(df_bs)} rows")
    
    df_cf = get_cf("COMP01")
    assert not df_cf.empty, "get_cf returned empty DataFrame for COMP01"
    print(f"[OK] get_cf(COMP01): {len(df_cf)} rows")
    
    df_sec = get_sectors()
    assert not df_sec.empty, "get_sectors returned empty DataFrame"
    print(f"[OK] get_sectors: {len(df_sec)} rows")
    
    df_peers = get_peers()
    assert not df_peers.empty, "get_peers returned empty DataFrame"
    print(f"[OK] get_peers: {len(df_peers)} rows")
    
    df_val = get_valuation("COMP01")
    assert not df_val.empty, "get_valuation returned empty DataFrame"
    print(f"[OK] get_valuation: {len(df_val)} rows")
    
    df_pc = get_pros_cons("COMP01")
    print(f"[OK] get_pros_cons: {len(df_pc)} rows")
    
    df_doc = get_documents("COMP01")
    print(f"[OK] get_documents: {len(df_doc)} rows")
    
    df_cap = get_capital_allocation()
    assert not df_cap.empty, "get_capital_allocation returned empty DataFrame"
    print(f"[OK] get_capital_allocation: {len(df_cap)} rows")
    
    print("\nALL DB LOADER TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_db_loaders()
