from pathlib import Path

import pandas as pd


def generate_mock_data():
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 1. sectors.xlsx (Core 1)
    sectors = ["Technology", "Financials", "Healthcare", "Energy", "Consumer Goods"]
    df_sectors = pd.DataFrame(
        {
            "sector_name": sectors,
            "sector_description": [f"Sector for {s}" for s in sectors],
        }
    )
    df_sectors.to_excel(raw_dir / "sectors.xlsx", index=False)

    # 2. companies.xlsx (Core 2)
    # Target: 92 companies
    tickers = [f"COMP{i:02d}" for i in range(1, 93)]
    company_names = [f"Company Name {i:02d}" for i in range(1, 93)]
    company_sectors = [sectors[i % len(sectors)] for i in range(92)]
    company_industries = [f"Industry {i % 10}" for i in range(92)]

    # Include some ticker normalisation test cases in the raw data
    raw_tickers = []
    for i, t in enumerate(tickers):
        if i == 0:
            raw_tickers.append("comp01.ns")  # Lowercase and suffix
        elif i == 1:
            raw_tickers.append(" COMP02.BO  ")  # Leading/trailing space and suffix
        else:
            raw_tickers.append(t)

    df_companies = pd.DataFrame(
        {
            "ticker": raw_tickers,
            "name": company_names,
            "sector_name": company_sectors,
            "industry": company_industries,
        }
    )
    df_companies.to_excel(raw_dir / "companies.xlsx", index=False)

    norm_tickers = tickers.copy()

    # 3. income_statements.xlsx (Core 3)
    # Target: 1276 rows.
    # We will distribute 1276 rows across 92 companies.
    # 1276 = 92 * 13 + 80. So 80 companies will have 14 years, 12 companies will have 13 years.
    rows_pnl = []
    for i, ticker in enumerate(norm_tickers):
        years_to_add = 14 if i < 80 else 13
        # Company-specific parameters
        growth_rate = 0.05 + (i % 5) * 0.04
        npm_factor = 0.05 + (i % 4) * 0.04
        for y_idx in range(years_to_add):
            year = 2010 + y_idx

            # Values
            sales = (500.0 + i * 40.0) * ((1.0 + growth_rate) ** y_idx)
            op_profit = sales * 0.18
            opm = 0.18
            gp = sales * 0.40
            net_inc = sales * npm_factor
            eps = net_inc / (10.0 + (i % 4) * 10.0)
            shares = 40.0

            # Intentionally add a warning case (DQ-10: non-positive sales) for COMP10 year 2010
            if ticker == "COMP10" and year == 2010:
                sales = 0.0
            # Intentionally add a warning case (DQ-16: GP < OP) for COMP12 year 2012
            if ticker == "COMP12" and year == 2012:
                gp = 50.0
                op_profit = 100.0

            rows_pnl.append(
                {
                    "ticker": (
                        ticker.lower() if i % 10 == 0 else ticker
                    ),  # test ticker normalisation
                    "year": (
                        f"'{year}" if i % 15 == 0 else year
                    ),  # test year normalisation
                    "sales": sales,
                    "operating_profit": op_profit,
                    "opm": opm,
                    "gross_profit": gp,
                    "net_income": net_inc,
                    "eps": eps,
                    "shares_outstanding": shares,
                }
            )

    df_pnl = pd.DataFrame(rows_pnl)
    df_pnl.to_excel(raw_dir / "income_statements.xlsx", index=False)

    # 4. balance_sheets.xlsx (Core 4)
    # Target: 1312 rows.
    rows_bs = []
    for i, ticker in enumerate(norm_tickers):
        years_to_add = 15 if i < 24 else 14
        # Company-specific parameters
        base_debt_ratio = 0.2 + (i % 3) * 0.2
        if i % 6 == 0:
            base_debt_ratio = 0.0
        for y_idx in range(years_to_add):
            year = 2010 + y_idx

            # Decline slightly each year only for even indices
            if i % 2 == 0:
                debt_ratio = max(0.0, base_debt_ratio - y_idx * 0.01)
            else:
                debt_ratio = base_debt_ratio
            assets = (1500.0 + i * 80.0) * (1.06 ** y_idx)
            liabs = assets * debt_ratio
            equity = assets * (1.0 - debt_ratio)
            retained = equity * 0.3

            # Intentionally add a warning case (DQ-12: Assets != Liab + Equity) for COMP20 year 2010
            if ticker == "COMP20" and year == 2010:
                assets = 9999.0

            rows_bs.append(
                {
                    "ticker": ticker,
                    "year": year,
                    "total_assets": assets,
                    "total_liabilities": liabs,
                    "total_equity": equity,
                    "retained_earnings": retained,
                }
            )

    df_bs = pd.DataFrame(rows_bs)
    df_bs.to_excel(raw_dir / "balance_sheets.xlsx", index=False)

    # 5. cash_flows.xlsx (Core 5)
    # Target: 1187 rows.
    rows_cf = []
    for i, ticker in enumerate(norm_tickers):
        years_to_add = 13 if i < 83 else 12
        for y_idx in range(years_to_add):
            year = 2010 + y_idx

            start_cash = 100.0 + (y_idx * 10)
            net_change = 20.0 + (i * 0.5)
            end_cash = start_cash + net_change

            # Intentionally add a warning case (DQ-13: CF mismatch) for COMP30 year 2010
            if ticker == "COMP30" and year == 2010:
                end_cash = 999.0

            rows_cf.append(
                {
                    "ticker": ticker,
                    "year": year,
                    "beginning_cash": start_cash,
                    "ending_cash": end_cash,
                    "net_cash_flow": net_change,
                }
            )

    df_cf = pd.DataFrame(rows_cf)
    df_cf.to_excel(raw_dir / "cash_flows.xlsx", index=False)

    # 6-9. stock_prices
    # Target: 5520 rows total.
    all_prices = []
    dates = (
        pd.date_range(start="2026-01-01", periods=60).strftime("%Y-%m-%d").tolist()
    )  # 60 days

    for i, ticker in enumerate(norm_tickers):
        for d_idx, dt in enumerate(dates):
            open_p = 100.0 + (i * 7) + (d_idx * 0.5)
            high_p = open_p + 5.0
            low_p = open_p - 3.0
            close_p = open_p + 1.0
            vol = 10000 + i * 100

            # Intentionally add a warning case (DQ-15: high < low) for COMP41 on date 2026-01-01
            if ticker == "COMP41" and dt == "2026-01-01":
                high_p = 50.0
                low_p = 150.0

            all_prices.append(
                {
                    "ticker": ticker,
                    "date": dt,
                    "open": open_p,
                    "high": high_p,
                    "low": low_p,
                    "close": close_p,
                    "volume": vol,
                }
            )

    df_prices_core = pd.DataFrame(all_prices[:3000])
    df_prices_supp1 = pd.DataFrame(all_prices[3000:4000])
    df_prices_supp2 = pd.DataFrame(all_prices[4000:5000])
    df_prices_supp3 = pd.DataFrame(all_prices[5000:])

    df_prices_core.to_excel(raw_dir / "stock_prices_core.xlsx", index=False)
    df_prices_supp1.to_excel(raw_dir / "stock_prices_supp1.xlsx", index=False)
    df_prices_supp2.to_excel(raw_dir / "stock_prices_supp2.xlsx", index=False)
    df_prices_supp3.to_excel(raw_dir / "stock_prices_supp3.xlsx", index=False)

    # 7. ratios.xlsx (Core 7)
    # Target: 1000 rows
    rows_ratios = []
    for i, ticker in enumerate(norm_tickers):
        years_to_add = 11 if i < 80 else 10
        for y_idx in range(years_to_add):
            year = 2015 + y_idx
            rows_ratios.append(
                {
                    "ticker": ticker,
                    "year": year,
                    "pe_ratio": 10.0 + (i * 0.35),
                    "pb_ratio": 1.0 + (i % 5) * 0.5 + (y_idx * 0.05),
                    "roe": 12.5 + (i * 0.05),
                    "debt_to_equity": max(0.0, 1.0 - (y_idx * 0.05) + (i % 3) * 0.2) if i % 2 == 0 else 0.5 + (y_idx * 0.02),
                }
            )
    df_ratios = pd.DataFrame(rows_ratios)
    df_ratios.to_excel(raw_dir / "ratios.xlsx", index=False)

    # 11. corporate_actions.xlsx (Supplementary 4)
    # Generate annual dividends from 2010 to 2024 for all companies to ensure realistic yield
    rows_corp = []
    for i, ticker in enumerate(norm_tickers):
        for year in range(2010, 2025):
            dt = f"{year}-06-{(i % 28) + 1:02d}"
            rows_corp.append(
                {
                    "ticker": ticker,
                    "date": dt,
                    "action_type": "Dividend",
                    "value": (2.0 + (i * 0.15) + (i % 5) * 0.5) if i % 2 == 0 else 0.5
                }
            )
            # Add some split actions
            if year == 2018 and i % 10 == 0:
                rows_corp.append(
                    {
                        "ticker": ticker,
                        "date": f"{year}-09-15",
                        "action_type": "Split",
                        "value": 2.0
                    }
                )
    df_corp = pd.DataFrame(rows_corp)
    df_corp.to_excel(raw_dir / "corporate_actions.xlsx", index=False)

    # 12. audit_metadata.xlsx (Supplementary 5)
    df_audit = pd.DataFrame(
        {
            "audit_id": range(1, 11),
            "ticker": [norm_tickers[i % len(norm_tickers)] for i in range(10)],
            "auditor_opinion": ["Unqualified" for _ in range(10)],
            "audit_year": [2024 for _ in range(10)],
        }
    )
    df_audit.to_excel(raw_dir / "audit_metadata.xlsx", index=False)

    print(f"Mock data generation complete. Created 12 Excel files in {raw_dir}")


if __name__ == "__main__":
    generate_mock_data()
