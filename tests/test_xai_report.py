import os
from src.reports.url_explainable_ai_report import ExplainableAIReportEngine


def test_xai_report_generation(tmp_path):
    output_dir = str(tmp_path / "xai_reports")
    engine = ExplainableAIReportEngine(output_dir=output_dir)
    
    output_pdf = os.path.join(output_dir, "test_xai_report.pdf")
    pdf_path = engine.generate_pdf_report(
        site_url="https://example.com/analytics",
        company_ticker="COMP01",
        output_filename=output_pdf
    )
    
    assert os.path.exists(pdf_path)
    # Verify file size > 30 KB
    assert os.path.getsize(pdf_path) > 30 * 1024
