from fastmcp import FastMCP
import re

mcp = FastMCP("parser")

@mcp.tool()
def parse_signal(text: str):
    """
    Parses a trading signal from raw text.
    Format:
    SYMBOL
    SIDE XLEVERAGE
    ENTRADA: PRICE
    RIESGO: %
    TP: PRICE
    SL: PRICE
    """
    try:
        text_upper = text.upper()
        
        # Symbol: Usually first line or start of line
        symbol_match = re.search(r"^([A-Z0-9]+)", text_upper, re.MULTILINE)
        symbol = symbol_match.group(1) if symbol_match else "UNKNOWN"
        
        # Side: LONG / SHORT
        side = "long" if "LONG" in text_upper else "short" if "SHORT" in text_upper else "unknown"
        
        # Leverage: X followed by numbers
        leverage_match = re.search(r"X(\d+)", text_upper)
        leverage = int(leverage_match.group(1)) if leverage_match else 1
        
        # Entries, TP, SL, Risk
        def find_value(key):
            match = re.search(rf"{key}:\s*([\d\.]+)", text_upper)
            return float(match.group(1)) if match else 0.0

        entry = find_value("ENTRADA")
        tp = find_value("TP")
        sl = find_value("SL")
        risk = find_value("RIESGO")

        # Cleanup symbol if not USDT
        if symbol != "UNKNOWN" and not symbol.endswith("USDT"):
            symbol = symbol + "USDT"

        return {
            "symbol": symbol,
            "side": side,
            "leverage": leverage,
            "entry": entry,
            "tp": tp,
            "sl": sl,
            "risk_pct": risk,
            "type": "new_signal" if entry > 0 else "update"
        }

    except Exception as e:
        return {"error": str(e), "raw": text}

if __name__ == "__main__":
    mcp.run()
