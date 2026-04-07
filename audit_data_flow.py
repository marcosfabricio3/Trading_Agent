import asyncio
import sqlite3
import sys
import os

# Añadimos el path para importar los módulos del bot
sys.path.append(os.getcwd())

from app.engine import TradingEngine
from app.services.db import DBService

async def audit_flow():
    print("--- INICIANDO AUDITORÍA DE FLUJO ---")
    db = DBService()
    engine = TradingEngine() # El engine usa db internamente

    # 1. Nombre de canal exacto de la config
    test_source = "RETO 1k a 10k"
    test_message = "LONG BTC entry 65000 sl 64000 tp 68000"
    
    print(f"Propagando señal de prueba para fuente: '{test_source}'...")
    
    # 2. Forzamos el procesamiento
    thought = await engine.process_signal(test_message, source=test_source)
    print(f"Resultado del motor (thought): {thought}")
    
    # 3. Verificamos DB
    conn = sqlite3.connect("trading.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n--- CONTENIDO DE TABLA EVENTS PARA ESTA FUENTE ---")
    cursor.execute("SELECT * FROM events WHERE source = ? ORDER BY id DESC LIMIT 5", (test_source,))
    rows = cursor.fetchall()
    
    if not rows:
        print(f"❌ ERROR CRÍTICO: No se encontró NADA en la DB para la fuente '{test_source}'")
        print("Buscando sin filtro para ver qué se guardó...")
        cursor.execute("SELECT source, event_type, message FROM events ORDER BY id DESC LIMIT 5")
        for r in cursor.fetchall():
            print(f"Encontrado: Source='{r['source']}' | Type='{r['event_type']}'")
    else:
        for r in rows:
            print(f"✅ LOG OK: [{r['timestamp']}] {r['event_type']} -> {r['message'][:50]}...")

    conn.close()

if __name__ == "__main__":
    asyncio.run(audit_flow())
