# Sprint 1 Data Ingestion & Data Quality Report

This report summarizes the results of the Sprint 1 Data Foundation ingestion pipeline, including row counts, validation checks, and foreign key referential integrity audits.

## 📊 Database Row Counts

| Table Name | Row Count |
| --- | --- |
| `sectors` | 5 |
| `companies` | 92 |
| `profitandloss` | 1276 |
| `balancesheet` | 1312 |
| `cashflow` | 1187 |
| `stock_prices` | 5520 |
| `financial_ratios` | 1276 |
| `corporate_actions` | 50 |
| `analysis` | 10 |
| `documents` | 5 |
| `prosandcons` | 10 |
| `peer_groups` | 10 |
| `validation_failures` | 7 |
| `load_audit` | 12 |


## 📂 Source File Ingestion Audit

| File Name | Processed | Loaded | Failures Logged | Status |
| --- | --- | --- | --- | --- |
| `audit_metadata.xlsx` | 10 | 0 | 0 | SUCCESS |
| `corporate_actions.xlsx` | 50 | 50 | 0 | SUCCESS |
| `stock_prices_supp3.xlsx` | 520 | 520 | 0 | SUCCESS |
| `stock_prices_supp2.xlsx` | 1000 | 1000 | 0 | SUCCESS |
| `stock_prices_supp1.xlsx` | 1000 | 1000 | 0 | SUCCESS |
| `stock_prices_core.xlsx` | 3000 | 3000 | 1 | SUCCESS |
| `ratios.xlsx` | 1000 | 1000 | 0 | SUCCESS |
| `cash_flows.xlsx` | 1187 | 1187 | 1 | SUCCESS |
| `balance_sheets.xlsx` | 1312 | 1312 | 1 | SUCCESS |
| `income_statements.xlsx` | 1276 | 1276 | 3 | SUCCESS |
| `companies.xlsx` | 92 | 92 | 1 | SUCCESS |
| `sectors.xlsx` | 5 | 5 | 0 | SUCCESS |


## 🔍 Data Quality Rules Validation Logs

| Rule ID | Severity | Failure Count | Sample Issue |
| --- | --- | --- | --- |
| `DQ-04` | **WARNING** | 1 | Balance sheet discrepancy exceeds 1%: Assets != Liabilities + Equity |
| `DQ-05` | **WARNING** | 1 | OPM cross-check failed: reported=0.1500, computed=0.0826 (Diff: 0.0674) |
| `DQ-06` | **WARNING** | 1 | Revenue/Sales should be positive. Found: 0 |
| `DQ-07` | **WARNING** | 1 | Cash flow reconciliation discrepancy: End Cash != Start Cash + Net Cash Flow |
| `DQ-10` | **WARNING** | 1 | Invalid website URL format: invalid_website_url_test |
| `DQ-15` | **WARNING** | 1 | Inconsistent daily stock prices (High must be maximum and Low must be minimum) |
| `DQ-16` | **WARNING** | 1 | Inconsistent profit ordering (Gross Profit >= Operating Profit >= Net Income) |


## 🛡️ Integrity Verification

### Foreign Key Check
- **Status**: Passed (0 violations) ✅
- `PRAGMA foreign_key_check` returned 0 rows.


### Critical Rejections Audit
- **Status**: Passed (0 critical rejections) ✅
- All raw inputs loaded without schema or referential critical failures.