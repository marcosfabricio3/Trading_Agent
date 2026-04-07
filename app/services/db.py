from opencode.mcp.db_server import (
    save_signal, save_trade, log_event, get_active_trades, update_trade_status,
    get_settings, update_setting
)

class DBService:
    """
    Wrapper for the DB MCP server.
    """
    def save_signal(self, raw_text, **kwargs):
        # Mapeamos campos si vienen con otros nombres o desde el diccionario spread
        symbol = kwargs.get("symbol", "UNKNOWN")
        side = kwargs.get("side", "unknown")
        entry = kwargs.get("entry", 0.0)
        tp = kwargs.get("tp", 0.0)
        sl = kwargs.get("sl", 0.0)
        leverage = kwargs.get("leverage")
        # Soportamos tanto 'risk' como 'risk_pct'
        risk = kwargs.get("risk", kwargs.get("risk_pct", 0.0))
        source = kwargs.get("source", "Global")
        
        return save_signal(raw_text, symbol, side, entry, tp, sl, risk, leverage, source)

    def save_trade(self, signal_id, symbol, side, entry, margin, leverage=10):
        """Guarda un nuevo trade en la base de datos."""
        return save_trade(signal_id, symbol, side, entry, margin, leverage)

    def log_event(self, event_type, message, details=None, source="Global"):
        return log_event(event_type, message, details, source)

    def get_active_trades(self):
        return get_active_trades()

    def update_trade_status(self, trade_id, tp1_hit=None, sl_moved=None, exit_price=None):
        return update_trade_status(trade_id, tp1_hit=tp1_hit, sl_moved=sl_moved, exit_price=exit_price)

    def get_settings(self):
        """Retorna las reglas de trading guardadas."""
        return get_settings()

    def update_setting(self, name, value):
        """Actualiza una regla de trading."""
        return update_setting(name, value)

    def update_trade_parameters(self, trade_id, sl=None, tp=None):
        """Actualiza los parámetros SL/TP de un trade."""
        from opencode.mcp.db_server import update_trade_parameters
        return update_trade_parameters(trade_id, sl=sl, tp=tp)
