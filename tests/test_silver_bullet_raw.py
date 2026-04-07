import asyncio
import os
import ccxt
from opencode.mcp.bitget_server import (
    create_order, set_sl_tp, close_position_full, get_position
)

async def test_silver_bullet_raw():
    print("="*60)
    print("  TEST SILVER BULLET (RAW): BUSCANDO ERROR 22002")
    print("="*60)
    
    symbol = "XRP/USDT:USDT"
    qty = 10.0
    
    try:
        print("\n1. Abriendo posicion...")
        await create_order(symbol, 'buy', 'market', qty)
        print("2. Poniendo SL...")
        await set_sl_tp(symbol, sl_price=1.10)
        await asyncio.sleep(1)
        
        print("\n3. Intentando cierre directo (vía Herramienta MCP)...")
        # Esto debería imprimir "!!! Margen bloqueado detectado" si funciona.
        res = await close_position_full(symbol)
        print(f"\nResultado MCP: {res}")
        
    except Exception as e:
        print(f"ERROR CAPTURADO EN TEST: {type(e)} - {e}")

if __name__ == "__main__":
    asyncio.run(test_silver_bullet_raw())
