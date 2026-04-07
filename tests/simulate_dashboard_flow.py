import asyncio
import os
import sqlite3
from app.engine import TradingEngine
from app.services.exchange import ExchangeService
from app.services.db import DBService

async def simulate_dashboard_liquidation():
    print("\n" + "="*80)
    print("  SIMULACION DE DASHBOARD: PRUEBA DE LIQUIDACION ROBUSTA")
    print("="*80)
    
    # Inicializar servicios reales
    engine = TradingEngine()
    db = DBService()
    
    symbol = "XRP/USDT:USDT"
    
    print("\n[Trade] Abriendo posicion LONG (con apalancamiento X5)...")
    # Simulamos una señal que el engine procesará
    # Usamos XRP para que sea barato y rapido
    trade_thought = await engine.handle_new_signal(
        "LONG XRP entry 1.30 tp 1.60 sl 1.10 x5", 
        source="DASHBOARD_TEST"
    )
    print(f"Engine Thought: {trade_thought}")
    
    await asyncio.sleep(3) # Esperar a que se asiente en el exchange y DB
    
    # Obtener el ID del trade activo
    active = db.get_active_trades()
    target_trade = next((t for t in active if t["symbol"].startswith("XRP")), None)
    
    if not target_trade:
        print("❌ Error: No se encontró el trade en la DB.")
        return
        
    tid = target_trade["id"]
    print(f"✅ Trade registrado en DB con ID: {tid}. SL/TP activos en Exchange.")

    print(f"\n[Dashboard] >>> CLICK EN BOTON 'LIQUIDATE' (ID: {tid}) <<<")
    print("Iniciando protocolo de desbloqueo proactivo...")
    
    res = await engine.close_trade_by_id(tid)
    
    if res.get("status") == "success":
        print("\n🎯 ¡EXITO TOTAL! La posicion fue liquidada y la DB actualizada.")
    else:
        print(f"\n❌ FALLO: {res.get('message')}")

    # Verificacion final DB
    conn = sqlite3.connect("trading.db")
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT status, exit_price FROM trades WHERE id = ?", (tid,)).fetchone()
    print(f"\n[DB Check] Status: {row['status']}, Exit Price: {row['exit_price']}")
    conn.close()

if __name__ == "__main__":
    asyncio.run(simulate_dashboard_liquidation())
