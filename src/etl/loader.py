from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.database import DatabaseManager
from src.etl.normaliser import normalize_ticker, normalize_year
from src.etl.validator import SchemaValidator


class ETLLoader:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_manager = DatabaseManager(db_path) if db_path else DatabaseManager()
        self.validator = SchemaValidator()
        self.raw_dir = Path("data/raw")
        self.processed_dir = Path("data/processed")
        self.output_dir = Path("output")

        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_pipeline(self):
        print("Starting Sprint 1 ETL Pipeline...")

        # 1. Initialize schema (re-initializes cleanly, dropping old tables)
        self.db_manager.initialize_schema()

        # 2. Get connection
        conn = self.db_manager.get_connection()

        # We will keep track of loaded companies to validate relationships
        companies_master_df = pd.DataFrame(columns=["ticker"])

        # Audit records list to save to load_audit
        audit_records = []

        # Ingestion configurations for the 12 files
        files_config = [
            {"file": "sectors.xlsx", "table": "sectors", "type": "sectors"},
            {"file": "companies.xlsx", "table": "companies", "type": "companies"},
            {
                "file": "income_statements.xlsx",
                "table": "profitandloss",
                "type": "pnl",
            },
            {"file": "balance_sheets.xlsx", "table": "balancesheet", "type": "bs"},
            {"file": "cash_flows.xlsx", "table": "cashflow", "type": "cf"},
            {"file": "ratios.xlsx", "table": "financial_ratios", "type": "ratios"},
            {
                "file": "stock_prices_core.xlsx",
                "table": "stock_prices",
                "type": "prices",
            },
            {
                "file": "stock_prices_supp1.xlsx",
                "table": "stock_prices",
                "type": "prices",
            },
            {
                "file": "stock_prices_supp2.xlsx",
                "table": "stock_prices",
                "type": "prices",
            },
            {
                "file": "stock_prices_supp3.xlsx",
                "table": "stock_prices",
                "type": "prices",
            },
            {
                "file": "corporate_actions.xlsx",
                "table": "corporate_actions",
                "type": "corp",
            },
            {
                "file": "audit_metadata.xlsx",
                "table": None,
                "type": "audit_meta",
            },  # supplementary metadata (no direct table mapping)
        ]

        for config in files_config:
            file_name = config["file"]
            file_path = self.raw_dir / file_name
            table_name = config["table"]
            sheet_type = config["type"]

            if not file_path.is_file():
                print(f"Warning: File {file_name} not found in raw data directory.")
                continue

            print(f"Processing {file_name}...")

            # Load file
            try:
                df = pd.read_excel(file_path)
            except Exception as e:
                print(f"Error loading {file_name}: {e}")
                audit_records.append(
                    {
                        "file_name": file_name,
                        "records_processed": 0,
                        "records_loaded": 0,
                        "failures_count": 1,
                        "status": "FAILED",
                    }
                )
                continue

            records_processed = len(df)

            # If the file is empty, log success with 0 loads
            if df.empty:
                audit_records.append(
                    {
                        "file_name": file_name,
                        "records_processed": 0,
                        "records_loaded": 0,
                        "failures_count": 0,
                        "status": "SUCCESS",
                    }
                )
                continue

            # Perform Ticker & Year/Date normalisation on appropriate columns
            if "ticker" in df.columns:
                df["ticker"] = df["ticker"].apply(
                    lambda x: normalize_ticker(x) if pd.notna(x) else x
                )

            if "year" in df.columns:
                df["year"] = df["year"].apply(
                    lambda x: normalize_year(x) if pd.notna(x) else x
                )

            if "date" in df.columns:
                # Standardize date format to YYYY-MM-DD
                df["date"] = df["date"].apply(
                    lambda x: (
                        pd.to_datetime(x).strftime("%Y-%m-%d") if pd.notna(x) else x
                    )
                )

            # For companies, add a mock website URL if website doesn't exist
            if sheet_type == "companies":
                if "website" not in df.columns:
                    df["website"] = df.apply(
                        lambda r: (
                            f"https://www.{str(r['ticker']).lower()}.com"
                            if pd.notna(r["ticker"])
                            else np.nan
                        ),
                        axis=1,
                    )
                    # Add one invalid URL case for warning logging test
                    if len(df) > 5:
                        df.loc[5, "website"] = "invalid_website_url_test"

            # Store the normalized staging dataframe to processed directory
            processed_file_path = self.processed_dir / f"{Path(file_name).stem}.csv"
            df.to_csv(processed_file_path, index=False)

            # Perform Data Quality validations
            initial_failures_count = len(self.validator.failures)

            if sheet_type == "companies":
                self.validator.validate_companies(df, file_name)
            elif sheet_type == "sectors":
                pass
            elif sheet_type == "prices":
                self.validator.validate_relationships(
                    df, companies_master_df, file_name, is_prices=True
                )
                self.validator.validate_prices(df, file_name)
            elif sheet_type in ["pnl", "bs", "cf"]:
                self.validator.validate_relationships(
                    df, companies_master_df, file_name, is_prices=False
                )
                self.validator.validate_financials(df, file_name, sheet_type)
            elif sheet_type == "ratios":
                self.validator.validate_relationships(
                    df, companies_master_df, file_name, is_prices=False
                )
                self.validator.validate_financials(df, file_name, "ratios")
            elif sheet_type == "corp":
                self.validator.validate_relationships(
                    df, companies_master_df, file_name, is_prices=True
                )
                self.validator.validate_corporate_actions(df, file_name)

            # Fetch failures generated during this file's run
            file_failures = self.validator.failures[initial_failures_count:]
            failures_count = len(file_failures)

            # Identify indices with CRITICAL errors to reject/drop
            critical_indices = set()
            for failure in file_failures:
                if failure.severity == "CRITICAL" and failure.row_index is not None:
                    # Ignore duplicate PK rules here, as we handle them via drop_duplicates to keep the first occurrence
                    if failure.rule_id in ["DQ-01"]:
                        continue
                    critical_indices.add(failure.row_index)

            # Keep track of records we'll actually load
            df_to_load = df.copy()
            if critical_indices:
                df_to_load = df_to_load.drop(index=list(critical_indices))
                print(
                    f"  Rejected {len(critical_indices)} rows due to CRITICAL failures in {file_name}"
                )

            # SQLite enforce constraints: We must also filter out duplicate primary keys
            if not df_to_load.empty:
                if sheet_type == "companies" and "ticker" in df_to_load.columns:
                    dups = df_to_load[
                        df_to_load.duplicated(subset=["ticker"], keep="first")
                    ]
                    for idx, row in dups.iterrows():
                        self.validator.log_failure(
                            company_ticker=row["ticker"],
                            file_name=file_name,
                            row_index=int(idx),
                            rule_id="DQ-01",
                            severity="CRITICAL",
                            column_name="ticker",
                            invalid_value=row["ticker"],
                            message=f"Duplicate primary key dropped: {row['ticker']}",
                        )
                    df_to_load = df_to_load.drop_duplicates(
                        subset=["ticker"], keep="first"
                    )
                elif (
                    sheet_type == "prices"
                    and "ticker" in df_to_load.columns
                    and "date" in df_to_load.columns
                ):
                    dups = df_to_load[
                        df_to_load.duplicated(subset=["ticker", "date"], keep="first")
                    ]
                    for idx, row in dups.iterrows():
                        self.validator.log_failure(
                            company_ticker=row["ticker"],
                            file_name=file_name,
                            row_index=int(idx),
                            rule_id="DQ-01",
                            severity="CRITICAL",
                            column_name="ticker, date",
                            invalid_value=f"({row['ticker']}, {row['date']})",
                            message=f"Duplicate PK dropped: ({row['ticker']}, {row['date']})",
                        )
                    df_to_load = df_to_load.drop_duplicates(
                        subset=["ticker", "date"], keep="first"
                    )
                elif (
                    sheet_type in ["pnl", "bs", "cf", "ratios"]
                    and "ticker" in df_to_load.columns
                    and "year" in df_to_load.columns
                ):
                    dups = df_to_load[
                        df_to_load.duplicated(subset=["ticker", "year"], keep="first")
                    ]
                    for idx, row in dups.iterrows():
                        self.validator.log_failure(
                            company_ticker=row["ticker"],
                            file_name=file_name,
                            row_index=int(idx),
                            rule_id="DQ-01",
                            severity="CRITICAL",
                            column_name="ticker, year",
                            invalid_value=f"({row['ticker']}, {row['year']})",
                            message=f"Duplicate PK dropped: ({row['ticker']}, {row['year']})",
                        )
                    df_to_load = df_to_load.drop_duplicates(
                        subset=["ticker", "year"], keep="first"
                    )

            records_loaded = len(df_to_load) if table_name else 0

            # Load into database
            if table_name and not df_to_load.empty:
                try:
                    df_to_load.to_sql(table_name, conn, if_exists="append", index=False)
                    conn.commit()
                    print(
                        f"  Successfully loaded {records_loaded} rows into {table_name}"
                    )
                except Exception as e:
                    print(f"  Database insert error for {file_name}: {e}")
                    audit_records.append(
                        {
                            "file_name": file_name,
                            "records_processed": records_processed,
                            "records_loaded": 0,
                            "failures_count": failures_count + 1,
                            "status": "FAILED",
                        }
                    )
                    continue

            # If companies table was loaded, keep track of companies df for FK relations
            if sheet_type == "companies" and not df_to_load.empty:
                companies_master_df = df_to_load[["ticker"]].copy()

            audit_records.append(
                {
                    "file_name": file_name,
                    "records_processed": records_processed,
                    "records_loaded": records_loaded,
                    "failures_count": failures_count,
                    "status": "SUCCESS",
                }
            )

        # 3. Populate placeholder tables (analysis, documents, prosandcons, peer_groups) with realistic dummy data
        if not companies_master_df.empty:
            tickers = list(companies_master_df["ticker"].dropna().unique())

            # Populate analysis table
            analysis_data = []
            for i, t in enumerate(tickers[:10]):  # First 10 companies
                rating = "Buy" if i % 3 == 0 else ("Hold" if i % 3 == 1 else "Sell")
                target_p = 1500.0 + (i * 250)
                analysis_data.append(
                    {
                        "ticker": t,
                        "year": 2026,
                        "rating": rating,
                        "target_price": target_p,
                    }
                )
            df_analysis = pd.DataFrame(analysis_data)
            df_analysis.to_sql("analysis", conn, if_exists="append", index=False)

            # Populate documents table
            doc_data = []
            for i, t in enumerate(tickers[:5]):
                doc_data.append(
                    {
                        "ticker": t,
                        "document_name": f"Annual_Report_FY25_{t}",
                        "file_path": f"/reports/FY25_{t}.pdf",
                    }
                )
            df_docs = pd.DataFrame(doc_data)
            df_docs.to_sql("documents", conn, if_exists="append", index=False)

            # Populate prosandcons table
            pro_con_data = []
            for i, t in enumerate(tickers[:5]):
                pro_con_data.append(
                    {
                        "ticker": t,
                        "type": "Pro",
                        "point": "Strong management and operating cash flows.",
                    }
                )
                pro_con_data.append(
                    {
                        "ticker": t,
                        "type": "Con",
                        "point": "High leverage ratio and intense industry competition.",
                    }
                )
            df_pro_con = pd.DataFrame(pro_con_data)
            df_pro_con.to_sql("prosandcons", conn, if_exists="append", index=False)

            # Populate peer_groups table
            peer_data = []
            for i, t in enumerate(tickers[:10]):
                group_name = (
                    "Nifty Top Tech Peers"
                    if i % 2 == 0
                    else "Nifty Top Financial Peers"
                )
                peer_data.append({"group_name": group_name, "ticker": t})
            df_peers = pd.DataFrame(peer_data)
            df_peers.to_sql("peer_groups", conn, if_exists="append", index=False)

            conn.commit()
            print(
                "  Successfully populated dummy records in analysis, documents, prosandcons, and peer_groups."
            )

        # Write validation failures to database
        df_failures = self.validator.get_failures_df()
        if not df_failures.empty:
            try:
                df_failures_to_db = df_failures.copy()
                df_failures_to_db["invalid_value"] = df_failures_to_db[
                    "invalid_value"
                ].astype(str)
                df_failures_to_db.to_sql(
                    "validation_failures", conn, if_exists="append", index=False
                )
                conn.commit()
            except Exception as e:
                print(f"Error saving validation failures to database: {e}")

        # Write load audit records to database
        df_audit = pd.DataFrame(audit_records)
        if not df_audit.empty:
            try:
                df_audit_to_db = df_audit.copy()
                df_audit_to_db.to_sql(
                    "load_audit", conn, if_exists="append", index=False
                )
                conn.commit()
            except Exception as e:
                print(f"Error saving load audit to database: {e}")

        conn.close()

        # Save logs to CSV files
        self.validator.save_failures(self.output_dir / "validation_failures.csv")
        df_audit.to_csv(self.output_dir / "load_audit.csv", index=False)

        # Final Foreign Key check
        fk_violations = self.db_manager.run_fk_check()
        print("\nETL Ingestion Run Summary:")
        print(f"  Total validation failures logged: {len(self.validator.failures)}")
        print(
            f"  Critical failures: {len([f for f in self.validator.failures if f.severity == 'CRITICAL'])}"
        )
        print(
            f"  Warnings: {len([f for f in self.validator.failures if f.severity == 'WARNING'])}"
        )
        print(f"  Foreign Key violations in SQLite: {len(fk_violations)}")

        # Print per-table counts loaded
        print("\nLoaded Row Counts:")
        for record in audit_records:
            print(
                f"  {record['file_name']}: processed={record['records_processed']}, loaded={record['records_loaded']}, rejected={record['records_processed'] - record['records_loaded']}"
            )

        return len(fk_violations)


if __name__ == "__main__":
    loader = ETLLoader()
    loader.run_pipeline()
