import os
import asyncio
import ccxt
from dotenv import load_dotenv
from fastmcp import FastMCP
from typing import List, Dict

# Configuración del servidor MCP
mcp = FastMCP("Bitget Exchange Server")

def get_exchange():
    """
    Inicializa y retorna la instancia del exchange configurada con API Keys.
    """
    load_dotenv()
    api_key = os.getenv("BITGET_API_KEY")
    api_secret = os.getenv("BITGET_SECRET_KEY")
    api_passphrase = os.getenv("BITGET_PASSPHRASE")
    
    if not all([api_key, api_secret, api_passphrase]):
        raise ValueError("Faltan las API Keys de Bitget en el archivo .env")
        
    return ccxt.bitget({
        'apiKey': api_key,
        'secret': api_secret,
        'password': api_passphrase,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap'
        }
    })

# Instancia global del exchange (Síncrona)
exchange = get_exchange()
current_pos_mode = "one_way_mode" # Default

def initialize_bitget():
    """
    Detecta el modo de posición de la cuenta al inicio.
    """
    global current_pos_mode
    try:
        print("[Bitget] Cargando mercados...")
        exchange.load_markets()
        
        print("[Bitget] Detectando modo de posición...")
        # En v2 Unified account, fetch_balance o una llamada privada nos da el modo
        # Usamos la llamada privada v2 para estar seguros
        res = exchange.private_get_v2_mix_account_account({'productType': 'usdt-futures'})
        if 'data' in res and len(res['data']) > 0:
            current_pos_mode = res['data'][0].get('posMode', 'one_way_mode')
            print(f"[Bitget] MODO DETECTADO: {current_pos_mode}")
        else:
            print("[Bitget] No se pudo detectar modo, usando One-way por defecto.")
    except Exception as e:
        print(f"[Bitget] Error en inicialización: {e}")

# Inicializamos
initialize_bitget()

@mcp.tool()
async def get_balance() -> Dict:
    """
    Obtiene el balance de la cuenta de futuros (USDT-M).
    """
    try:
        balance = await asyncio.to_thread(exchange.fetch_balance)
        usdt_free = balance.get('USDT', {}).get('free', 0.0)
        return {"balance": float(usdt_free), "currency": "USDT", "mode": "real"}
    except Exception as e:
        return {"error": str(e), "mode": "real"}

@mcp.tool()
async def get_market_price(symbol: str) -> Dict:
    """
    Obtiene el precio actual de un símbolo (ej: BTCUSDT).
    """
    try:
        if "/" not in symbol:
            if "USDT" in symbol:
                symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
            
        ticker = await asyncio.to_thread(exchange.fetch_ticker, symbol)
        return {"price": float(ticker['last']), "mode": "real"}
    except Exception as e:
        return {"error": str(e), "mode": "real"}

@mcp.tool()
async def get_position(symbol: str) -> Dict:
    """
    Retorna la posición abierta actual para un símbolo específico.
    """
    try:
        if "/" not in symbol:
            if "USDT" in symbol:
                symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
                
        positions = await asyncio.to_thread(exchange.fetch_positions, [symbol])
        if positions:
            # Buscamos la primera posición con tamaño > 0
            for pos in positions:
                size = float(pos.get('contracts', 0) or 0)
                if size > 0:
                    return {
                        "symbol": symbol,
                        "size": size,
                        "side": pos.get('side'),
                        "entry_price": float(pos.get('entryPrice', 0) or 0),
                        "unrealized_pnl": float(pos.get('unrealizedPnl', 0) or 0),
                        "mode": "real"
                    }
        return {"symbol": symbol, "size": 0.0, "mode": "real"}
    except Exception as e:
        return {"error": str(e), "mode": "real"}

