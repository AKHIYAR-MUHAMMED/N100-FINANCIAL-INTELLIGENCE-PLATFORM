import datetime
from typing import Any

import numpy as np
import pandas as pd


def normalize_year(year: Any) -> int:
    """Normalise year representation to a 4-digit integer.

    Acceptable inputs:
    - 4-digit integer or float: 2026, 2026.0 -> 2026
    - 2-digit integer or float: 26, 26.0 -> 2026
      (assumes pivot year 50: <50 -> 20XX, >=50 -> 19XX)
    - 4-digit or 2-digit string: "2026", "26" -> 2026
    - Datetime-like objects (datetime, date, Timestamp)
    - Standard date strings that can be parsed (extracts year)

    Raises:
        ValueError: If the year is invalid or cannot be parsed/normalised.
        TypeError: If the input type is unsupported.
    """
    if year is None or (isinstance(year, float) and pd.isna(year)):
        raise ValueError("Year cannot be null or empty")

    if isinstance(year, bool):
        raise TypeError("Boolean values are not supported for year normalization")

    # Handle datetime/date/Timestamp objects
    if isinstance(year, (datetime.datetime, datetime.date, pd.Timestamp)):
        return year.year

    # If input is string
    if isinstance(year, str):
        year_str = year.strip()
        if not year_str:
            raise ValueError("Year cannot be empty string")

        # Remove any leading single quotes if formatted as text in Excel (e.g. "'2026")
        if year_str.startswith("'"):
            year_str = year_str[1:]

        # Try converting directly to float first (handles "2026.0", "2026", "26")
        try:
            val = float(year_str)
        except ValueError:
            # If direct conversion fails, try parsing as a generic date string
            try:
                dt = pd.to_datetime(year_str, errors="raise")
                return dt.year
            except Exception:
                raise ValueError(f"Could not parse year string: {year}")
    elif isinstance(year, (int, float, np.integer, np.floating)):
        val = float(year)
    else:
        raise TypeError(f"Unsupported type for year: {type(year)}")

    # Check for NaN or infinity values
    if pd.isna(val) or not np.isfinite(val):
        raise ValueError(f"Invalid numeric year: {year}")

    val_int = int(round(val))

    # Handle 2-digit years
    if 0 <= val_int <= 99:
        if val_int < 50:
            return 2000 + val_int
        else:
            return 1900 + val_int

    # Handle 4-digit years
    if 1000 <= val_int <= 9999:
        return val_int

    raise ValueError(f"Year out of bounds: {year}")


def normalize_ticker(ticker: Any) -> str:
    """Normalise stock ticker symbols.

    Normalisation steps:
    1. Check for null values.
    2. Convert to string and strip whitespace.
    3. Convert to uppercase.
    4. Remove common exchange suffixes (e.g., .NS, .BO, .BSE, .NSE).

    Raises:
        ValueError: If the ticker is empty or invalid.
        TypeError: If the input cannot be converted to a ticker string.
    """
    if ticker is None or (isinstance(ticker, float) and pd.isna(ticker)):
        raise ValueError("Ticker cannot be null or empty")

    if isinstance(ticker, bool):
        raise TypeError("Boolean values are not supported for ticker normalization")

    if isinstance(ticker, (int, float, np.integer, np.floating)):
        val = float(ticker)
        if pd.isna(val) or not np.isfinite(val):
            raise ValueError("Ticker cannot be NaN or infinite")
        # Format whole float numbers to int string (e.g., 12345.0 -> '12345')
        if val.is_integer():
            ticker_str = str(int(val))
        else:
            ticker_str = str(ticker)
    elif isinstance(ticker, str):
        ticker_str = ticker.strip()
    else:
        raise TypeError(f"Unsupported type for ticker: {type(ticker)}")

    if not ticker_str:
        raise ValueError("Ticker cannot be empty string")

    normalized = ticker_str.upper()

    # Remove standard exchange suffixes
    for suffix in [".NS", ".BO", ".BSE", ".NSE"]:
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break

    normalized = normalized.strip()
    if not normalized:
        raise ValueError(f"Ticker became empty after normalisation: {ticker}")

    return normalized
