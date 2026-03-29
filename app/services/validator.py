from opencode.mcp.validator_server import validate_signal as core_validate, check_market_distance as core_check_dist

def validate_signal(signal_data: dict):
    """
    Wrapper for the core validator logic.
    """
    return core_validate(signal_data)

def check_market_distance(entry_price: float, market_price: float):
    """
    Wrapper for market price distance check.
    """
    return core_check_dist(entry_price, market_price)
