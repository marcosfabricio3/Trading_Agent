from app.engine import TradingEngine
from app.services import parser, validator, risk, exchange, db, ingestion, telegram_ingestion
from app.logger import logger

def main():
    logger.info("=== TRADING AGENT v1.0 (PRO) ===")
    
    # 1. Inicialización
    engine = TradingEngine(
        parser=parser,
        validator=validator,
        risk_manager=risk,
        exchange=exchange,
        db=db
    )
    
    # 2. Selección de modo (Por ahora usaremos Mock para el test final)
    mode = "mock" # Cambiar a "telegram" para usar la integración real
    
    if mode == "mock":
        listener = ingestion.MockListener(engine)
        test_signals = [
            "XRP LONG ENTRADA: 1.34 TP: 1.88 SL: 1.22 RIESGO: 5",
            "BTC LONG ENTRADA: 95000 TP: 105000 SL: 94000 RIESGO: 2"
        ]
        logger.info("Iniciando en modo SIMULACIÓN...")
        listener.listen_and_process(test_signals)
    else:
        listener = telegram_ingestion.TelegramListener(engine)
        logger.info("Iniciando en modo TELEGRAM (Real)...")
        listener.run_forever()
    
    logger.info("=== Aplicación Finalizada Correctamente ===")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n[!] Deteniendo bot por el usuario...")
    except Exception as e:
        logger.critical(f"Error fatal: {e}")
