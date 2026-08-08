"""DuPont Analysis Decomposition Engine.

Provides 3-step and 5-step DuPont decomposition models to break down Return on Equity (ROE)
into its underlying operational, financial, and tax efficiency drivers.
"""

from typing import Dict, Any, Optional
import sqlite3
import pandas as pd


def calculate_dupont_3step(
    net_income: float,
    revenue: float,
    total_assets: float,
    total_equity: float,
) -> Dict[str, Optional[float]]:
    """Calculates 3-step DuPont Analysis components.
    
    Formula:
      ROE = Net Profit Margin * Asset Turnover * Financial Leverage
      
      - Net Profit Margin (Operating Efficiency) = Net Income / Revenue
      - Asset Turnover (Asset Efficiency) = Revenue / Total Assets
      - Financial Leverage (Equity Multiplier) = Total Assets / Total Equity
    """
    if revenue <= 0 or total_assets <= 0 or total_equity <= 0:
        return {
            "net_profit_margin": None,
            "asset_turnover": None,
            "equity_multiplier": None,
            "calculated_roe": None,
        }

    npm = (net_income / revenue) * 100.0
    asset_turnover = revenue / total_assets
    equity_multiplier = total_assets / total_equity
    roe = (npm / 100.0) * asset_turnover * equity_multiplier * 100.0

    return {
        "net_profit_margin": round(npm, 2),
        "asset_turnover": round(asset_turnover, 4),
        "equity_multiplier": round(equity_multiplier, 4),
        "calculated_roe": round(roe, 2),
    }


def calculate_dupont_5step(
    net_income: float,
    ebt: float,
    ebit: float,
    revenue: float,
    total_assets: float,
    total_equity: float,
) -> Dict[str, Optional[float]]:
    """Calculates 5-step DuPont Analysis components.
    
    Formula:
      ROE = Tax Burden * Interest Burden * Operating Margin * Asset Turnover * Financial Leverage
      
      - Tax Burden = Net Income / EBT
      - Interest Burden = EBT / EBIT
      - Operating Margin = EBIT / Revenue
      - Asset Turnover = Revenue / Total Assets
      - Financial Leverage = Total Assets / Total Equity
    """
    if (
        ebt <= 0
        or ebit <= 0
        or revenue <= 0
        or total_assets <= 0
        or total_equity <= 0
    ):
        return {
            "tax_burden": None,
            "interest_burden": None,
            "operating_margin": None,
            "asset_turnover": None,
            "equity_multiplier": None,
            "calculated_roe": None,
        }

    tax_burden = net_income / ebt
    interest_burden = ebt / ebit
    op_margin = (ebit / revenue) * 100.0
    asset_turnover = revenue / total_assets
    equity_multiplier = total_assets / total_equity

    roe = (
        tax_burden
        * interest_burden
        * (op_margin / 100.0)
        * asset_turnover
        * equity_multiplier
        * 100.0
    )

    return {
        "tax_burden": round(tax_burden, 4),
        "interest_burden": round(interest_burden, 4),
        "operating_margin": round(op_margin, 2),
        "asset_turnover": round(asset_turnover, 4),
        "equity_multiplier": round(equity_multiplier, 4),
        "calculated_roe": round(roe, 2),
    }


def analyze_company_dupont(db_path: str, company_id: str) -> Dict[str, Any]:
    """Retrieves multi-year financials for a company and computes DuPont 3-step and 5-step models."""
    conn = sqlite3.connect(db_path)
    query = """
        SELECT 
            year,
            sales as revenue,
            net_profit as net_income,
            profit_before_tax as ebt,
            operating_profit as ebit,
            total_assets,
            (equity_capital + reserves) as total_equity
        FROM company_financials
        WHERE company_id = ?
        ORDER BY year ASC
    """
    df = pd.read_sql_query(query, conn, params=(company_id,))
    conn.close()

    if df.empty:
        return {"company_id": company_id, "history": []}

    history = []
    for _, row in df.iterrows():
        rev = float(row["revenue"] or 0)
        ni = float(row["net_income"] or 0)
        ebt = float(row["ebt"] or 0)
        ebit = float(row["ebit"] or 0)
        assets = float(row["total_assets"] or 0)
        equity = float(row["total_equity"] or 0)

        step3 = calculate_dupont_3step(ni, rev, assets, equity)
        step5 = calculate_dupont_5step(ni, ebt, ebit, rev, assets, equity)

        history.append({
            "year": int(row["year"]),
            "three_step": step3,
            "five_step": step5,
        })

    return {
        "company_id": company_id,
        "history": history,
    }
