import pytest
import os
import pandas as pd
from src.reports.tearsheet import build_tearsheet
from src.reports.sector_report import build_sector_report


def test_tearsheet_single_generation():
    success, msg = build_tearsheet("COMP01", "data/db/nifty100.db", "reports/tearsheets")
    assert success
    pdf_path = "reports/tearsheets/COMP01_tearsheet.pdf"
    assert os.path.exists(pdf_path)
    # File size > 30 KB
    assert os.path.getsize(pdf_path) >= 30 * 1024


def test_sector_report_single_generation():
    success, msg = build_sector_report("IT Services", "data/db/nifty100.db", "reports/sector")
    assert success
    pdf_path = "reports/sector/IT Services_report.pdf"
    assert os.path.exists(pdf_path)
