import os
import pandas as pd
import pytest
from src.screener.multi_factor import (
    MultiFactorWeights,
    calculate_multi_factor_scores,
    rank_companies_from_db,
)


def test_multi_factor_weights_normalize():
    weights = MultiFactorWeights(1.0, 1.0, 1.0, 1.0)
    norm = weights.normalize()
    assert norm.growth_weight == 0.25
    assert norm.value_weight == 0.25


def test_calculate_multi_factor_scores():
    df = pd.DataFrame([
        {
            "company_id": "C1",
            "roe": 25.0,
            "roce": 28.0,
            "pe_ratio": 15.0,
            "pb_ratio": 2.5,
            "sales_growth": 20.0,
            "debt_to_equity": 0.2,
        },
        {
            "company_id": "C2",
            "roe": 12.0,
            "roce": 14.0,
            "pe_ratio": 35.0,
            "pb_ratio": 5.0,
            "sales_growth": 5.0,
            "debt_to_equity": 1.5,
        },
    ])
    scored = calculate_multi_factor_scores(df)
    assert len(scored) == 2
    assert "composite_score" in scored.columns
    assert "rank" in scored.columns
    # C1 should rank 1st because of better growth, lower PE, higher ROE, lower debt
    assert scored.iloc[0]["company_id"] == "C1"
    assert scored.iloc[0]["rank"] == 1


def test_rank_companies_from_db_integration():
    db_path = os.path.join(os.path.dirname(__file__), "..", "db", "financials.db")
    if os.path.exists(db_path):
        results = rank_companies_from_db(db_path)
        assert isinstance(results, list)
        if results:
            assert "composite_score" in results[0]
            assert "rank" in results[0]
