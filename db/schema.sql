-- SQLite schema for Nifty 100 stock market analysis database (nifty100.db)

PRAGMA foreign_keys = OFF;

-- Drop legacy tables if they exist
DROP TABLE IF EXISTS income_statements;
DROP TABLE IF EXISTS balance_sheets;
DROP TABLE IF EXISTS cash_flows;
DROP TABLE IF EXISTS ratios;

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS load_audit;
DROP TABLE IF EXISTS validation_failures;
DROP TABLE IF EXISTS peer_groups;
DROP TABLE IF EXISTS prosandcons;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS analysis;
DROP TABLE IF EXISTS corporate_actions;
DROP TABLE IF EXISTS financial_ratios;
DROP TABLE IF EXISTS stock_prices;
DROP TABLE IF EXISTS cashflow;
DROP TABLE IF EXISTS balancesheet;
DROP TABLE IF EXISTS profitandloss;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS sectors;

PRAGMA foreign_keys = ON;

-- 1. Table: sectors (Sector and industry master)
CREATE TABLE sectors (
    sector_name TEXT PRIMARY KEY,
    sector_description TEXT
);

-- 2. Table: companies (Company metadata)
CREATE TABLE companies (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    sector_name TEXT NOT NULL,
    industry TEXT,
    website TEXT, -- Website URL for companies, used to validate DQ-10
    FOREIGN KEY (sector_name) REFERENCES sectors (sector_name) ON DELETE RESTRICT
);

-- 3. Table: profitandloss (Profit & Loss statements)
CREATE TABLE profitandloss (
    ticker TEXT,
    year INTEGER CHECK (year BETWEEN 2000 AND 2030),
    sales REAL CHECK (sales >= 0),
    operating_profit REAL,
    opm REAL CHECK (opm BETWEEN -1.0 AND 1.0),
    gross_profit REAL,
    net_income REAL,
    eps REAL,
    shares_outstanding REAL CHECK (shares_outstanding >= 0),
    PRIMARY KEY (ticker, year),
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 4. Table: balancesheet (Balance Sheet statements)
CREATE TABLE balancesheet (
    ticker TEXT,
    year INTEGER CHECK (year BETWEEN 2000 AND 2030),
    total_assets REAL CHECK (total_assets >= 0),
    total_liabilities REAL CHECK (total_liabilities >= 0),
    total_equity REAL,
    retained_earnings REAL,
    PRIMARY KEY (ticker, year),
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 5. Table: cashflow (Cash Flow statements)
CREATE TABLE cashflow (
    ticker TEXT,
    year INTEGER CHECK (year BETWEEN 2000 AND 2030),
    beginning_cash REAL,
    ending_cash REAL,
    net_cash_flow REAL,
    PRIMARY KEY (ticker, year),
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 6. Table: stock_prices (Daily prices)
CREATE TABLE stock_prices (
    ticker TEXT,
    date TEXT NOT NULL,
    open REAL CHECK (open > 0),
    high REAL CHECK (high > 0),
    low REAL CHECK (low > 0),
    close REAL CHECK (close > 0),
    volume INTEGER CHECK (volume >= 0),
    PRIMARY KEY (ticker, date),
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 7. Table: financial_ratios (Financial metrics)
CREATE TABLE financial_ratios (
    ticker TEXT,
    year INTEGER CHECK (year BETWEEN 2000 AND 2030),
    pe_ratio REAL,
    pb_ratio REAL,
    roe REAL,
    debt_to_equity REAL,
    PRIMARY KEY (ticker, year),
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 8. Table: corporate_actions (Dividends & Splits)
CREATE TABLE corporate_actions (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    action_type TEXT CHECK (action_type IN ('Dividend', 'Split')),
    value REAL CHECK (value >= 0),
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 9. Table: analysis (Analyst rating and target price)
CREATE TABLE analysis (
    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    year INTEGER CHECK (year BETWEEN 2000 AND 2030),
    rating TEXT CHECK (rating IN ('Buy', 'Hold', 'Sell')),
    target_price REAL,
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 10. Table: documents (Annual and quarterly report file paths)
CREATE TABLE documents (
    document_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    document_name TEXT NOT NULL,
    file_path TEXT,
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 11. Table: prosandcons (Pros and cons analysis)
CREATE TABLE prosandcons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    type TEXT CHECK (type IN ('Pro', 'Con')),
    point TEXT NOT NULL,
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 12. Table: peer_groups (Peer group categorizations)
CREATE TABLE peer_groups (
    peer_group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL,
    ticker TEXT NOT NULL,
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 13. Table: validation_failures (Data Quality fail logs)
CREATE TABLE validation_failures (
    failure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_ticker TEXT,
    file_name TEXT NOT NULL,
    row_index INTEGER,
    rule_id TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('CRITICAL', 'WARNING')),
    column_name TEXT,
    invalid_value TEXT,
    message TEXT
);

-- 14. Table: load_audit (Database load trace logs)
CREATE TABLE load_audit (
    load_id INTEGER PRIMARY KEY AUTOINCREMENT,
    load_timestamp TEXT DEFAULT (datetime('now', 'localtime')),
    file_name TEXT NOT NULL,
    records_processed INTEGER NOT NULL,
    records_loaded INTEGER NOT NULL,
    failures_count INTEGER NOT NULL,
    status TEXT CHECK (status IN ('SUCCESS', 'FAILED'))
);

-- Indexes for performance optimization
CREATE INDEX idx_stock_prices_ticker_date ON stock_prices (ticker, date);
CREATE INDEX idx_profitandloss_ticker ON profitandloss (ticker);
CREATE INDEX idx_balancesheet_ticker ON balancesheet (ticker);
CREATE INDEX idx_cashflow_ticker ON cashflow (ticker);
