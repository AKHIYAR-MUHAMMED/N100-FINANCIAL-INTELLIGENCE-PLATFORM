import os
import re
import sqlite3
import pandas as pd
from pathlib import Path


def parse_analysis_text(input_excel_path: str = "data/raw/analysis.xlsx", output_dir: str = "output"):
    """Parse text fields in analysis.xlsx using regex and cross-validate against computed ratios."""
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(input_excel_path):
        raise FileNotFoundError(f"Input file {input_excel_path} not found.")

    df_analysis = pd.read_excel(input_excel_path)
    
    target_fields = [
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ]
    
    pattern = re.compile(r"(\d+)\s*Years?:?\s*([\d.]+)%", re.IGNORECASE)
    
    parsed_records = []
    failures = []
    
    for idx, row in df_analysis.iterrows():
        company_id = row.get("company_id") or row.get("ticker")
        if not company_id:
            continue
            
        for field in target_fields:
            if field not in row or pd.isna(row[field]):
                failures.append({
                    "company_id": company_id,
                    "metric_type": field,
                    "raw_text": str(row.get(field, "")),
                    "reason": "Missing or NaN value"
                })
                continue
                
            text = str(row[field])
            matches = pattern.findall(text)
            
            if not matches:
                failures.append({
                    "company_id": company_id,
                    "metric_type": field,
                    "raw_text": text,
                    "reason": "No regex match for period and percentage pattern"
                })
            else:
                for period_str, val_str in matches:
                    parsed_records.append({
                        "company_id": company_id,
                        "metric_type": field,
                        "period_years": int(period_str),
                        "value_pct": float(val_str),
                    })
                    
    df_parsed = pd.DataFrame(parsed_records)
    df_failures = pd.DataFrame(failures)
    
    # Connect to SQLite DB to cross-validate parsed CAGR values
    db_path = "data/db/nifty100.db"
    if os.path.exists(db_path) and not df_parsed.empty:
        conn = sqlite3.connect(db_path)
        try:
            ratios_df = pd.read_sql("SELECT * FROM financial_ratios WHERE year = 2023", conn)
            
            divergence_flags = []
            divergence_pcts = []
            
            for _, row in df_parsed.iterrows():
                cid = row["company_id"]
                metric = row["metric_type"]
                period = row["period_years"]
                val = row["value_pct"]
                
                computed_val = None
                comp_row = ratios_df[ratios_df["ticker"] == cid]
                if not comp_row.empty:
                    comp_row = comp_row.iloc[0]
                    if metric == "compounded_sales_growth":
                        col_name = f"revenue_cagr_{period}yr"
                        if col_name in comp_row:
                            computed_val = comp_row[col_name]
                    elif metric == "compounded_profit_growth":
                        col_name = f"pat_cagr_{period}yr"
                        if col_name in comp_row:
                            computed_val = comp_row[col_name]
                    elif metric == "roe":
                        if "roe" in comp_row:
                            computed_val = comp_row["roe"]
                            
                if computed_val is not None and not pd.isna(computed_val) and computed_val != 0:
                    diff = abs(val - computed_val)
                    div_pct = (diff / abs(computed_val)) * 100.0
                    flag = 1 if div_pct > 5.0 else 0
                else:
                    div_pct = 0.0
                    flag = 0
                    
                divergence_pcts.append(round(div_pct, 2))
                divergence_flags.append(flag)
                
            df_parsed["divergence_pct"] = divergence_pcts
            df_parsed["divergence_flag"] = divergence_flags
        finally:
            conn.close()
    else:
        df_parsed["divergence_pct"] = 0.0
        df_parsed["divergence_flag"] = 0

    parsed_csv_path = os.path.join(output_dir, "analysis_parsed.csv")
    failures_csv_path = os.path.join(output_dir, "parse_failures.csv")
    
    df_parsed.to_csv(parsed_csv_path, index=False)
    df_failures.to_csv(failures_csv_path, index=False)
    
    print(f"Analysis text parsing complete. Parsed: {len(df_parsed)} records -> {parsed_csv_path}")
    print(f"Parse failures logged: {len(df_failures)} records -> {failures_csv_path}")
    return df_parsed, df_failures


if __name__ == "__main__":
    parse_analysis_text()
