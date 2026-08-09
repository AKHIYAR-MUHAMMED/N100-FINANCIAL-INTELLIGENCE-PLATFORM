import os
import glob
from src.nlp.parser import parse_analysis_text
from src.nlp.pros_cons_generator import generate_pros_cons
from src.analytics.cashflow_kpis import generate_cashflow_intelligence


def test_nlp_parser():
    df_parsed, df_failures = parse_analysis_text("data/raw/analysis.xlsx", "output")
    assert not df_parsed.empty
    assert os.path.exists("output/analysis_parsed.csv")
    assert os.path.exists("output/parse_failures.csv")
    assert set(["company_id", "metric_type", "period_years", "value_pct"]).issubset(df_parsed.columns)
    # Parse success rate should exceed 50%
    total = len(df_parsed) + len(df_failures)
    assert total > 0
    parse_rate = len(df_parsed) / total
    assert parse_rate > 0.5, f"Parse success rate too low: {parse_rate:.1%}"


def test_pros_cons_generator():
    df_pc = generate_pros_cons("data/db/nifty100.db", "output")
    assert not df_pc.empty
    assert os.path.exists("output/pros_cons_generated.csv")
    
    # Check column names
    expected_cols = ["company_id", "type", "rule_id", "text", "confidence_pct"]
    assert list(df_pc.columns) == expected_cols
    
    # Check that confidence_pct > 60 for all entries
    assert (df_pc["confidence_pct"] > 60).all()
    
    # Verify every company has at least 1 pro and at least 1 con
    pros_set = set(df_pc[df_pc["type"] == "pro"]["company_id"])
    cons_set = set(df_pc[df_pc["type"] == "con"]["company_id"])
    assert len(pros_set) == 92
    assert len(cons_set) == 92
    
    # Verify rule_ids are valid
    assert df_pc["rule_id"].str.startswith(("PRO_", "CON_")).all()


def test_cashflow_intelligence_module():
    df_intel, df_distress, df_pattern = generate_cashflow_intelligence("data/db/nifty100.db", "output")
    assert os.path.exists("output/cashflow_intelligence.xlsx")
    assert os.path.exists("output/distress_alerts.csv")
    assert os.path.exists("output/pattern_changes.csv")
    
    assert len(df_intel) == 92
    expected_cols = [
        "company_id", "sector", "cfo_quality_score", "cfo_quality_label",
        "capex_intensity_pct", "capex_label", "fcf_cagr_5yr", "fcf_conversion_pct",
        "distress_flag", "deleveraging_flag", "capital_allocation_label"
    ]
    assert list(df_intel.columns) == expected_cols
    
    # Verify CFO quality labels are valid
    valid_cfo_labels = {"High Quality", "Moderate", "Accrual Risk"}
    assert set(df_intel["cfo_quality_label"]).issubset(valid_cfo_labels)
    
    # Verify CapEx labels are valid
    valid_capex_labels = {"Asset Light", "Moderate", "Capital Intensive"}
    assert set(df_intel["capex_label"]).issubset(valid_capex_labels)
    
    # Verify flags are binary
    assert df_intel["distress_flag"].isin([0, 1]).all()
    assert df_intel["deleveraging_flag"].isin([0, 1]).all()


def test_batch_tearsheets():
    pdf_files = glob.glob("reports/tearsheets/*.pdf")
    assert len(pdf_files) == 92
    for pdf_path in pdf_files:
        size = os.path.getsize(pdf_path)
        assert size >= 30 * 1024, f"{pdf_path} is only {size/1024:.1f} KB, expected >= 30 KB"


def test_batch_sector_reports():
    sector_pdfs = glob.glob("reports/sector/*.pdf")
    assert len(sector_pdfs) == 11
    for pdf_path in sector_pdfs:
        assert os.path.getsize(pdf_path) > 2.5 * 1024, f"{pdf_path} too small"


def test_portfolio_summary_report():
    pdf_path = "reports/portfolio/portfolio_summary.pdf"
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 50 * 1024
