import asyncio
import os
import sys

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from opencode.mcp.bitget_server import get_balance, get_market_price, is_mock

async def main():
    print("=== TEST DE CONEXIÓN BITGET ===")
    print(f"Modo detectado: {'SIMULACIÓN (Mock)' if is_mock else 'REAL (API)'}")
    print("-" * 30)
    
    # 1. Probar Balance
    print("\n[1/2] Consultando Balance...")
    balance = await get_balance()
    if "error" in balance:
        print(f"[X] Error en balance: {balance['error']}")
    else:
        print(f"[OK] Balance: {balance.get('balance')} {balance.get('currency')}")
    
    # 2. Probar Precio de Mercado
    symbol = "BTCUSDT"
    print(f"\n[2/2] Consultando Precio de {symbol}...")
    price_data = await get_market_price(symbol)
    if "error" in price_data:
        print(f"[X] Error en precio: {price_data['error']}")
    else:
        print(f"[OK] Precio actual de {symbol}: {price_data.get('price')}")
    
    print("\n" + "=" * 30)
    if not is_mock and "error" not in balance and "error" not in price_data:
        print("CONEXIÓN REAL EXITOSA!")
    elif is_mock:
        print("INFO: El test se completó en modo simulación.")

if __name__ == "__main__":
    asyncio.run(main())
