from opencode.mcp.bitget_server import (
    create_order, set_sl_tp, get_balance, get_position, 
    get_market_price as core_market_price, close_position_partial, update_sl, update_tp,
    close_position_full as core_close_full, set_leverage, get_market_info, fast_close_chase,
    get_plan_orders
)

class ExchangeService:
    """
    Wrapper for the Bitget MCP server.
    """
    async def create_order(self, symbol, side, order_type, qty, price, sl=None, tp=None):
        return await create_order(symbol, side, order_type, qty, price, sl_price=sl, tp_price=tp)



    async def set_leverage(self, symbol, leverage):
        return await set_leverage(symbol, leverage)

    async def set_sl_tp(self, symbol, sl_price=None, tp_price=None):
        return await set_sl_tp(symbol, sl_price=sl_price, tp_price=tp_price)

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

    async def update_tp(self, symbol, new_tp):
        return await update_tp(symbol, new_tp)

    async def fast_close_chase(self, symbol):
        """Implementa el cierre rápido moviendo el SL."""
        return await fast_close_chase(symbol)
    async def get_plan_orders(self, symbol):
        """Obtiene las órdenes SL/TP activas del exchange."""
        return await get_plan_orders(symbol)
