from opencode.mcp.parser_server import parse_signal as core_parse

def parse_signal(text: str):
    """
    Wrapper for the core parser logic.
    """
    return core_parse(text)
