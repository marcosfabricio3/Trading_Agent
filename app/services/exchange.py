from opencode.mcp.bitget_server import (
    create_order, set_sl_tp, get_balance, get_position, 
    get_market_price as core_market_price, close_position_partial, update_sl
)

class ExchangeService:
    """
    Wrapper for the Bitget MCP server.
    """
    def create_order(self, symbol, side, order_type, qty, price):
        return create_order(symbol, side, order_type, qty, price)

    def set_sl_tp(self, symbol, sl, tp):
        return set_sl_tp(symbol, sl, tp)

    def get_balance(self):
        return get_balance()

    def get_position(self, symbol):
        return get_position(symbol)

    def get_market_price(self, symbol):
        return core_market_price(symbol)

    def close_position_partial(self, symbol, side, qty):
        return close_position_partial(symbol, side, qty)

    def update_sl(self, symbol, side, new_sl):
        return update_sl(symbol, side, new_sl)
