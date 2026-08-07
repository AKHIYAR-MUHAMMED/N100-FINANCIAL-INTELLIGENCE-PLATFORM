"""
Command-Line Interface (CLI) for BlueStocks Financial Intelligence Platform.

Provides commands for:
- Database status & data quality health check
- Stock screening and filtering
- Financial analytics and CAGR evaluation
- Risk modeling and Monte Carlo simulations
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from src.database import DatabaseManager
from src.analytics.cagr import calculate_cagr
from src.analytics.risk import (
    calculate_historical_var,
    calculate_sharpe_ratio,
    monte_carlo_forecast,
)
from src.screener.engine import ScreenerEngine


def cmd_status(db_path: Path) -> int:
    """Print database health, row counts, and data quality overview."""
    db = DatabaseManager(db_path)
    conn = db.get_connection()
    cursor = conn.cursor()

    print("\n=======================================================")
    print("  BlueStocks Data Foundation - System & DB Health      ")
    print("=======================================================")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]
    
    print("\n[Table Record Counts]")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"  * {table:<25}: {count:>6} rows")
        
    cursor.execute("SELECT severity, COUNT(*) FROM validation_failures GROUP BY severity;")
    dq_summary = dict(cursor.fetchall())
    print("\n[Data Quality Failure Log]")
    print(f"  * CRITICAL: {dq_summary.get('CRITICAL', 0)}")
    print(f"  * WARNING : {dq_summary.get('WARNING', 0)}")
    print(f"  * INFO    : {dq_summary.get('INFO', 0)}")

    fk_violations = db.run_fk_check()
    print(f"\n[Foreign Key Violations]: {len(fk_violations)}")
    print("=======================================================\n")
    conn.close()
    return 0


def cmd_screen(
    db_path: Path,
    sector: Optional[str] = None,
    min_roe: Optional[float] = None,
    max_pe: Optional[float] = None,
    limit: int = 10
) -> int:
    """Screen stocks based on sector, ROE, and Valuation criteria."""
    screener = ScreenerEngine(db_path)
    criteria = {}
    if min_roe is not None:
        criteria["roe_min"] = min_roe
    if max_pe is not None:
        criteria["pe_max"] = max_pe
    if sector:
        criteria["sector"] = sector
        
    results = screener.screen(criteria) if hasattr(screener, "screen") else []
    
    print(f"\nScreening results ({len(results)} matches, showing top {limit}):")
    print("-" * 75)
    print(f"{'Ticker':<10} | {'Company Name':<30} | {'Sector':<20} | {'Score':<6}")
    print("-" * 75)
    for r in results[:limit]:
        ticker = r.get("ticker", "N/A")
        name = r.get("company_name", "N/A")[:28]
        sec = r.get("sector_name", "N/A")[:18]
        score = r.get("composite_score", 0.0)
        print(f"{ticker:<10} | {name:<30} | {sec:<20} | {score:>6.2f}")
    print("-" * 75 + "\n")
    return 0


def cmd_risk(
    ticker: str,
    db_path: Path,
    simulations: int = 500,
    growth: float = 0.12,
    volatility: float = 0.20
) -> int:
    """Run risk analysis and Monte Carlo forecast for a company."""
    print(f"\n================ Risk Profile: {ticker} ================")
    print(f"Simulations : {simulations}")
    print(f"Mean Growth : {growth * 100:.1f}%")
    print(f"Volatility  : {volatility * 100:.1f}%\n")
    
    mc = monte_carlo_forecast(
        initial_value=100.0,
        mean_growth=growth,
        volatility=volatility,
        periods=5,
        n_simulations=simulations,
        seed=42
    )
    
    print("[Monte Carlo 5-Year Trajectory (% Baseline)]")
    print(f"  * Expected Value (Mean): {mc['final_expected_value']:.2f}")
    print(f"  * Median (50th %ile)   : {mc['final_median_value']:.2f}")
    print(f"  * Bear Case (10th %ile): {mc['final_p10_value']:.2f}")
    print(f"  * Bull Case (90th %ile): {mc['final_p90_value']:.2f}")
    print("========================================================\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for BlueStocks CLI."""
    parser = argparse.ArgumentParser(
        prog="bluestocks",
        description="BlueStocks Financial Intelligence & Analytics CLI"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/db/nifty100.db"),
        help="Path to SQLite database"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available sub-commands")
    
    # status command
    subparsers.add_parser("status", help="Display database health and records")
    
    # screen command
    screen_parser = subparsers.add_parser("screen", help="Screen universe by criteria")
    screen_parser.add_argument("--sector", type=str, help="Filter by sector")
    screen_parser.add_argument("--min-roe", type=float, help="Minimum ROE threshold")
    screen_parser.add_argument("--max-pe", type=float, help="Maximum P/E threshold")
    screen_parser.add_argument("--limit", type=int, default=10, help="Max results to display")
    
    # risk command
    risk_parser = subparsers.add_parser("risk", help="Run risk and Monte Carlo simulation")
    risk_parser.add_argument("--ticker", type=str, required=True, help="Stock ticker")
    risk_parser.add_argument("--simulations", type=int, default=500, help="Number of paths")
    risk_parser.add_argument("--growth", type=float, default=0.12, help="Expected growth rate")
    risk_parser.add_argument("--volatility", type=float, default=0.20, help="Annual volatility")
    
    return parser


def main(args: Optional[list] = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)
    
    if not parsed.command:
        parser.print_help()
        return 0
        
    if parsed.command == "status":
        return cmd_status(parsed.db)
    elif parsed.command == "screen":
        return cmd_screen(
            db_path=parsed.db,
            sector=parsed.sector,
            min_roe=parsed.min_roe,
            max_pe=parsed.max_pe,
            limit=parsed.limit
        )
    elif parsed.command == "risk":
        return cmd_risk(
            ticker=parsed.ticker,
            db_path=parsed.db,
            simulations=parsed.simulations,
            growth=parsed.growth,
            volatility=parsed.volatility
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
