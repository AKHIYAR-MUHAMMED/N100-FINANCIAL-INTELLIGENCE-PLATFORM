"""
Financial Risk Analytics & Monte Carlo Simulation Module.

Provides institutional risk modeling capabilities including:
- Value at Risk (VaR): Historical & Parametric
- Conditional Value at Risk (CVaR / Expected Shortfall)
- Sharpe and Sortino Risk-Adjusted Return Ratios
- Maximum Drawdown and Peak-to-Trough Recovery
- Monte Carlo Scenario Forecasting for Revenue and Cash Flow Projections
"""

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


def calculate_historical_var(
    returns: List[float],
    confidence_level: float = 0.95
) -> float:
    """
    Calculate Historical Value at Risk (VaR) at a given confidence level.
    VaR represents the maximum expected loss over a specific horizon at confidence level.
    Returns positive value representing loss magnitude.
    """
    if not returns:
        return 0.0
    
    clean_returns = [r for r in returns if r is not None and not np.isnan(r)]
    if not clean_returns:
        return 0.0
    
    percentile_cutoff = (1.0 - confidence_level) * 100.0
    var_cutoff = float(np.percentile(clean_returns, percentile_cutoff))
    # Return as positive loss magnitude if negative, or 0 if all positive returns
    return max(0.0, -var_cutoff)


def calculate_parametric_var(
    mean_return: float,
    std_dev: float,
    confidence_level: float = 0.95
) -> float:
    """
    Calculate Parametric (Gaussian) Value at Risk.
    Uses Z-score distribution approximation:
    90% -> 1.282, 95% -> 1.645, 99% -> 2.326
    """
    if std_dev <= 0:
        return max(0.0, -mean_return)
    
    # Common standard normal inverse CDF values
    if math.isclose(confidence_level, 0.95, abs_tol=0.01):
        z_score = 1.6448536269514722
    elif math.isclose(confidence_level, 0.99, abs_tol=0.01):
        z_score = 2.3263478740408408
    elif math.isclose(confidence_level, 0.90, abs_tol=0.01):
        z_score = 1.2815515655446004
    else:
        # Simple polynomial approximation of normal quantile
        # rational approximation for standard normal inverse
        p = 1.0 - confidence_level
        if p > 0.5:
            z_score = 0.0
        else:
            t = math.sqrt(-2.0 * math.log(p))
            c0, c1, c2 = 2.515517, 0.802853, 0.010328
            d1, d2, d3 = 1.432788, 0.189269, 0.001308
            z_score = t - ((c2 * t + c1) * t + c0) / (((d3 * t + d2) * t + d1) * t + 1.0)
            
    var_estimate = -(mean_return - z_score * std_dev)
    return max(0.0, float(var_estimate))


def calculate_cvar(
    returns: List[float],
    confidence_level: float = 0.95
) -> float:
    """
    Calculate Conditional Value at Risk (CVaR / Expected Shortfall).
    CVaR is the expected loss given that the loss exceeds the VaR threshold.
    """
    if not returns:
        return 0.0
    
    clean_returns = np.array([r for r in returns if r is not None and not np.isnan(r)], dtype=float)
    if len(clean_returns) == 0:
        return 0.0
    
    percentile_cutoff = (1.0 - confidence_level) * 100.0
    var_threshold = np.percentile(clean_returns, percentile_cutoff)
    
    tail_losses = clean_returns[clean_returns <= var_threshold]
    if len(tail_losses) == 0:
        return max(0.0, float(-var_threshold))
    
    expected_shortfall = float(np.mean(tail_losses))
    return max(0.0, -expected_shortfall)


def calculate_sharpe_ratio(
    returns: List[float],
    risk_free_rate: float = 0.065,
    periods_per_year: int = 1
) -> float:
    """
    Calculate the Sharpe Ratio measuring risk-adjusted excess returns.
    Sharpe = (Mean Return - Rf) / Volatility
    """
    clean_returns = [r for r in returns if r is not None and not np.isnan(r)]
    if len(clean_returns) < 2:
        return 0.0
    
    mean_ret = float(np.mean(clean_returns)) * periods_per_year
    vol = float(np.std(clean_returns, ddof=1)) * math.sqrt(periods_per_year)
    
    if vol == 0.0 or math.isclose(vol, 0.0, abs_tol=1e-8):
        return 0.0
    
    return round((mean_ret - risk_free_rate) / vol, 4)


