from unittest.mock import patch, MagicMock
from app.engine import TradingEngine
from app.services import parser, validator, risk, exchange, db

def test_security_rules():
    engine = TradingEngine(parser, validator, risk, exchange, db)
    
    # 1. Test: Anti-Overload (Symbol already open)
    print("\n--- Test 1: Anti-Overload (Symbol already open) ---")
    with patch('app.services.exchange.get_position') as mock_pos:
        mock_pos.return_value = {"symbol": "XRPUSDT", "size": 100.0}
        
        signal = "XRP LONG ENTRADA: 1.34 TP: 1.88 SL: 1.22 RIESGO: 1"
        engine.process_signal(signal)
    
    # 2. Test: Market Distance (Price too far)
    print("\n--- Test 2: Market Distance (Price too far) ---")
    with patch('app.services.exchange.get_position') as mock_pos, \
         patch('app.services.exchange.get_market_price') as mock_price:
        
        mock_pos.return_value = {"symbol": "XRPUSDT", "size": 0.0} # No position
        mock_price.return_value = {"price": 1.40} # Market at 1.40, Entry at 1.30
        
        far_signal = "XRP LONG ENTRADA: 1.30 TP: 1.88 SL: 1.22 RIESGO: 1"
        engine.process_signal(far_signal)

if __name__ == "__main__":
    test_security_rules()
