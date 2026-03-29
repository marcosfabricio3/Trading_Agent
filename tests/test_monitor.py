import asyncio
import unittest
from unittest.mock import MagicMock
from app.services.monitor import TradeMonitor
from app.logger import logger

class TestTradeMonitor(unittest.TestCase):
    def setUp(self):
        self.engine = MagicMock()
        self.exchange = MagicMock()
        self.db = MagicMock()
        self.monitor = TradeMonitor(self.engine, self.exchange, self.db)

    def test_tp1_logic(self):
        """
        Verifica que al tocar TP1 se active el parcial y el break-even.
        """
        trade = {
            "id": 1,
            "symbol": "XRPUSDT",
            "side": "long",
            "entry_price": 1.0,
            "tp": 1.5,
            "sl": 0.5,
            "tp1_hit": 0
        }
        
        # Simulamos precio por encima del TP1
        current_price = 1.6
        
        logger.info("--- Iniciando Test de TP1 ---")
        self.monitor.check_targets(trade, current_price)
        
        # Verificaciones
        self.exchange.close_position_partial.assert_called_with("XRPUSDT", 0.5)
        self.exchange.update_sl.assert_called_with("XRPUSDT", 1.0)
        self.db.update_trade_status.assert_called_with(1, tp1_hit=True, sl_moved=True)
        logger.info("--- Test de TP1: EXITOSO ---")

    def test_sl_logic(self):
        """
        Verifica que al tocar SL se cierre el trade en DB.
        """
        trade = {
            "id": 2,
            "symbol": "BTCUSDT",
            "side": "long",
            "entry_price": 95000,
            "tp": 100000,
            "sl": 90000,
            "tp1_hit": 0
        }
        
        # Simulamos precio por debajo del SL
        current_price = 89000
        
        logger.info("--- Iniciando Test de SL ---")
        self.monitor.check_targets(trade, current_price)
        
        # Verificaciones
        self.db.update_trade_status.assert_called_with(2, exit_price=89000)
        logger.info("--- Test de SL: EXITOSO ---")

if __name__ == "__main__":
    unittest.main()
