import pytest
from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_return_on_equity,
    calculate_return_on_capital_employed,
    calculate_return_on_assets,
    calculate_debt_to_equity,
    calculate_interest_coverage,
    calculate_net_debt,
    calculate_asset_turnover,
)
from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cfo_quality_score,
    calculate_capex_intensity,
    calculate_fcf_conversion_rate,
    classify_capital_allocation,
)

# ==============================================================================
# DAY 08: PROFITABILITY RATIOS TESTS (8+ tests required)
# ==============================================================================

def test_npm_normal():
    # NPM: net_profit / sales * 100
    assert calculate_net_profit_margin(80.0, 1000.0) == 8.0

def test_npm_zero_sales():
    # NPM: returns None if sales == 0
    assert calculate_net_profit_margin(80.0, 0.0) is None

def test_opm_normal():
    # OPM: operating_profit / sales * 100
    assert calculate_operating_profit_margin(150.0, 1000.0) == 15.0

def test_opm_zero_sales():
    assert calculate_operating_profit_margin(150.0, 0.0) is None

def test_roe_normal():
    # ROE: net_profit / (equity_capital + reserves) * 100
    assert calculate_return_on_equity(120.0, 600.0, 400.0) == 12.0

def test_roe_zero_denominator():
    assert calculate_return_on_equity(120.0, 0.0, 0.0) is None

def test_roe_negative_equity():
    # ROE returns None if equity + reserves <= 0
    assert calculate_return_on_equity(120.0, -100.0, 50.0) is None
    assert calculate_return_on_equity(120.0, -200.0, -100.0) is None

def test_roce_normal():
    # ROCE: EBIT / (equity + reserves + borrowings) * 100
    assert calculate_return_on_capital_employed(150.0, 500.0, 300.0, 200.0) == 15.0

def test_roce_zero_denominator():
    assert calculate_return_on_capital_employed(150.0, -200.0, -100.0, 300.0) is None

def test_roa_normal():
    assert calculate_return_on_assets(80.0, 1000.0) == 8.0

def test_roa_zero_assets():
    assert calculate_return_on_assets(80.0, 0.0) is None
    assert calculate_return_on_assets(80.0, -500.0) is None


# ==============================================================================
# DAY 09: LEVERAGE & EFFICIENCY RATIOS TESTS (8+ tests required)
# ==============================================================================

def test_de_normal():
    # D/E: borrowings / (equity + reserves)
    assert calculate_debt_to_equity(200.0, 300.0, 100.0) == 0.5

def test_de_debt_free():
    # D/E debt-free returns 0 (not None)
    assert calculate_debt_to_equity(0.0, 300.0, 100.0) == 0.0

def test_de_negative_denominator():
    assert calculate_debt_to_equity(200.0, -100.0, 50.0) is None

def test_icr_normal():
    # ICR: (operating_profit + other_income) / interest
    assert calculate_interest_coverage(120.0, 30.0, 50.0) == 3.0

def test_icr_interest_zero():
    # ICR interest = 0 returns None
    assert calculate_interest_coverage(120.0, 30.0, 0.0) is None

def test_net_debt():
    # Net Debt = borrowings - investments
    assert calculate_net_debt(500.0, 200.0) == 300.0
    assert calculate_net_debt(100.0, 200.0) == -100.0

def test_asset_turnover():
    # Asset Turnover = sales / total_assets
    assert calculate_asset_turnover(1500.0, 1000.0) == 1.5

def test_asset_turnover_zero():
    assert calculate_asset_turnover(1500.0, 0.0) is None


# ==============================================================================
# DAY 10: CAGR ENGINE TESTS (10+ tests required)
# ==============================================================================

def test_cagr_normal():
    # Normal CAGR: start=100, end=144, n=2 -> 20.0%
    val, flag = calculate_cagr(100.0, 144.0, 2)
    assert val is not None
    assert pytest.approx(val, 0.001) == 20.0
    assert flag is None

