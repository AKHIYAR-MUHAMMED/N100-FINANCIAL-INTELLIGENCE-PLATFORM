import pytest
import os
import pandas as pd
from src.nlp.parser import parse_analysis_text
from src.nlp.pros_cons_generator import generate_pros_cons


def test_nlp_parser_execution():
    df_parsed, df_failures = parse_analysis_text("data/raw/analysis.xlsx", "output")
    assert not df_parsed.empty
    assert "company_id" in df_parsed.columns
    assert "metric_type" in df_parsed.columns
    assert "period_years" in df_parsed.columns
    assert "value_pct" in df_parsed.columns
    assert os.path.exists("output/analysis_parsed.csv")
    assert os.path.exists("output/parse_failures.csv")


def test_pros_cons_generator_execution():
    df_pros_cons = generate_pros_cons("data/db/nifty100.db", "output")
    assert not df_pros_cons.empty
    assert "company_id" in df_pros_cons.columns
    assert "type" in df_pros_cons.columns
    assert "rule_id" in df_pros_cons.columns
    assert "text" in df_pros_cons.columns
    assert "confidence_pct" in df_pros_cons.columns
    
    # Check that all companies have at least 1 pro and at least 1 con
    pros_comps = set(df_pros_cons[df_pros_cons["type"] == "pro"]["company_id"])
    cons_comps = set(df_pros_cons[df_pros_cons["type"] == "con"]["company_id"])
    
    assert len(pros_comps) >= 92
    assert len(cons_comps) >= 92
