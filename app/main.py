import asyncio
import os
import uvicorn
from app.engine import TradingEngine
from app.services.exchange import ExchangeService
from app.services.db import DBService
from app.services.monitor import TradeMonitor
from app.services.telegram_ingestion import TelegramService
from app.services.parser import SignalParser
from app.services.validator import SignalValidator
from app.services.risk import RiskManager
from app.logger import logger
from dotenv import load_dotenv
from app.dashboard_api import app

load_dotenv()

async def run_api():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="error")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    logger.info("=== TRADING AGENT v1.0 (PRO) ===")
    
    # 1. Inicialización de Servicios Base (MCP Wrappers)
    exchange = ExchangeService()
    db = DBService()
    
    # 2. Inicialización de Lógica de Negocio
    parser = SignalParser()
    validator = SignalValidator()
    risk_manager = RiskManager()
    
    # 3. Inicialización del Motor Central
    engine = TradingEngine(parser, validator, risk_manager, exchange, db)
    
    # 4. Inicialización de Monitor y Entrada
    monitor = TradeMonitor(engine, exchange, db)
    telegram = TelegramService(engine)
    
    mode = os.getenv("APP_MODE", "dev")
    
    if mode == "dev":
        logger.info("Modo SIMULACIÓN: Inyectando señal inicial de prueba...")
        # Inyectamos una señal que coincida con el formato del parser y precio actual
        test_msg = "XRP\nLONG X20\nENTRADA: 1.35\nTP: 1.65\nSL: 1.25\nRIESGO: 1"
        asyncio.create_task(engine.process_signal(test_msg))
    
    logger.info("=== Iniciando Servicios del Agente (Engine + API) ===")
    
    try:
        # Ejecutamos el monitor, el listener de Telegram y el Dashboard API en paralelo
        await asyncio.gather(
            monitor.run(),
            telegram.start(),
            run_api()
        )
    except KeyboardInterrupt:
        logger.info("[!] Deteniendo bot por el usuario...")
    except Exception as e:
        logger.error(f"Error crítico en el loop principal: {e}")
    finally:
        logger.info("=== Aplicación Finalizada Correctamente ===")

if __name__ == "__main__":
    asyncio.run(main())
