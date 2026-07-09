import pandas as pd

from src.database import DatabaseManager


def calculate_ratios():
    print("Calculating financial ratios...")
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    # Clear existing financial ratios to calculate cleanly
    cursor.execute("DELETE FROM financial_ratios;")
    conn.commit()

    # Query all P&L and Balance Sheet records matching ticker and year
    query = """
        SELECT
            p.ticker,
            p.year,
            p.sales,
            p.operating_profit,
            p.net_income,
            p.eps,
            p.shares_outstanding,
            b.total_assets,
            b.total_liabilities,
            b.total_equity
        FROM profitandloss p
        JOIN balancesheet b ON p.ticker = b.ticker AND p.year = b.year
    """
    df_fin = pd.read_sql_query(query, conn)

    if df_fin.empty:
        print("No financial statement records found to calculate ratios.")
        conn.close()
        return

    # For PE and PB ratios, we'll fetch average stock prices per year for each company
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

    # Fetch company overall average close price as fallback
    fallback_query = """
        SELECT
            ticker,
            AVG(close) as overall_avg_close
        FROM stock_prices
        GROUP BY ticker
    """
    df_fallback = pd.read_sql_query(fallback_query, conn)

    # Merge financial statements, stock prices, and fallbacks
    df_merged = pd.merge(
        df_fin,
        df_prices,
        left_on=["ticker", "year"],
        right_on=["ticker", "price_year"],
        how="left"
    )
    df_merged = pd.merge(df_merged, df_fallback, on="ticker", how="left")

    ratios_to_insert = []

    for idx, row in df_merged.iterrows():
        ticker = row["ticker"]
        year = int(row["year"])
        net_inc = row["net_income"]
        eq = row["total_equity"]
        liab = row["total_liabilities"]
        eps = row["eps"]
        shares = row["shares_outstanding"]
        avg_close = row["avg_close"]
        overall_avg = row["overall_avg_close"]

        # Use fallback if year-specific close is missing
        close_price = avg_close if pd.notna(avg_close) else overall_avg

        # 1. ROE (Return on Equity) = Net Income / Total Equity * 100
        roe = None
        if pd.notna(eq) and eq != 0:
            roe = (net_inc / eq) * 100.0

        # 2. Debt-to-Equity = Total Liabilities / Total Equity
        d_e = None
        if pd.notna(eq) and eq != 0:
            d_e = liab / eq

        # 3. PE Ratio = Close Price / EPS
        pe = None
        if pd.notna(close_price) and pd.notna(eps) and eps != 0:
            pe = close_price / eps

        # 4. PB Ratio = Close Price / Book Value Per Share
        # Book Value Per Share = Total Equity / Shares Outstanding
        pb = None
        if pd.notna(close_price) and pd.notna(eq) and pd.notna(shares) and shares > 0:
            bvps = eq / shares
            if bvps != 0:
                pb = close_price / bvps

        ratios_to_insert.append((ticker, year, pe, pb, roe, d_e))

    # Insert into financial_ratios
    try:
        cursor.executemany(
            """
            INSERT INTO financial_ratios (ticker, year, pe_ratio, pb_ratio, roe, debt_to_equity)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            ratios_to_insert,
        )
        conn.commit()
        print(
            f"Successfully calculated and inserted {len(ratios_to_insert)} ratios records into financial_ratios table."
        )
    except Exception as e:
        print(f"Error saving financial ratios to database: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    calculate_ratios()
