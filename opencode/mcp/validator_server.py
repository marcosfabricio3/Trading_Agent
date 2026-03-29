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
            
        entry = parsed_signal.get("entry", 0)
        tp = parsed_signal.get("tp", 0)
        sl = parsed_signal.get("sl", 0)
        
        if entry <= 0 or tp <= 0 or sl <= 0:
            return {"valid": False, "reason": "Missing entry, TP, or SL price"}
            
        # R:R Calculation
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
            "rr_ratio": round(rr_ratio, 2),
            "side": parsed_signal["side"],
            "message": "Signal validated successfully"
        }

    except Exception as e:
        return {"valid": False, "reason": f"Validation error: {str(e)}"}

if __name__ == "__main__":
    mcp.run()
