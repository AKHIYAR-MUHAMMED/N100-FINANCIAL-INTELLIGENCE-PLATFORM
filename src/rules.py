from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd


@dataclass
class ValidationFailure:
    company_ticker: str
    file_name: str
    row_index: Optional[int]
    rule_id: str
    severity: str  # 'CRITICAL' or 'WARNING'
    column_name: str
    invalid_value: Any
    message: str


class SchemaValidator:
    def __init__(self):
        self.failures: List[ValidationFailure] = []

    def log_failure(
        self,
        company_ticker: str,
        file_name: str,
        row_index: Optional[int],
        rule_id: str,
        severity: str,
        column_name: str,
        invalid_value: Any,
        message: str,
    ) -> None:
        """Helper to append a validation failure."""
        self.failures.append(
            ValidationFailure(
                company_ticker=str(company_ticker),
                file_name=str(file_name),
                row_index=row_index,
                rule_id=rule_id,
                severity=severity,
                column_name=column_name,
                invalid_value=invalid_value,
                message=message,
            )
        )

    def get_failures_df(self) -> pd.DataFrame:
        """Returns log failures as a pandas DataFrame."""
        if not self.failures:
            return pd.DataFrame(
                columns=[
                    "company_ticker",
                    "file_name",
                    "row_index",
                    "rule_id",
                    "severity",
                    "column_name",
                    "invalid_value",
                    "message",
                ]
            )
        return pd.DataFrame([asdict(f) for f in self.failures])

    def save_failures(self, output_path: Path) -> None:
        """Saves failures log to a CSV file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = self.get_failures_df()
        df.to_csv(output_path, index=False)

    def has_critical_failures(self) -> bool:
        """Checks if any critical failures were encountered."""
        return any(f.severity == "CRITICAL" for f in self.failures)

    # -------------------------------------------------------------------------
    # DQ-01 & DQ-02: Companies PK Checks
    # -------------------------------------------------------------------------
    def validate_companies(self, df: pd.DataFrame, file_name: str) -> None:
        """Validates the companies master DataFrame."""
        if df.empty:
            return

        ticker_col = "ticker"
        if ticker_col not in df.columns:
            self.log_failure(
                company_ticker="UNKNOWN",
                file_name=file_name,
                row_index=None,
                rule_id="DQ-02",
                severity="CRITICAL",
                column_name=ticker_col,
                invalid_value=None,
                message="Missing ticker primary key column in companies table",
            )
            return

        # DQ-02: PK Non-Null Check
        null_rows = df[
            df[ticker_col].isna() | (df[ticker_col].astype(str).str.strip() == "")
        ]
        for idx, row in null_rows.iterrows():
            self.log_failure(
                company_ticker="NULL",
                file_name=file_name,
                row_index=int(idx),
                rule_id="DQ-02",
                severity="CRITICAL",
                column_name=ticker_col,
                invalid_value=None,
                message="Company ticker is null or empty",
            )

        # DQ-01: PK Uniqueness Check
        duplicated_tickers = df[df[ticker_col].duplicated(keep=False)]
        for idx, row in duplicated_tickers.iterrows():
            ticker = row[ticker_col]
            self.log_failure(
                company_ticker=ticker,
                file_name=file_name,
                row_index=int(idx),
                rule_id="DQ-01",
                severity="CRITICAL",
                column_name=ticker_col,
                invalid_value=ticker,
                message=f"Duplicate ticker found: {ticker}",
            )

    # -------------------------------------------------------------------------
    # DQ-03 & DQ-04 & DQ-07 & DQ-08: Financials/Prices Integrity Checks
    # -------------------------------------------------------------------------
    def validate_relationships(
        self,
        df: pd.DataFrame,
        companies_df: pd.DataFrame,
        file_name: str,
        is_prices: bool = False,
    ) -> None:
        """Validates FK integrity constraints (DQ-03, DQ-04)."""
        if df.empty:
            return

        ticker_col = "ticker"
        if ticker_col not in df.columns:
            return

        valid_tickers = set()
        if not companies_df.empty and "ticker" in companies_df.columns:
            valid_tickers = set(companies_df["ticker"].dropna().unique())

        rule_id = "DQ-04" if is_prices else "DQ-03"

        # Check FK integrity
        for idx, row in df.iterrows():
            ticker = row[ticker_col]
            if pd.isna(ticker) or str(ticker).strip() == "":
                continue
            if ticker not in valid_tickers:
                self.log_failure(
                    company_ticker=ticker,
                    file_name=file_name,
                    row_index=int(idx),
                    rule_id=rule_id,
                    severity="CRITICAL",
                    column_name=ticker_col,
                    invalid_value=ticker,
                    message=f"Referential integrity failure: ticker '{ticker}' does not exist in companies master",
                )

    def validate_prices(self, df: pd.DataFrame, file_name: str) -> None:
        """Validates stock prices details (DQ-05, DQ-06, DQ-08, DQ-09, DQ-14, DQ-15)."""
        if df.empty:
            return

        ticker_col = "ticker"
        date_col = "date"

        # DQ-06: PK Non-Null Check
        for col in [ticker_col, date_col]:
            if col in df.columns:
                null_rows = df[df[col].isna()]
                for idx, row in null_rows.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    self.log_failure(
                        company_ticker=ticker,
                        file_name=file_name,
                        row_index=int(idx),
                        rule_id="DQ-06",
                        severity="CRITICAL",
                        column_name=col,
                        invalid_value=None,
                        message=f"Primary key field '{col}' is null in stock prices",
                    )

        # DQ-05: PK Uniqueness Check (ticker, date)
        if ticker_col in df.columns and date_col in df.columns:
            duplicates = df[df.duplicated(subset=[ticker_col, date_col], keep=False)]
            for idx, row in duplicates.iterrows():
                ticker = row[ticker_col]
                dt = row[date_col]
                self.log_failure(
                    company_ticker=ticker,
                    file_name=file_name,
                    row_index=int(idx),
                    rule_id="DQ-05",
                    severity="CRITICAL",
                    column_name=f"{ticker_col}, {date_col}",
                    invalid_value=f"({ticker}, {dt})",
                    message=f"Duplicate primary key entry found for ticker {ticker} on date {dt}",
                )

        # DQ-08: Date Validity
        if date_col in df.columns:
            for idx, row in df.iterrows():
                ticker = row.get(ticker_col, "UNKNOWN")
                dt = row[date_col]
                try:
                    pd.to_datetime(dt, errors="raise")
                except Exception:
                    self.log_failure(
                        company_ticker=ticker,
                        file_name=file_name,
                        row_index=int(idx),
                        rule_id="DQ-08",
                        severity="CRITICAL",
                        column_name=date_col,
                        invalid_value=dt,
                        message=f"Invalid date format: {dt}",
                    )

        # DQ-09: Positive Prices Check (open, high, low, close)
        price_cols = ["open", "high", "low", "close"]
        for col in price_cols:
            if col in df.columns:
                bad_prices = df[pd.to_numeric(df[col], errors="coerce") <= 0]
                for idx, row in bad_prices.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    val = row[col]
                    self.log_failure(
                        company_ticker=ticker,
                        file_name=file_name,
                        row_index=int(idx),
                        rule_id="DQ-09",
                        severity="CRITICAL",
                        column_name=col,
                        invalid_value=val,
                        message=f"Stock price must be positive. Found: {val}",
                    )

        # DQ-14: Positive Volume (Warning)
        vol_col = "volume"
        if vol_col in df.columns:
            bad_vols = df[pd.to_numeric(df[vol_col], errors="coerce") < 0]
            for idx, row in bad_vols.iterrows():
                ticker = row.get(ticker_col, "UNKNOWN")
                val = row[vol_col]
                self.log_failure(
                    company_ticker=ticker,
                    file_name=file_name,
                    row_index=int(idx),
                    rule_id="DQ-14",
                    severity="WARNING",
                    column_name=vol_col,
                    invalid_value=val,
                    message=f"Daily stock volume must be non-negative. Found: {val}",
                )

        # DQ-15: Price Consistency (Warning: high >= open, high >= close, high >= low, open >= low, close >= low)
        if all(c in df.columns for c in ["open", "high", "low", "close"]):
            for idx, row in df.iterrows():
                ticker = row.get(ticker_col, "UNKNOWN")
                o = pd.to_numeric(row["open"], errors="coerce")
                h = pd.to_numeric(row["high"], errors="coerce")
                low_val = pd.to_numeric(row["low"], errors="coerce")
                c = pd.to_numeric(row["close"], errors="coerce")

                if pd.isna(o) or pd.isna(h) or pd.isna(low_val) or pd.isna(c):
                    continue

                if not (
                    h >= o and h >= c and h >= low_val and o >= low_val and c >= low_val
                ):
                    self.log_failure(
                        company_ticker=ticker,
                        file_name=file_name,
                        row_index=int(idx),
                        rule_id="DQ-15",
                        severity="WARNING",
                        column_name="open, high, low, close",
                        invalid_value=f"O:{o}, H:{h}, L:{low_val}, C:{c}",
                        message="Inconsistent daily stock prices (High must be maximum and Low must be minimum)",
                    )

    def validate_financials(
        self, df: pd.DataFrame, file_name: str, sheet_type: str
    ) -> None:
        """Validates P&L, Balance Sheet, and Cash Flow statements."""
        if df.empty:
            return

        ticker_col = "ticker"
        year_col = "year"

        # DQ-07: PK Uniqueness Check (ticker, year)
        if ticker_col in df.columns and year_col in df.columns:
            duplicates = df[df.duplicated(subset=[ticker_col, year_col], keep=False)]
            for idx, row in duplicates.iterrows():
                ticker = row[ticker_col]
                yr = row[year_col]
                self.log_failure(
                    company_ticker=ticker,
                    file_name=file_name,
                    row_index=int(idx),
                    rule_id="DQ-07",
                    severity="CRITICAL",
                    column_name=f"{ticker_col}, {year_col}",
                    invalid_value=f"({ticker}, {yr})",
                    message=f"Duplicate primary key record found for ticker {ticker} in year {yr} ({sheet_type})",
                )

        # DQ-08: Year bounds check
        if year_col in df.columns:
            for idx, row in df.iterrows():
                ticker = row.get(ticker_col, "UNKNOWN")
                yr = row[year_col]
                try:
                    yr_val = int(yr)
                    if not (2000 <= yr_val <= 2030):
                        raise ValueError()
                except Exception:
                    self.log_failure(
                        company_ticker=ticker,
                        file_name=file_name,
                        row_index=int(idx),
                        rule_id="DQ-08",
                        severity="CRITICAL",
                        column_name=year_col,
                        invalid_value=yr,
                        message=f"Year is invalid or out of bounds [2000, 2030]: {yr}",
                    )

        # ---------------------------------------------------------------------
        # P&L Specific Checks (DQ-10, DQ-11, DQ-16)
        # ---------------------------------------------------------------------
        if sheet_type == "pnl":
            # DQ-10: Positive Sales (Warning)
            sales_col = next(
                (
                    c
                    for c in df.columns
                    if c.lower() in ["sales", "revenue", "total_revenue"]
                ),
                None,
            )
            if sales_col:
                bad_sales = df[pd.to_numeric(df[sales_col], errors="coerce") <= 0]
                for idx, row in bad_sales.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    val = row[sales_col]
                    self.log_failure(
                        company_ticker=ticker,
                        file_name=file_name,
                        row_index=int(idx),
                        rule_id="DQ-10",
                        severity="WARNING",
                        column_name=sales_col,
                        invalid_value=val,
                        message=f"Revenue/Sales should be positive. Found: {val}",
                    )

            # DQ-11: Operating Profit Margin (OPM) (Warning)
            # Checked if within [-1.0, 1.0] or [-100.0, 100.0] depending on reporting unit
            opm_col = next(
                (
                    c
                    for c in df.columns
                    if c.lower()
                    in ["opm", "operating_margin", "operating_profit_margin"]
                ),
                None,
            )
            if opm_col:
                for idx, row in df.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    val = pd.to_numeric(row[opm_col], errors="coerce")
                    if pd.isna(val):
                        continue
                    # Check absolute value bounds
                    if abs(val) > 1.0:
                        self.log_failure(
                            company_ticker=ticker,
                            file_name=file_name,
                            row_index=int(idx),
                            rule_id="DQ-11",
                            severity="WARNING",
                            column_name=opm_col,
                            invalid_value=val,
                            message=f"OPM is out of normal boundaries: {val}",
                        )

            # DQ-16: Logical Profit Order (Warning: gross_profit >= operating_profit >= net_income)
            gp_col = next(
                (c for c in df.columns if c.lower() in ["gross_profit", "gp"]), None
            )
            op_col = next(
                (c for c in df.columns if c.lower() in ["operating_profit", "op"]), None
            )
            ni_col = next(
                (
                    c
                    for c in df.columns
                    if c.lower() in ["net_income", "net_profit", "pat"]
                ),
                None,
            )
            if gp_col and op_col and ni_col:
                for idx, row in df.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    gp = pd.to_numeric(row[gp_col], errors="coerce")
                    op = pd.to_numeric(row[op_col], errors="coerce")
                    ni = pd.to_numeric(row[ni_col], errors="coerce")
                    if pd.isna(gp) or pd.isna(op) or pd.isna(ni):
                        continue
                    if not (gp >= op >= ni):
                        self.log_failure(
                            company_ticker=ticker,
                            file_name=file_name,
                            row_index=int(idx),
                            rule_id="DQ-16",
                            severity="WARNING",
                            column_name="gp, op, net_income",
                            invalid_value=f"GP:{gp}, OP:{op}, NI:{ni}",
                            message="Inconsistent profit ordering (Gross Profit >= Operating Profit >= Net Income)",
                        )

        # ---------------------------------------------------------------------
        # Balance Sheet Specific Checks (DQ-12)
        # ---------------------------------------------------------------------
        elif sheet_type == "bs":
            # DQ-12: Balance Check (Warning: Assets = Liabilities + Equity)
            asset_col = next(
                (c for c in df.columns if c.lower() in ["assets", "total_assets"]), None
            )
            liab_col = next(
                (
                    c
                    for c in df.columns
                    if c.lower() in ["liabilities", "total_liabilities"]
                ),
                None,
            )
            eq_col = next(
                (
                    c
                    for c in df.columns
                    if c.lower() in ["equity", "total_equity", "shareholders_equity"]
                ),
                None,
            )

            if asset_col and liab_col and eq_col:
                for idx, row in df.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    a = pd.to_numeric(row[asset_col], errors="coerce")
                    liab = pd.to_numeric(row[liab_col], errors="coerce")
                    e = pd.to_numeric(row[eq_col], errors="coerce")
                    if pd.isna(a) or pd.isna(liab) or pd.isna(e):
                        continue

                    diff = abs(a - (liab + e))
                    # Allow 1.0 tolerance due to rounding units in reports
                    if diff > 1.0:
                        self.log_failure(
                            company_ticker=ticker,
                            file_name=file_name,
                            row_index=int(idx),
                            rule_id="DQ-12",
                            severity="WARNING",
                            column_name="assets, liabilities, equity",
                            invalid_value=f"A:{a}, L:{liab}, E:{e} (Diff: {diff:.2f})",
                            message="Balance sheet does not balance: Assets != Liabilities + Equity",
                        )

        # ---------------------------------------------------------------------
        # Cash Flow Specific Checks (DQ-13)
        # ---------------------------------------------------------------------
        elif sheet_type == "cf":
            # DQ-13: Cash flow reconciliation (Warning: end_cash = start_cash + net_cash_flow)
            start_col = next(
                (
                    c
                    for c in df.columns
                    if "start" in c.lower()
                    or "beginning" in c.lower()
                    or "opening" in c.lower()
                ),
                None,
            )
            end_col = next(
                (c for c in df.columns if "end" in c.lower() or "closing" in c.lower()),
                None,
            )
            net_col = next(
                (c for c in df.columns if "net" in c.lower() or "change" in c.lower()),
                None,
            )

            if start_col and end_col and net_col:
                for idx, row in df.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    s = pd.to_numeric(row[start_col], errors="coerce")
                    e = pd.to_numeric(row[end_col], errors="coerce")
                    n = pd.to_numeric(row[net_col], errors="coerce")
                    if pd.isna(s) or pd.isna(e) or pd.isna(n):
                        continue

                    diff = abs(e - (s + n))
                    # Allow 1.0 tolerance
                    if diff > 1.0:
                        self.log_failure(
                            company_ticker=ticker,
                            file_name=file_name,
                            row_index=int(idx),
                            rule_id="DQ-13",
                            severity="WARNING",
                            column_name="beginning_cash, ending_cash, net_change",
                            invalid_value=f"Start:{s}, End:{e}, Net:{n} (Diff: {diff:.2f})",
                            message="Cash flow reconciliation discrepancy: End Cash != Start Cash + Net Change",
                        )
