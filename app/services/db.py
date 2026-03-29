from opencode.mcp.db_server import (
    save_signal, save_trade, log_event, get_active_trades, update_trade_status
)

class DBService:
    """
    Wrapper for the DB MCP server.
    """
    def save_signal(self, raw_text, symbol, side, entry, tp, sl, risk):
        return save_signal(raw_text, symbol, side, entry, tp, sl, risk)

    def save_trade(self, signal_id, symbol, side, entry_price):
        return save_trade(signal_id, symbol, side, entry_price)

    def log_event(self, event_type, message, details=None):
        return log_event(event_type, message, details)

    def get_active_trades(self):
        return get_active_trades()

    def update_trade_status(self, trade_id, status, details=None):
        return update_trade_status(trade_id, status, details)
