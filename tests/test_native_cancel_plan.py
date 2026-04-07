import asyncio
import os
import ccxt
from opencode.mcp.bitget_server import (
    create_order, set_sl_tp
)

async def test_native_cancel_plan():
    print("="*60)
    print("  TEST NATIVO CCXT: cancel_all_orders(plan=True)")
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
        
        print("\n3. Cancelando planes con cancel_all_orders(symbol, {'plan': True})...")
        # Native CCXT method for Bitget V2
        res = await asyncio.to_thread(
            exchange.cancel_all_orders, 
            symbol, 
            {'plan': True}
        )
        print(f"✅ EXITO CANCEL: {res}")
        
        await asyncio.sleep(2)
        
        print("\n4. Intentando cierre final tras cancelacion nativa...")
        # Ahora debería funcionar el cierre normal
        close_res = await asyncio.to_thread(
            exchange.create_order,
            symbol, 'market', 'sell', qty, None, {'tradeSide': 'close', 'reduceOnly': True}
        )
        print(f"🎯 CIERRE EXITOSO: {close_res['id']}")
        
    except Exception as e:
        print(f"❌ FALLO PRUEBA: {e}")

if __name__ == "__main__":
    asyncio.run(test_native_cancel_plan())
