from opencode.mcp.bitget_server import (
    create_order, set_sl_tp, get_balance, get_position, 
    get_market_price as core_market_price, close_position_partial, update_sl
)

def get_market_price(symbol: str):
    """
    Returns the current market price for a symbol.
    """
    return core_market_price(symbol)
