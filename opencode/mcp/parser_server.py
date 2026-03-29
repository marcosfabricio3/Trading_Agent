from fastmcp import FastMCP
import re

mcp = FastMCP("parser")


@mcp.tool()
def parse_signal(text: str):
    try:
        symbol = re.search(r"([A-Z]{3,6})", text).group(1)
        side = "long" if "LONG" in text.upper() else "short"

        entry = float(re.search(r"ENTRADA:\s*([\d\.]+)", text).group(1))
        tp = float(re.search(r"TP:\s*([\d\.]+)", text).group(1))
        sl = float(re.search(r"SL:\s*([\d\.]+)", text).group(1))
        risk = float(re.search(r"RIESGO:\s*([\d\.]+)", text).group(1))

        return {
            "symbol": symbol + "USDT",
            "side": side,
            "entry": entry,
            "tp": tp,
            "sl": sl,
            "risk": risk
        }

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run()