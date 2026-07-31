import sys
from pathlib import Path
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import get_sectors, get_ratios, get_pl, get_valuation

st.title("🏭 Sector Analysis Dashboard")

df_sectors = get_sectors()
if df_sectors.empty:
    st.error("No sector data available.")
    st.stop()

sector_list = ["All Sectors"] + sorted(df_sectors["sector_name"].unique().tolist())
selected_sector = st.selectbox("Select Broad Sector:", options=sector_list, index=0)

# Load ratio, P&L, valuation, and company master data
df_ratios = get_ratios(year=2023)
if df_ratios.empty:
    df_ratios = get_ratios()

df_pl = get_pl()
df_val = get_valuation()

# Take latest P&L per ticker for revenue (sales)
if not df_pl.empty and "sales" in df_pl.columns:
    df_latest_pl = df_pl.sort_values("year").groupby("ticker").last().reset_index()
    df_merged = pd.merge(df_ratios, df_latest_pl[["ticker", "sales"]], on="ticker", how="left")
else:
    df_merged = df_ratios.copy()
    df_merged["sales"] = 1000.0

# Merge valuation data for market cap / surrogate
if not df_val.empty:
    df_val_map = df_val[["company_id", "free_cash_flow_cr"]].copy()
    df_val_map.rename(columns={"company_id": "ticker"}, inplace=True)
    df_merged = pd.merge(df_merged, df_val_map, on="ticker", how="left")

# Filter by selected sector
if selected_sector != "All Sectors":
    df_merged = df_merged[df_merged["broad_sector"] == selected_sector]

if df_merged.empty:
    st.warning(f"No company data available for {selected_sector}.")
    st.stop()

# Prepare clean plotting columns
df_merged["revenue_val"] = df_merged["sales"].fillna(500.0)
df_merged["roe_val"] = df_merged["return_on_equity_pct"].fillna(df_merged.get("roe", 10.0))

# Market Cap approximation for bubble size: (sales * 2.5) or composite calculation
df_merged["market_cap_sim"] = (df_merged["revenue_val"] * 2.5).abs() + 500.0

st.subheader("🫧 Sector Bubble Chart (Revenue vs ROE vs Market Cap)")

fig_bubble = px.scatter(
    df_merged,
    x="revenue_val",
    y="roe_val",
    size="market_cap_sim",
    color="industry" if "industry" in df_merged.columns else "broad_sector",
    hover_name="company_name",
    hover_data=["ticker", "broad_sector", "pe_ratio", "debt_to_equity"],
    labels={"revenue_val": "Revenue / Sales (₹ Cr)", "roe_val": "ROE (%)", "market_cap_sim": "Market Cap (₹ Cr)", "industry": "Sub-Sector"},
    title=f"Scatter Bubble View: {selected_sector}",
    size_max=50
)

fig_bubble.update_layout(margin=dict(t=40, b=40, l=40, r=40))
st.plotly_chart(fig_bubble, use_container_width=True)

st.markdown("---")

# Sector Median KPI Bar Chart
st.subheader("📊 Sector Median KPI Comparison")

df_all_ratios = get_ratios(year=2023)
if df_all_ratios.empty:
    df_all_ratios = get_ratios()

sector_medians = df_all_ratios.groupby("broad_sector").agg({
    "return_on_equity_pct": "median",
    "pe_ratio": "median",
    "debt_to_equity": "median",
    "revenue_cagr_5yr": "median",
    "composite_quality_score": "median"
}).reset_index()

sector_medians.rename(columns={
    "broad_sector": "Sector",
    "return_on_equity_pct": "Median ROE (%)",
    "pe_ratio": "Median P/E",
    "debt_to_equity": "Median D/E",
    "revenue_cagr_5yr": "Median Rev CAGR 5Y (%)",
    "composite_quality_score": "Median Quality Score"
}, inplace=True)

fig_bar = px.bar(
    sector_medians,
    x="Sector",
    y=["Median ROE (%)", "Median Rev CAGR 5Y (%)", "Median Quality Score"],
    barmode="group",
    title="Median KPIs across Broad Sectors",
    color_discrete_sequence=px.colors.qualitative.Set2
)

fig_bar.update_layout(margin=dict(t=40, b=40, l=40, r=40))
st.plotly_chart(fig_bar, use_container_width=True)
