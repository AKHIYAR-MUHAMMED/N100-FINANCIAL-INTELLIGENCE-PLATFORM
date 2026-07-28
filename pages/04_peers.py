import sys
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import get_peers, get_ratios

st.title("⚔️ Peer Comparison Screen")

df_peers_all = get_peers()

if df_peers_all.empty:
    st.error("No peer group mappings found in database.")
    st.stop()

# Group selection dropdown
groups = sorted(df_peers_all["group_name"].unique())
selected_group = st.selectbox("Select Peer Group:", options=groups, index=0)

# Filter companies in group
df_group_members = df_peers_all[df_peers_all["group_name"] == selected_group]
group_tickers = df_group_members["ticker"].tolist()

# Select target company for comparison
selected_ticker = st.selectbox(
    "Select Target Company for Radar Comparison:",
    options=group_tickers,
    format_func=lambda x: f"{x} - {df_group_members[df_group_members['ticker']==x]['company_name'].values[0]}"
)

# Fetch latest ratios for group tickers
df_ratios_all = get_ratios(year=2023)
if df_ratios_all.empty:
    df_ratios_all = get_ratios()

df_group_ratios = df_ratios_all[df_ratios_all["ticker"].isin(group_tickers)].copy()

if df_group_ratios.empty:
    st.warning("No ratio data available for this peer group.")
    st.stop()

# 8 Metrics for Radar Chart
radar_metrics = [
    ("ROE (%)", "return_on_equity_pct"),
    ("ROCE (%)", "return_on_capital_employed_pct"),
    ("NPM (%)", "net_profit_margin_pct"),
    ("Rev CAGR 5Y", "revenue_cagr_5yr"),
    ("PAT CAGR 5Y", "pat_cagr_5yr"),
    ("OPM (%)", "operating_profit_margin_pct"),
    ("Asset Turnover", "asset_turnover"),
    ("Composite Score", "composite_quality_score")
]

# Extract target company metrics
target_row = df_group_ratios[df_group_ratios["ticker"] == selected_ticker]
target_vals = []
peer_avg_vals = []
categories = []

for label, col_name in radar_metrics:
    categories.append(label)
    # Target value
    if not target_row.empty and col_name in target_row.columns and pd.notna(target_row[col_name].values[0]):
        val = float(target_row[col_name].values[0])
    else:
        val = 0.0
    target_vals.append(val)
    
    # Peer group average value
    if col_name in df_group_ratios.columns:
        avg_val = float(df_group_ratios[col_name].dropna().mean()) if not df_group_ratios[col_name].dropna().empty else 0.0
    else:
        avg_val = 0.0
    peer_avg_vals.append(avg_val)

# Close radar loop
categories_closed = categories + [categories[0]]
target_vals_closed = target_vals + [target_vals[0]]
peer_avg_vals_closed = peer_avg_vals + [peer_avg_vals[0]]

# Plotly Radar Chart (Scatterpolar)
fig_radar = go.Figure()

fig_radar.add_trace(go.Scatterpolar(
    r=target_vals_closed,
    theta=categories_closed,
    fill='toself',
    name=f"Target: {selected_ticker}",
    line_color="#1f77b4"
))

fig_radar.add_trace(go.Scatterpolar(
    r=peer_avg_vals_closed,
    theta=categories_closed,
    fill='toself',
    name=f"{selected_group} Average",
    line_color="#ff7f0e",
    opacity=0.6
))

fig_radar.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True,
            showticklabels=True
        )
    ),
    showlegend=True,
    title=dict(text=f"Radar Metric Profile: {selected_ticker} vs. {selected_group} Peer Average", x=0.5),
    margin=dict(t=50, b=30, l=40, r=40)
)

st.plotly_chart(fig_radar, use_container_width=True)

st.markdown("---")

# Side-by-side KPI Comparison Table
st.subheader(f"📊 Peer Group Side-by-Side Table ({selected_group})")

table_cols = ["ticker", "company_name", "pe_ratio", "pb_ratio", "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr", "revenue_cagr_5yr", "composite_quality_score"]
existing_cols = [c for c in table_cols if c in df_group_ratios.columns]

df_table = df_group_ratios[existing_cols].copy()
df_table.rename(columns={
    "ticker": "Ticker",
    "company_name": "Company Name",
    "pe_ratio": "P/E",
    "pb_ratio": "P/B",
    "return_on_equity_pct": "ROE (%)",
    "debt_to_equity": "D/E",
    "free_cash_flow_cr": "FCF (Cr)",
    "revenue_cagr_5yr": "Rev CAGR 5Y (%)",
    "composite_quality_score": "Composite Score"
}, inplace=True)

# Highlight benchmark / selected company row function
def highlight_selected(row):
    if row["Ticker"] == selected_ticker:
        return ['background-color: rgba(255, 215, 0, 0.3); font-weight: bold'] * len(row)
    return [''] * len(row)

st.dataframe(df_table.style.apply(highlight_selected, axis=1), use_container_width=True, hide_index=True)
