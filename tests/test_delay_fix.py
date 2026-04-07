import asyncio
import os
import ccxt
from dotenv import load_dotenv

# Re-cargar entorno
load_dotenv()

async def definitive_fix_test():
    print("="*80)
    print("  TEST DEFINITIVO: ¿EL DELAY TRAS CANCELAR ES LA CLAVE?")
    print("="*80)
    
    exchange = ccxt.bitget({
        'apiKey': os.getenv("BITGET_API_KEY"),
        'secret': os.getenv("BITGET_SECRET_KEY"),
        'password': os.getenv("BITGET_PASSPHRASE"),
        'options': {'defaultType': 'swap'}
    })
    
    symbol = "XRP/USDT:USDT"
    qty = 10.0
    
    print("\n1. Abriendo posicion y bloqueando con SL...")
    try:
        exchange.create_order(symbol, 'market', 'buy', qty, None, {'tradeSide': 'open'})
        await asyncio.sleep(2)
        exchange.create_order(symbol, 'market', 'buy', qty, None, {'stopLossPrice': 1.0, 'reduceOnly': True, 'tradeSide': 'close'})
        print("✅ Escenario bloqueado listo.")
    except Exception as e:
        print(f"Error preparacion: {e}")
        return

    print("\n2. Cancelando PLAN ORDERS...")
    try:
        exchange.request('v2/mix/plan/cancel-all-plan-order', 'private', 'POST', {
            'symbol': 'XRPUSDT',
            'productType': 'usdt-futures'
        })
        print("✅ Planes cancelados.")
    except Exception as e:
        print(f"Error cancelando: {e}")

    # TEST DE TIEMPOS
    for delay in [0, 0.5, 1.0, 2.0]:
        print(f"\n3. Esperando {delay}s y probando CIERRE...")
        await asyncio.sleep(delay)
        try:
            res = exchange.create_order(symbol, 'market', 'sell', qty, None, {'tradeSide': 'close', 'reduceOnly': True})
            print(f"🎯 EXITO con {delay}s de espera! ID: {res['id']}")
            break
        except Exception as e:
            print(f"❌ FALLO con {delay}s: {e}")

    # Limpieza
    try: exchange.create_order(symbol, 'market', 'sell', qty, None, {'tradeSide': 'close'})
    except: pass

if __name__ == "__main__":
    asyncio.run(definitive_fix_test())
