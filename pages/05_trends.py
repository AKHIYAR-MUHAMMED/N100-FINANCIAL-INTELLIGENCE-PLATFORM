import sys
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import get_companies, get_ratios, get_pl

st.title("📈 Trend Analysis - Multi-Metric 10-Year View")

df_companies = get_companies()
if df_companies.empty:
    st.error("No companies found.")
    st.stop()

company_options = [f"{row['ticker']} - {row['name']}" for _, row in df_companies.iterrows()]
selected_option = st.selectbox("Search Company:", options=company_options, index=0)
selected_ticker = selected_option.split(" - ")[0].strip()

# Available metrics mapping
AVAILABLE_METRICS = {
    "Sales / Revenue (Cr)": ("pl", "sales"),
    "Net Income / Profit (Cr)": ("pl", "net_income"),
    "Operating Profit (Cr)": ("pl", "operating_profit"),
    "ROE (%)": ("ratios", "return_on_equity_pct"),
    "ROCE (%)": ("ratios", "return_on_capital_employed_pct"),
    "Net Profit Margin (%)": ("ratios", "net_profit_margin_pct"),
    "Debt to Equity": ("ratios", "debt_to_equity"),
    "Free Cash Flow (Cr)": ("ratios", "free_cash_flow_cr"),
    "P/E Ratio": ("ratios", "pe_ratio")
}

selected_metric_names = st.multiselect(
    "Select Up to 3 Metrics to Overlay:",
    options=list(AVAILABLE_METRICS.keys()),
    default=["Sales / Revenue (Cr)", "Net Income / Profit (Cr)"],
    max_selections=3
)

if not selected_metric_names:
    st.info("Please select at least 1 metric to view trend chart.")
    st.stop()

# Fetch data
df_ratios = get_ratios(ticker=selected_ticker)
df_pl = get_pl(ticker=selected_ticker)

fig = go.Figure()

colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

for idx, metric_label in enumerate(selected_metric_names):
    source, col_name = AVAILABLE_METRICS[metric_label]
    df_src = df_pl if source == "pl" else df_ratios
    
    if df_src.empty or col_name not in df_src.columns:
        st.warning(f"Data not available for {metric_label}.")
        continue
    
    df_metric = df_src[["year", col_name]].dropna().sort_values(by="year")
    if df_metric.empty:
        continue
    
    # Calculate YoY % change
    df_metric["yoy_pct"] = df_metric[col_name].pct_change() * 100
    
    text_labels = []
    for i, row in df_metric.reset_index().iterrows():
        val = row[col_name]
        yoy = row["yoy_pct"]
        if i == 0 or pd.isna(yoy):
            text_labels.append(f"{val:,.1f}")
        else:
            prefix = "+" if yoy >= 0 else ""
            text_labels.append(f"{val:,.1f} ({prefix}{yoy:.1f}%)")

    fig.add_trace(go.Scatter(
        x=df_metric["year"],
        y=df_metric[col_name],
        mode="lines+markers+text",
        name=metric_label,
        text=text_labels,
        textposition="top center",
        line=dict(color=colors[idx % len(colors)], width=3),
        marker=dict(size=8)
    ))

fig.update_layout(
    title=dict(text=f"10-Year Financial Trends for {selected_ticker} with YoY % Change", x=0.5),
    xaxis_title="Financial Year",
    yaxis_title="Value",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=60, b=40, l=40, r=40)
)

st.plotly_chart(fig, use_container_width=True)
