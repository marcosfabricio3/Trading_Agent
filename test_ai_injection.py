import asyncio
import logging
import os
from dotenv import load_dotenv

# Importaciones del proyecto
from app.engine import TradingEngine
from app.services.exchange import ExchangeService
from app.services.db import DBService
from app.services.parser import SignalParser
from app.services.validator import SignalValidator
from app.services.risk import RiskManager
from app.logger import logger

load_dotenv()

async def test_signal_processing():
    # 1. Inicialización de Servicios (Idéntico a main.py)
    exchange = ExchangeService()
    db = DBService()
    parser = SignalParser()
    validator = SignalValidator()
    risk_manager = RiskManager()
    
    # 2. Inicialización del Motor
    engine = TradingEngine(parser, validator, risk_manager, exchange, db)
    
    # 3. Señal de prueba (Simulando mensaje de Telegram)
    test_raw_text = """
    🚀 CRYPTO SIGNAL 🚀
    Symbol: BTCUSDT
    Side: LONG
    Entry: 60000
    Take Profit: 65000
    Stop Loss: 58000
    Leverage: 10x
    """
    
    source = "PRUEBA_EXHAUSTIVA_IA"
    
    print(f"\n--- [INICIO DE PRUEBA] Enviando señal a la IA: ---\n{test_raw_text.replace('🚀', '[COHETE]')}\n")
    
    # 4. Inyectar señal al motor
    try:
        # Esto disparará el pipeline completo: Parse -> Validate -> Risk -> Execution
        await engine.process_signal(test_raw_text, source=source)
        print("\n--- [RESULTADO] ¡Señal enviada al motor con éxito! ---")
        print("Revisa los logs arriba para ver el razonamiento de la IA (AI_THOUGHT).")
    except Exception as e:
        print(f"\n--- [ERROR] Fallo en el procesamiento interno: {e} ---")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_signal_processing())
