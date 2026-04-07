import asyncio
import os
import ccxt
from opencode.mcp.bitget_server import (
    create_order, set_sl_tp
)

async def test_opposite_order_netting():
    print("="*60)
    print("  TEST FINAL: Neteo de Posicion (Side Opposite)")
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
        print("\n1. Abriendo posicion LONG (V2)...")
        await create_order(symbol, 'buy', 'market', qty)
        print("2. Poniendo SL (Bloqueo)...")
        await set_sl_tp(symbol, sl_price=1.10)
        await asyncio.sleep(2)
        
        print("\n3. Intentando cerrar enviando orden SELL (NON-REDUCE-ONLY)...")
        # En modo One-Way, una orden contraria debería netear la posición
        # Usamos tradeSide='close' pero reduceOnly=False? No.
        # Solo enviamos una orden de mercado normal.
        close_res = await asyncio.to_thread(
            exchange.create_order,
            symbol, 'market', 'sell', qty, None, {'tradeSide': 'close'} 
        )
        print(f"🎯 RESIDUO DE ORDEN CONTRARIA: {close_res['id']}")
        
        await asyncio.sleep(2)
        
        pos = await asyncio.to_thread(exchange.fetch_position, symbol)
        if float(pos.get('info', {}).get('total', 0)) == 0:
            print("🏆 VICTORIA: La posicion se neteo incluso con SL activo!")
        else:
            print(f"❌ FALLO: La posicion persiste: {pos.get('info', {}).get('total')}")
        
    except Exception as e:
        print(f"❌ FALLO PRUEBA: {e}")

if __name__ == "__main__":
    asyncio.run(test_opposite_order_netting())
