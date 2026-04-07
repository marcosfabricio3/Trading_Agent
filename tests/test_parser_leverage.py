import asyncio
import os
from opencode.mcp.parser_server import interpret_with_ai

async def test_leverage_parsing():
    print("=== TEST DE EXTRACCION DE APALANCAMIENTO ===")
    test_signals = [
        "LONG XRP entry 1.30 tp 1.40 sl 1.25 x5",
        "SHORT BTC entry 65000 sl 67000 leverage 10x",
        "Ventas en ETH desde 3500. TP 3300. SL 3600 (x20)"
    ]
    
    for sig in test_signals:
        print(f"\nAnalizando: '{sig}'")
        res = await interpret_with_ai(sig)
        data = res.get("data", {})
        lev = data.get("leverage")
        print(f"Resultado: Category={res.get('category')} Leverage={lev}")
        if lev:
            print(f"✅ EXITO: Extraido {lev}")
        else:
            print(f"❌ FALLO: No se detecto apalancamiento")

if __name__ == "__main__":
    asyncio.run(test_leverage_parsing())
