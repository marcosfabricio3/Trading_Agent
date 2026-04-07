import asyncio
import os
from opencode.mcp.bitget_server import (
    create_order, set_sl_tp, close_position_full, get_position
)

async def test_silver_bullet_protocol():
    print("="*60)
    print("  TEST SILVER BULLET: PROTOCOLO DE DESBLOQUEO")
    print("="*60)
    
    symbol = "XRP/USDT:USDT"
    qty = 10.0
    
    print("\n1. Abriendo posicion...")
    open_res = await create_order(symbol, 'buy', 'market', qty)
    if open_res["status"] != "success":
        print(f"Error apertura: {open_res}")
        return
        
    print("2. Poniendo SL (Bloqueando Margen)...")
    ticker = await asyncio.to_thread(lambda: os.system("python -c \"import ccxt; e=ccxt.bitget(); print(e.fetch_ticker('XRP/USDT:USDT')['last'])\""))
    # Calculamos un SL lejano
    await set_sl_tp(symbol, sl_price=1.10)
    print("✅ SL puesto.")
    
    await asyncio.sleep(2)
    
    print("\n3. Lanzando CLOSE_POSITION_FULL (Debe activar el protocolo)...")
    close_res = await close_position_full(symbol)
    
    print(f"\nResultado Final: {close_res['status']}")
    if close_res["status"] == "success":
        print("🎯 ¡EXITO! El protocolo de desbloqueo funcionó perfectamente.")
    else:
        print(f"❌ FALLO: {close_res.get('message')}")

if __name__ == "__main__":
    asyncio.run(test_silver_bullet_protocol())
