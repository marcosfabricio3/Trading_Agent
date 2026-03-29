from fastmcp import FastMCP

mcp = FastMCP("risk")

@mcp.tool()
def calculate_position_size(capital: float, risk_pct: float, entry: float, sl: float):
    """
    Calculates the position size based on the risk model.
    Formula: position_size = (capital * risk_pct) / sl_distance_pct
    """
    try:
        if entry <= 0:
            return {"error": "Entry price must be greater than 0"}
            
        sl_distance_pct = abs(entry - sl) / entry
        
        if sl_distance_pct == 0:
            return {"error": "SL distance cannot be 0"}
            
        # position_size is in USDT (nominal value)
        position_size = (capital * (risk_pct / 100)) / sl_distance_pct
        
        # Constraints from risk_model.md
        # 1. Max 30% capital
        max_capital_usdt = capital * 0.30
        if position_size > max_capital_usdt:
            position_size = max_capital_usdt
            reason = "capped by max 30% capital rule"
        else:
            reason = "calculated according to risk percentage"
            
        return {
            "position_size": round(position_size, 2),
            "sl_distance_pct": round(sl_distance_pct * 100, 2),
            "risk_amount_usdt": round(capital * (risk_pct / 100), 2),
            "reason": reason
        }

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
