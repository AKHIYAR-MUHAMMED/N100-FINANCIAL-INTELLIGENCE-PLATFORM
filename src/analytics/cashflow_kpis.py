from typing import List, Optional

def calculate_free_cash_flow(operating_activity: float, investing_activity: float) -> float:
    """Calculate Free Cash Flow: operating_activity + investing_activity.
    
    Negative values are allowed.
    """
    return operating_activity + investing_activity


def calculate_cfo_quality_score(cfo_list: List[float], pat_list: List[float]) -> Optional[float]:
    """Calculate CFO Quality Score: CFO / PAT ratio averaged over 5 years.
    
    Returns None if any PAT in the 5-year window is 0, or if there are fewer than 5 years of data.
    """
    if len(cfo_list) < 5 or len(pat_list) < 5:
        return None
    
    # Take the last 5 years
    window_cfo = cfo_list[-5:]
    window_pat = pat_list[-5:]
    
    ratios = []
    for cfo, pat in zip(window_cfo, window_pat):
        if pat == 0:
            return None
        ratios.append(cfo / pat)
        
    return sum(ratios) / len(ratios)


def calculate_capex_intensity(investing_activity: float, sales: float) -> Optional[float]:
    """Calculate CapEx Intensity: abs(investing_activity) / sales * 100.
    
    Returns None if sales == 0.
    """
    if sales == 0:
        return None
    return (abs(investing_activity) / sales) * 100.0


def calculate_fcf_conversion_rate(fcf: float, operating_profit: float) -> Optional[float]:
    """Calculate FCF Conversion Rate: FCF / operating_profit * 100.
    
    Returns None if operating_profit == 0.
    """
    if operating_profit == 0:
        return None
    return (fcf / operating_profit) * 100.0


def classify_capital_allocation(
    cfo: float, cfi: float, cff: float, cfo_pat_ratio: Optional[float] = None
) -> str:
    """Classify the capital allocation pattern based on the signs of (CFO, CFI, CFF).
    
    Signs are defined as:
    '+' if value >= 0
    '-' if value < 0
    """
    cfo_sign = "+" if cfo >= 0 else "-"
    cfi_sign = "+" if cfi >= 0 else "-"
    cff_sign = "+" if cff >= 0 else "-"
    
    pattern = (cfo_sign, cfi_sign, cff_sign)
    
    if pattern == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
            return "Shareholder Returns"
        return "Reinvestor"
    elif pattern == ("+", "+", "-"):
        return "Liquidating Assets"
    elif pattern == ("-", "+", "+"):
        return "Distress Signal"
    elif pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"
    elif pattern == ("+", "+", "+"):
        return "Cash Accumulator"
    elif pattern == ("-", "-", "-"):
        return "Pre-Revenue"
    elif pattern == ("+", "-", "+"):
        return "Mixed"
    else:
        return "Mixed"
