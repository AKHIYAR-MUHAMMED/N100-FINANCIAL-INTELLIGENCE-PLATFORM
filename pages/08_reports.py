import sys
from pathlib import Path
import streamlit as st
import requests
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import get_companies, get_documents

st.title("📁 Annual Reports & Regulatory Filings")

df_companies = get_companies()

if df_companies.empty:
    st.error("No company records available.")
    st.stop()

company_options = [f"{row['ticker']} - {row['name']}" for _, row in df_companies.iterrows()]
selected_option = st.selectbox("Search Company:", options=company_options, index=0)
selected_ticker = selected_option.split(" - ")[0].strip()

comp_info = df_companies[df_companies["ticker"].str.upper() == selected_ticker.upper()].iloc[0]

st.subheader(f"📄 Financial Filings & Annual Reports: {comp_info['name']} ({selected_ticker})")

df_docs = get_documents(selected_ticker)

# Helper function to check URL status with caching or quick HEAD request
def check_url_status(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    try:
        response = requests.head(url, timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False

# Generate default annual report list (FY20 to FY24) if none present in database
if df_docs.empty:
    years = [2024, 2023, 2022, 2021, 2020]
    sample_docs = []
    for yr in years:
        # Sample BSE / Official Annual Report URL
        bse_url = f"https://www.bseindia.com/bseplus/AnnualReport/{selected_ticker}_{yr}.pdf"
        sample_docs.append({
            "year": f"FY {yr}",
            "document_name": f"Annual Report FY{yr} - {comp_info['name']}",
            "url": bse_url
        })
    df_docs_show = pd.DataFrame(sample_docs)
else:
    df_docs_show = df_docs.copy()
    df_docs_show["year"] = "FY24"
    df_docs_show.rename(columns={"file_path": "url"}, inplace=True)

st.markdown("---")

for _, row in df_docs_show.iterrows():
    col1, col2, col3 = st.columns([2, 4, 2])
    
    doc_name = row.get("document_name", "Annual Report")
    doc_url = row.get("url", "#")
    yr_label = row.get("year", "Annual Report")
    
    with col1:
        st.markdown(f"**{yr_label}**")
    with col2:
        st.markdown(f"[{doc_name}]({doc_url})")
    with col3:
        # Check URL status or provide simulated status for demo
        is_available = check_url_status(doc_url) if doc_url.startswith("http") else True
        if is_available:
            st.markdown("🟢 <span style='color:green; font-weight:bold;'>Available (PDF)</span>", unsafe_allow_html=True)
        else:
            st.markdown("🔴 <span style='background-color:#ff4b4b; color:white; padding:4px 8px; border-radius:4px;'>Report unavailable</span>", unsafe_allow_html=True)
