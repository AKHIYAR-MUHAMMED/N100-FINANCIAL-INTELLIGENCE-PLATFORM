import os
import pytest
from src.analytics.dupont import (
    calculate_dupont_3step,
    calculate_dupont_5step,
    analyze_company_dupont,
)

def test_calculate_dupont_3step_valid():
    # Net Income = 100, Revenue = 1000, Assets = 2000, Equity = 800
    # NPM = 10.0%, Asset Turnover = 0.5, Equity Multiplier = 2.5
    # ROE = 10.0% * 0.5 * 2.5 = 12.5%
    result = calculate_dupont_3step(
        net_income=100.0,
        revenue=1000.0,
        total_assets=2000.0,
        total_equity=800.0,
    )
    assert result["net_profit_margin"] == 10.0
    assert result["asset_turnover"] == 0.5
    assert result["equity_multiplier"] == 2.5
    assert result["calculated_roe"] == 12.5


def test_calculate_dupont_3step_zero_division():
    result = calculate_dupont_3step(
        net_income=100.0,
        revenue=0.0,
        total_assets=1000.0,
        total_equity=500.0,
    )
    assert result["calculated_roe"] is None
    assert result["net_profit_margin"] is None


def test_calculate_dupont_5step_valid():
    # Net Income = 80, EBT = 100, EBIT = 150, Revenue = 1000, Assets = 2000, Equity = 800
    # Tax Burden = 80/100 = 0.8
    # Interest Burden = 100/150 = 0.6667
    # Operating Margin = 150/1000 = 15.0%
    # Asset Turnover = 1000/2000 = 0.5
    # Equity Multiplier = 2000/800 = 2.5
    # ROE = 0.8 * 0.6667 * 0.15 * 0.5 * 2.5 * 100 = 10.0%
    result = calculate_dupont_5step(
        net_income=80.0,
        ebt=100.0,
        ebit=150.0,
        revenue=1000.0,
        total_assets=2000.0,
        total_equity=800.0,
    )
    assert result["tax_burden"] == 0.8
    assert result["interest_burden"] == 0.6667
    assert result["operating_margin"] == 15.0
    assert result["asset_turnover"] == 0.5
    assert result["equity_multiplier"] == 2.5
    assert result["calculated_roe"] == 10.0


def test_calculate_dupont_5step_invalid():
    result = calculate_dupont_5step(
        net_income=80.0,
        ebt=0.0,
        ebit=150.0,
        revenue=1000.0,
        total_assets=2000.0,
        total_equity=800.0,
    )
    assert result["calculated_roe"] is None


def test_analyze_company_dupont_integration():
    db_path = os.path.join(os.path.dirname(__file__), "..", "db", "financials.db")
    if os.path.exists(db_path):
        result = analyze_company_dupont(db_path, "COMP01")
        assert result["company_id"] == "COMP01"
        assert len(result["history"]) > 0
        first_year = result["history"][0]
        assert "three_step" in first_year
        assert "five_step" in first_year
