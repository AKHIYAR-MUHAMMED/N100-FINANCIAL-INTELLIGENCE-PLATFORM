import os
import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "db" / "nifty100.db"


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    if not db_path.exists():
        # Fallback if relative to current working directory
        db_path = Path("data/db/nifty100.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """Fetch all 92 companies with sector details."""
    conn = get_connection()
    try:
        query = """
            SELECT 
                c.ticker,
                c.name,
                c.sector_name,
                c.industry,
                c.website
            FROM companies c
            ORDER BY c.ticker
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_ratios(ticker: str = None, year: int = None) -> pd.DataFrame:
    """Fetch financial ratios data with optional ticker and year filter."""
    conn = get_connection()
    try:
        query = """
            SELECT 
                fr.*,
                c.name as company_name,
                c.sector_name as broad_sector,
                c.industry
            FROM financial_ratios fr
            JOIN companies c ON fr.ticker = c.ticker
            WHERE 1=1
        """
        params = []
        if ticker:
            query += " AND UPPER(fr.ticker) = UPPER(?)"
            params.append(ticker)
        if year:
            query += " AND fr.year = ?"
            params.append(year)
        query += " ORDER BY fr.ticker, fr.year ASC"
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_pl(ticker: str = None) -> pd.DataFrame:
    """Fetch Profit & Loss statement data."""
    conn = get_connection()
    try:
        query = """
            SELECT pl.*, c.name as company_name
            FROM profitandloss pl
            JOIN companies c ON pl.ticker = c.ticker
            WHERE 1=1
        """
        params = []
        if ticker:
            query += " AND UPPER(pl.ticker) = UPPER(?)"
            params.append(ticker)
        query += " ORDER BY pl.ticker, pl.year ASC"
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_bs(ticker: str = None) -> pd.DataFrame:
    """Fetch Balance Sheet statement data."""
    conn = get_connection()
    try:
        query = """
            SELECT bs.*, c.name as company_name
            FROM balancesheet bs
            JOIN companies c ON bs.ticker = c.ticker
            WHERE 1=1
        """
        params = []
        if ticker:
            query += " AND UPPER(bs.ticker) = UPPER(?)"
            params.append(ticker)
        query += " ORDER BY bs.ticker, bs.year ASC"
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_cf(ticker: str = None) -> pd.DataFrame:
    """Fetch Cash Flow statement data."""
    conn = get_connection()
    try:
        query = """
            SELECT cf.*, c.name as company_name
            FROM cashflow cf
            JOIN companies c ON cf.ticker = c.ticker
            WHERE 1=1
        """
        params = []
        if ticker:
            query += " AND UPPER(cf.ticker) = UPPER(?)"
            params.append(ticker)
        query += " ORDER BY cf.ticker, cf.year ASC"
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Fetch sector information with company counts."""
    conn = get_connection()
    try:
        query = """
            SELECT 
                s.sector_name,
                s.sector_description,
                COUNT(c.ticker) as company_count
            FROM sectors s
            LEFT JOIN companies c ON s.sector_name = c.sector_name
            GROUP BY s.sector_name, s.sector_description
            ORDER BY company_count DESC
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_peers(group_name: str = None) -> pd.DataFrame:
    """Fetch peer group mappings."""
    conn = get_connection()
    try:
        query = """
            SELECT 
                pg.group_name,
                pg.ticker,
                c.name as company_name,
                c.sector_name
            FROM peer_groups pg
            JOIN companies c ON pg.ticker = c.ticker
            WHERE 1=1
        """
        params = []
        if group_name:
            query += " AND UPPER(pg.group_name) = UPPER(?)"
            params.append(group_name)
        query += " ORDER BY pg.group_name, pg.ticker"
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_valuation(ticker: str = None) -> pd.DataFrame:
    """Fetch valuation parameters and calculated multiples."""
    conn = get_connection()
    try:
        query = """
            SELECT 
                c.ticker as company_id,
                c.name as company_name,
                c.sector_name as sector,
                fr.year,
                fr.pe_ratio as 'P/E',
                fr.pb_ratio as 'P/B',
                fr.free_cash_flow_cr,
                pl.net_income,
                pl.shares_outstanding,
                sp.latest_close
            FROM companies c
            LEFT JOIN (
                SELECT ticker, MAX(year) as max_year
                FROM financial_ratios
                GROUP BY ticker
            ) latest ON c.ticker = latest.ticker
            LEFT JOIN financial_ratios fr ON c.ticker = fr.ticker AND fr.year = latest.max_year
            LEFT JOIN profitandloss pl ON c.ticker = pl.ticker AND pl.year = latest.max_year
            LEFT JOIN (
                SELECT ticker, close as latest_close
                FROM stock_prices
                WHERE date = (SELECT MAX(date) FROM stock_prices)
            ) sp ON c.ticker = sp.ticker
            WHERE 1=1
        """
        params = []
        if ticker:
            query += " AND UPPER(c.ticker) = UPPER(?)"
            params.append(ticker)
        df = pd.read_sql_query(query, conn, params=params)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_pros_cons(ticker: str) -> pd.DataFrame:
    """Fetch pros and cons for a given company ticker."""
    conn = get_connection()
    try:
        query = "SELECT type, point FROM prosandcons WHERE UPPER(ticker) = UPPER(?)"
        df = pd.read_sql_query(query, conn, params=[ticker])
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_documents(ticker: str) -> pd.DataFrame:
    """Fetch documents/annual reports for a given company ticker."""
    conn = get_connection()
    try:
        query = "SELECT document_name, file_path FROM documents WHERE UPPER(ticker) = UPPER(?)"
        df = pd.read_sql_query(query, conn, params=[ticker])
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_capital_allocation() -> pd.DataFrame:
    """Fetch latest capital allocation patterns for all companies."""
    conn = get_connection()
    try:
        query = """
            SELECT 
                c.ticker as company_id,
                c.name as company_name,
                c.sector_name as sector,
                fr.capital_allocation_pattern,
                fr.composite_quality_score,
                fr.year
            FROM companies c
            JOIN (
                SELECT ticker, MAX(year) as max_year
                FROM financial_ratios
                GROUP BY ticker
            ) latest ON c.ticker = latest.ticker
            JOIN financial_ratios fr ON c.ticker = fr.ticker AND fr.year = latest.max_year
            ORDER BY c.ticker
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()
