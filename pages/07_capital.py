import sys
from pathlib import Path
import streamlit as st
import plotly.express as px
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import get_capital_allocation

st.title("🗺️ Capital Allocation Treemap")

df_cap = get_capital_allocation()

if df_cap.empty:
    st.error("No capital allocation data available in database.")
    st.stop()

# Handle missing or null patterns
df_cap["capital_allocation_pattern"] = df_cap["capital_allocation_pattern"].fillna("Balanced Expansion / Reinvestment")
df_cap["composite_quality_score"] = df_cap["composite_quality_score"].fillna(50.0)

st.subheader("📊 Nifty 100 Capital Allocation Strategy Breakdown")
st.markdown("Treemap visualizing companies grouped by their primary capital allocation behavior (Reinvestment, Debt Paydown, Shareholder Returns, etc.).")

fig_treemap = px.treemap(
    df_cap,
    path=["capital_allocation_pattern", "sector", "company_id"],
    values="composite_quality_score",
    color="composite_quality_score",
    color_continuous_scale="Viridis",
    hover_data=["company_name", "sector", "capital_allocation_pattern"],
    title="Capital Allocation Map by Strategy Pattern & Sector"
)

fig_treemap.update_layout(margin=dict(t=50, b=10, l=10, r=10))
st.plotly_chart(fig_treemap, use_container_width=True)

st.markdown("---")

# Interactive Pattern Drilldown
st.subheader("🔍 Explore Companies by Allocation Pattern")

patterns = sorted(df_cap["capital_allocation_pattern"].unique().tolist())
selected_pattern = st.selectbox("Select Capital Allocation Pattern:", options=patterns, index=0)

df_pattern_filtered = df_cap[df_cap["capital_allocation_pattern"] == selected_pattern]

st.markdown(f"#### **{len(df_pattern_filtered)} companies** classified under *'{selected_pattern}'*:")

df_display = df_pattern_filtered[["company_id", "company_name", "sector", "composite_quality_score"]].copy()
df_display.rename(columns={
    "company_id": "Ticker",
    "company_name": "Company Name",
    "sector": "Broad Sector",
    "composite_quality_score": "Composite Quality Score"
}, inplace=True)

st.dataframe(df_display, use_container_width=True, hide_index=True)
