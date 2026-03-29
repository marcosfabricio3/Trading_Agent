import unittest
from opencode.mcp.parser_server import parse_signal

class TestParser(unittest.TestCase):
    def test_standard_signal(self):
        text = """XRP
LONG X10
ENTRADA: 1.34
RIESGO: 5
TP: 1.88
SL: 1.22"""
        result = parse_signal(text)
        self.assertEqual(result["symbol"], "XRPUSDT")
        self.assertEqual(result["side"], "long")
        self.assertEqual(result["leverage"], 10)
        self.assertEqual(result["entry"], 1.34)
        self.assertEqual(result["tp"], 1.88)
        self.assertEqual(result["sl"], 1.22)
        self.assertEqual(result["risk_pct"], 5.0)

    def test_lowercase_signal(self):
        text = "btc short x20 entrada: 50000 tp: 45000 sl: 52000 riesgo: 1"
        result = parse_signal(text)
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["side"], "short")
        self.assertEqual(result["leverage"], 20)
        self.assertEqual(result["entry"], 50000.0)

if __name__ == "__main__":
    unittest.main()
