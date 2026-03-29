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
def get_market_price(symbol: str):
    """
    Returns the current market price for a symbol.
    """
    # Mock prices for common symbols
    prices = {
        "XRPUSDT": 1.35,
        "BTCUSDT": 95000.0,
        "ETHUSDT": 2700.0
    }
    return {"price": prices.get(symbol, 1.0)}

@mcp.tool()
def get_position(symbol: str):
    """
    Returns the current position for a symbol.
    """
    # Mock position (0.0 means no active trade)
    return {
        "symbol": symbol,
        "size": 0.0,
        "entry_price": 0.0,
        "unrealized_pnl": 0.0
    }

@mcp.tool()
def close_position_partial(symbol: str, pct: float):
    """
    Closes a percentage of an open position.
    Example: pct=0.5 closes 50% of the position.
    """
    return {
        "status": "success",
        "symbol": symbol,
        "closed_pct": pct,
        "message": f"Closed {pct*100}% of position on {symbol}"
    }

@mcp.tool()
def update_sl(symbol: str, new_sl: float):
    """
    Updates the Stop Loss price for an existing position.
    """
    return {
        "status": "success",
        "symbol": symbol,
        "new_sl": new_sl
    }

if __name__ == "__main__":
    mcp.run()
