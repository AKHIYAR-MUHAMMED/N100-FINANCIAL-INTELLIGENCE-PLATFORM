import pytest
import numpy as np
from src.analytics.risk import (
    calculate_historical_var,
    calculate_parametric_var,
    calculate_cvar,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown,
    monte_carlo_forecast
)


def test_historical_var():
    returns = [-0.05, -0.02, 0.01, 0.03, 0.04, -0.01, 0.02, 0.05, -0.03, 0.02]
    var_95 = calculate_historical_var(returns, confidence_level=0.95)
    assert var_95 > 0.0
    assert var_95 >= 0.03

    # Empty and None handling
    assert calculate_historical_var([]) == 0.0
    assert calculate_historical_var([None, np.nan]) == 0.0


def test_parametric_var():
    mean_ret = 0.12
    std_dev = 0.20
    var_95 = calculate_parametric_var(mean_ret, std_dev, confidence_level=0.95)
    # Expected: -(0.12 - 1.645 * 0.20) = -(0.12 - 0.329) = 0.209
    assert 0.20 <= var_95 <= 0.22

    var_99 = calculate_parametric_var(mean_ret, std_dev, confidence_level=0.99)
    assert var_99 > var_95

    # Zero volatility
    assert calculate_parametric_var(0.10, 0.0) == 0.0
    assert calculate_parametric_var(-0.05, 0.0) == 0.05


def test_cvar_expected_shortfall():
    returns = [-0.10, -0.08, -0.05, 0.02, 0.04, 0.06, 0.08]
    cvar_90 = calculate_cvar(returns, confidence_level=0.90)
    var_90 = calculate_historical_var(returns, confidence_level=0.90)
    
    # CVaR is greater than or equal to VaR by definition
    assert cvar_90 >= var_90
    assert calculate_cvar([]) == 0.0


def test_sharpe_ratio():
    returns = [0.10, 0.15, 0.12, 0.18, 0.14]
    sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.06, periods_per_year=1)
    assert sharpe > 0.0

    # Constant returns (zero std dev)
    assert calculate_sharpe_ratio([0.10, 0.10, 0.10]) == 0.0
    assert calculate_sharpe_ratio([0.10]) == 0.0


def test_sortino_ratio():
    returns = [0.15, -0.05, 0.20, 0.10, -0.02, 0.25]
    sortino = calculate_sortino_ratio(returns, target_return=0.05)
    assert sortino > 0.0

    # No downside deviation
    assert calculate_sortino_ratio([0.10, 0.15, 0.20], target_return=0.0) == 0.0
    assert calculate_sortino_ratio([]) == 0.0


def test_max_drawdown():
    prices = [100.0, 120.0, 110.0, 90.0, 130.0, 125.0]
    mdd, peak_idx, trough_idx = calculate_max_drawdown(prices)
    # Peak at 120.0 (idx 1), Trough at 90.0 (idx 3) -> Drawdown = (120 - 90)/120 = 25% (0.25)
    assert mdd == 0.25
    assert peak_idx == 1
    assert trough_idx == 3

    assert calculate_max_drawdown([]) == (0.0, 0, 0)
    assert calculate_max_drawdown([100.0]) == (0.0, 0, 0)


def test_monte_carlo_forecast():
    result = monte_carlo_forecast(
        initial_value=1000.0,
        mean_growth=0.10,
        volatility=0.15,
        periods=5,
        n_simulations=500,
        seed=42
    )

    assert result["initial_value"] == 1000.0
    assert len(result["median_trajectory"]) == 6
    assert result["median_trajectory"][0] == 1000.0
    assert result["final_expected_value"] > 1000.0
    assert result["final_p10_value"] <= result["final_median_value"] <= result["final_p90_value"]

    # Edge cases
    edge_res = monte_carlo_forecast(0.0, 0.1, 0.1, periods=5)
    assert edge_res["final_expected_value"] == 0.0
