import asyncio
import os
import sys

# Añadir el directorio raíz al path para importar el servidor
sys.path.append(os.getcwd())

from opencode.mcp.bitget_server import (
    get_balance, create_order, set_sl_tp, get_position, close_position_full, get_market_price
)

async def run_diagnostic_test():
    """
    Diagnostico sin caracteres especiales para Windows.
    """
    print("\n" + "="*50)
    print("  INICIANDO DIAGNOSTICO DE SINCRONIZACION BITGET")
    print("="*50 + "\n")
    
    symbol = "XRP/USDT:USDT"
    
    # 1. Verificar Balance
    print("[1/4] Verificando conexion...")
    bal = await get_balance()
    if "error" in bal:
        print(f"ERROR: {bal['error']}")
        return
    print(f"OK: Balance: {bal['balance']} USDT")
    
    # 2. Precio
    mkt = await get_market_price(symbol)
    if "error" in mkt:
        print(f"ERROR mkt: {mkt['error']}")
        return
    price = mkt['price']
    print(f"OK: Precio: {price}")
    
    # 3. Apertura
    qty = 5.0 
    print(f"\nACCION: Abriendo LONG de prueba ({qty} XRP)...")
    order = await create_order(symbol, "long", "market", qty)
    
    if order["status"] == "error":
        print(f"ERROR open: {order['message']}")
        return
    
    mode_info = "FALLBACK" if order.get('fallback') else "DIRECTO"
    print(f"OK: Orden abierta ({mode_info}).")
    
    await asyncio.sleep(2.5)
    
    # 4. SL/TP
    sl = round(price * 0.96, 4)
    tp = round(price * 1.04, 4)
    print(f"\nACCION: Sincronizando SL ({sl}) y TP ({tp})...")
    
    res = await set_sl_tp(symbol, sl_price=sl, tp_price=tp)
    
    if res["status"] == "success":
        details = res["details"]
        sl_res = details.get("sl", {}).get("status", "SKIP")
        tp_res = details.get("tp", {}).get("status", "SKIP")
        print(f"RESULTADO: SL={sl_res}, TP={tp_res}")
        if sl_res == "error": print(f"  Error SL: {details['sl'].get('message')}")
        if tp_res == "error": print(f"  Error TP: {details['tp'].get('message')}")
    else:
        print(f"ERROR critico SL/TP: {res['message']}")
        
    # 5. Cierre
    print("\nLIMPIEZA: Liquidando posicion...")
    close = await close_position_full(symbol)
    print(f"OK: Cierre finalizado ({close['status']})")
    
    print("\n" + "="*50)
    print("  DIAGNOSTICO FINALIZADO")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(run_diagnostic_test())
