import asyncio
import os
import ccxt
from opencode.mcp.bitget_server import (
    create_order, set_sl_tp
)

async def test_ccxt_close_position_native():
    print("="*60)
    print("  TEST NATIVO CCXT: close_position()")
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
        print("2. Poniendo SL (Bloqueo)...")
        await set_sl_tp(symbol, sl_price=1.10)
        await asyncio.sleep(2)
        
        print("\n3. Intentando close_position(symbol, side='sell')...")
        # Native CCXT high-level close method
        res = await asyncio.to_thread(
            exchange.close_position, 
            symbol, 
            'sell', 
            {'reduceOnly': True}
        )
        print(f"🎯 EXITO NATIVO CLOSE: {res['id']}")
        
    except Exception as e:
        print(f"❌ FALLO PRUEBA: {e}")

if __name__ == "__main__":
    asyncio.run(test_ccxt_close_position_native())
