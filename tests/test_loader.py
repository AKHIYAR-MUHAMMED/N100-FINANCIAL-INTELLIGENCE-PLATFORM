import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.loader import load_excel_data, normalize_ticker, normalize_year

# ==============================================================================
# Tests for normalize_year()
# ==============================================================================


@pytest.mark.parametrize(
    "year,expected",
    [
        (2026, 2026),
        (2026.0, 2026),
        ("2026", 2026),
        (" 2026 ", 2026),
        ("2026.0", 2026),
    ],
)
def test_normalize_year_standard(year, expected):
    """Test 4-digit valid year inputs of different types."""
    assert normalize_year(year) == expected


@pytest.mark.parametrize(
    "year,expected",
    [
        (26, 2026),
        (26.0, 2026),
        ("26", 2026),
        ("26.0", 2026),
        (0, 2000),
        ("00", 2000),
        (49, 2049),
        ("49", 2049),
    ],
)
def test_normalize_year_2digit_under_50(year, expected):
    """Test 2-digit years mapped to 20XX (< 50 pivot)."""
    assert normalize_year(year) == expected


@pytest.mark.parametrize(
    "year,expected",
    [
        (99, 1999),
        (99.0, 1999),
        ("99", 1999),
        ("99.0", 1999),
        (50, 1950),
        ("50", 1950),
        (75, 1975),
        ("75", 1975),
    ],
)
def test_normalize_year_2digit_over_50(year, expected):
    """Test 2-digit years mapped to 19XX (>= 50 pivot)."""
    assert normalize_year(year) == expected


def test_normalize_year_datetime_objects():
    """Test datetime, date, and pandas Timestamps."""
    dt = datetime.datetime(2026, 7, 8, 12, 34, 56)
    d = datetime.date(2026, 7, 8)
    ts = pd.Timestamp("2026-07-08")
    assert normalize_year(dt) == 2026
    assert normalize_year(d) == 2026
    assert normalize_year(ts) == 2026


@pytest.mark.parametrize(
    "date_str",
    [
        "2026-07-08",
        "08-07-2026",
        "07/08/2026",
        "July 8, 2026",
        "2026/07/08 12:00:00",
    ],
)
def test_normalize_year_parseable_date_strings(date_str):
    """Test standard date string formats from which year can be parsed."""
    assert normalize_year(date_str) == 2026


@pytest.mark.parametrize(
    "invalid_input",
    [
        None,
        np.nan,
        float("nan"),
        float("inf"),
        float("-inf"),
        "invalid_year",
        "2026-abc",
        "",
        "   ",
        100,  # Too small for 4-digit, too large for 2-digit
        999,  # Too small for 4-digit, too large for 2-digit
        10000,  # Too large (5-digit)
    ],
)
def test_normalize_year_invalid_values(invalid_input):
    """Test value errors for unparseable or out of bounds years."""
    with pytest.raises(ValueError):
        normalize_year(invalid_input)


@pytest.mark.parametrize(
    "invalid_type",
    [
        True,
        False,
        [],
        {},
        (2026,),
    ],
)
def test_normalize_year_invalid_types(invalid_type):
    """Test type errors for unsupported data types."""
    with pytest.raises(TypeError):
        normalize_year(invalid_type)


# ==============================================================================
# Tests for normalize_ticker()
# ==============================================================================


@pytest.mark.parametrize(
    "ticker,expected",
    [
        ("RELIANCE", "RELIANCE"),
        ("reliance", "RELIANCE"),
        ("  Reliance  ", "RELIANCE"),
        ("reliance.ns", "RELIANCE"),
        ("TCS.NS", "TCS"),
        ("INFY.BO", "INFY"),
        ("SBIN.BSE", "SBIN"),
        ("HDFCBANK.NSE", "HDFCBANK"),
    ],
)
def test_normalize_ticker_standard(ticker, expected):
    """Test various casings, spaces, and exchange suffixes."""
    assert normalize_ticker(ticker) == expected


def test_normalize_ticker_numeric():
    """Test numeric values converted to standard ticker strings."""
    assert normalize_ticker(12345) == "12345"
    assert normalize_ticker(12345.0) == "12345"


@pytest.mark.parametrize(
    "invalid_input",
    [
        None,
        np.nan,
        "",
        "   ",
        ".NS",  # becomes empty after stripping suffix
        "  .BO  ",  # becomes empty after stripping suffix
    ],
)
def test_normalize_ticker_invalid_values(invalid_input):
    """Test invalid ticker values that should raise ValueError."""
    with pytest.raises(ValueError):
        normalize_ticker(invalid_input)


@pytest.mark.parametrize(
    "invalid_type",
    [
        True,
        False,
        [],
        {},
        ("TCS",),
    ],
)
def test_normalize_ticker_invalid_types(invalid_type):
    """Test type errors for unsupported ticker types."""
    with pytest.raises(TypeError):
        normalize_ticker(invalid_type)


def test_normalize_ticker_multiple_dots():
    """Test ticker normalisation for tickers with multiple periods."""
    # Suffix is removed, but middle dot is preserved
    assert normalize_ticker("NIFTY.50.NS") == "NIFTY.50"
    assert normalize_ticker("COM.RELIANCE") == "COM.RELIANCE"


# ==============================================================================
# Tests for load_excel_data()
# ==============================================================================


def test_load_excel_data_missing_file():
    """Test that a missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_excel_data(Path("non_existent_file.xlsx"))


def test_load_excel_data_invalid_file(tmp_path):
    """Test that a corrupted or invalid file raises ValueError."""
    bad_file = tmp_path / "bad_file.xlsx"
    bad_file.write_text("not a real excel file")
    with pytest.raises(ValueError):
        load_excel_data(bad_file)


def test_load_excel_data_success(tmp_path):
    """Test successful reading of a valid Excel sheet."""
    excel_file = tmp_path / "test_data.xlsx"
    df_expected = pd.DataFrame({"Ticker": ["TCS", "RELIANCE"], "Year": [2026, 2025]})

    # Save to Excel
    df_expected.to_excel(excel_file, index=False)

    # Load and verify
    df_loaded = load_excel_data(excel_file)
    pd.testing.assert_frame_equal(df_loaded, df_expected)
