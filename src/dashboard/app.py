import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern dark/light look
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .stMetric {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Main entry point welcome screen & routing helper
st.sidebar.title("📌 Nifty 100 Analytics")
st.sidebar.caption("Comprehensive Financial Dashboard & Valuation Engine")

st.markdown("# 🚀 Welcome to Nifty 100 Analytics Dashboard")
st.markdown("""
Select a screen from the sidebar to explore financial metrics, peer comparisons, screener, capital allocation maps, and valuation analytics across all 92 Nifty 100 companies.

---
### 🧭 Navigation Guide:
1. **01 Home**: High-level market overview, sector distribution, top performers, and summary KPIs.
2. **02 Company Profile**: Comprehensive deep dive into individual company financials, 10-year trends, and pros/cons.
3. **03 Screener**: Dynamic multi-metric filter engine with preset criteria and live CSV export.
4. **04 Peer Comparison**: Radar chart and side-by-side metric comparison within peer groups.
5. **05 Trend Analysis**: Multi-metric 10-year trend comparison with YoY percentage change annotations.
6. **06 Sector Analysis**: Interactive bubble chart (Revenue vs ROE vs Market Cap) and sector medians.
7. **07 Capital Allocation**: Treemap map of 92 companies categorized by 8 capital allocation patterns.
8. **08 Annual Reports**: Repository of annual reports and filing links with status badges.
""")

st.info("👈 Please select a page from the sidebar to begin navigation.")
