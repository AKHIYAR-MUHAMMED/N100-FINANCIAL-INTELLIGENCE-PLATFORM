import sys
from pathlib import Path
import streamlit as st
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import get_ratios

st.title("🔎 Stock Screener Engine")

df_latest = get_ratios(year=2023)
if df_latest.empty:
    df_latest = get_ratios()  # fallback to all/latest

# Preset Definitions
PRESETS = {
    "Quality": {"roe_min": 15.0, "de_max": 0.5, "fcf_min": 50.0, "cagr_min": 8.0, "pat_cagr_min": 8.0, "opm_min": 15.0, "pe_max": 60.0, "pb_max": 10.0, "div_min": 10.0, "icr_min": 5.0},
    "Value": {"roe_min": 10.0, "de_max": 1.0, "fcf_min": 0.0, "cagr_min": 0.0, "pat_cagr_min": 0.0, "opm_min": 8.0, "pe_max": 20.0, "pb_max": 2.5, "div_min": 15.0, "icr_min": 2.0},
    "Growth": {"roe_min": 12.0, "de_max": 1.0, "fcf_min": 0.0, "cagr_min": 15.0, "pat_cagr_min": 15.0, "opm_min": 12.0, "pe_max": 80.0, "pb_max": 15.0, "div_min": 0.0, "icr_min": 3.0},
    "Dividend": {"roe_min": 10.0, "de_max": 0.8, "fcf_min": 20.0, "cagr_min": 0.0, "pat_cagr_min": 0.0, "opm_min": 10.0, "pe_max": 35.0, "pb_max": 5.0, "div_min": 30.0, "icr_min": 3.0},
    "Debt-Free": {"roe_min": 8.0, "de_max": 0.05, "fcf_min": 0.0, "cagr_min": 0.0, "pat_cagr_min": 0.0, "opm_min": 5.0, "pe_max": 100.0, "pb_max": 20.0, "div_min": 0.0, "icr_min": 10.0},
    "Turnaround": {"roe_min": 5.0, "de_max": 2.0, "fcf_min": -50.0, "cagr_min": -5.0, "pat_cagr_min": -5.0, "opm_min": 2.0, "pe_max": 40.0, "pb_max": 3.0, "div_min": 0.0, "icr_min": 1.0}
}

# Initialize session state for sliders if not set
default_vals = {"roe_min": 0.0, "de_max": 3.0, "fcf_min": -500.0, "cagr_min": -20.0, "pat_cagr_min": -20.0, "opm_min": -10.0, "pe_max": 150.0, "pb_max": 30.0, "div_min": 0.0, "icr_min": 0.0}

for k, v in default_vals.items():
    if k not in st.session_state:
        st.session_state[k] = float(v)

# Preset buttons in sidebar
st.sidebar.subheader("⚡ Quick Preset Filters")
p_cols = st.sidebar.columns(3)
for idx, (preset_name, vals) in enumerate(PRESETS.items()):
    col = p_cols[idx % 3]
    if col.button(preset_name, key=f"btn_{preset_name}"):
        for k, v in vals.items():
            st.session_state[k] = float(v)

st.sidebar.markdown("---")
st.sidebar.subheader("🎚️ Custom Screener Sliders")

# Sliders bound directly to session_state keys
roe_min_val = st.sidebar.slider("ROE Min (%)", -50.0, 100.0, key="roe_min", step=1.0)
de_max_val = st.sidebar.slider("D/E Max", 0.0, 5.0, key="de_max", step=0.1)
fcf_min_val = st.sidebar.slider("FCF Min (₹ Cr)", -1000.0, 5000.0, key="fcf_min", step=50.0)
cagr_min_val = st.sidebar.slider("Revenue CAGR 5yr Min (%)", -30.0, 100.0, key="cagr_min", step=1.0)
pat_cagr_min_val = st.sidebar.slider("PAT CAGR 5yr Min (%)", -30.0, 100.0, key="pat_cagr_min", step=1.0)
opm_min_val = st.sidebar.slider("OPM Min (%)", -20.0, 80.0, key="opm_min", step=1.0)
pe_max_val = st.sidebar.slider("P/E Max", 0.0, 200.0, key="pe_max", step=5.0)
pb_max_val = st.sidebar.slider("P/B Max", 0.0, 50.0, key="pb_max", step=0.5)
div_min_val = st.sidebar.slider("Dividend Payout Min (%)", 0.0, 100.0, key="div_min", step=1.0)
icr_min_val = st.sidebar.slider("Interest Coverage Min", 0.0, 50.0, key="icr_min", step=0.5)

