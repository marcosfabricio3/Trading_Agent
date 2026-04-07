import asyncio
import os
import sys
import ccxt
from dotenv import load_dotenv

# Re-cargar entorno
load_dotenv()

async def debug_bitget_params():
    print("\n" + "="*50)
    print("  INVESTIGACION DINAMICA DE PARAMETROS BITGET")
    print("="*50 + "\n")
    
    api_key = os.getenv("BITGET_API_KEY")
    api_secret = os.getenv("BITGET_SECRET_KEY")
    api_passphrase = os.getenv("BITGET_PASSPHRASE")
    
    if not all([api_key, api_secret, api_passphrase]):
        print("ERROR: Faltan llaves en .env")
        return

    exchange = ccxt.bitget({
        'apiKey': api_key,
        'secret': api_secret,
        'password': api_passphrase,
        'options': {'defaultType': 'swap'}
    })
    
    symbol = "XRP/USDT:USDT"
    qty = 5.0
    
    print("1. Abriendo posicion LONG (Unilateral)...")
    try:
        order = exchange.create_order(symbol, 'market', 'buy', qty, None, {'tradeSide': 'open'})
        print(f"OK: Apertura exitosa: {order['id']}")
    except Exception as e:
        print(f"ERROR apertura: {e}")
        return

    await asyncio.sleep(3)
    
    try:
        mark_price = exchange.fetch_ticker(symbol)['last']
        sl_price = round(mark_price * 0.95, 4)
        print(f"Mark Price: {mark_price}, Intento SL: {sl_price}")

        # Combinaciones críticas
        combinations = [
            {"name": "Action Only (Sell + ReduceOnly)", "side": "sell", "params": {"reduceOnly": True}},
            {"name": "No Sides (Buy + Trigger)", "side": "buy", "params": {"stopLossPrice": sl_price, "reduceOnly": True}},
            {"name": "Buy + HoldSide", "side": "buy", "params": {"stopLossPrice": sl_price, "holdSide": "long", "reduceOnly": True}},
            {"name": "Standard Close (Sell + Close)", "side": "sell", "params": {"tradeSide": "close", "reduceOnly": True}},
        ]

        for combo in combinations:
            print(f"\nProbando: {combo['name']}...")
            p = combo['params'].copy()
            # Si no tiene el trigger en params, lo añadimos
            if 'stopLossPrice' not in p:
                p['stopLossPrice'] = sl_price
            
            try:
                # CCXT mapping for trigger orders
                res = exchange.create_order(symbol, 'market', combo['side'], qty, None, p)
                print(f"EXITO con {combo['name']}! ID: {res['id']}")
                # Limpiar si funcionó
                try: exchange.cancel_order(res['id'], symbol, {'planType': 'normal_plan'})
                except: pass
                break 
            except Exception as e:
                print(f"Fallo {combo['name']}: {e}")

    finally:
        print("\nLiquidando posicion...")
        try:
            exchange.create_order(symbol, 'market', 'sell', qty, None, {'tradeSide': 'close', 'reduceOnly': True})
            print("OK: Posicion liquidada.")
        except Exception as e:
            print(f"ERROR liquidacion: {e}")

if __name__ == "__main__":
    asyncio.run(debug_bitget_params())
