import asyncio
import os
import ccxt
import json
from dotenv import load_dotenv

# Re-cargar entorno
load_dotenv()

async def extreme_investigation():
    print("\n" + "="*70)
    print("  DIAGNOSTICO PROFUNDO: ESTADO DE POSICION Y CIERRE V2")
    print("="*70 + "\n")
    
    exchange = ccxt.bitget({
        'apiKey': os.getenv("BITGET_API_KEY"),
        'secret': os.getenv("BITGET_SECRET_KEY"),
        'password': os.getenv("BITGET_PASSPHRASE"),
        'options': {'defaultType': 'swap'}
    })
    
    symbol = "XRP/USDT:USDT"
    qty = 5.0
    
    print("1. Abriendo posicion LONG...")
    try:
        order = exchange.create_order(symbol, 'market', 'buy', qty, None, {'tradeSide': 'open'})
        print(f"✅ Orden apertura: {order['id']}")
    except Exception as e:
        print(f"❌ Error apertura: {e}")
        return

    await asyncio.sleep(2)
    
    print("\n2. Consultando POSICION REAL (crudo)...")
    try:
        poss = exchange.fetch_positions([symbol])
        for p in poss:
            if float(p.get('contracts', 0)) > 0:
                print(f"🔍 DETECTADA: {p['side']} size={p['contracts']} mode={p.get('info', {}).get('posMode')}")
                print(f"   RAW: {json.dumps(p.get('info'))}")
    except Exception as e:
        print(f"❌ Error fetch_positions: {e}")

    print("\n3. Intento de CIERRE SIN tradeSide (Solo reduceOnly)...")
    try:
        res = exchange.create_order(symbol, 'market', 'sell', qty, None, {'reduceOnly': True})
        print(f"🎯 EXITO SI (Solo reduceOnly): {res['id']}")
    except Exception as e:
        print(f"❌ FALLO (Solo reduceOnly): {e}")

    await asyncio.sleep(1)

    print("\n4. Intento de CIERRE SIN NADA (Market Sell directo)...")
    try:
        res = exchange.create_order(symbol, 'market', 'sell', qty, None, {})
        print(f"🎯 EXITO SI (Market Sell sin params): {res['id']}")
    except Exception as e:
        print(f"❌ FALLO (Market Sell sin params): {e}")

    print("\nResultados finales obtenidos.")

if __name__ == "__main__":
    asyncio.run(extreme_investigation())
