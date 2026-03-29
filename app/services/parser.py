from opencode.mcp.parser_server import parse_signal as core_parse

class SignalParser:
    """
    Wrapper for the core parser logic.
    """
    def parse_signal(self, text: str):
        return core_parse(text)
