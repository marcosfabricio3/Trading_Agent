from opencode.mcp.bitget_server import (
    create_order, set_sl_tp, get_balance, get_position, 
    get_market_price as core_market_price, close_position_partial, update_sl,
    close_position_full as core_close_full, set_leverage, get_market_info
)

class ExchangeService:
    """
    Wrapper for the Bitget MCP server.
    """
    async def create_order(self, symbol, side, order_type, qty, price):
        return await create_order(symbol, side, order_type, qty, price)

    async def set_leverage(self, symbol, leverage):
        return await set_leverage(symbol, leverage)

    async def set_sl_tp(self, symbol, sl, tp):
        return await set_sl_tp(symbol, sl, tp)

    async def get_balance(self):
        return await get_balance()

    async def get_position(self, symbol):
        return await get_position(symbol)

    async def get_market_price(self, symbol):
        return await core_market_price(symbol)

    async def get_market_info(self, symbol):
        return await get_market_info(symbol)

    async def close_position_partial(self, symbol, pct):
        return await close_position_partial(symbol, pct=pct)

    async def close_position_full(self, symbol):
        """Liquida el 100% de la posición en el exchange."""
        return await core_close_full(symbol)

    async def update_sl(self, symbol, new_sl):
        return await update_sl(symbol, new_sl)
