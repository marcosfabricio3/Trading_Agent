import asyncio
import os
import ccxt
from opencode.mcp.bitget_server import (
    create_order, set_sl_tp
)

async def test_v1_cancel_v2_unlock():
    print("="*60)
    print("  TEST FINAL: V1 Cancel -> V2 Close")
    print("="*60)
    
    exchange = ccxt.bitget({
        'apiKey': os.getenv("BITGET_API_KEY"),
        'secret': os.getenv("BITGET_SECRET_KEY"),
        'password': os.getenv("BITGET_PASSPHRASE"),
        'options': {'defaultType': 'swap'}
    })
    
    symbol = "XRP/USDT:USDT"
    clean_symbol = "XRPUSDT"
    qty = 20.0
    
    try:
        print("\n1. Abriendo posicion (V2)...")
        await create_order(symbol, 'buy', 'market', qty)
        print("2. Poniendo SL (Bloqueo V2)...")
        await set_sl_tp(symbol, sl_price=1.10)
        await asyncio.sleep(2)
        
        print("\n3. Cancelando planes con V1: privateMixPostMixV1PlanCancelAllPlanOrder...")
        # Larga vida al Rey
        res = await asyncio.to_thread(
            exchange.privateMixPostMixV1PlanCancelAllPlanOrder,
            {
                'symbol': clean_symbol + "_UMCBL",
                'productType': 'umcbl'
            }
        )
        print(f"✅ EXITO V1 CANCEL: {res}")
        
        await asyncio.to_thread(asyncio.sleep, 3) # Esperamos liberación
        
        print("\n4. Intentando cierre final V2...")
        close_res = await asyncio.to_thread(
            exchange.create_order,
            symbol, 'market', 'sell', qty, None, {'tradeSide': 'close', 'reduceOnly': True}
        )
        print(f"🎯 CIERRE V2 EXITOSO TRAS V1 CANCEL: {close_res['id']}")
        
    except Exception as e:
        print(f"❌ FALLO PRUEBA: {e}")

if __name__ == "__main__":
    asyncio.run(test_v1_cancel_v2_unlock())
