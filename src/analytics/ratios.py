from typing import Optional

def calculate_net_profit_margin(net_profit: float, sales: float) -> Optional[float]:
    """Calculate Net Profit Margin: net_profit / sales * 100.
    
    Returns None if sales == 0.
    """
    if sales == 0:
        return None
    return (net_profit / sales) * 100.0


def calculate_operating_profit_margin(operating_profit: float, sales: float) -> Optional[float]:
    """Calculate Operating Profit Margin: operating_profit / sales * 100.
    
    Returns None if sales == 0.
    """
    if sales == 0:
        return None
    return (operating_profit / sales) * 100.0


def calculate_return_on_equity(net_profit: float, equity_capital: float, reserves: float) -> Optional[float]:
    """Calculate Return on Equity: net_profit / (equity_capital + reserves) * 100.
    
    Returns None if equity_capital + reserves <= 0.
    """
    denominator = equity_capital + reserves
    if denominator <= 0:
        return None
    return (net_profit / denominator) * 100.0


def calculate_return_on_capital_employed(
    ebit: float, equity: float, reserves: float, borrowings: float
) -> Optional[float]:
    """Calculate Return on Capital Employed (ROCE): EBIT / (equity + reserves + borrowings) * 100.
    
    Returns None if equity + reserves + borrowings <= 0.
    """
    denominator = equity + reserves + borrowings
    if denominator <= 0:
        return None
    return (ebit / denominator) * 100.0


def calculate_return_on_assets(net_profit: float, total_assets: float) -> Optional[float]:
    """Calculate Return on Assets (ROA): net_profit / total_assets * 100.
    
    Returns None if total_assets <= 0.
    """
    if total_assets <= 0:
        return None
    return (net_profit / total_assets) * 100.0


def calculate_debt_to_equity(borrowings: float, equity_capital: float, reserves: float) -> Optional[float]:
    """Calculate Debt-to-Equity: borrowings / (equity_capital + reserves).
    
    Returns 0 if borrowings == 0.
    Returns None if equity_capital + reserves <= 0.
    """
    if borrowings == 0:
        return 0.0
    denominator = equity_capital + reserves
    if denominator <= 0:
        return None
    return borrowings / denominator


def calculate_interest_coverage(operating_profit: float, other_income: float, interest: float) -> Optional[float]:
    """Calculate Interest Coverage Ratio: (operating_profit + other_income) / interest.
    
    Returns None if interest == 0.
    """
    if interest == 0:
        return None
    return (operating_profit + other_income) / interest


def calculate_net_debt(borrowings: float, investments: float) -> float:
    """Calculate Net Debt: borrowings - investments."""
    return borrowings - investments


def calculate_asset_turnover(sales: float, total_assets: float) -> Optional[float]:
    """Calculate Asset Turnover: sales / total_assets.
    
    Returns None if total_assets == 0.
    """
    if total_assets == 0:
        return None
    return sales / total_assets
