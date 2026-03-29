from opencode.mcp.risk_server import calculate_position_size as core_risk

class RiskManager:
    """
    Wrapper for the core risk management logic.
    """
    def calculate_position_size(self, capital: float, risk_pct: float, entry: float, sl: float):
        return core_risk(capital, risk_pct, entry, sl)
