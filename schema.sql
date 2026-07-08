-- SQLite schema for Nifty 100 stock market analysis database (nifty100.db)

-- 1. Table: sectors (Sector and industry master)
CREATE TABLE IF NOT EXISTS sectors (
    sector_name TEXT PRIMARY KEY,
    sector_description TEXT
);

-- 2. Table: companies (Company metadata)
CREATE TABLE IF NOT EXISTS companies (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    sector_name TEXT NOT NULL,
    industry TEXT,
    FOREIGN KEY (sector_name) REFERENCES sectors (sector_name) ON DELETE RESTRICT
);

-- 3. Table: income_statements (Profit & Loss statements)
CREATE TABLE IF NOT EXISTS income_statements (
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

-- 4. Table: balance_sheets (Balance Sheet statements)
CREATE TABLE IF NOT EXISTS balance_sheets (
    ticker TEXT,
    year INTEGER CHECK (year BETWEEN 2000 AND 2030),
    total_assets REAL CHECK (total_assets >= 0),
    total_liabilities REAL CHECK (total_liabilities >= 0),
    total_equity REAL,
    retained_earnings REAL,
    PRIMARY KEY (ticker, year),
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 5. Table: cash_flows (Cash Flow statements)
CREATE TABLE IF NOT EXISTS cash_flows (
    ticker TEXT,
    year INTEGER CHECK (year BETWEEN 2000 AND 2030),
    beginning_cash REAL,
    ending_cash REAL,
    net_cash_flow REAL,
    PRIMARY KEY (ticker, year),
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 6. Table: stock_prices (Daily prices)
CREATE TABLE IF NOT EXISTS stock_prices (
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

-- 7. Table: ratios (Financial metrics)
CREATE TABLE IF NOT EXISTS ratios (
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
CREATE TABLE IF NOT EXISTS corporate_actions (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    action_type TEXT CHECK (action_type IN ('Dividend', 'Split')),
    value REAL CHECK (value >= 0),
    FOREIGN KEY (ticker) REFERENCES companies (ticker) ON DELETE CASCADE
);

-- 9. Table: validation_failures (Data Quality fail logs)
CREATE TABLE IF NOT EXISTS validation_failures (
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

-- 10. Table: load_audit (Database load trace logs)
CREATE TABLE IF NOT EXISTS load_audit (
    load_id INTEGER PRIMARY KEY AUTOINCREMENT,
    load_timestamp TEXT DEFAULT (datetime('now', 'localtime')),
    file_name TEXT NOT NULL,
    records_processed INTEGER NOT NULL,
    records_loaded INTEGER NOT NULL,
    failures_count INTEGER NOT NULL,
    status TEXT CHECK (status IN ('SUCCESS', 'FAILED'))
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_date ON stock_prices (ticker, date);
CREATE INDEX IF NOT EXISTS idx_income_statements_ticker ON income_statements (ticker);
CREATE INDEX IF NOT EXISTS idx_balance_sheets_ticker ON balance_sheets (ticker);
CREATE INDEX IF NOT EXISTS idx_cash_flows_ticker ON cash_flows (ticker);
