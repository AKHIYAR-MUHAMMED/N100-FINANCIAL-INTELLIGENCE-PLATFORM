import pandas as pd
from pathlib import Path

def generate_peer_groups():
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # 92 companies (COMP01 to COMP92)
    tickers = [f"COMP{i:02d}" for i in range(1, 93)]
    
    # We will exclude COMP85, COMP86, COMP87, COMP88 from the peer groups to test the unassigned company logic
    excluded_tickers = {"COMP85", "COMP86", "COMP87", "COMP88"}
    
    # Define mapping rules based on index
    # We will map them based on (i % len(sectors)) and (i % 10) as in generate_mock_data.py
    sectors = ["Technology", "Financials", "Healthcare", "Energy", "Consumer Goods"]
    
    peer_data = []
    
    for i in range(92):
        ticker = f"COMP{i+1:02d}"
        if ticker in excluded_tickers:
            continue
            
        # Determine the group name
        # If it is one of the last few, put them in "Diversified Conglomerates"
        if ticker in {"COMP89", "COMP90", "COMP91", "COMP92"}:
            group_name = "Diversified Conglomerates"
        else:
            sector = sectors[i % len(sectors)]
            industry_num = i % 10
            
            if sector == "Technology":
                if industry_num == 0:
                    group_name = "IT Services"
                else:
                    group_name = "Software & Tech"
            elif sector == "Financials":
                if industry_num == 1:
                    group_name = "Banking"
                else:
                    group_name = "Non-Banking Financials"
            elif sector == "Healthcare":
                if industry_num == 2:
                    group_name = "Pharmaceuticals"
                else:
                    group_name = "Hospitals & Healthcare"
            elif sector == "Energy":
                if industry_num == 3:
                    group_name = "Oil & Gas"
                else:
                    group_name = "Power & Utilities"
            elif sector == "Consumer Goods":
                if industry_num == 4:
                    group_name = "FMCG"
                else:
                    group_name = "Automobile"
                    
        peer_data.append({
            "ticker": ticker,
            "group_name": group_name
        })
        
    df = pd.DataFrame(peer_data)
    
    # Designate benchmark company for each peer group
    # We choose the first company appearing in each group as the benchmark
    benchmarks = {}
    for group in df["group_name"].unique():
        first_ticker = df[df["group_name"] == group]["ticker"].iloc[0]
        benchmarks[group] = first_ticker
        
    df["is_benchmark"] = df.apply(lambda r: 1 if r["ticker"] == benchmarks[r["group_name"]] else 0, axis=1)
    
    excel_path = raw_dir / "peer_groups.xlsx"
    df.to_excel(excel_path, index=False)
    print(f"Generated peer_groups.xlsx with {len(df)} companies assigned to {df['group_name'].nunique()} groups.")
    print("Benchmark companies:")
    for g, t in benchmarks.items():
        print(f" - {g}: {t}")

if __name__ == '__main__':
    generate_peer_groups()
