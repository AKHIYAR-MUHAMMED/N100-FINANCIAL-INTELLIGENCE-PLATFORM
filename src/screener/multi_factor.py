"""Multi-Factor Screener Ranking Strategy Engine.

Provides multi-factor scoring (Growth, Value, Quality, Solvency, Momentum)
and ranking logic with customizable weights across equity portfolios.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import sqlite3
import pandas as pd
import numpy as np


@dataclass
class MultiFactorWeights:
    growth_weight: float = 0.25
    value_weight: float = 0.25
    quality_weight: float = 0.25
    solvency_weight: float = 0.25

    def normalize(self) -> "MultiFactorWeights":
        total = (
            self.growth_weight
            + self.value_weight
            + self.quality_weight
            + self.solvency_weight
        )
        if total <= 0:
            return MultiFactorWeights(0.25, 0.25, 0.25, 0.25)
        return MultiFactorWeights(
            growth_weight=self.growth_weight / total,
            value_weight=self.value_weight / total,
            quality_weight=self.quality_weight / total,
            solvency_weight=self.solvency_weight / total,
        )


def score_percentiles(series: pd.Series, ascending: bool = True) -> pd.Series:
    """Calculates percentile ranks between 0 and 100."""
    return series.rank(pct=True, ascending=ascending) * 100.0


def calculate_multi_factor_scores(
    df: pd.DataFrame,
    weights: Optional[MultiFactorWeights] = None,
) -> pd.DataFrame:
    """Calculates composite multi-factor score for companies in DataFrame.
    
    Expected columns:
      - roe, roce (Quality)
      - pe, pb (Value: lower is better)
      - sales_cagr or revenue_growth (Growth)
      - debt_to_equity (Solvency: lower is better)
    """
    if weights is None:
        weights = MultiFactorWeights().normalize()
    else:
        weights = weights.normalize()

    result = df.copy()

    # Quality Score (ROE + ROCE)
    roe_score = score_percentiles(result.get("roe", pd.Series([50] * len(result))), ascending=True)
    roce_score = score_percentiles(result.get("roce", pd.Series([50] * len(result))), ascending=True)
    result["quality_score"] = (roe_score + roce_score) / 2.0

    # Value Score (Lower PE and PB = higher rank)
    pe_score = score_percentiles(result.get("pe_ratio", result.get("pe", pd.Series([50] * len(result)))), ascending=False)
    pb_score = score_percentiles(result.get("pb_ratio", result.get("pb", pd.Series([50] * len(result)))), ascending=False)
    result["value_score"] = (pe_score + pb_score) / 2.0

    # Growth Score
    growth_col = "sales_growth" if "sales_growth" in result.columns else "revenue_growth"
    if growth_col in result.columns:
        result["growth_score"] = score_percentiles(result[growth_col], ascending=True)
    else:
        result["growth_score"] = 50.0

    # Solvency Score (Lower debt/equity = higher rank)
    de_col = "debt_to_equity" if "debt_to_equity" in result.columns else "debt_equity"
    if de_col in result.columns:
        result["solvency_score"] = score_percentiles(result[de_col], ascending=False)
    else:
        result["solvency_score"] = 50.0

    # Composite Score
    result["composite_score"] = (
        result["growth_score"] * weights.growth_weight
        + result["value_score"] * weights.value_weight
        + result["quality_score"] * weights.quality_weight
        + result["solvency_score"] * weights.solvency_weight
    ).round(2)

    result["rank"] = result["composite_score"].rank(ascending=False, method="min").astype(int)
    return result.sort_values(by="rank", ascending=True)


def rank_companies_from_db(
    db_path: str,
    weights: Optional[MultiFactorWeights] = None,
    sector: Optional[str] = None,
) -> List[Dict]:
    """Loads latest metrics from SQLite DB and produces multi-factor ranked results."""
    conn = sqlite3.connect(db_path)
    query = """
        SELECT 
            c.ticker as company_id,
            c.name,
            c.sector_name as sector,
            fr.roe,
            fr.roce,
            fr.pe_ratio,
            fr.pb_ratio,
            fr.debt_equity as debt_to_equity
        FROM companies c
        JOIN (
            SELECT ticker, roe, roce, pe_ratio, pb_ratio, debt_equity,
                   ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY year DESC) as rn
            FROM financial_ratios
        ) fr ON c.ticker = fr.ticker AND fr.rn = 1
    """
    try:
        df = pd.read_sql_query(query, conn)
    except Exception:
        fallback_query = """
            SELECT 
                c.company_id,
                c.name,
                c.sector,
                cf.roe,
                cf.roce,
                cf.pe_ratio,
                cf.pb_ratio,
                cf.debt_to_equity
            FROM companies c
            JOIN (
                SELECT company_id, roe, roce, pe_ratio, pb_ratio, debt_to_equity,
                       ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
                FROM company_financials
            ) cf ON c.company_id = cf.company_id AND cf.rn = 1
        """
        try:
            df = pd.read_sql_query(fallback_query, conn)
        except Exception:
            df = pd.DataFrame()
    finally:
        conn.close()

    if df.empty:
        return []

    if sector and "sector" in df.columns:
        df = df[df["sector"].str.lower() == sector.lower()]

    ranked = calculate_multi_factor_scores(df, weights)
    return ranked.to_dict(orient="records")
