from fastmcp import FastMCP
import random

mcp = FastMCP("bitget")

@mcp.tool()
def create_order(symbol: str, side: str, order_type: str, qty: float, price: float = None):
    """
    Creates a new order on Bitget.
    In dev mode, this is a mock.
    """
    order_id = f"bitget_{random.randint(10000, 99999)}"
    return {
        "status": "success",
        "order_id": order_id,
        "symbol": symbol,
        "side": side,
        "qty": qty,
        "price": price or "market"
    }

@mcp.tool()
def set_sl_tp(symbol: str, sl_price: float, tp_price: float):
    """
    Sets Stop Loss and Take Profit for a symbol.
    """
    return {
        "status": "success",
        "symbol": symbol,
        "sl": sl_price,
        "tp": tp_price
    }

@mcp.tool()
def get_balance():
    """
    Returns the account balance in USDT.
    """
    return {"balance": 500.0, "currency": "USDT"}

@mcp.tool()
def get_position(symbol: str):
    """
    Returns the current position for a symbol.
    """
    # Mock position
    return {
        "symbol": symbol,
        "size": 0.0,
        "entry_price": 0.0,
        "unrealized_pnl": 0.0
    }

if __name__ == "__main__":
    mcp.run()
