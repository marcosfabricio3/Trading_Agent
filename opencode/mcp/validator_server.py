from fastmcp import FastMCP

mcp = FastMCP("validator")

@mcp.tool()
def validate_signal(parsed_signal: dict):
    """
    Validates a parsed signal according to trading rules.
    - Reject if symbol is UNKNOWN
    - Reject if any critical value (entry, tp, sl) is 0
    - Check for minimum R:R (Risk/Reward) ratio
    - Ensure side is valid
    """
    try:
        if parsed_signal.get("symbol") == "UNKNOWN":
            return {"valid": False, "reason": "Unknown symbol"}
            
        if parsed_signal.get("side") not in ["long", "short"]:
            return {"valid": False, "reason": f"Invalid side: {parsed_signal.get('side')}"}
            
        # Robust numeric casting
        def to_float(val, name):
            if val is None: return 0.0
            s_val = str(val).replace('%', '').strip()
            try:
                return float(s_val)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid numeric value for {name}: '{val}'")

        try:
            entry = to_float(parsed_signal.get("entry", 0), "entry")
            tp = to_float(parsed_signal.get("tp", 0), "tp")
            sl = to_float(parsed_signal.get("sl", 0), "sl")
        except ValueError as e:
            return {"valid": False, "reason": str(e)}

        
        # entry and sl are mandatory (sl can be added by engine)
        if entry <= 0:
            return {"valid": False, "reason": "Missing entry price"}
        if sl <= 0:
            return {"valid": False, "reason": "Missing Stop Loss (SL) price"}
            
        # R:R Calculation (Only if TP is provided)
        rr_ratio = 0
        if tp > 0:
            if parsed_signal["side"] == "long":
                if sl >= entry: return {"valid": False, "reason": "SL must be below entry for LONG"}
                if tp <= entry: return {"valid": False, "reason": "TP must be above entry for LONG"}
                reward = tp - entry
                risk = entry - sl
            else: # short
                if sl <= entry: return {"valid": False, "reason": "SL must be above entry for SHORT"}
                if tp >= entry: return {"valid": False, "reason": "TP must be below entry for SHORT"}
                reward = entry - tp
                risk = sl - entry
                
            rr_ratio = reward / risk if risk > 0 else 0
            if rr_ratio < 1.0:
                return {"valid": False, "reason": f"Bad R:R ratio ({rr_ratio:.2f}). Minimum 1.0 required."}
            
        return {
            "valid": True,
            "rr_ratio": round(rr_ratio, 2) if tp > 0 else "N/A",
            "side": parsed_signal["side"],
            "message": "Signal validated successfully" + (" (No TP)" if tp <= 0 else "")
        }

    except Exception as e:
        return {"valid": False, "reason": f"Unexpected validation error: {str(e)}"}

@mcp.tool()
def check_market_distance(entry_price: float, market_price: float, max_distance_pct: float = 1.0):
    """
    Checks if the entry price is within a maximum percentage distance from market price.
    """
    distance_pct = abs(entry_price - market_price) / market_price * 100
    if distance_pct > max_distance_pct:
        return {
            "valid": False,
            "distance_pct": round(distance_pct, 2),
            "reason": f"Market price ({market_price}) is too far from entry ({entry_price}). Distance: {distance_pct:.2f}%"
        }
    return {"valid": True, "distance_pct": round(distance_pct, 2)}

if __name__ == "__main__":
    mcp.run()
