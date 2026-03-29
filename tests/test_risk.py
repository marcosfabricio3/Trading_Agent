import unittest
from opencode.mcp.risk_server import calculate_position_size

class TestRisk(unittest.TestCase):
    def test_standard_calc(self):
        # capital 1000, risk 1%, entry 100, sl 90
        # dist = 10%
        # size = (1000 * 0.01) / 0.1 = 10 / 0.1 = 100
        result = calculate_position_size(1000, 1, 100, 90)
        self.assertEqual(result["position_size"], 100.0)
        self.assertEqual(result["sl_distance_pct"], 10.0)

    def test_cap_at_30_percent(self):
        # capital 1000, risk 5%, entry 100, sl 99
        # dist = 1%
        # size = (1000 * 0.05) / 0.01 = 50 / 0.01 = 5000
        # capped: 1000 * 0.3 = 300
        result = calculate_position_size(1000, 5, 100, 99)
        self.assertEqual(result["position_size"], 300.0)
        self.assertEqual(result["reason"], "capped by max 30% capital rule")

if __name__ == "__main__":
    unittest.main()
