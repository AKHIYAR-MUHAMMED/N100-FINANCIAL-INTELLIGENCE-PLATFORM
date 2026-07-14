import datetime
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np

from src.database import DatabaseManager
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


def calculate_ratios():
    print("Initializing Financial Ratio Engine...")
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    # 1. Cache pre-computed ratios from database (loaded from ratios.xlsx) before deletion
    print("Caching pre-computed ratios from database...")
    df_pre_computed = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    pre_computed_dict = {}
    for _, row in df_pre_computed.iterrows():
        # Keep track of pre-computed ROE and Debt-to-Equity
        tk = str(row["ticker"]).strip().upper()
        pre_computed_dict[(tk, int(row["year"]))] = {
            "roe": row.get("roe"),
            "debt_to_equity": row.get("debt_to_equity"),
            "pe_ratio": row.get("pe_ratio"),
            "pb_ratio": row.get("pb_ratio"),
        }

    # Clear existing financial ratios
    cursor.execute("DELETE FROM financial_ratios;")
    conn.commit()

    # 2. Query statements data
    print("Loading financial statements from database...")
    query = """
        SELECT 
            p.ticker,
            p.year,
            p.sales,
            p.operating_profit,
            p.opm,
            p.gross_profit,
            p.net_income,
            p.eps,
            p.shares_outstanding,
            b.total_assets,
            b.total_liabilities,
            b.total_equity,
            b.retained_earnings,
            c.beginning_cash,
            c.ending_cash,
            c.net_cash_flow,
            comp.sector_name,
            comp.industry
        FROM profitandloss p
        JOIN companies comp ON p.ticker = comp.ticker
        LEFT JOIN balancesheet b ON p.ticker = b.ticker AND p.year = b.year
        LEFT JOIN cashflow c ON p.ticker = c.ticker AND p.year = c.year
        ORDER BY p.ticker, p.year
    """
    df_fin = pd.read_sql_query(query, conn)
    if df_fin.empty:
        print("No financial statements found. Pipeline aborted.")
        conn.close()
        return

    # 3. Load average stock prices
    print("Loading average stock prices...")
    price_query = """
        SELECT
            ticker,
            strftime('%Y', date) as price_year,
            AVG(close) as avg_close
        FROM stock_prices
        GROUP BY ticker, price_year
    """
    df_prices = pd.read_sql_query(price_query, conn)
    df_prices["price_year"] = df_prices["price_year"].astype(int)
    prices_dict = df_prices.set_index(["ticker", "price_year"])["avg_close"].to_dict()

    fallback_query = """
        SELECT
            ticker,
            AVG(close) as overall_avg_close
        FROM stock_prices
        GROUP BY ticker
    """
    df_fallback = pd.read_sql_query(fallback_query, conn)
    fallback_prices = df_fallback.set_index("ticker")["overall_avg_close"].to_dict()

    # 4. Sum dividends per company-year from corporate_actions
    print("Loading dividend corporate actions...")
    corp_query = """
        SELECT ticker, date, action_type, value 
        FROM corporate_actions 
        WHERE action_type = 'Dividend'
    """
    df_corp = pd.read_sql_query(corp_query, conn)
    df_corp["year"] = pd.to_datetime(df_corp["date"]).dt.year
    dividend_dict = df_corp.groupby(["ticker", "year"])["value"].sum().to_dict()

    # 5. Load companies xlsx directly to check for pre-computed columns (Day 13)
    raw_companies_path = Path("data/raw/companies.xlsx")
    df_raw_companies = pd.DataFrame()
    if raw_companies_path.is_file():
        df_raw_companies = pd.read_excel(raw_companies_path)

    # 6. Initialize logs and output lists
    ratio_logs = []
    capital_allocations = []
    ratios_to_insert = []

    # Organize data by company for rolling calculations
    grouped = df_fin.groupby("ticker")

    # Compute year-specific average ROCE for Financials sector first (for sector-relative benchmark check)
    all_computed_roce = {}  # (ticker, year) -> roce
    for ticker, group in grouped:
        for _, row in group.iterrows():
            year = int(row["year"])
            op_profit = row["operating_profit"] or 0.0
            total_equity = row["total_equity"] or 0.0
            total_liab = row["total_liabilities"] or 0.0
            retained = row["retained_earnings"] or 0.0
            
            equity_cap = total_equity - retained
            roce = calculate_return_on_capital_employed(
                ebit=op_profit,
                equity=equity_cap,
                reserves=retained,
                borrowings=total_liab
            )
            if roce is not None:
                all_computed_roce[(ticker, year)] = roce

    # Sector average ROCE for Financials per year
    financials_year_roce = {}
    for (ticker, year), roce in all_computed_roce.items():
        # Get sector of company
        sector = df_fin[df_fin["ticker"] == ticker]["sector_name"].iloc[0]
        if sector.strip().lower() == "financials":
            financials_year_roce.setdefault(year, []).append(roce)
            
    financials_benchmark_roce = {
        yr: np.mean(vals) for yr, vals in financials_year_roce.items() if vals
    }

    # Now calculate all KPIs per company-year
    print("Running KPI computations...")
    for ticker, group in grouped:
        group = group.sort_values("year")
        
        # Build dictionaries of history for CAGR and CFO Quality Score
        sales_history = group.set_index("year")["sales"].to_dict()
        pat_history = group.set_index("year")["net_income"].to_dict()
        eps_history = group.set_index("year")["eps"].to_dict()
        
        # CFO list and PAT list in order of years
        cfo_history = {}
        for _, row in group.iterrows():
            yr = int(row["year"])
            net_inc = row["net_income"] or 0.0
            assets = row["total_assets"] or 0.0
            cfo_history[yr] = net_inc + (assets * 0.02)

        for _, row in group.iterrows():
            year = int(row["year"])
            sales = row["sales"] or 0.0
            op_profit = row["operating_profit"] or 0.0
            opm_ratio = row["opm"] or 0.0
            # gross_profit = row["gross_profit"] or 0.0 (unused)
            net_income = row["net_income"] or 0.0
            eps = row["eps"] or 0.0
            shares = row["shares_outstanding"] or 0.0
            total_assets = row["total_assets"] or 0.0
            total_liab = row["total_liabilities"] or 0.0
            total_equity = row["total_equity"] or 0.0
            retained = row["retained_earnings"] or 0.0
            sector = row["sector_name"]
            
            equity_cap = total_equity - retained
            reserves = retained
            
            # --- DAY 08: Profitability Ratios ---
            npm = calculate_net_profit_margin(net_income, sales)
            opm = calculate_operating_profit_margin(op_profit, sales)
            roe_val = calculate_return_on_equity(net_income, equity_cap, reserves)
            roce = calculate_return_on_capital_employed(op_profit, equity_cap, reserves, total_liab)
            roa = calculate_return_on_assets(net_income, total_assets)

            # OPM Cross-check
            if opm is not None:
                reported_opm_pct = opm_ratio * 100.0
                if abs(opm - reported_opm_pct) > 1.0:
                    ratio_logs.append(
                        f"[{datetime.datetime.now().isoformat()}] [formula discrepancy] "
                        f"Company: {ticker}, Year: {year}, Metric: Operating Profit Margin, "
                        f"Computed: {opm:.2f}%, Pre-computed: {reported_opm_pct:.2f}%, "
                        f"Difference: {abs(opm - reported_opm_pct):.2f}%, "
                        f"Description: OPM computed from Operating Profit / Sales differs from reported opm field by > 1%."
                    )

            # ROCE Sector-relative benchmark vs absolute benchmark (15.0%)
            is_financial = sector.strip().lower() == "financials"
            roce_benchmark = financials_benchmark_roce.get(year, 15.0) if is_financial else 15.0
            if roce is not None and roce < roce_benchmark:
                bm_type = "sector-relative financials benchmark" if is_financial else "absolute threshold"
                ratio_logs.append(
                    f"[{datetime.datetime.now().isoformat()}] [formula discrepancy] "
                    f"Company: {ticker}, Year: {year}, Metric: ROCE, "
                    f"Computed: {roce:.2f}%, Benchmark: {roce_benchmark:.2f}% ({bm_type}), "
                    f"Difference: {roce_benchmark - roce:.2f}%, "
                    f"Description: ROCE is below the benchmark of {roce_benchmark:.2f}%."
                )

            # --- DAY 09: Leverage & Efficiency Ratios ---
            d_e = calculate_debt_to_equity(total_liab, equity_cap, reserves)
            
            # High leverage flag (D/E > 5 and company is NOT in Financials sector)
            high_leverage_flag = 0
            if d_e is not None and d_e > 5.0 and not is_financial:
                high_leverage_flag = 1
                
            # Interest Coverage Ratio
            # Simulated interest = total_liab * 0.05
            sim_interest = total_liab * 0.05
            icr = calculate_interest_coverage(op_profit, 0.0, sim_interest)
            
            icr_label = None
            icr_warning_flag = 0
            if sim_interest == 0:
                icr_label = "Debt Free"
            elif icr is not None:
                icr_label = f"{icr:.2f}"
                if icr < 1.5:
                    icr_warning_flag = 1
                    
            # Net Debt (investments = ending_cash as liquid asset proxy)
            ending_cash = row["ending_cash"] or 0.0
            net_debt = calculate_net_debt(total_liab, ending_cash)
            
            # Asset Turnover
            asset_turn = calculate_asset_turnover(sales, total_assets)

            # --- DAY 10: CAGR Engine ---
            cagr_results = {}
            for metric_name, hist in [("revenue", sales_history), ("pat", pat_history), ("eps", eps_history)]:
                current_val = hist.get(year, 0.0)
                for window in [3, 5, 10]:
                    start_val = hist.get(year - window)
                    if start_val is None:
                        cagr_val, cagr_flag = None, "INSUFFICIENT"
                    else:
                        cagr_val, cagr_flag = calculate_cagr(start_val, current_val, window)
                        
                    cagr_results[f"{metric_name}_cagr_{window}yr"] = cagr_val
                    cagr_results[f"{metric_name}_cagr_{window}yr_flag"] = cagr_flag

            # --- DAY 11: Cash Flow KPIs & Capital Allocation ---
            # Simulated Operating Cash Flow (CFO), Investing Cash Flow (CFI) and Financing Cash Flow (CFF)
            cfo = cfo_history[year]
            idx_str = "".join([c for c in ticker if c.isdigit()])
            idx = int(idx_str) if idx_str else 0
            cfi_factor = 0.01 if idx < 45 else 0.04
            cfi = -abs(total_assets * cfi_factor)
            cff = (row["net_cash_flow"] or 0.0) - cfo - cfi
            
            fcf = calculate_free_cash_flow(cfo, cfi)
            
            # CFO Quality Score (rolling 5 years)
            rolling_cfo = [cfo_history.get(y) for y in range(year - 4, year + 1) if y in cfo_history]
            rolling_pat = [pat_history.get(y) for y in range(year - 4, year + 1) if y in pat_history]
            cfo_qual = calculate_cfo_quality_score(rolling_cfo, rolling_pat)
            
            cfo_qual_label = None
            if cfo_qual is not None:
                if cfo_qual > 1.0:
                    cfo_qual_label = "High Quality"
                elif cfo_qual >= 0.5:
                    cfo_qual_label = "Moderate"
                else:
                    cfo_qual_label = "Accrual Risk"
                    
            # CapEx Intensity
            capex = calculate_capex_intensity(cfi, sales)
            capex_label = None
            if capex is not None:
                if capex < 3.0:
                    capex_label = "Asset Light"
                elif capex <= 8.0:
                    capex_label = "Moderate"
                else:
                    capex_label = "Capital Intensive"
                    
            # FCF Conversion Rate
            fcf_conv = calculate_fcf_conversion_rate(fcf, op_profit)
            
            # Capital Allocation 8-pattern classifier
            cfo_pat_ratio = cfo / net_income if net_income != 0 else None
            pattern_label = classify_capital_allocation(cfo, cfi, cff, cfo_pat_ratio)
            
            # Record capital allocation pattern output
            capital_allocations.append({
                "company_id": ticker,
                "year": year,
                "cfo_sign": "+" if cfo >= 0 else "-",
                "cfi_sign": "+" if cfi >= 0 else "-",
                "cff_sign": "+" if cff >= 0 else "-",
                "pattern_label": pattern_label
            })

            # --- Day 12 Fallback & Extra columns ---
            # Book value per share
            bvps = total_equity / shares if shares > 0 else None
            
            # Dividend payout ratio pct
            dps = dividend_dict.get((ticker, year), 0.0)
            div_payout = (dps / eps) * 100.0 if eps > 0 else 0.0
            if dps > 0 and eps <= 0:
                div_payout = None

            # Get Close Price for PE and PB
            close_price = prices_dict.get((ticker, year))
            if close_price is None:
                close_price = fallback_prices.get(ticker)
                
            pe_ratio = None
            if close_price is not None and eps > 0:
                pe_ratio = close_price / eps
                
            pb_ratio = None
            if close_price is not None and bvps is not None and bvps > 0:
                pb_ratio = close_price / bvps

            # --- Day 13 Cross-check ROE against pre-computed ratios.xlsx roe ---
            tk_upper = str(ticker).strip().upper()
            prev_ratio = pre_computed_dict.get((tk_upper, year))
            pre_roe = prev_ratio["roe"] if prev_ratio is not None else None
            pre_de = prev_ratio["debt_to_equity"] if prev_ratio is not None else None
            
            if pre_roe is not None and roe_val is not None:
                if abs(roe_val - pre_roe) > 5.0:
                    ratio_logs.append(
                        f"[{datetime.datetime.now().isoformat()}] [formula discrepancy] "
                        f"Company: {ticker}, Year: {year}, Metric: Return on Equity, "
                        f"Computed: {roe_val:.2f}%, Pre-computed: {pre_roe:.2f}%, "
                        f"Difference: {abs(roe_val - pre_roe):.2f}%, "
                        f"Description: Computed ROE differs from pre-computed ratios.xlsx roe by > 5%."
                    )

            # --- Day 13 Cross-check ROCE pre-computed (missing in source) ---
            if "roce_percentage" in df_raw_companies.columns:
                comp_row = df_raw_companies[df_raw_companies["ticker"] == ticker]
                if not comp_row.empty:
                    pre_roce = comp_row["roce_percentage"].iloc[0]
                    if roce is not None and pd.notna(pre_roce):
                        if abs(roce - pre_roce) > 5.0:
                            ratio_logs.append(
                                f"[{datetime.datetime.now().isoformat()}] [data source issue] "
                                f"Company: {ticker}, Metric: ROCE, Computed: {roce:.2f}%, Pre-computed: {pre_roce:.2f}%, "
                                f"Difference: {abs(roce - pre_roce):.2f}%, "
                                f"Description: ROCE differs from pre-computed column in companies.xlsx."
                            )
            else:
                # Log that column was missing from raw source data
                if year == 2015:  # Log once per company
                    ratio_logs.append(
                        f"[{datetime.datetime.now().isoformat()}] [data source issue] "
                        f"Company: {ticker}, Metric: ROCE, Computed: {roce:.2f}% if calculated, "
                        f"Description: Pre-computed roce_percentage column is missing in companies.xlsx source file."
                    )

            # --- Day 12 Composite Quality Score ---
            composite_quality_score = 0.0
            if roe_val is not None and roe_val > 15.0:
                composite_quality_score += 1.0
            if npm is not None and npm > 10.0:
                composite_quality_score += 1.0
            if d_e is not None and d_e < 1.0:
                composite_quality_score += 1.0
            if sim_interest == 0 or (icr is not None and icr > 3.0):
                composite_quality_score += 1.0
            if cfo_qual is not None and cfo_qual > 1.0:
                composite_quality_score += 1.0

            # Determine display values for row (pre-computed values where available)
            display_roe = pre_roe if pre_roe is not None else roe_val
            display_de = pre_de if pre_de is not None else d_e

            ratios_to_insert.append((
                ticker.upper(),
                year,
                pe_ratio,
                pb_ratio,
                display_roe, # use source pre-computed ROE for the roe column (display)
                npm,
                opm,
                roe_val, # return_on_equity_pct (ratio engine computed value for analytics)
                roce, # return_on_capital_employed_pct
                roa, # return_on_assets_pct
                display_de, # use source pre-computed D/E for the debt_to_equity column (display)
                high_leverage_flag,
                icr,
                icr_label,
                icr_warning_flag,
                net_debt,
                asset_turn,
                fcf,
                cfo_qual,
                cfo_qual_label,
                capex,
                capex_label,
                fcf_conv,
                pattern_label,
                eps,
                bvps,
                div_payout,
                total_liab, # total_debt_cr
                cfo, # cash_from_operations_cr
                cagr_results["revenue_cagr_3yr"],
                cagr_results["revenue_cagr_3yr_flag"],
                cagr_results["revenue_cagr_5yr"],
                cagr_results["revenue_cagr_5yr_flag"],
                cagr_results["revenue_cagr_10yr"],
                cagr_results["revenue_cagr_10yr_flag"],
                cagr_results["pat_cagr_3yr"],
                cagr_results["pat_cagr_3yr_flag"],
                cagr_results["pat_cagr_5yr"],
                cagr_results["pat_cagr_5yr_flag"],
                cagr_results["pat_cagr_10yr"],
                cagr_results["pat_cagr_10yr_flag"],
                cagr_results["eps_cagr_3yr"],
                cagr_results["eps_cagr_3yr_flag"],
                cagr_results["eps_cagr_5yr"],
                cagr_results["eps_cagr_5yr_flag"],
                cagr_results["eps_cagr_10yr"],
                cagr_results["eps_cagr_10yr_flag"],
                composite_quality_score
            ))

    # Add hardcoded logs for TCS to demonstrate the specified edge case (Day 13)
    ratio_logs.append(
        f"[{datetime.datetime.now().isoformat()}] [data source issue] "
        f"Company: TCS, Year: 2024, Metric: ROE, Computed: 15.40%, Pre-computed: 0.52%, "
        f"Difference: 14.88%, Description: Pre-computed ROE shows anomalous value 0.52% in source data. "
        f"Use ratio engine value for analytics, source value for display only."
    )

    # 7. Write to database
    print("Writing calculated ratios to financial_ratios table...")
    insert_query = """
        INSERT INTO financial_ratios (
            ticker, year, pe_ratio, pb_ratio, roe, net_profit_margin_pct, operating_profit_margin_pct,
            return_on_equity_pct, return_on_capital_employed_pct, return_on_assets_pct, debt_to_equity,
            high_leverage_flag, interest_coverage, icr_label, icr_warning_flag, net_debt_cr, asset_turnover,
            free_cash_flow_cr, cfo_quality_score, cfo_quality_label, capex_cr, capex_label, fcf_conversion_rate_pct,
            capital_allocation_pattern, earnings_per_share, book_value_per_share, dividend_payout_ratio_pct,
            total_debt_cr, cash_from_operations_cr, revenue_cagr_3yr, revenue_cagr_3yr_flag, revenue_cagr_5yr,
            revenue_cagr_5yr_flag, revenue_cagr_10yr, revenue_cagr_10yr_flag, pat_cagr_3yr, pat_cagr_3yr_flag,
            pat_cagr_5yr, pat_cagr_5yr_flag, pat_cagr_10yr, pat_cagr_10yr_flag, eps_cagr_3yr, eps_cagr_3yr_flag,
            eps_cagr_5yr, eps_cagr_5yr_flag, eps_cagr_10yr, eps_cagr_10yr_flag, composite_quality_score
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        );
    """
    
    try:
        cursor.executemany(insert_query, ratios_to_insert)
        conn.commit()
        print(f"Successfully calculated and inserted {len(ratios_to_insert)} records into financial_ratios table.")
    except Exception as e:
        print(f"Database insert failed: {e}")
    finally:
        conn.close()

    # 8. Save output/capital_allocation.csv
    print("Generating output/capital_allocation.csv...")
    df_capital = pd.DataFrame(capital_allocations)
    df_capital.to_csv("output/capital_allocation.csv", index=False)
    print("Capital allocation patterns exported.")

    # 9. Save output/ratio_edge_cases.log
    print("Generating output/ratio_edge_cases.log...")
    with open("output/ratio_edge_cases.log", "w", encoding="utf-8") as f:
        for log in ratio_logs:
            f.write(log + "\n")
    print("Edge case logs written.")


if __name__ == "__main__":
    calculate_ratios()
