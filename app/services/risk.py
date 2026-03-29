from opencode.mcp.risk_server import calculate_position_size as core_risk

def calculate_position_size(capital: float, risk_pct: float, entry: float, sl: float):
    """
    Wrapper for the core risk management logic.
    """
    return core_risk(capital, risk_pct, entry, sl)
