-- ==============================================================================
-- NIFTY 100 EXPLORATORY QUERIES
-- This file contains 10 SQL queries for exploring, validating, and auditing the database.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 1: Database Table Row Counts
-- Purpose: Verify that all tables contain the expected number of records.
-- ------------------------------------------------------------------------------
SELECT 'sectors' AS table_name, COUNT(*) AS row_count FROM sectors
UNION ALL
SELECT 'companies', COUNT(*) FROM companies
UNION ALL
SELECT 'income_statements', COUNT(*) FROM income_statements
UNION ALL
SELECT 'balance_sheets', COUNT(*) FROM balance_sheets
UNION ALL
SELECT 'cash_flows', COUNT(*) FROM cash_flows
UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL
SELECT 'ratios', COUNT(*) FROM ratios
UNION ALL
SELECT 'corporate_actions', COUNT(*) FROM corporate_actions
UNION ALL
SELECT 'validation_failures', COUNT(*) FROM validation_failures
UNION ALL
SELECT 'load_audit', COUNT(*) FROM load_audit;

-- ------------------------------------------------------------------------------
-- Query 2: Sector Breakdown
-- Purpose: Get the distribution of companies across different sectors.
-- ------------------------------------------------------------------------------
SELECT sector_name, COUNT(*) AS company_count
FROM companies
GROUP BY sector_name
ORDER BY company_count DESC;

-- ------------------------------------------------------------------------------
-- Query 3: NULL Value Check on Critical Columns
-- Purpose: Check if there are any NULL values in primary key or critical columns.
-- ------------------------------------------------------------------------------
SELECT 
    SUM(CASE WHEN ticker IS NULL THEN 1 ELSE 0 END) AS null_ticker_companies,
    SUM(CASE WHEN name IS NULL THEN 1 ELSE 0 END) AS null_name_companies,
    SUM(CASE WHEN sector_name IS NULL THEN 1 ELSE 0 END) AS null_sector_companies
FROM companies;

-- ------------------------------------------------------------------------------
-- Query 4: Duplicate Primary Key Check on Stock Prices
-- Purpose: Ensure that there are no duplicate entries for the same ticker on the same date.
-- ------------------------------------------------------------------------------
SELECT ticker, date, COUNT(*) AS record_count
FROM stock_prices
GROUP BY ticker, date
HAVING record_count > 1;

-- ------------------------------------------------------------------------------
-- Query 5: Average Financial Metrics by Sector
-- Purpose: Calculate average Sales, Gross Profit, and Net Income per sector.
-- ------------------------------------------------------------------------------
SELECT 
    c.sector_name,
    COUNT(DISTINCT c.ticker) AS companies_count,
    ROUND(AVG(i.sales), 2) AS avg_sales,
    ROUND(AVG(i.gross_profit), 2) AS avg_gross_profit,
    ROUND(AVG(i.net_income), 2) AS avg_net_income
FROM companies c
JOIN income_statements i ON c.ticker = i.ticker
GROUP BY c.sector_name
ORDER BY avg_net_income DESC;

-- ------------------------------------------------------------------------------
-- Query 6: Balance Sheet Equation Discrepancies
-- Purpose: Identify any records where Assets != Liabilities + Equity (DQ-12 check).
-- ------------------------------------------------------------------------------
SELECT 
    ticker, 
    year, 
    total_assets, 
    total_liabilities, 
    total_equity,
    ROUND(ABS(total_assets - (total_liabilities + total_equity)), 2) AS discrepancy
FROM balance_sheets
WHERE ABS(total_assets - (total_liabilities + total_equity)) > 1.0;

-- ------------------------------------------------------------------------------
-- Query 7: Cash Flow Reconciliation Discrepancies
-- Purpose: Identify any records where End Cash != Start Cash + Net Change (DQ-13 check).
-- ------------------------------------------------------------------------------
SELECT 
    ticker, 
    year, 
    beginning_cash, 
    ending_cash, 
    net_cash_flow,
    ROUND(ABS(ending_cash - (beginning_cash + net_cash_flow)), 2) AS discrepancy
FROM cash_flows
WHERE ABS(ending_cash - (beginning_cash + net_cash_flow)) > 1.0;

-- ------------------------------------------------------------------------------
-- Query 8: Stock Prices Statistics
-- Purpose: Get min, max, average close prices, and average volumes for companies.
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
-- Query 9: Validation Warnings Count by Rule ID
-- Purpose: Aggregate validator failures by Rule ID to see which rule was violated most.
-- ------------------------------------------------------------------------------
SELECT rule_id, severity, COUNT(*) AS failure_count
FROM validation_failures
GROUP BY rule_id, severity
ORDER BY failure_count DESC;

-- ------------------------------------------------------------------------------
-- Query 10: Corporate Actions Summary
-- Purpose: Get count and average values of dividend distributions and stock splits.
-- ------------------------------------------------------------------------------
SELECT 
    action_type, 
    COUNT(*) AS action_count, 
    ROUND(AVG(value), 2) AS average_value
FROM corporate_actions
GROUP BY action_type;
