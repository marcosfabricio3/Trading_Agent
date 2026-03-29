from opencode.mcp.validator_server import validate_signal as core_validate, check_market_distance as core_check_dist

class SignalValidator:
    """
    Wrapper for the core validator logic.
    """
    def validate_signal(self, signal_data: dict):
        return core_validate(signal_data)

    def check_market_distance(self, entry_price: float, market_price: float):
        return core_check_dist(entry_price, market_price)