# Filtering logic
df_filtered = df_latest.copy()

# Match helper column names safely
roe_col = "return_on_equity_pct" if "return_on_equity_pct" in df_filtered else "roe"
opm_col = "operating_profit_margin_pct" if "operating_profit_margin_pct" in df_filtered else "opm"

if roe_col in df_filtered:
    df_filtered = df_filtered[df_filtered[roe_col].fillna(-999) >= st.session_state["roe_min"]]
if "debt_to_equity" in df_filtered:
    df_filtered = df_filtered[df_filtered["debt_to_equity"].fillna(999) <= st.session_state["de_max"]]
if "free_cash_flow_cr" in df_filtered:
    df_filtered = df_filtered[df_filtered["free_cash_flow_cr"].fillna(-9999) >= st.session_state["fcf_min"]]
if "revenue_cagr_5yr" in df_filtered:
    df_filtered = df_filtered[df_filtered["revenue_cagr_5yr"].fillna(-999) >= st.session_state["cagr_min"]]
if "pat_cagr_5yr" in df_filtered:
    df_filtered = df_filtered[df_filtered["pat_cagr_5yr"].fillna(-999) >= st.session_state["pat_cagr_min"]]
if opm_col in df_filtered:
    df_filtered = df_filtered[df_filtered[opm_col].fillna(-999) >= st.session_state["opm_min"]]
if "pe_ratio" in df_filtered:
    df_filtered = df_filtered[df_filtered["pe_ratio"].fillna(999) <= st.session_state["pe_max"]]
if "pb_ratio" in df_filtered:
    df_filtered = df_filtered[df_filtered["pb_ratio"].fillna(999) <= st.session_state["pb_max"]]
if "dividend_payout_ratio_pct" in df_filtered:
    df_filtered = df_filtered[df_filtered["dividend_payout_ratio_pct"].fillna(-999) >= st.session_state["div_min"]]
if "interest_coverage" in df_filtered:
    df_filtered = df_filtered[df_filtered["interest_coverage"].fillna(0) >= st.session_state["icr_min"]]

# Results Header and Count Label
result_count = len(df_filtered)
st.markdown(f"### 📋 Filtered Results: **{result_count} companies match your filters**")

if df_filtered.empty:
    st.info("No companies matched the current filter criteria. Try relaxing slider constraints.")
else:
    # Select display columns
    cols_to_show = ["ticker", "company_name", "broad_sector", "composite_quality_score", "pe_ratio", "pb_ratio", roe_col, "debt_to_equity", "free_cash_flow_cr", "revenue_cagr_5yr", "pat_cagr_5yr", opm_col]
    cols_exist = [c for c in cols_to_show if c in df_filtered.columns]
    
    df_show = df_filtered[cols_exist].copy()
    df_show.rename(columns={
        "ticker": "Ticker",
        "company_name": "Company Name",
        "broad_sector": "Sector",
        "composite_quality_score": "Composite Score",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        roe_col: "ROE (%)",
        "debt_to_equity": "D/E",
        "free_cash_flow_cr": "FCF (Cr)",
        "revenue_cagr_5yr": "Rev CAGR 5Y (%)",
        "pat_cagr_5yr": "PAT CAGR 5Y (%)",
        opm_col: "OPM (%)"
    }, inplace=True)
    
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    # CSV Download Button
    csv_data = df_show.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv_data,
        file_name="screener_filtered_results.csv",
        mime="text/csv"
    )
