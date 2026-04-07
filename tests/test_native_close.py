import asyncio
import os
import ccxt
from opencode.mcp.bitget_server import (
    create_order, set_sl_tp, get_position
)

async def test_close_all_positions_native():
    print("="*60)
    print("  TEST NATIVO CCXT: close_all_positions()")
    print("="*60)
    
    exchange = ccxt.bitget({
        'apiKey': os.getenv("BITGET_API_KEY"),
        'secret': os.getenv("BITGET_SECRET_KEY"),
        'password': os.getenv("BITGET_PASSPHRASE"),
        'options': {'defaultType': 'swap'}
    })
    
    symbol = "XRP/USDT:USDT"
    qty = 20.0
    
    try:
        print("\n1. Abriendo posicion...")
        await create_order(symbol, 'buy', 'market', qty)
        print("2. Poniendo SL (Bloqueo de Margen)...")
        await set_sl_tp(symbol, sl_price=1.10)
        await asyncio.sleep(2)
        
        print("\n3. Intentando close_all_positions(symbols=[symbol])...")
        # Native CCXT method
        res = await asyncio.to_thread(
            exchange.close_all_positions, 
            [symbol], 
            {'marginMode': 'isolated'}
        )
        print(f"🎯 EXITO NATIVO: {res}")
        
    except Exception as e:
        print(f"❌ FALLO NATIVO: {e}")

if __name__ == "__main__":
    asyncio.run(test_close_all_positions_native())
