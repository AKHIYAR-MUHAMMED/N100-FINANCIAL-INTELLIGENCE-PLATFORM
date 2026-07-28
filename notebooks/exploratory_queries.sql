-- ==============================================================================
-- NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM: EXPLORATORY & AUDIT SQL SUITE
-- 
-- Purpose:
--   Comprehensive repository of SQL exploratory, data quality (DQ), financial statement
--   reconciliation, and data integrity audit queries for the Nifty 100 SQLite database (nifty100.db).
--
-- Target Schema Tables:
--   - sectors, companies, profitandloss, balancesheet, cashflow, stock_prices,
--     financial_ratios, corporate_actions, analysis, documents, prosandcons,
--     peer_groups, validation_failures, load_audit.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 1: Database Table Row Counts & Ingestion Integrity Verification
-- Purpose:
--   Aggregates total record counts across all 14 schema tables using a set of UNION ALL queries.
--   Enables data engineers and analysts to instantly verify database load completeness
--   against raw Excel row counts and ETL load audit logs.
-- ------------------------------------------------------------------------------
SELECT 'sectors' AS table_name, COUNT(*) AS row_count FROM sectors
UNION ALL
SELECT 'companies', COUNT(*) FROM companies
UNION ALL
SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL
SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL
SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL
SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL
SELECT 'corporate_actions', COUNT(*) FROM corporate_actions
UNION ALL
SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL
SELECT 'peer_groups', COUNT(*) FROM peer_groups
UNION ALL
SELECT 'validation_failures', COUNT(*) FROM validation_failures
UNION ALL
SELECT 'load_audit', COUNT(*) FROM load_audit;

-- ------------------------------------------------------------------------------
-- Query 2: Sector Distribution & Industry Diversification Audit
-- Purpose:
--   Calculates company counts per broad sector to monitor market coverage, sectoral concentration,
--   and ensure proper categorization across consumer, energy, financials, healthcare, and technology.
-- ------------------------------------------------------------------------------
SELECT 
    sector_name, 
    COUNT(*) AS company_count
FROM companies
GROUP BY sector_name
ORDER BY company_count DESC;

-- ------------------------------------------------------------------------------
-- Query 3: NULL Value & Primary Key Integrity Check on Company Metadata
-- Purpose:
--   Performs a conditional null-check aggregation over critical company metadata fields
--   (ticker, company name, sector_name). Expects 0 nulls for clean primary key enforcement.
-- ------------------------------------------------------------------------------
SELECT 
    SUM(CASE WHEN ticker IS NULL THEN 1 ELSE 0 END) AS null_ticker_companies,
    SUM(CASE WHEN name IS NULL THEN 1 ELSE 0 END) AS null_name_companies,
    SUM(CASE WHEN sector_name IS NULL THEN 1 ELSE 0 END) AS null_sector_companies
FROM companies;

-- ------------------------------------------------------------------------------
-- Query 4: Duplicate Primary Key & Composite Key Check on Daily Stock Prices
-- Purpose:
--   Groups daily stock price records by (ticker, date) composite primary key to identify
--   duplicate daily trading records. Returns empty set if PK uniqueness is clean.
-- ------------------------------------------------------------------------------
SELECT 
    ticker, 
    date, 
    COUNT(*) AS record_count
FROM stock_prices
GROUP BY ticker, date
HAVING record_count > 1;

-- ------------------------------------------------------------------------------
-- Query 5: Sectoral Financial Performance Aggregation & Profitability Benchmarking
-- Purpose:
--   Computes average Sales (Revenue), Gross Profit, and Net Income across broad sectors by joining
--   the companies metadata table with profitandloss statement history. Orders by average net income.
-- ------------------------------------------------------------------------------
SELECT 
    c.sector_name,
    COUNT(DISTINCT c.ticker) AS companies_count,
    ROUND(AVG(i.sales), 2) AS avg_sales,
    ROUND(AVG(i.gross_profit), 2) AS avg_gross_profit,
    ROUND(AVG(i.net_income), 2) AS avg_net_income
FROM companies c
JOIN profitandloss i ON c.ticker = i.ticker
GROUP BY c.sector_name
ORDER BY avg_net_income DESC;

-- ------------------------------------------------------------------------------
-- Query 6: Balance Sheet Fundamental Accounting Identity Audit (DQ-04 Rule)
-- Purpose:
--   Validates the fundamental accounting identity: Total Assets = Total Liabilities + Total Equity.
--   Flags records with relative discrepancy >= 1.0% (0.01) for data quality investigation.
-- ------------------------------------------------------------------------------
SELECT 
    ticker, 
    year, 
    total_assets, 
    total_liabilities, 
    total_equity,
    ROUND(ABS(total_assets - (total_liabilities + total_equity)), 2) AS discrepancy
FROM balancesheet
WHERE ABS(total_assets - (total_liabilities + total_equity)) / total_assets >= 0.01;

-- ------------------------------------------------------------------------------
-- Query 7: Cash Flow Statement Reconciliation Audit (DQ-07 Rule)
-- Purpose:
--   Validates cash flow balance reconciliation equation: Ending Cash = Beginning Cash + Net Cash Flow.
--   Flags records with absolute difference exceeding ₹1 Crore for DQ investigation.
-- ------------------------------------------------------------------------------
SELECT 
    ticker, 
    year, 
    beginning_cash, 
    ending_cash, 
    net_cash_flow,
    ROUND(ABS(ending_cash - (beginning_cash + net_cash_flow)), 2) AS discrepancy
FROM cashflow
WHERE ABS(ending_cash - (beginning_cash + net_cash_flow)) > 1.0;

-- ------------------------------------------------------------------------------
-- Query 8: Stock Price Trading Volatility & Volume Summary Statistics
-- Purpose:
--   Calculates 52-week/historical price ranges (Min Low, Max High, Average Close) and average daily
--   trading volume across Nifty 100 constituents for liquidity assessment.
-- ------------------------------------------------------------------------------
SELECT 
    ticker,
    COUNT(*) AS trading_days,
    ROUND(MIN(low), 2) AS min_price,
    ROUND(MAX(high), 2) AS max_price,
    ROUND(AVG(close), 2) AS avg_close_price,
    ROUND(AVG(volume), 0) AS avg_daily_volume
FROM stock_prices
GROUP BY ticker
LIMIT 10;

-- ------------------------------------------------------------------------------
-- Query 9: Data Quality Validation Failure Frequency Analysis
-- Purpose:
--   Groups validation failures logged in validation_failures table by Rule ID and Severity
--   (CRITICAL vs WARNING) to rank top data quality failure modes across dataset files.
-- ------------------------------------------------------------------------------
SELECT 
    rule_id, 
    severity, 
    COUNT(*) AS failure_count
FROM validation_failures
GROUP BY rule_id, severity
ORDER BY failure_count DESC;

-- ------------------------------------------------------------------------------
-- Query 10: Corporate Actions Aggregation (Dividends & Stock Splits)
-- Purpose:
--   Summarizes corporate action occurrences and average values split by action type (Dividend vs Split),
--   providing corporate payout historical insights across portfolio companies.
-- ------------------------------------------------------------------------------
SELECT 
    action_type, 
    COUNT(*) AS action_count, 
    ROUND(AVG(value), 2) AS average_value
FROM corporate_actions
GROUP BY action_type;
