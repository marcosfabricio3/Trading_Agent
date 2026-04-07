from opencode.mcp.risk_server import _calculate_logic as core_risk

class RiskManager:
    """
    Wrapper for the core risk management logic.
    """
    def calculate_position_size(self, capital: float, risk_pct: float, entry: float, sl: float, 
                                 risk_strategy: str = "CAP", max_total_margin: float = 300, 
                                 max_trade_margin: float = 100, current_total_margin: float = 0.0,
                                 min_notional_usdt: float = 5.0):
        """Calcula el tamaño de posición considerando límites dinámicos."""
        return core_risk(
            capital=capital, 
            risk_pct=risk_pct, 
            entry=entry, 
            sl=sl, 
            risk_strategy=risk_strategy, 
            max_trade_margin=max_trade_margin,
            max_total_margin=max_total_margin,
            current_total_margin=current_total_margin,
            min_notional_usdt=min_notional_usdt
        )