@mcp.tool()
async def get_market_info(symbol: str) -> Dict:
    """
    Obtiene información técnica de un mercado (límites, lot size, precisión).
    """
    try:
        if "/" not in symbol:
            if "USDT" in symbol:
                symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
        
        await asyncio.to_thread(exchange.load_markets)
        market = exchange.market(symbol)
        return {
            "status": "success",
            "symbol": symbol,
            "precision": market.get("precision", {}),
            "limits": market.get("limits", {}),
            "lot_size": market.get("limits", {}).get("amount", {}).get("min", 0.001)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def set_leverage(symbol: str, leverage: int, margin_mode: str = 'cross') -> Dict:
    """
    Establece el apalancamiento para un símbolo.
    """
    try:
        if "/" not in symbol:
            if "USDT" in symbol:
                symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
        
        # In Bitget set_leverage takes (leverage, symbol, params)
        res = await asyncio.to_thread(exchange.set_leverage, int(leverage), symbol)
        return {"status": "success", "leverage": leverage, "result": res}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def create_order(symbol: str, side: str, order_type: str, qty: float, price: float = None) -> Dict:
    """
    Crea una orden detectando automáticamente si la cuenta es One-Way o Hedge.
    """
    try:
        if "/" not in symbol:
            if "USDT" in symbol:
                symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
            
        ccxt_side = 'buy' if side.lower() in ['long', 'buy'] else 'sell'
        params = {}

        if current_pos_mode == "hedge_mode":
            # HEDGE MODE: Requiere posSide (long/short)
            params['posSide'] = 'long' if side.lower() in ['long', 'buy'] else 'short'
        else:
            # ONE-WAY MODE: Requiere tradeSide (open/close)
            params['tradeSide'] = 'open' # Simplificado: buy=open_long, sell=open_short
            # Para abrir, siempre es 'open'. Para cerrar usaremos las herramientas de cierre.
            
        qty = float(exchange.amount_to_precision(symbol, qty)) if hasattr(exchange, 'amount_to_precision') else qty
        
        if order_type.lower() == "market":
            order = await asyncio.to_thread(exchange.create_order, symbol, "market", ccxt_side, qty, None, params)
        else:
            if price:
                price = float(exchange.price_to_precision(symbol, price)) if hasattr(exchange, 'price_to_precision') else price
            order = await asyncio.to_thread(exchange.create_order, symbol, "limit", ccxt_side, qty, price, params)
            
        return {"status": "success", "order": order}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def set_sl_tp(symbol: str, sl_price: float = None, tp_price: float = None) -> Dict:
    """
    Configura SL/TP.
    En One-Way se usa tradeSide:close. En Hedge se usa posSide.
    """
    try:
        pos = await get_position(symbol)
        if pos.get("size", 0) == 0:
            return {"status": "error", "message": "No hay posición activa"}
            
        pos_side = pos['side'] # 'long' o 'short'
        close_side = 'sell' if pos_side == 'long' else 'buy'
        
        params = {'reduceOnly': True}
        if current_pos_mode == "hedge_mode":
            params['posSide'] = pos_side
        else:
            params['tradeSide'] = 'close'

        results = {}
        if "/" not in symbol:
            if "USDT" in symbol:
                symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"

        if sl_price:
            p_sl = params.copy()
            p_sl['stopLossPrice'] = sl_price
            sl_order = await asyncio.to_thread(
                exchange.create_order, symbol, 'market', close_side, pos['size'], None, p_sl
            )
            results["sl_id"] = sl_order['id']
            
        if tp_price:
            p_tp = params.copy()
            p_tp['takeProfitPrice'] = tp_price
            tp_order = await asyncio.to_thread(
                exchange.create_order, symbol, 'market', close_side, pos['size'], None, p_tp
            )
            results["tp_id"] = tp_order['id']
            
        return {"status": "success", "details": results, "mode": "real"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def close_position_partial(symbol: str, pct: float) -> Dict:
    """
    Cierra posición parcial usando el modo correcto.
    """
    try:
        pos = await get_position(symbol)
        if pos.get("size", 0) > 0:
            close_qty = pos['size'] * pct
            pos_side = pos['side']
            close_side = 'sell' if pos_side == 'long' else 'buy'
            
            if "/" not in symbol:
                if "USDT" in symbol:
                    symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
                    
            params = {'reduceOnly': True}
            if current_pos_mode == "hedge_mode":
                params['posSide'] = pos_side
            else:
                params['tradeSide'] = 'close'
            
            await asyncio.to_thread(exchange.create_order, symbol, 'market', close_side, close_qty, None, params)
            return {"status": "success", "message": f"Cerrado {pct*100}% de {symbol}"}
        return {"status": "error", "message": "No hay posición abierta."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def close_position_full(symbol: str) -> Dict:
    return await close_position_partial(symbol, pct=1.0)

@mcp.tool()
async def update_sl(symbol: str, new_sl: float) -> Dict:
    return await set_sl_tp(symbol, sl_price=new_sl)

if __name__ == "__main__":
    mcp.run()
