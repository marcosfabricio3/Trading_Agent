from fastmcp import FastMCP

mcp = FastMCP("risk")

def _calculate_logic(capital: float, risk_pct: float, entry: float, sl: float, 
                     risk_strategy: str = "CAP", max_trade_margin: float = 100.0,
                     max_total_margin: float = 300.0, current_total_margin: float = 0.0,
                     min_notional_usdt: float = 5.0):
    # Ensure all inputs are float to allow for string-numeric and integer inputs
    try:
        capital = float(capital)
        risk_pct = float(risk_pct)
        entry = float(entry)
        sl = float(sl)
    except (ValueError, TypeError):
        return {"error": "Invalid numeric inputs for risk calculation"}

    if entry <= 0: return {"error": "Entry price <= 0"}
    sl_dist = abs(entry - sl) / entry
    if sl_dist == 0: return {"error": "SL distance is 0"}
    
    # Base size based on Risk %
    ideal_size = (capital * (risk_pct / 100)) / sl_dist
    pos_size = ideal_size

    # A. Enforce Minimum Notional (New safety floor)
    if pos_size < min_notional_usdt:
        return {
            "status": "DISCARDED", 
            "reason": f"Size {pos_size:.2f} USDT is below minimum required ({min_notional_usdt} USDT)"
        }
    
    # 1. Enforce Individual Max Trade Margin (Notional)
    if pos_size > max_trade_margin:
        if risk_strategy == "DISCARD":
            return {"status": "DISCARDED", "reason": f"Size {pos_size:.2f} > Max Trade {max_trade_margin}"}
        pos_size = max_trade_margin
        
    # 2. Enforce Total Safety Wall (Max Total Margin)
    if current_total_margin + pos_size > max_total_margin:
        if risk_strategy == "DISCARD":
            return {"status": "DISCARDED", "reason": f"Total {current_total_margin + pos_size:.2f} > Wall {max_total_margin}"}
        # Capping: Adjust size to fit exactly into the remaining wall
        pos_size = max_total_margin - current_total_margin
        if pos_size < min_notional_usdt:
            return {"status": "DISCARDED", "reason": f"Safety Wall reached ({current_total_margin:.2f}/{max_total_margin})"}
        
    return {
        "status": "APPROVED",
        "position_size": round(float(pos_size), 2),
        "risk_amount": round(float(capital * (risk_pct / 100)), 2),
        "original_size": round(float(ideal_size), 2),
        "reason": "Capped by limits" if pos_size < ideal_size else "Calculated size"
    }

@mcp.tool()
def calculate_position_size(capital: float, risk_pct: float, entry: float, sl: float, 
                             risk_strategy: str = "CAP", max_trade_margin: float = 100.0,
                             max_total_margin: float = 300.0, current_total_margin: float = 0.0):
    """Calculates size based on SL distance and user constraints."""
    try:
        return _calculate_logic(capital, risk_pct, entry, sl, risk_strategy, max_trade_margin, max_total_margin, current_total_margin)
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def validate_leverage(leverage: int):
    """
    Validates leverage against risk constraints (max 20x).
    """
    if leverage > 20:
        return {"valid": False, "max": 20, "message": "Leverage exceeds maximum allowed (20x)"}
    return {"valid": True, "leverage": leverage}

if __name__ == "__main__":
    mcp.run()
