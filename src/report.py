from pathlib import Path

import pandas as pd

from src.database import DatabaseManager


def generate_report():
    print("Generating data quality report...")
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()

    report_path = Path("output/report.md")

    # Fetch total rows per table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

    table_counts = []
    for tbl in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cursor.fetchone()[0]
        table_counts.append((tbl, cnt))

    # Fetch validation failures summary
    query_failures = """
        SELECT rule_id, severity, COUNT(*) as count, message
        FROM validation_failures
        GROUP BY rule_id, severity
        ORDER BY count DESC
    """
    df_failures = pd.read_sql_query(query_failures, conn)

    # Fetch audit load history
    query_audit = """
        SELECT file_name, records_processed, records_loaded, failures_count, status
        FROM load_audit
        ORDER BY load_id DESC
        LIMIT 12
    """
    df_audit = pd.read_sql_query(query_audit, conn)

    # Check for foreign key violations
    violations = db_manager.run_fk_check()
    conn.close()

    # Generate markdown content
    md = []
    md.append("# Sprint 1 Data Ingestion & Data Quality Report\n")
    md.append(
        "This report summarizes the results of the Sprint 1 Data Foundation ingestion pipeline, including row counts, validation checks, and foreign key referential integrity audits.\n"
    )

    md.append("## 📊 Database Row Counts\n")
    md.append("| Table Name | Row Count |")
    md.append("| --- | --- |")
    for tbl, count in table_counts:
        md.append(f"| `{tbl}` | {count} |")
    md.append("\n")

    md.append("## 📂 Source File Ingestion Audit\n")
    md.append("| File Name | Processed | Loaded | Failures Logged | Status |")
    md.append("| --- | --- | --- | --- | --- |")
    for idx, row in df_audit.iterrows():
        md.append(
            f"| `{row['file_name']}` | {row['records_processed']} | {row['records_loaded']} | {row['failures_count']} | {row['status']} |"
        )
    md.append("\n")

    md.append("## 🔍 Data Quality Rules Validation Logs\n")
    if df_failures.empty:
        md.append(
            "No validation failures or warnings were logged in this ingestion run. 🎉\n"
        )
    else:
        md.append("| Rule ID | Severity | Failure Count | Sample Issue |")
        md.append("| --- | --- | --- | --- |")
        for idx, row in df_failures.iterrows():
            md.append(
                f"| `{row['rule_id']}` | **{row['severity']}** | {row['count']} | {row['message']} |"
            )
        md.append("\n")

    md.append("## 🛡️ Integrity Verification\n")
    md.append("### Foreign Key Check")
    if len(violations) == 0:
        md.append("- **Status**: Passed (0 violations) ✅")
        md.append("- `PRAGMA foreign_key_check` returned 0 rows.")
    else:
        md.append(f"- **Status**: Failed ({len(violations)} violations) ❌")
        md.append("- Violations list:")
        for v in violations:
            md.append(f"  - Table `{v[0]}`, Row ID `{v[1]}`, Parent Table `{v[2]}`")
    md.append("\n")

    md.append("### Critical Rejections Audit")
    critical_count = (
        len(df_failures[df_failures["severity"] == "CRITICAL"])
        if not df_failures.empty
        else 0
    )
    if critical_count == 0:
        md.append("- **Status**: Passed (0 critical rejections) ✅")
        md.append(
            "- All raw inputs loaded without schema or referential critical failures."
        )
    else:
        md.append(
            f"- **Status**: Warning ({critical_count} critical records dropped) ⚠️"
        )
        md.append("- Critical rows were dropped to preserve database constraints.")

    # Write report
    report_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Report generated successfully at {report_path.resolve()}")


if __name__ == "__main__":
    generate_report()
