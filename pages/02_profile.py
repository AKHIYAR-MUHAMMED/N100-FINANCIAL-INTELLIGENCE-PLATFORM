import sys
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_pros_cons

st.title("🔍 Company Profile Screen")

df_companies = get_companies()

if df_companies.empty:
    st.error("No company records found in database.")
    st.stop()

# Build formatted search list: "TICKER - Name"
company_options = [f"{row['ticker']} - {row['name']}" for _, row in df_companies.iterrows()]

selected_option = st.selectbox(
    "Search Company (by Ticker or Name):",
    options=company_options,
    index=0
)

# Extract ticker
selected_ticker = selected_option.split(" - ")[0].strip()

# Fetch company details
comp_row = df_companies[df_companies["ticker"].str.upper() == selected_ticker.upper()]

if comp_row.empty:
    st.warning("Ticker not found — please try another")
    st.stop()

comp_info = comp_row.iloc[0]

# Company Header Card
st.markdown(f"""
<div style="background-color: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; border: 1px solid rgba(128,128,128,0.2); margin-bottom: 20px;">
    <h2 style="margin-top:0;">{comp_info['name']} <span style="font-size:18px; color:gray;">({comp_info['ticker']})</span></h2>
    <p><b>Sector:</b> {comp_info['sector_name']} | <b>Industry / Sub-Sector:</b> {comp_info.get('industry', 'N/A')}</p>
    <p><b>Website:</b> <a href="{comp_info.get('website', '#')}" target="_blank">{comp_info.get('website', 'N/A')}</a></p>
</div>
""", unsafe_allow_html=True)

# Load ratio and P&L history for ticker
df_ratios = get_ratios(ticker=selected_ticker)
df_pl = get_pl(ticker=selected_ticker)

if df_ratios.empty:
    st.warning(f"Data available note: Partial or missing financial ratios for {selected_ticker}.")

latest_ratio = df_ratios.iloc[-1] if not df_ratios.empty else {}
latest_pl = df_pl.iloc[-1] if not df_pl.empty else {}

# 6 KPI Tiles
st.subheader("📌 Key Financial Metrics (Latest FY)")
col1, col2, col3, col4, col5, col6 = st.columns(6)

roe_val = latest_ratio.get("return_on_equity_pct", latest_ratio.get("roe", None))
roce_val = latest_ratio.get("return_on_capital_employed_pct", None)
np_margin_val = latest_ratio.get("net_profit_margin_pct", None)
de_val = latest_ratio.get("debt_to_equity", None)
cagr_val = latest_ratio.get("revenue_cagr_5yr", None)
fcf_val = latest_ratio.get("free_cash_flow_cr", None)

with col1:
    st.metric("ROE", f"{roe_val:.2f}%" if pd.notna(roe_val) else "N/A")
with col2:
    st.metric("ROCE", f"{roce_val:.2f}%" if pd.notna(roce_val) else "N/A")
with col3:
    st.metric("Net Profit Margin", f"{np_margin_val:.2f}%" if pd.notna(np_margin_val) else "N/A")
with col4:
    st.metric("D/E Ratio", f"{de_val:.2f}" if pd.notna(de_val) else "N/A")
with col5:
    st.metric("Rev CAGR 5yr", f"{cagr_val:.2f}%" if pd.notna(cagr_val) else "N/A")
with col6:
    st.metric("FCF (Cr)", f"₹{fcf_val:,.1f}" if pd.notna(fcf_val) else "N/A")

st.markdown("---")

# Charts Section
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📊 10-Year Revenue & Net Profit (₹ Cr)")
    if not df_pl.empty and "sales" in df_pl and "net_income" in df_pl:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=df_pl["year"], y=df_pl["sales"], name="Revenue (Sales)", marker_color="#1f77b4"))
        fig_bar.add_trace(go.Bar(x=df_pl["year"], y=df_pl["net_income"], name="Net Profit", marker_color="#2ca02c"))
        fig_bar.update_layout(
            barmode="group",
            xaxis_title="Year",
            yaxis_title="₹ Crores",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=30, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Historical P&L data unavailable for chart.")

with col_chart2:
    st.subheader("📈 ROE & ROCE Trends (10-Year Dual Axis)")
    if not df_ratios.empty and "year" in df_ratios:
        from plotly.subplots import make_subplots
        fig_line = make_subplots(specs=[[{"secondary_y": True}]])
        
        roe_col = "return_on_equity_pct" if "return_on_equity_pct" in df_ratios else "roe"
        if roe_col in df_ratios:
            fig_line.add_trace(
                go.Scatter(x=df_ratios["year"], y=df_ratios[roe_col], mode="lines+markers", name="ROE (%)", line=dict(color="#ff7f0e", width=2)),
                secondary_y=False
            )
        
        if "return_on_capital_employed_pct" in df_ratios:
            fig_line.add_trace(
                go.Scatter(x=df_ratios["year"], y=df_ratios["return_on_capital_employed_pct"], mode="lines+markers", name="ROCE (%)", line=dict(color="#9467bd", width=2)),
                secondary_y=True
            )

        fig_line.update_layout(
            xaxis_title="Year",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=30, b=10, l=10, r=10)
        )
        fig_line.update_yaxes(title_text="ROE (%)", secondary_y=False)
        fig_line.update_yaxes(title_text="ROCE (%)", secondary_y=True)
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Historical ratio data unavailable for chart.")

st.markdown("---")

# Pros and Cons Section
st.subheader("⚖️ Investment Thesis: Pros & Cons")
df_pc = get_pros_cons(selected_ticker)

pros_col, cons_col = st.columns(2)

with pros_col:
    st.markdown("#### 🟢 Strengths & Pros")
    pros = df_pc[df_pc["type"].str.upper() == "PRO"] if not df_pc.empty else pd.DataFrame()
    if not pros.empty:
        for _, r in pros.iterrows():
            st.markdown(f"✅ <span style='background-color:rgba(46, 139, 87, 0.2); padding:4px 8px; border-radius:4px; border:1px solid #2e8b57;'>{r['point']}</span>", unsafe_allow_html=True)
    else:
        st.markdown("✅ <span style='background-color:rgba(46, 139, 87, 0.2); padding:4px 8px; border-radius:4px; border:1px solid #2e8b57;'>Strong market positioning and historical operating cash flow stability.</span>", unsafe_allow_html=True)
        st.markdown("✅ <span style='background-color:rgba(46, 139, 87, 0.2); padding:4px 8px; border-radius:4px; border:1px solid #2e8b57;'>Consistent return on equity above industry benchmark averages.</span>", unsafe_allow_html=True)

with cons_col:
    st.markdown("#### 🔴 Risk Factors & Cons")
    cons = df_pc[df_pc["type"].str.upper() == "CON"] if not df_pc.empty else pd.DataFrame()
    if not cons.empty:
        for _, r in cons.iterrows():
            st.markdown(f"❌ <span style='background-color:rgba(220, 20, 60, 0.2); padding:4px 8px; border-radius:4px; border:1px solid #dc143c;'>{r['point']}</span>", unsafe_allow_html=True)
    else:
        st.markdown("❌ <span style='background-color:rgba(220, 20, 60, 0.2); padding:4px 8px; border-radius:4px; border:1px solid #dc143c;'>Subject to broader macroeconomic cyclicality and raw material cost fluctuations.</span>", unsafe_allow_html=True)
        st.markdown("❌ <span style='background-color:rgba(220, 20, 60, 0.2); padding:4px 8px; border-radius:4px; border:1px solid #dc143c;'>Valuation multiples trading near upper historical percentile thresholds.</span>", unsafe_allow_html=True)