def calculate_sortino_ratio(
    returns: List[float],
    target_return: float = 0.0,
    periods_per_year: int = 1
) -> float:
    """
    Calculate the Sortino Ratio penalizing only downside volatility.
    Sortino = (Mean Return - Target) / Downside Deviation
    """
    clean_returns = np.array([r for r in returns if r is not None and not np.isnan(r)], dtype=float)
    if len(clean_returns) < 2:
        return 0.0
    
    mean_ret = float(np.mean(clean_returns)) * periods_per_year
    downside = clean_returns[clean_returns < target_return] - target_return
    
    if len(downside) == 0:
        return 0.0
    
    downside_dev = math.sqrt(float(np.mean(downside ** 2))) * math.sqrt(periods_per_year)
    if downside_dev == 0.0:
        return 0.0
    
    return round((mean_ret - target_return) / downside_dev, 4)


def calculate_max_drawdown(values: List[float]) -> Tuple[float, int, int]:
    """
    Compute Maximum Drawdown (MDD) from a sequence of portfolio/equity values.
    Returns:
        (max_drawdown_percentage, peak_index, trough_index)
    """
    if not values or len(values) < 2:
        return (0.0, 0, 0)
    
    max_dd = 0.0
    peak_idx = 0
    trough_idx = 0
    current_peak_idx = 0
    current_peak_val = values[0]
    
    for i, val in enumerate(values):
        if val > current_peak_val:
            current_peak_val = val
            current_peak_idx = i
        else:
            if current_peak_val > 0:
                dd = (current_peak_val - val) / current_peak_val
                if dd > max_dd:
                    max_dd = dd
                    peak_idx = current_peak_idx
                    trough_idx = i
                    
    return (round(max_dd, 4), peak_idx, trough_idx)


def monte_carlo_forecast(
    initial_value: float,
    mean_growth: float,
    volatility: float,
    periods: int = 5,
    n_simulations: int = 1000,
    seed: Optional[int] = 42
) -> Dict[str, Any]:
    """
    Generate Geometric Brownian Motion (GBM) Monte Carlo forward trajectories.
    
    Returns:
        Dictionary containing percentiles (10th, 25th, 50th, 75th, 90th) at each period,
        final mean, and confidence intervals.
    """
    if initial_value <= 0 or periods <= 0 or n_simulations <= 0:
        return {
            "initial_value": initial_value,
            "periods": periods,
            "simulations": n_simulations,
            "median_trajectory": [initial_value] * (periods + 1),
            "p10_trajectory": [initial_value] * (periods + 1),
            "p90_trajectory": [initial_value] * (periods + 1),
            "final_expected_value": initial_value
        }
    
    if seed is not None:
        np.random.seed(seed)
    
    dt = 1.0
    drift = mean_growth - 0.5 * (volatility ** 2)
    
    # Simulation matrix: shape (n_simulations, periods + 1)
    trajectories = np.zeros((n_simulations, periods + 1))
    trajectories[:, 0] = initial_value
    
    for t in range(1, periods + 1):
        random_shocks = np.random.normal(0, 1, n_simulations)
        growth_factors = np.exp(drift * dt + volatility * math.sqrt(dt) * random_shocks)
        trajectories[:, t] = trajectories[:, t - 1] * growth_factors
    
    p10 = np.percentile(trajectories, 10, axis=0).round(2).tolist()
    p25 = np.percentile(trajectories, 25, axis=0).round(2).tolist()
    p50 = np.percentile(trajectories, 50, axis=0).round(2).tolist()
    p75 = np.percentile(trajectories, 75, axis=0).round(2).tolist()
    p90 = np.percentile(trajectories, 90, axis=0).round(2).tolist()
    
    final_values = trajectories[:, -1]
    
    return {
        "initial_value": initial_value,
        "periods": periods,
        "simulations": n_simulations,
        "mean_growth": mean_growth,
        "volatility": volatility,
        "p10_trajectory": p10,
        "p25_trajectory": p25,
        "median_trajectory": p50,
        "p75_trajectory": p75,
        "p90_trajectory": p90,
        "final_expected_value": round(float(np.mean(final_values)), 2),
        "final_median_value": round(float(p50[-1]), 2),
        "final_p10_value": round(float(p10[-1]), 2),
        "final_p90_value": round(float(p90[-1]), 2)
    }
