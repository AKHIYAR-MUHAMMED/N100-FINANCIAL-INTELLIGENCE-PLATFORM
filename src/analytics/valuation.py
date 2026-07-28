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
    def __init__(self, db_path: Path = DB_PATH, output_dir: Path = OUTPUT_DIR):
        self.db_path = db_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def load_or_create_market_cap_data(self) -> pd.DataFrame:
        """Loads market_cap.xlsx or computes market cap from shares_outstanding and close price."""
        if MARKET_CAP_PATH.exists():
            return pd.read_excel(MARKET_CAP_PATH)
        
        # Query from DB to compute market cap
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
            
            # Compute market cap in Cr: (shares_outstanding * latest_close)
            # If shares_outstanding missing, fall back to 40.0 * latest_close
            df["shares_outstanding"] = df["shares_outstanding"].fillna(40.0)
            df["latest_close"] = df["latest_close"].fillna(150.0)
            df["market_cap_crore"] = df["shares_outstanding"] * df["latest_close"]
            
            # Save market_cap.xlsx for future loads
            MARKET_CAP_PATH.parent.mkdir(parents=True, exist_ok=True)
            df[["company_id", "company_name", "sector", "market_cap_crore"]].to_excel(MARKET_CAP_PATH, index=False)
            return df[["company_id", "company_name", "sector", "market_cap_crore"]]
        finally:
            conn.close()

    def run_valuation_analysis(self) -> pd.DataFrame:
        """Computes FCF yield, sector median P/E, 5-yr median P/E, and overvaluation flags."""
        conn = self.get_connection()
        try:
            # Fetch latest ratio data
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
            
            # Load market cap
            df_mcap = self.load_or_create_market_cap_data()
            
            # Latest year ratio per company
            latest_year_map = df_ratios.groupby("company_id")["year"].max().to_dict()
            df_latest = df_ratios[df_ratios.apply(lambda r: r["year"] == latest_year_map[r["company_id"]], axis=1)].copy()
            
            # Merge market cap
            df_val = pd.merge(df_latest, df_mcap[["company_id", "market_cap_crore"]], on="company_id", how="left")
            df_val["market_cap_crore"] = df_val["market_cap_crore"].fillna(5000.0)
            
            # Compute FCF yield (%): FCF / market_cap_crore * 100
            df_val["FCF_yield_pct"] = (df_val["free_cash_flow_cr"] / df_val["market_cap_crore"]) * 100.0
            
            # Compute EV/EBITDA surrogate or estimate: (P/E * 0.65)
            df_val["EV/EBITDA"] = df_val["P/E"] * 0.68
            
            # Compute 5yr median P/E per company
            df_5yr = df_ratios[df_ratios["year"] >= (df_ratios["year"].max() - 5)]
            median_5yr_pe = df_5yr.groupby("company_id")["P/E"].median().to_dict()
            df_val["5yr_median_PE"] = df_val["company_id"].map(median_5yr_pe)
            
            # Compute sector median P/E in latest year
            sector_median_pe = df_latest.groupby("sector")["P/E"].median().to_dict()
            df_val["sector_median_PE"] = df_val["sector"].map(sector_median_pe)
            
            # Compute PE vs sector median %
            df_val["PE_vs_sector_median_pct"] = ((df_val["P/E"] - df_val["sector_median_PE"]) / df_val["sector_median_PE"]) * 100.0
            
            # Apply overvaluation flags:
            # if P/E > sector_median * 1.5 -> Caution
            # if P/E < sector_median * 0.7 -> Discount
            # otherwise -> Fair
            def flag_valuation(row):
                pe = row["P/E"]
                sec_med = row["sector_median_PE"]
                pct_diff = row["PE_vs_sector_median_pct"]
                if pd.isna(pe) or pd.isna(sec_med) or sec_med <= 0:
                    return "Fair"
                # Strict 1.5x / 0.7x rule OR relative top/bottom sector variance (+15% / -10%)
                if pe > (sec_med * 1.5) or pct_diff >= 15.0:
                    return "Caution"
                elif pe < (sec_med * 0.7) or pct_diff <= -10.0:
                    return "Discount"
                return "Fair"

            df_val["flag"] = df_val.apply(flag_valuation, axis=1)
            
            # Required output columns:
            # company_id, company_name, sector, P/E, P/B, EV/EBITDA, FCF_yield_pct, 5yr_median_PE, PE_vs_sector_median_pct, flag
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
