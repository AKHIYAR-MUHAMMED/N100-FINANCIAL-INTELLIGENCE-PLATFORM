import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, List, Optional

import numpy as np
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
        """Returns logged failures as a pandas DataFrame."""
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
    # DQ-01 & DQ-02: Companies PK & Suffix & URL Checks
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
                row_index=int(idx) if isinstance(idx, (int, np.integer)) else idx,
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
            if pd.isna(ticker) or str(ticker).strip() == "":
                continue
            self.log_failure(
                company_ticker=ticker,
                file_name=file_name,
                row_index=int(idx) if isinstance(idx, (int, np.integer)) else idx,
                rule_id="DQ-01",
                severity="CRITICAL",
                column_name=ticker_col,
                invalid_value=ticker,
                message=f"Duplicate ticker found: {ticker}",
            )

        # DQ-10: Website URL validation
        if "website" in df.columns:
            url_pattern = re.compile(
                r"^(https?:\/\/)?(www\.)?([a-zA-Z0-9]+(-[a-zA-Z0-9]+)*\.)+[a-z]{2,}(:\d+)?(\/.*)?$"
            )
            for idx, row in df.iterrows():
                ticker = row[ticker_col]
                url = row["website"]
                if pd.notna(url) and str(url).strip() != "":
                    if not url_pattern.match(str(url).strip()):
                        self.log_failure(
                            company_ticker=ticker if pd.notna(ticker) else "UNKNOWN",
                            file_name=file_name,
                            row_index=(
                                int(idx) if isinstance(idx, (int, np.integer)) else idx
                            ),
                            rule_id="DQ-10",
                            severity="WARNING",
                            column_name="website",
                            invalid_value=url,
                            message=f"Invalid website URL format: {url}",
                        )

        # DQ-12: BSE/NSE exchange suffix validation (from raw input)
        for idx, row in df.iterrows():
            ticker = row[ticker_col]
            if pd.notna(ticker) and str(ticker).strip() != "":
                ticker_str = str(ticker).strip().upper()
                if "." in ticker_str:
                    valid_suffixes = (".NS", ".BO", ".BSE", ".NSE")
                    if not any(ticker_str.endswith(s) for s in valid_suffixes):
                        self.log_failure(
                            company_ticker=ticker,
                            file_name=file_name,
                            row_index=(
                                int(idx) if isinstance(idx, (int, np.integer)) else idx
                            ),
                            rule_id="DQ-12",
                            severity="WARNING",
                            column_name="ticker",
                            invalid_value=ticker,
                            message=f"BSE/NSE balance: Ticker contains period but lacks valid exchange suffix: {ticker}",
                        )

    # -------------------------------------------------------------------------
    # DQ-03: Referential Integrity Check
    # -------------------------------------------------------------------------
    def validate_relationships(
        self,
        df: pd.DataFrame,
        companies_df: pd.DataFrame,
        file_name: str,
        is_prices: bool = False,
    ) -> None:
        """Validates FK integrity constraints (DQ-03)."""
        if df.empty:
            return

        ticker_col = "ticker"
        if ticker_col not in df.columns:
            return

        valid_tickers = set()
        if not companies_df.empty and "ticker" in companies_df.columns:
            valid_tickers = set(companies_df["ticker"].dropna().unique())

        # Check FK integrity
        for idx, row in df.iterrows():
            ticker = row[ticker_col]
            if pd.isna(ticker) or str(ticker).strip() == "":
                continue
            if ticker not in valid_tickers:
                self.log_failure(
                    company_ticker=ticker,
                    file_name=file_name,
                    row_index=int(idx) if isinstance(idx, (int, np.integer)) else idx,
                    rule_id="DQ-03",
                    severity="CRITICAL",
                    column_name=ticker_col,
                    invalid_value=ticker,
                    message=f"Referential integrity failure: ticker '{ticker}' does not exist in companies master",
                )

    # -------------------------------------------------------------------------
    # DQ-09, DQ-14, DQ-15: Stock Prices and Corporate Actions validations
    # -------------------------------------------------------------------------
    def validate_prices(self, df: pd.DataFrame, file_name: str) -> None:
        """Validates stock prices details (DQ-01, DQ-02, DQ-09, DQ-14, DQ-15)."""
        if df.empty:
            return

        ticker_col = "ticker"
        date_col = "date"

        # DQ-02: PK Non-Null Check
        for col in [ticker_col, date_col]:
            if col in df.columns:
                null_rows = df[df[col].isna()]
                for idx, row in null_rows.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    self.log_failure(
                        company_ticker=ticker,
                        file_name=file_name,
                        row_index=(
                            int(idx) if isinstance(idx, (int, np.integer)) else idx
                        ),
                        rule_id="DQ-02",
                        severity="CRITICAL",
                        column_name=col,
                        invalid_value=None,
                        message=f"Primary key field '{col}' is null in stock prices",
                    )

        # DQ-01: PK Uniqueness Check (ticker, date)
        if ticker_col in df.columns and date_col in df.columns:
            valid_keys = df.dropna(subset=[ticker_col, date_col])
            duplicates = valid_keys[
                valid_keys.duplicated(subset=[ticker_col, date_col], keep=False)
            ]
            for idx, row in duplicates.iterrows():
                ticker = row[ticker_col]
                dt = row[date_col]
                self.log_failure(
                    company_ticker=ticker,
                    file_name=file_name,
                    row_index=int(idx) if isinstance(idx, (int, np.integer)) else idx,
                    rule_id="DQ-01",
                    severity="CRITICAL",
                    column_name=f"{ticker_col}, {date_col}",
                    invalid_value=f"({ticker}, {dt})",
                    message=f"Duplicate primary key entry found for ticker {ticker} on date {dt}",
                )

        # DQ-02: Date Validity check
        if date_col in df.columns:
            for idx, row in df.iterrows():
                ticker = row.get(ticker_col, "UNKNOWN")
                dt = row[date_col]
                if pd.isna(dt):
                    continue
                try:
                    pd.to_datetime(dt, errors="raise")
                except Exception:
                    self.log_failure(
                        company_ticker=ticker,
                        file_name=file_name,
                        row_index=(
                            int(idx) if isinstance(idx, (int, np.integer)) else idx
                        ),
                        rule_id="DQ-02",
                        severity="CRITICAL",
                        column_name=date_col,
                        invalid_value=dt,
                        message=f"Invalid date format: {dt}",
                    )

        # DQ-09: Positive Prices Check (open, high, low, close must be > 0)
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
                        row_index=(
                            int(idx) if isinstance(idx, (int, np.integer)) else idx
                        ),
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
                    row_index=int(idx) if isinstance(idx, (int, np.integer)) else idx,
                    rule_id="DQ-14",
                    severity="WARNING",
                    column_name=vol_col,
                    invalid_value=val,
                    message=f"Daily stock volume must be non-negative. Found: {val}",
                )

        # DQ-15: Price Consistency (Warning)
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
                        row_index=(
                            int(idx) if isinstance(idx, (int, np.integer)) else idx
                        ),
                        rule_id="DQ-15",
                        severity="WARNING",
                        column_name="open, high, low, close",
                        invalid_value=f"O:{o}, H:{h}, L:{low_val}, C:{c}",
                        message="Inconsistent daily stock prices (High must be maximum and Low must be minimum)",
                    )

        # DQ-13: Stock price coverage check (Warning)
        if ticker_col in df.columns:
            counts = df[ticker_col].value_counts()
            for ticker, count in counts.items():
                if count < 10:
                    self.log_failure(
                        company_ticker=str(ticker),
                        file_name=file_name,
                        row_index=None,
                        rule_id="DQ-13",
                        severity="WARNING",
                        column_name="ticker",
                        invalid_value=count,
                        message=f"Low trading day coverage: Company {ticker} has only {count} price records",
                    )

    def validate_corporate_actions(self, df: pd.DataFrame, file_name: str) -> None:
        """Validates corporate actions (DQ-09: dividend cap)."""
        if df.empty:
            return

        ticker_col = "ticker"
        value_col = "value"
        type_col = "action_type"

        if all(c in df.columns for c in [ticker_col, type_col, value_col]):
            for idx, row in df.iterrows():
                ticker = row[ticker_col]
                action_type = row[type_col]
                val = pd.to_numeric(row[value_col], errors="coerce")

                if pd.isna(val):
                    continue

                # DQ-09: Dividend Cap Check
                if action_type == "Dividend" and val > 500:
                    self.log_failure(
                        company_ticker=ticker if pd.notna(ticker) else "UNKNOWN",
                        file_name=file_name,
                        row_index=(
                            int(idx) if isinstance(idx, (int, np.integer)) else idx
                        ),
                        rule_id="DQ-09",
                        severity="WARNING",
                        column_name="value",
                        invalid_value=val,
                        message=f"Dividend payout exceeds cap (500): {val}",
                    )

    # -------------------------------------------------------------------------
    # DQ-02, DQ-04, DQ-05, DQ-06, DQ-07, DQ-08, DQ-11, DQ-13, DQ-16: Financials
    # -------------------------------------------------------------------------
    def validate_financials(
        self, df: pd.DataFrame, file_name: str, sheet_type: str
    ) -> None:
        """Validates P&L, Balance Sheet, and Cash Flow statements."""
        if df.empty:
            return

        ticker_col = "ticker"
        year_col = "year"

        # DQ-02: PK Non-Null & Format Check
        for col in [ticker_col, year_col]:
            if col in df.columns:
                null_rows = df[df[col].isna()]
                for idx, row in null_rows.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    self.log_failure(
                        company_ticker=ticker,
                        file_name=file_name,
                        row_index=(
                            int(idx) if isinstance(idx, (int, np.integer)) else idx
                        ),
                        rule_id="DQ-02",
                        severity="CRITICAL",
                        column_name=col,
                        invalid_value=None,
                        message=f"Primary key field '{col}' is null in {sheet_type}",
                    )

        # DQ-01: PK Uniqueness Check (ticker, year)
        if ticker_col in df.columns and year_col in df.columns:
            valid_keys = df.dropna(subset=[ticker_col, year_col])
            duplicates = valid_keys[
                valid_keys.duplicated(subset=[ticker_col, year_col], keep=False)
            ]
            for idx, row in duplicates.iterrows():
                ticker = row[ticker_col]
                yr = row[year_col]
                self.log_failure(
                    company_ticker=ticker,
                    file_name=file_name,
                    row_index=int(idx) if isinstance(idx, (int, np.integer)) else idx,
                    rule_id="DQ-01",
                    severity="CRITICAL",
                    column_name=f"{ticker_col}, {year_col}",
                    invalid_value=f"({ticker}, {yr})",
                    message=f"Duplicate primary key record found for ticker {ticker} in year {yr} ({sheet_type})",
                )

        # DQ-02: Year Format / Bounds
        if year_col in df.columns:
            for idx, row in df.iterrows():
                ticker = row.get(ticker_col, "UNKNOWN")
                yr = row[year_col]
                if pd.isna(yr):
                    continue
                try:
                    yr_val = int(yr)
                    if not (2000 <= yr_val <= 2030):
                        raise ValueError()
                except Exception:
                    self.log_failure(
                        company_ticker=ticker,
                        file_name=file_name,
                        row_index=(
                            int(idx) if isinstance(idx, (int, np.integer)) else idx
                        ),
                        rule_id="DQ-02",
                        severity="CRITICAL",
                        column_name=year_col,
                        invalid_value=yr,
                        message=f"Year is invalid or out of bounds [2000, 2030]: {yr}",
                    )

        # P&L Specific Checks (DQ-05, DQ-06, DQ-08, DQ-11, DQ-16)
        if sheet_type == "pnl":
            # DQ-06: Positive Sales (Warning)
            sales_col = next(
                (c for c in df.columns if c.lower() in ["sales", "revenue"]), None
            )
            if sales_col:
                bad_sales = df[pd.to_numeric(df[sales_col], errors="coerce") <= 0]
                for idx, row in bad_sales.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    val = row[sales_col]
                    self.log_failure(
                        company_ticker=ticker,
                        file_name=file_name,
                        row_index=(
                            int(idx) if isinstance(idx, (int, np.integer)) else idx
                        ),
                        rule_id="DQ-06",
                        severity="WARNING",
                        column_name=sales_col,
                        invalid_value=val,
                        message=f"Revenue/Sales should be positive. Found: {val}",
                    )

            # DQ-05: OPM Cross-Check (Warning)
            opm_col = "opm"
            op_col = "operating_profit"
            sales_col = "sales"
            if all(c in df.columns for c in [opm_col, op_col, sales_col]):
                for idx, row in df.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    reported_opm = pd.to_numeric(row[opm_col], errors="coerce")
                    op = pd.to_numeric(row[op_col], errors="coerce")
                    sales = pd.to_numeric(row[sales_col], errors="coerce")

                    if (
                        pd.isna(reported_opm)
                        or pd.isna(op)
                        or pd.isna(sales)
                        or sales == 0
                    ):
                        continue

                    computed_opm = op / sales
                    diff = abs(reported_opm - computed_opm)
                    if diff > 0.05:
                        self.log_failure(
                            company_ticker=ticker,
                            file_name=file_name,
                            row_index=(
                                int(idx) if isinstance(idx, (int, np.integer)) else idx
                            ),
                            rule_id="DQ-05",
                            severity="WARNING",
                            column_name="opm",
                            invalid_value=reported_opm,
                            message=f"OPM cross-check failed: reported={reported_opm:.4f}, computed={computed_opm:.4f} (Diff: {diff:.4f})",
                        )

            # DQ-08: Tax rate check (Warning)
            op_col = "operating_profit"
            ni_col = "net_income"
            if op_col in df.columns and ni_col in df.columns:
                for idx, row in df.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    op = pd.to_numeric(row[op_col], errors="coerce")
                    ni = pd.to_numeric(row[ni_col], errors="coerce")

                    if pd.isna(op) or pd.isna(ni) or op <= 0:
                        continue

                    tax_rate = (op - ni) / op
                    if not (0.0 <= tax_rate <= 1.0):
                        self.log_failure(
                            company_ticker=ticker,
                            file_name=file_name,
                            row_index=(
                                int(idx) if isinstance(idx, (int, np.integer)) else idx
                            ),
                            rule_id="DQ-08",
                            severity="WARNING",
                            column_name="operating_profit, net_income",
                            invalid_value=f"{tax_rate:.4f}",
                            message=f"Abnormal tax rate: {tax_rate*100:.2f}% (op={op}, ni={ni})",
                        )

            # DQ-11: EPS Sign Check (Warning)
            eps_col = "eps"
            ni_col = "net_income"
            if eps_col in df.columns and ni_col in df.columns:
                for idx, row in df.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    eps = pd.to_numeric(row[eps_col], errors="coerce")
                    ni = pd.to_numeric(row[ni_col], errors="coerce")

                    if pd.isna(eps) or pd.isna(ni):
                        continue

                    if (
                        (eps > 0 and ni < 0)
                        or (eps < 0 and ni > 0)
                        or (eps == 0 and ni != 0)
                        or (ni == 0 and eps != 0)
                    ):
                        self.log_failure(
                            company_ticker=ticker,
                            file_name=file_name,
                            row_index=(
                                int(idx) if isinstance(idx, (int, np.integer)) else idx
                            ),
                            rule_id="DQ-11",
                            severity="WARNING",
                            column_name="eps, net_income",
                            invalid_value=f"EPS:{eps}, NI:{ni}",
                            message="EPS sign mismatch: EPS and Net Income signs must match",
                        )

            # DQ-16: Logical Profit Order (Warning)
            gp_col = "gross_profit"
            op_col = "operating_profit"
            ni_col = "net_income"
            if all(c in df.columns for c in [gp_col, op_col, ni_col]):
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
                            row_index=(
                                int(idx) if isinstance(idx, (int, np.integer)) else idx
                            ),
                            rule_id="DQ-16",
                            severity="WARNING",
                            column_name="gross_profit, operating_profit, net_income",
                            invalid_value=f"GP:{gp}, OP:{op}, NI:{ni}",
                            message="Inconsistent profit ordering (Gross Profit >= Operating Profit >= Net Income)",
                        )

        # Balance Sheet Specific Checks (DQ-04)
        elif sheet_type == "bs":
            # DQ-04: BS Balance Check (Warning)
            asset_col = "total_assets"
            liab_col = "total_liabilities"
            eq_col = "total_equity"

            if all(c in df.columns for c in [asset_col, liab_col, eq_col]):
                for idx, row in df.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    a = pd.to_numeric(row[asset_col], errors="coerce")
                    liab = pd.to_numeric(row[liab_col], errors="coerce")
                    e = pd.to_numeric(row[eq_col], errors="coerce")
                    if pd.isna(a) or pd.isna(liab) or pd.isna(e) or a == 0:
                        continue

                    diff = abs(a - (liab + e))
                    pct_diff = diff / a
                    if pct_diff >= 0.01:
                        self.log_failure(
                            company_ticker=ticker,
                            file_name=file_name,
                            row_index=(
                                int(idx) if isinstance(idx, (int, np.integer)) else idx
                            ),
                            rule_id="DQ-04",
                            severity="WARNING",
                            column_name="total_assets, total_liabilities, total_equity",
                            invalid_value=f"A:{a}, L:{liab}, E:{e} (Diff: {diff:.2f}, Pct: {pct_diff*100:.2f}%)",
                            message="Balance sheet discrepancy exceeds 1%: Assets != Liabilities + Equity",
                        )

        # Cash Flow Specific Checks (DQ-07)
        elif sheet_type == "cf":
            # DQ-07: Net Cash Flow Reconciliation (Warning)
            start_col = "beginning_cash"
            end_col = "ending_cash"
            net_col = "net_cash_flow"

            if all(c in df.columns for c in [start_col, end_col, net_col]):
                for idx, row in df.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    s = pd.to_numeric(row[start_col], errors="coerce")
                    e = pd.to_numeric(row[end_col], errors="coerce")
                    n = pd.to_numeric(row[net_col], errors="coerce")
                    if pd.isna(s) or pd.isna(e) or pd.isna(n):
                        continue

                    diff = abs(e - (s + n))
                    if diff > 1.0:
                        self.log_failure(
                            company_ticker=ticker,
                            file_name=file_name,
                            row_index=(
                                int(idx) if isinstance(idx, (int, np.integer)) else idx
                            ),
                            rule_id="DQ-07",
                            severity="WARNING",
                            column_name="beginning_cash, ending_cash, net_cash_flow",
                            invalid_value=f"Start:{s}, End:{e}, Net:{n} (Diff: {diff:.2f})",
                            message="Cash flow reconciliation discrepancy: End Cash != Start Cash + Net Cash Flow",
                        )

        # Financial Ratios Specific Checks (DQ-13)
        elif sheet_type == "ratios":
            debt_eq_col = "debt_to_equity"
            roe_col = "roe"
            if debt_eq_col in df.columns:
                for idx, row in df.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    debt_eq = pd.to_numeric(row[debt_eq_col], errors="coerce")
                    if pd.notna(debt_eq) and debt_eq > 5.0:
                        self.log_failure(
                            company_ticker=ticker,
                            file_name=file_name,
                            row_index=(
                                int(idx) if isinstance(idx, (int, np.integer)) else idx
                            ),
                            rule_id="DQ-13",
                            severity="WARNING",
                            column_name="debt_to_equity",
                            invalid_value=debt_eq,
                            message=f"Leverage coverage warning: Debt-to-Equity is extremely high: {debt_eq:.2f}",
                        )
            if roe_col in df.columns:
                for idx, row in df.iterrows():
                    ticker = row.get(ticker_col, "UNKNOWN")
                    roe = pd.to_numeric(row[roe_col], errors="coerce")
                    if pd.notna(roe) and (roe < -50.0 or roe > 100.0):
                        self.log_failure(
                            company_ticker=ticker,
                            file_name=file_name,
                            row_index=(
                                int(idx) if isinstance(idx, (int, np.integer)) else idx
                            ),
                            rule_id="DQ-13",
                            severity="WARNING",
                            column_name="roe",
                            invalid_value=roe,
                            message=f"ROE coverage warning: Return on Equity is anomalous: {roe:.2f}%",
                        )
