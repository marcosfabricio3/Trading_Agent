import asyncio
from app.engine import TradingEngine
from app.services import (
    parser, validator, risk, exchange, db, 
    ingestion, telegram_ingestion, monitor
)
from app.logger import logger

async def run_bot():
    logger.info("=== TRADING AGENT v1.0 (PRO) ===")
    
    # 1. Inicialización
    engine = TradingEngine(
        parser=parser,
        validator=validator,
        risk_manager=risk,
        exchange=exchange,
        db=db
    )
    
    trade_monitor = monitor.TradeMonitor(engine, exchange, db)
    
    # 2. Selección de modo
    mode = "mock" # Cambiar a "telegram" para real
    
    tasks = []
    
    # Tarea 1: Monitor de Trades (Habilitado siempre)
    tasks.append(trade_monitor.run(interval=2))
    
    # Tarea 2: Ingestión de Señales
    if mode == "mock":
        listener = ingestion.MockListener(engine)
        test_signals = [
            "XRP LONG ENTRADA: 1.34 TP: 1.88 SL: 1.22 RIESGO: 5"
        ]
        logger.info("Modo SIMULACIÓN: Inyectando señal inicial...")
        # Corremos la simulación una vez
        listener.listen_and_process(test_signals)
    else:
        listener = telegram_ingestion.TelegramListener(engine)
        tasks.append(listener.start())
        logger.info("Modo TELEGRAM: Esperando señales reales...")

    # Ejecutar todas las tareas asíncronas
    if tasks:
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("\n[!] Deteniendo bot por el usuario...")
    except Exception as e:
        logger.critical(f"Error fatal: {e}")
