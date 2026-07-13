from typing import Optional, Tuple

def calculate_cagr(start_val: float, end_val: float, n_years: int) -> Tuple[Optional[float], Optional[str]]:
    """Compute CAGR: ((end / start) ** (1 / n) - 1) * 100.
    
    Handles 6 edge cases:
    1. Positive -> Positive: compute normally.
    2. Positive -> Negative/Zero: return None with flag DECLINE_TO_LOSS.
    3. Negative -> Positive/Zero: return None with flag TURNAROUND.
    4. Negative -> Negative: return None with flag BOTH_NEGATIVE.
    5. Zero base: return None with flag ZERO_BASE.
    6. Less than n years of data: return None with flag INSUFFICIENT.
    """
    if n_years <= 0:
        return None, "INSUFFICIENT"
        
    if start_val == 0:
        return None, "ZERO_BASE"
        
    if start_val > 0 and end_val <= 0:
        return None, "DECLINE_TO_LOSS"
        
    if start_val < 0 and end_val >= 0:
        return None, "TURNAROUND"
        
    if start_val < 0 and end_val < 0:
        return None, "BOTH_NEGATIVE"
        
    # Standard compute
    try:
        ratio = end_val / start_val
        if ratio <= 0:
            return None, "BOTH_NEGATIVE"
        cagr_value = (ratio ** (1.0 / n_years) - 1.0) * 100.0
        return cagr_value, None
    except Exception:
        return None, "BOTH_NEGATIVE"
