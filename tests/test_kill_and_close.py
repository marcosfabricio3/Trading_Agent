import asyncio
import os
import ccxt
from dotenv import load_dotenv

# Re-cargar entorno
load_dotenv()

async def test_kill_plans_then_close():
    print("\n" + "="*70)
    print("  TEST DE LIQUIDACION DEFINITIVA: CANCELAR PLANES + CIERRE")
    print("="*70 + "\n")
    
    exchange = ccxt.bitget({
        'apiKey': os.getenv("BITGET_API_KEY"),
        'secret': os.getenv("BITGET_SECRET_KEY"),
        'password': os.getenv("BITGET_PASSPHRASE"),
        'options': {'defaultType': 'swap'}
    })
    
    symbol = "XRP/USDT:USDT"
    qty = 10.0
    
    print("1. Abriendo posicion y estableciendo SL/TP (Escenario de Bloqueo)...")
    try:
        exchange.create_order(symbol, 'market', 'buy', qty, None, {'tradeSide': 'open'})
        await asyncio.sleep(2)
        # Protecciones
        exchange.create_order(symbol, 'market', 'buy', qty, None, {'stopLossPrice': 1.0, 'reduceOnly': True, 'tradeSide': 'close'})
        print("✅ Escenario listo: LONG con SL activo.")
    except Exception as e:
        print(f"❌ Error preparacion: {e}")
        return

    print("\n2. Intento de cierre DIRECTO (Sin cancelar planes)...")
    try:
        exchange.create_order(symbol, 'market', 'sell', qty, None, {'tradeSide': 'close', 'reduceOnly': True})
        print("🎯 EXITO DIRECTO? (No deberia)")
    except Exception as e:
        print(f"⚠️ FALLO ESPERADO (Bloqueado por SL): {e}")

    print("\n3. CANCELANDO TODAS LAS PLAN ORDERS...")
    try:
        # ccxt bitget cancelAllPlanOrders
        res = exchange.request('v2/mix/plan/cancel-all-plan-order', 'private', 'POST', {
            'symbol': 'XRPUSDT',
            'productType': 'usdt-futures'
        })
        print(f"✅ Planes cancelados: {res.get('msg')}")
    except Exception as e:
        print(f"❌ Error cancelando: {e}")

    await asyncio.sleep(1)

    print("\n4. Intento de cierre TRAS CANCELAR...")
    try:
        res = exchange.create_order(symbol, 'market', 'sell', qty, None, {'tradeSide': 'close', 'reduceOnly': True})
        print(f"🎯 ¡EXITO TOTAL! La liquidacion funciono tras limpiar planes. ID: {res['id']}")
    except Exception as e:
        print(f"❌ FALLO TRAS CANCELAR: {e}")

if __name__ == "__main__":
    asyncio.run(test_kill_plans_then_close())
