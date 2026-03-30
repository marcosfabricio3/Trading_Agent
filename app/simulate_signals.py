import asyncio
import os
from app.services.exchange import ExchangeService
from app.services.db import DBService
from app.services.parser import SignalParser
from app.services.validator import SignalValidator
from app.services.risk import RiskManager
from app.engine import TradingEngine
from app.logger import logger
from dotenv import load_dotenv

load_dotenv()

async def run_simulation():
    """
    Simula una secuencia de mensajes humanos para probar el cerebro de IA.
    """
    # 1. Inicialización idéntica a app/main.py
    exchange = ExchangeService()
    db = DBService()
    parser = SignalParser()
    validator = SignalValidator()
    risk_manager = RiskManager()
    
    # 2. Inicialización del Motor Central
    engine = TradingEngine(parser, validator, risk_manager, exchange, db)

    # Lista de mensajes de prueba (Lenguaje Natural)
    test_messages = [
        # 1. Señal desordenada (Nueva Señal)
        "Equipo, atención: XRP parece que va a volar. Entramos LONG ahora en 1.35, stop ajustado en 1.25 y target ambicioso en 1.65. Riesgo moderado del 1%.",
        
        # 2. Ruido (Debe ser ignorado)
        "Buenos días a todos, hoy el mercado está muy tranquilo, ¿alguien vio el café?",
        
        # 3. Gestión (Parcial Grande + BE automático)
        "¡XRP está en zona! Tomamos una parte grande de ganancias aquí y aseguramos a BE.",
        
        # 4. Gestión (Cierre Total)
        "Bueno chicos, cerramos todo lo de XRP por hoy, mejor esperar a mañana."
    ]

    print("\n" + "="*50)
    print("--- INICIANDO SIMULACION DEL CEREBRO DE IA ---")
    print("="*50 + "\n")

    for i, msg in enumerate(test_messages, 1):
        print(f"\n[PRUEBA {i}] Mensaje entrante: '{msg}'")
        await engine.process_signal(msg)
        await asyncio.sleep(2) # Pausa para leer el log

    print("\n" + "="*50)
    print("--- SIMULACION COMPLETADA ---")
    print("="*50 + "\n")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ ERROR: Primero debes poner tu GEMINI_API_KEY en el .env")
    else:
        asyncio.run(run_simulation())
