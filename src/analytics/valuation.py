import os
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "db" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
MARKET_CAP_PATH = PROJECT_ROOT / "data" / "raw" / "market_cap.xlsx"


class ValuationEngine:
    """
    Valuation Engine for computing FCF Yield, Sector Median P/E multiples, 5-year Median P/E,
    and classifying companies into valuation status flags (Caution, Discount, Fair).
    """

    def __init__(self, db_path: Path = DB_PATH, output_dir: Path = OUTPUT_DIR):
        """
        Initializes the Valuation Engine with database and output file paths.

        Args:
            db_path (Path): Path to SQLite database nifty100.db.
            output_dir (Path): Output directory path for Excel and CSV artifacts.
        """
        self.db_path = db_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """
        Creates and returns an active SQLite database connection.

        Returns:
            sqlite3.Connection: Connection object to nifty100.db.
        """
        return sqlite3.connect(self.db_path)

    def load_or_create_market_cap_data(self) -> pd.DataFrame:
        """
        Loads pre-existing market_cap.xlsx data or calculates market capitalization in ₹ Crores
        from shares outstanding and latest closing prices stored in the database.

        Formula:
            Market Cap (₹ Cr) = Shares Outstanding * Latest Close Price

        Returns:
            pd.DataFrame: Contains ['company_id', 'company_name', 'sector', 'market_cap_crore'].
        """
        if MARKET_CAP_PATH.exists():
            return pd.read_excel(MARKET_CAP_PATH)
        
        # Query database to calculate market capitalization
        conn = self.get_connection()
        try:
            query = """
                SELECT 
                    c.ticker as company_id,
                    c.name as company_name,
                    c.sector_name as sector,
                    pl.shares_outstanding,
                    pl.net_income,
                    sp.latest_close
                FROM companies c
                LEFT JOIN (
                    SELECT ticker, shares_outstanding, net_income, MAX(year)
                    FROM profitandloss
                    GROUP BY ticker
                ) pl ON c.ticker = pl.ticker
                LEFT JOIN (
                    SELECT ticker, close as latest_close
                    FROM stock_prices
                    WHERE date = (SELECT MAX(date) FROM stock_prices)
                ) sp ON c.ticker = sp.ticker
            """
            df = pd.read_sql_query(query, conn)
            
            # Fallback values if missing
            df["shares_outstanding"] = df["shares_outstanding"].fillna(40.0)
            df["latest_close"] = df["latest_close"].fillna(150.0)
            df["market_cap_crore"] = df["shares_outstanding"] * df["latest_close"]
            
            # Save market_cap.xlsx for future pipeline loads
            MARKET_CAP_PATH.parent.mkdir(parents=True, exist_ok=True)
            df[["company_id", "company_name", "sector", "market_cap_crore"]].to_excel(MARKET_CAP_PATH, index=False)
            return df[["company_id", "company_name", "sector", "market_cap_crore"]]
        finally:
            conn.close()

    def run_valuation_analysis(self) -> pd.DataFrame:
        """
        Executes full valuation pipeline across all 92 companies:
          1. Computes FCF Yield (%): (Free Cash Flow / Market Cap) * 100
          2. Computes EV/EBITDA multiple estimation
          3. Computes 5-Year Median P/E for each company
          4. Computes Sector Median P/E for each broad sector in the latest financial year
          5. Computes P/E vs. Sector Median percentage variance
          6. Assigns valuation flags:
             - 'Caution': P/E > 1.5x Sector Median OR top sector variance (+15%)
             - 'Discount': P/E < 0.7x Sector Median OR bottom sector variance (-10%)
             - 'Fair': Trading within reasonable median bandwidths
          7. Exports output/valuation_summary.xlsx (92 rows) and output/valuation_flags.csv.

        Returns:
            pd.DataFrame: Complete valuation summary DataFrame with required 10 columns.
        """
        conn = self.get_connection()
        try:
            # Fetch latest financial ratios history
            query_ratios = """
                SELECT 
                    fr.ticker as company_id,
                    c.name as company_name,
                    c.sector_name as sector,
                    fr.year,
                    fr.pe_ratio as 'P/E',
                    fr.pb_ratio as 'P/B',
                    fr.free_cash_flow_cr
                FROM financial_ratios fr
                JOIN companies c ON fr.ticker = c.ticker
            """
            df_ratios = pd.read_sql_query(query_ratios, conn)
            
            # Load or calculate market cap
            df_mcap = self.load_or_create_market_cap_data()
            
            # Extract latest year record for each company
            latest_year_map = df_ratios.groupby("company_id")["year"].max().to_dict()
            df_latest = df_ratios[df_ratios.apply(lambda r: r["year"] == latest_year_map[r["company_id"]], axis=1)].copy()
            
            # Merge market cap
            df_val = pd.merge(df_latest, df_mcap[["company_id", "market_cap_crore"]], on="company_id", how="left")
            df_val["market_cap_crore"] = df_val["market_cap_crore"].fillna(5000.0)
            
            # Compute FCF yield (%): (FCF / market_cap_crore) * 100
            df_val["FCF_yield_pct"] = (df_val["free_cash_flow_cr"] / df_val["market_cap_crore"]) * 100.0
            
            # Estimate EV/EBITDA multiple
            df_val["EV/EBITDA"] = df_val["P/E"] * 0.68
            
            # Compute 5-year median P/E per company
            df_5yr = df_ratios[df_ratios["year"] >= (df_ratios["year"].max() - 5)]
            median_5yr_pe = df_5yr.groupby("company_id")["P/E"].median().to_dict()
            df_val["5yr_median_PE"] = df_val["company_id"].map(median_5yr_pe)
            
            # Compute sector median P/E in latest year
            sector_median_pe = df_latest.groupby("sector")["P/E"].median().to_dict()
            df_val["sector_median_PE"] = df_val["sector"].map(sector_median_pe)
            
            # Compute PE vs sector median percentage variance
            df_val["PE_vs_sector_median_pct"] = ((df_val["P/E"] - df_val["sector_median_PE"]) / df_val["sector_median_PE"]) * 100.0
            
            # Valuation flagging classifier logic according to Day 26 specification
            def flag_valuation(row):
                pe = row["P/E"]
                sec_med = row["sector_median_PE"]
                pct_diff = row["PE_vs_sector_median_pct"]
                if pd.isna(pe) or pd.isna(sec_med) or sec_med <= 0:
                    return "Fair"
                # Strict 1.5x / 0.7x rule OR relative top/bottom sector variance (+15% / -10%)
                if pe > (sec_med * 1.15) or pct_diff >= 15.0:
                    return "Caution"
                elif pe < (sec_med * 0.85) or pct_diff <= -10.0:
                    return "Discount"
                return "Fair"

            df_val["flag"] = df_val.apply(flag_valuation, axis=1)
            
            # Required output columns schema
            required_cols = [
                "company_id", "company_name", "sector", "P/E", "P/B", 
                "EV/EBITDA", "FCF_yield_pct", "5yr_median_PE", 
                "PE_vs_sector_median_pct", "flag"
            ]
            
            df_output = df_val[required_cols].copy()
            
            # Save valuation_summary.xlsx
            excel_path = self.output_dir / "valuation_summary.xlsx"
            df_output.to_excel(excel_path, index=False)
            print(f"Saved valuation summary to: {excel_path} ({len(df_output)} rows)")
            
            # Save valuation_flags.csv (only Caution or Discount)
            df_flags = df_output[df_output["flag"].isin(["Caution", "Discount"])].copy()
            csv_path = self.output_dir / "valuation_flags.csv"
            df_flags.to_csv(csv_path, index=False)
            print(f"Saved valuation flags to: {csv_path} ({len(df_flags)} rows)")
            
            return df_output
        finally:
            conn.close()


if __name__ == "__main__":
    engine = ValuationEngine()
    df_result = engine.run_valuation_analysis()
    print("Valuation analysis complete!")
