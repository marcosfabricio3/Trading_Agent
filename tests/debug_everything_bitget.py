import asyncio
import os
import ccxt
import json
from dotenv import load_dotenv

# Re-cargar entorno
load_dotenv()

async def debug_everything():
    print("="*80)
    print("  DEBUG COMPLETO: POSICION REAL Y LIQUIDACION V2")
    print("="*80)
    
    exchange = ccxt.bitget({
        'apiKey': os.getenv("BITGET_API_KEY"),
        'secret': os.getenv("BITGET_SECRET_KEY"),
        'password': os.getenv("BITGET_PASSPHRASE"),
        'options': {'defaultType': 'swap'}
    })
    
    symbol = "XRP/USDT:USDT"
    qty = 10.0
    
    print("\n1. Abriendo posicion LONG...")
    try:
        exchange.create_order(symbol, 'market', 'buy', qty, None, {'tradeSide': 'open'})
    except Exception as e:
        print(f"Error apertura: {e}")
        return

    await asyncio.sleep(2)
    
    print("\n2. Estado detallado de la posicion:")
    try:
        poss = exchange.fetch_positions([symbol])
        if not poss:
            print("NO SE ENCONTRARON POSICIONES (lista vacia)")
        for p in poss:
            print(f"Side: {p['side']}, Size: {p['contracts']}, Notional: {float(p['contracts']) * p['markPrice'] if 'markPrice' in p else 'N/A'}")
            # El campo info tiene todo el crudo de Bitget
            info = p.get('info', {})
            print(f"Bitget RAW Info: available={info.get('available')}, positionId={info.get('posId')}, marginMode={info.get('marginMode')}")
            
    except Exception as e:
        print(f"Error fetch_positions: {e}")

    print("\n3. Intentando cerrado con tradeSide='close' Y EL SIZE EXACTO DETECTADO...")
    try:
        current_size = float(poss[0]['contracts'])
        res = exchange.create_order(symbol, 'market', 'sell', current_size, None, {'tradeSide': 'close', 'reduceOnly': True})
        print(f"🎯 EXITO: {res['id']}")
    except Exception as e:
        print(f"❌ FALLO 1: {e}")

    await asyncio.sleep(1)

    print("\n4. Intentando cerrado con el endpoint de CIERRE DE MERCADO (v2/mix/order/close-positions)...")
    try:
        # Bitget V2 has a dedicated endpoint to close positions
        res = exchange.request('v2/mix/order/close-positions', 'private', 'POST', {
            'symbol': 'XRPUSDT',
            'productType': 'usdt-futures',
            'marginMode': 'isolated' # O 'cross' segun sea el caso
        })
        print(f"🎯 EXITO 2 (Dedicated Endpoint): {res.get('msg')}")
    except Exception as e:
        print(f"❌ FALLO 2: {e}")

if __name__ == "__main__":
    asyncio.run(debug_everything())
