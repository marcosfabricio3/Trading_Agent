import asyncio
import os
import ccxt
from dotenv import load_dotenv

# Re-cargar entorno
load_dotenv()

async def deep_investigation_liquidation():
    print("\n" + "="*60)
    print("  INVESTIGACION PROFUNDA: FALLO DE LIQUIDACION BITGET V2")
    print("="*60 + "\n")
    
    exchange = ccxt.bitget({
        'apiKey': os.getenv("BITGET_API_KEY"),
        'secret': os.getenv("BITGET_SECRET_KEY"),
        'password': os.getenv("BITGET_PASSPHRASE"),
        'options': {'defaultType': 'swap'}
    })
    
    symbol = "XRP/USDT:USDT"
    qty = 10.0
    
    print(f"1. Preparando escenario: Abriendo LONG de {qty} XRP...")
    try:
        # Abrimos posicion
        exchange.create_order(symbol, 'market', 'buy', qty, None, {'tradeSide': 'open'})
        print("✅ Posicion abierta.")
    except Exception as e:
        print(f"❌ Error apertura: {e}")
        return

    await asyncio.sleep(2)
    
    mark_price = exchange.fetch_ticker(symbol)['last']
    sl_price = round(mark_price * 0.90, 4)
    tp_price = round(mark_price * 1.10, 4)
    
    print(f"2. Estableciendo PROTECCIONES (SL: {sl_price}, TP: {tp_price})...")
    try:
        # En Unilateral, para proteger un Long se usa side='buy' (el lado de la posicion)
        exchange.create_order(symbol, 'market', 'buy', qty, None, {'stopLossPrice': sl_price, 'reduceOnly': True, 'tradeSide': 'close'})
        exchange.create_order(symbol, 'market', 'buy', qty, None, {'takeProfitPrice': tp_price, 'reduceOnly': True, 'tradeSide': 'close'})
        print("✅ Protecciones (Plan Orders) establecidas.")
    except Exception as e:
        print(f"❌ Error protecciones: {e}")

    await asyncio.sleep(2)

    print("\n3. INTENTO DE LIQUIDACION #1: Con protecciones ACTIVAS...")
    try:
        # Intento de cierre de mercado tipico
        res = exchange.create_order(symbol, 'market', 'sell', qty, None, {'tradeSide': 'close', 'reduceOnly': True})
        print(f"🎯 EXITO INESPERADO (Liquidacion con SL/TP activos): {res['id']}")
    except Exception as e:
        print(f"❌ FALLO ESPERADO (#1): {e}")
        if "22002" in str(e):
            print("   MOTIVO: El error 22002 (No position) a menudo significa que la posicion esta 'bloqueada' por ordenes pendientes.")

    print("\n4. Cancelando todas las Plan Orders relacionadas...")
    try:
        # Cancelamos todo lo pendiente para este simbolo
        cancel_res = exchange.request('v2/mix/plan/cancel-all-plan-order', 'private', 'POST', {
            'symbol': 'XRPUSDT',
            'productType': 'usdt-futures'
        })
        print(f"✅ Plan Orders canceladas. Respuesta: {cancel_res.get('msg')}")
    except Exception as e:
        print(f"❌ Error cancelando planes: {e}")

    await asyncio.sleep(2)

    print("\n5. INTENTO DE LIQUIDACION #2: Tras limpieza de protecciones...")
    try:
        res = exchange.create_order(symbol, 'market', 'sell', qty, None, {'tradeSide': 'close', 'reduceOnly': True})
        print(f"🎯 EXITO (#2): Liquidacion completada tras cancelar planes. ID: {res['id']}")
    except Exception as e:
        print(f"❌ FALLO CRITICO (#2): {e}")

    # Limpieza final por si acaso
    print("\nFinalizando investigacion...")
    try:
        # Cierre incondicional (sin reduceOnly si hace falta)
        exchange.create_order(symbol, 'market', 'sell', qty, None, {'tradeSide': 'close'})
        print("✅ Limpieza final OK.")
    except: pass

if __name__ == "__main__":
    asyncio.run(deep_investigation_liquidation())
