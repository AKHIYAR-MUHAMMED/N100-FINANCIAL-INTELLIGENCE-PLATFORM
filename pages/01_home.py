import sys
from pathlib import Path
import streamlit as st
import plotly.express as px
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import get_ratios, get_companies, get_sectors

st.title("📊 Market Overview - Home")

# Sidebar Year Selector (2019 to 2024)
years = list(range(2019, 2025))
selected_year = st.sidebar.selectbox("Select Financial Year", options=years, index=len(years) - 2)

# Load data for selected year
df_ratios = get_ratios(year=selected_year)
df_companies = get_companies()
df_sectors = get_sectors()

if df_ratios.empty:
    st.warning(f"No financial data available for the year {selected_year}. Showing available overview.")
    # Fallback to latest year if selected year has no data
    df_ratios = get_ratios(year=2023)

st.subheader(f"📈 Executive KPI Summary ({selected_year})")

# Calculate metrics
avg_roe = df_ratios["return_on_equity_pct"].dropna().mean() if "return_on_equity_pct" in df_ratios and not df_ratios["return_on_equity_pct"].dropna().empty else df_ratios["roe"].dropna().mean()
median_pe = df_ratios["pe_ratio"].dropna().median() if "pe_ratio" in df_ratios else 0.0
median_de = df_ratios["debt_to_equity"].dropna().median() if "debt_to_equity" in df_ratios else 0.0
total_companies = len(df_companies)

median_rev_cagr_5yr = df_ratios["revenue_cagr_5yr"].dropna().median() if "revenue_cagr_5yr" in df_ratios else 0.0

# Debt-free companies count (where debt_to_equity <= 0.05 or icr_label == 'Debt Free')
if "debt_to_equity" in df_ratios:
    debt_free_count = len(df_ratios[df_ratios["debt_to_equity"] <= 0.05])
else:
    debt_free_count = 0

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Avg ROE", f"{avg_roe:.2f}%" if pd.notna(avg_roe) else "N/A")
with col2:
    st.metric("Median P/E", f"{median_pe:.2f}x" if pd.notna(median_pe) else "N/A")
with col3:
    st.metric("Median D/E", f"{median_de:.2f}" if pd.notna(median_de) else "N/A")
with col4:
    st.metric("Total Companies", f"{total_companies}")
with col5:
    st.metric("Median Rev CAGR (5Yr)", f"{median_rev_cagr_5yr:.2f}%" if pd.notna(median_rev_cagr_5yr) else "N/A")
with col6:
    st.metric("Debt-Free Companies", f"{debt_free_count}")

st.markdown("---")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🏢 Sector Distribution")
    if not df_sectors.empty:
        fig_donut = px.pie(
            df_sectors,
            names="sector_name",
            values="company_count",
            hole=0.4,
            title="Company Breakdown by Broad Sector",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_donut.update_traces(textinfo="percent+label")
        fig_donut.update_layout(margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("Sector breakdown data unavailable.")

with col_right:
    st.subheader("🏆 Top-5 Companies by Quality Score")
    if "composite_quality_score" in df_ratios and not df_ratios.empty:
        top_5 = df_ratios.sort_values(by="composite_quality_score", ascending=False).head(5)
        display_cols = ["ticker", "company_name", "broad_sector", "composite_quality_score", "pe_ratio"]
        existing_cols = [c for c in display_cols if c in top_5.columns]
        
        df_top5_show = top_5[existing_cols].copy()
        df_top5_show.rename(columns={
            "ticker": "Ticker",
            "company_name": "Company Name",
            "broad_sector": "Sector",
            "composite_quality_score": "Composite Score",
            "pe_ratio": "P/E Ratio"
        }, inplace=True)
        
        st.dataframe(df_top5_show.style.format({
            "Composite Score": "{:.2f}",
            "P/E Ratio": "{:.2f}"
        }), use_container_width=True, hide_index=True)
    else:
        st.info("Top companies data unavailable.")
