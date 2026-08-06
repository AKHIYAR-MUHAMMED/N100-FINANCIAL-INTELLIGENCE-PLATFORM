import pytest
import pandas as pd
import numpy as np


def compute_overvaluation_flag(pe_ratio: float, sector_median_pe: float) -> str:
    """
    Computes overvaluation flag based on 1.5x and 0.7x sector median thresholds.
    """
    if pd.isna(pe_ratio) or pd.isna(sector_median_pe) or sector_median_pe <= 0:
        return "UNKNOWN"
    if pe_ratio > 1.5 * sector_median_pe:
        return "OVERVALUED"
    elif pe_ratio < 0.7 * sector_median_pe:
        return "UNDERVALUED"
    return "FAIRLY_VALUED"


def calculate_debt_equity_health(debt_to_equity: float) -> str:
    """
    Evaluates financial leverage risk level from debt to equity ratio.
    """
    if pd.isna(debt_to_equity):
        return "UNKNOWN"
    if debt_to_equity < 0.5:
        return "LOW_RISK"
    elif debt_to_equity <= 1.5:
        return "MODERATE_RISK"
    return "HIGH_RISK"


def test_overvaluation_flag_overvalued():
    assert compute_overvaluation_flag(30.0, 15.0) == "OVERVALUED"


def test_overvaluation_flag_undervalued():
    assert compute_overvaluation_flag(9.0, 15.0) == "UNDERVALUED"


def test_overvaluation_flag_fairly_valued():
    assert compute_overvaluation_flag(18.0, 15.0) == "FAIRLY_VALUED"


def test_overvaluation_flag_edge_cases():
    assert compute_overvaluation_flag(np.nan, 15.0) == "UNKNOWN"
    assert compute_overvaluation_flag(20.0, np.nan) == "UNKNOWN"
    assert compute_overvaluation_flag(20.0, 0.0) == "UNKNOWN"


def test_debt_equity_health_levels():
    assert calculate_debt_equity_health(0.2) == "LOW_RISK"
    assert calculate_debt_equity_health(1.0) == "MODERATE_RISK"
    assert calculate_debt_equity_health(2.5) == "HIGH_RISK"
    assert calculate_debt_equity_health(np.nan) == "UNKNOWN"
