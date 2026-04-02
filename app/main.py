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

async def run_api(engine):
    app.state.engine = engine
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="error")
    server = uvicorn.Server(config)
    await server.serve()

async def heartbeat_loop(db):
    """
    Pulso constante del motor para el Dashboard.
    """
    while True:
        try:
            db.log_event("HEARTBEAT", "Bot Engine Pulse", {"service": "ENGINE", "status": "alive"})
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Heartbeat Error: {e}")
            await asyncio.sleep(5)

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
    
    # Inyectar dependencias en el estado de la app para la API
    app.state.engine = engine
    app.state.telegram = telegram
    
    logger.info("=== Iniciando Servicios del Agente (Engine + API) ===")
    
    try:
        # Ejecutamos el monitor, el listener de Telegram y el Dashboard API en paralelo
        await asyncio.gather(
            monitor.run(),
            telegram.start(),
            run_api(engine),
            heartbeat_loop(db)
        )
    except KeyboardInterrupt:
        logger.info("[!] Deteniendo bot por el usuario...")
    except Exception as e:
        logger.error(f"Error crítico en el loop principal: {e}")
    finally:
        logger.info("=== Aplicación Finalizada Correctamente ===")

if __name__ == "__main__":
    asyncio.run(main())