def test_cagr_decline_to_loss():
    # Positive -> Negative/Zero: DECLINE_TO_LOSS
    val, flag = calculate_cagr(100.0, -10.0, 3)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"
    
    val, flag = calculate_cagr(100.0, 0.0, 3)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"

def test_cagr_turnaround():
    # Negative -> Positive/Zero: TURNAROUND
    val, flag = calculate_cagr(-50.0, 100.0, 3)
    assert val is None
    assert flag == "TURNAROUND"
    
    val, flag = calculate_cagr(-50.0, 0.0, 3)
    assert val is None
    assert flag == "TURNAROUND"

def test_cagr_both_negative():
    # Negative -> Negative: BOTH_NEGATIVE
    val, flag = calculate_cagr(-50.0, -100.0, 3)
    assert val is None
    assert flag == "BOTH_NEGATIVE"

def test_cagr_zero_base():
    # Start value is 0: ZERO_BASE
    val, flag = calculate_cagr(0.0, 100.0, 3)
    assert val is None
    assert flag == "ZERO_BASE"

def test_cagr_insufficient():
    # n_years <= 0: INSUFFICIENT
    val, flag = calculate_cagr(100.0, 200.0, 0)
    assert val is None
    assert flag == "INSUFFICIENT"


# ==============================================================================
# DAY 11: CASH FLOW & CAPITAL ALLOCATION TESTS
# ==============================================================================

def test_free_cash_flow():
    assert calculate_free_cash_flow(150.0, -100.0) == 50.0
    assert calculate_free_cash_flow(-50.0, -80.0) == -130.0

def test_cfo_quality_score_normal():
    cfo = [100, 110, 120, 130, 140]
    pat = [90, 100, 110, 120, 130]
    score = calculate_cfo_quality_score(cfo, pat)
    assert score is not None
    assert pytest.approx(score, 0.01) == 1.092  # Avg of (1.11, 1.1, 1.09, 1.08, 1.077)

def test_cfo_quality_score_insufficient():
    cfo = [100, 110]
    pat = [90, 100]
    assert calculate_cfo_quality_score(cfo, pat) is None

def test_cfo_quality_score_zero_pat():
    cfo = [100, 110, 120, 130, 140]
    pat = [90, 0, 110, 120, 130]
    assert calculate_cfo_quality_score(cfo, pat) is None

def test_capex_intensity():
    assert calculate_capex_intensity(-50.0, 1000.0) == 5.0
    assert calculate_capex_intensity(-100.0, 0.0) is None

def test_fcf_conversion_rate():
    assert calculate_fcf_conversion_rate(120.0, 300.0) == 40.0
    assert calculate_fcf_conversion_rate(120.0, 0.0) is None

def test_classify_capital_allocation():
    # (+, -, -) High CFO/PAT -> Shareholder Returns
    assert classify_capital_allocation(150.0, -100.0, -50.0, 1.2) == "Shareholder Returns"
    # (+, -, -) Low CFO/PAT -> Reinvestor
    assert classify_capital_allocation(150.0, -100.0, -50.0, 0.8) == "Reinvestor"
    # (+, +, -) -> Liquidating Assets
    assert classify_capital_allocation(100.0, 50.0, -30.0) == "Liquidating Assets"
    # (-, +, +) -> Distress Signal
    assert classify_capital_allocation(-50.0, 30.0, 20.0) == "Distress Signal"
    # (-, -, +) -> Growth Funded by Debt
    assert classify_capital_allocation(-50.0, -30.0, 80.0) == "Growth Funded by Debt"
    # (+, +, +) -> Cash Accumulator
    assert classify_capital_allocation(50.0, 30.0, 20.0) == "Cash Accumulator"
    # (-, -, -) -> Pre-Revenue
    assert classify_capital_allocation(-50.0, -30.0, -20.0) == "Pre-Revenue"
    # (+, -, +) -> Mixed
    assert classify_capital_allocation(100.0, -50.0, 20.0) == "Mixed"
