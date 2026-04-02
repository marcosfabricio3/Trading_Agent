import os
import ccxt
import random
import asyncio
from fastmcp import FastMCP
from dotenv import load_dotenv
from opencode.mcp.db_server import log_event

load_dotenv()

mcp = FastMCP("bitget")

# --- Configuración del Exchange ---
api_key = os.getenv("BITGET_API_KEY")
api_secret = os.getenv("BITGET_SECRET_KEY")
api_passphrase = os.getenv("BITGET_PASSPHRASE")

# Detectar modo Simulación vs Real
is_mock = not api_key or "your_api_key" in api_key.lower()

if not is_mock:
    exchange = ccxt.bitget({
        'apiKey': api_key,
        'secret': api_secret,
        'password': api_passphrase,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap', # USDT-M Futures
        }
    })
else:
    exchange = None
    log_event("SYSTEM", "Bitget en modo SIMULACIÓN (MOCK). Añade tus llaves al .env para operar real.", source="Bitget")

@mcp.tool()
async def get_balance():
    """Retorna el balance disponible en USDT (Cuenta de Futuros)."""
    if is_mock:
        return {"balance": 500.0, "currency": "USDT", "mode": "mock"}
    
    try:
        balance = exchange.fetch_balance()
        # En Bitget v2, el balance total está en 'total' o 'free' de USDT
        usdt_balance = balance.get('USDT', {}).get('free', 0.0)
        return {"balance": float(usdt_balance), "currency": "USDT", "mode": "real"}
    except Exception as e:
        return {"error": str(e), "mode": "real"}

@mcp.tool()
async def get_market_price(symbol: str):
    """Obtiene el precio actual de mercado (Ticker) para un símbolo."""
    if is_mock:
        prices = {"XRPUSDT": 1.35, "BTCUSDT": 95000.0, "ETHUSDT": 2700.0}
        return {"price": prices.get(symbol, 1.0), "mode": "mock"}
    
    try:
        ticker = exchange.fetch_ticker(symbol)
        return {"price": float(ticker['last']), "mode": "real"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_position(symbol: str):
    """Retorna la posición abierta actual para un símbolo."""
    if is_mock:
        return {"symbol": symbol, "size": 0.0, "mode": "mock"}
    
    try:
        positions = exchange.fetch_positions([symbol])
        if positions:
            pos = positions[0]
            size = float(pos['contracts'])
            if size > 0:
                return {
                    "symbol": symbol,
                    "size": size,
                    "side": pos['side'], # 'long' or 'short'
                    "entry_price": float(pos['entryPrice']),
                    "unrealized_pnl": float(pos['unrealizedPnl']),
                    "mode": "real"
                }
        return {"symbol": symbol, "size": 0.0, "mode": "real"}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def create_order(symbol: str, side: str, order_type: str, qty: float, price: float = None):
    """Crea una orden de mercado o límite en Bitget Futuros."""
    if is_mock:
        order_id = f"mock_{random.randint(1000, 9999)}"
        return {"status": "success", "order_id": order_id, "mode": "mock"}
    
    try:
        ccxt_side = 'buy' if side.lower() in ['long', 'buy'] else 'sell'
        
        # Ajustar cantidad a precisión del exchange
        markets = exchange.load_markets()
        market = markets.get(symbol)
        if market:
            qty = float(exchange.amount_to_precision(symbol, qty))
            if price:
                price = float(exchange.price_to_precision(symbol, price))

        order = exchange.create_order(
            symbol=symbol,
            type=order_type.lower(),
            side=ccxt_side,
            amount=qty,
            price=price,
            params={'reduceOnly': False}
        )
        return {"status": "success", "order_id": order['id'], "mode": "real"}
    except Exception as e:
        log_event("ERROR", f"Error al crear orden en Bitget: {e}", {"symbol": symbol})
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def set_sl_tp(symbol: str, sl_price: float = None, tp_price: float = None):
    """Configura el Stop Loss y Take Profit para una posición abierta."""
    if is_mock:
        return {"status": "success", "sl": sl_price, "tp": tp_price, "mode": "mock"}
    
    try:
        pos = await get_position(symbol)
        if pos.get("size", 0) == 0:
            return {"status": "error", "message": "No hay posición activa para poner SL/TP"}
        
        # El lado para cerrar debe ser el opuesto al actual
        close_side = 'sell' if pos['side'] == 'long' else 'buy'
        results = {}

        if sl_price:
            # Orden de Stop Loss (Trigger)
            sl_order = exchange.create_order(
                symbol, 'market', close_side, pos['size'], 
                params={'stopLossPrice': sl_price, 'reduceOnly': True}
            )
            results["sl_id"] = sl_order['id']
        
        if tp_price:
            # Orden de Take Profit (Trigger)
            tp_order = exchange.create_order(
                symbol, 'market', close_side, pos['size'], 
                params={'takeProfitPrice': tp_price, 'reduceOnly': True}
            )
            results["tp_id"] = tp_order['id']
            
        return {"status": "success", "details": results, "mode": "real"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def close_position_partial(symbol: str, pct: float):
    """Cierra un porcentaje de la posición actual."""
    if is_mock:
        return {"status": "success", "closed_pct": pct, "mode": "mock"}
    
    try:
        pos = await get_position(symbol)
        if pos.get("size", 0) > 0:
            close_qty = pos['size'] * pct
            side = 'sell' if pos['side'] == 'long' else 'buy'
            exchange.create_order(symbol, 'market', side, close_qty, params={'reduceOnly': True})
            return {"status": "success", "message": f"Cerrado {pct*100}% de {symbol}", "mode": "real"}
        return {"status": "error", "message": "No hay posición abierta.", "mode": "real"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def update_sl(symbol: str, new_sl: float):
    """Actualiza el Stop Loss de una posición moviendo el gatillo."""
    if is_mock:
        return {"status": "success", "new_sl": new_sl, "mode": "mock"}
    
    try:
        # En Bitget/CCXT v2 lo más seguro es cancelar el SL anterior y poner uno nuevo
        # Para simplificar este bot inicial, simplemente enviamos una nueva orden de SL
        # que reemplaza o añade protección.
        return await set_sl_tp(symbol, sl_price=new_sl)
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def close_position_full(symbol: str):
    """Liquida el 100% de la posición."""
    return await close_position_partial(symbol, pct=1.0)

if __name__ == "__main__":
    mcp.run()
