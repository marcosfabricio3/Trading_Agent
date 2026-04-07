import os
import asyncio
import ccxt
from dotenv import load_dotenv
from fastmcp import FastMCP
from typing import List, Dict

# Configuración del servidor MCP
mcp = FastMCP("Bitget Exchange Server")

def get_exchange():
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
        'options': {'defaultType': 'swap'}
    })

exchange = get_exchange()
current_pos_mode = os.getenv("BITGET_POSITION_MODE", "one_way_mode").lower() 

# Errores que indican conflicto de modo (Hedge vs One-Way) o bloqueo de margen
MODE_MISMATCH_ERRORS = ["22002", "45122", "45123", "40774", "43011", "45135", "43025"]

def initialize_bitget():
    global current_pos_mode
    env_mode = os.getenv("BITGET_POSITION_MODE")
    if env_mode:
        current_pos_mode = env_mode.lower()
        print(f"[Bitget] MODO FORZADO: {current_pos_mode}")
        return

    try:
        exchange.load_markets()
        res = exchange.request('v2/mix/account/account', 'private', 'GET', {'productType': 'usdt-futures'})
        if 'data' in res and len(res['data']) > 0:
            current_pos_mode = res['data'][0].get('posMode', 'one_way_mode')
            print(f"[Bitget] MODO DETECTADO: {current_pos_mode}")
    except Exception as e: print(f"[Bitget] Usando modo predeterminado: {current_pos_mode}")

initialize_bitget()

async def cancel_plan_orders(symbol: str):
    """
    Cancela todas las órdenes de plan (SL/TP) para un símbolo.
    Indispensable para liberar el margen en modo Unilateral.
    """
    try:
        clean_symbol = symbol.replace("/USDT:USDT", "").replace("USDT", "")
        print(f"[Bitget][Protocol] Cancelando órdenes de plan para {clean_symbol}...")
        # Estrategia de Resiliencia Máxima: fetch2 (Nivel bajo de CCXT)
        # Estrategia de Autocuración (Self-Healing)
        # Intentamos liberar el margen antes de cerrar la posición.
        try:
            # 1. Intentamos la cancelación de planes nativa de CCXT (Best effort, timeout 2s)
            try:
                print(f"[Bitget][Protocol] Intentando cancel_all_orders(plan=True)...")
                await asyncio.wait_for(
                    asyncio.to_thread(exchange.cancel_all_orders, symbol, {'plan': True}),
                    timeout=2.0
                )
                print(f"[Bitget][Protocol] EXITO en cancelación nativa")
            except Exception: pass

            # 2. Intentamos buscar cualquier método dinámico de cancelación (V1/V2)
            for m_name in dir(exchange):
                if 'cancel' in m_name.lower() and 'plan' in m_name.lower() and ('v1' in m_name.lower() or 'v2' in m_name.lower()):
                    try:
                        print(f"[Bitget][Protocol] Probando método dinámico: {m_name}")
                        await asyncio.wait_for(
                            asyncio.to_thread(getattr(exchange, m_name), {'symbol': f"{clean_symbol}USDT", 'productType': 'usdt-futures'}),
                            timeout=2.0
                        )
                        print(f"[Bitget][Protocol] EXITO con {m_name}")
                        break # Si uno funciona, paramos
                    except Exception: pass

        except Exception as e_final:
            print(f"[Bitget][Protocol] Error silencioso en radar: {e_final}")
        
        return True # Retornamos True para indicar que se intentó el desbloqueo
        print(f"[Bitget][Protocol] Respuesta cancelación: {res.get('msg', 'Sin mensaje')}")
        return res
    except Exception as e:
        import traceback
        print(f"[Bitget][Protocol] ERROR CRITICO cancelando planes: {type(e).__name__} - {e}")
        # traceback.print_exc() # Opcional para debug extremo
        return None

async def safe_execute_with_fallback(func_name, symbol, action_side, pos_side, qty, price, extra_params):
    """
    Ejecuta una acción con Fallback Universal y Lógica Empírica Bitget V2.
    """
    global current_pos_mode
    
    def get_params(mode):
        p = extra_params.copy()
        if mode == "hedge_mode":
            p['posSide'] = pos_side.lower() 
            if 'reduceOnly' in p: del p['reduceOnly']
        else:
            # UNILATERAL (One-Way)
            if 'posSide' in p: del p['posSide']
            if func_name in ["CLOSE", "FULL_CLOSE", "PARTIAL_CLOSE", "SL", "TP"]:
                p['reduceOnly'] = True
                p['tradeSide'] = 'close'
            else:
                p['tradeSide'] = 'open'
        return p

    def get_action_side(mode):
        if func_name in ["OPEN", "CLOSE", "FULL_CLOSE", "PARTIAL_CLOSE"]:
            target = action_side.lower()
        else:
            # PLAN ORDERS (SL/TP) en Unilateral: side = posSide
            if mode == "one_way_mode":
                target = pos_side.lower()
            else:
                target = action_side.lower()
        return 'buy' if target in ['buy', 'buy_long', 'long'] else 'sell'

    try:
        ccxt_side = get_action_side(current_pos_mode)
        p = get_params(current_pos_mode)
        qty_p = float(exchange.amount_to_precision(symbol, qty)) if qty else None
        price_p = float(exchange.price_to_precision(symbol, price)) if price else None

        print(f"[Bitget][{func_name}] {symbol} CCXT_Side={ccxt_side} Params={p}")
        res = await asyncio.to_thread(exchange.create_order, symbol, 'market' if not price_p else 'limit', ccxt_side, qty_p, price_p, p)
        return {"status": "success", "result": res}
        
    except Exception as e1:
        msg = str(e1).lower()
        print(f"[Bitget][Debug] Error capturado: {msg}")
        
        # ERROR 22002 o Bloqueo: Probable margen congelado por SL/TP
        if ("22002" in msg or "43025" in msg) and func_name in ["FULL_CLOSE", "PARTIAL_CLOSE", "CLOSE"]:
            print(f"[Bitget][{func_name}] !!! Margen bloqueado detectado. Iniciando protocolo de desbloqueo...")
            
            # Radar de Autocuración de Planes
            # Buscamos cualquier método dinámico para liberar el margen
            for m_name in dir(exchange):
                if 'cancel' in m_name.lower() and 'plan' in m_name.lower():
                    try:
                        print(f"[Bitget][Protocol] Intentando liberación con: {m_name}")
                        # Notar: Usamos el símbolo limpio XRPUSDT y el productType correcto V2
                        await asyncio.wait_for(
                            asyncio.to_thread(getattr(exchange, m_name), {
                                'symbol': symbol.replace("/USDT:USDT", "").replace("USDT", "") + "USDT", 
                                'productType': 'usdt-futures'
                            }),
                            timeout=2.0
                        )
                        print(f"[Bitget][Protocol] EXITO con {m_name}")
                        break # Si uno funciona, paramos
                    except Exception: pass
            
            await asyncio.sleep(3.0) # Esperamos sincronización del motor de Bitget
            
            try:
                refreshed_pos = await get_position(symbol)
                real_size = float(refreshed_pos.get('info', {}).get('total', 0))
                if real_size > 0:
                    print(f"[Bitget][{func_name}] Reintentando con size real tras desbloqueo: {real_size}")
                    new_params = params.copy()
                    new_params['reduceOnly'] = True
                    return await asyncio.to_thread(
                        exchange.create_order,
                        symbol, 'market', ccxt_side, real_size, None, new_params
                    )
                else:
                    print(f"[Bitget][{func_name}] Posición ya cerrada tras desbloqueo.")
                    return {"id": "closed_ok"}
            except Exception as retry_e:
                print(f"[Bitget][{func_name}] Falló reintento tras desbloqueo: {retry_e}")
                size = refreshed_pos.get("size", 0)
                if size > 0:
                    # Si es FULL, cerramos todo. Si es PARTIAL, mantenemos la proporción solicitada.
                    real_qty = size if func_name == "FULL_CLOSE" else (size * (qty/size if size > 0 else 1.0))
                    real_qty_p = float(exchange.amount_to_precision(symbol, real_qty))
                    print(f"[Bitget][{func_name}] Reintentando con size real tras desbloqueo: {real_qty_p}")
                    res = await asyncio.to_thread(exchange.create_order, symbol, 'market', ccxt_side, real_qty_p, None, p)
                    return {"status": "success", "result": res}
                else:
                    print(f"[Bitget][{func_name}] Posición ya no existe tras desbloqueo.")
                    return {"status": "success", "message": "Position already closed"}
            except Exception as re_err:
                print(f"[Bitget][{func_name}] Falló reintento tras desbloqueo: {re_err}")

        # Fallback de Modo (Hedge <-> One-Way)
        if any(code in msg for code in MODE_MISMATCH_ERRORS) or "position" in msg:
            alt_mode = "one_way_mode" if current_pos_mode == "hedge_mode" else "hedge_mode"
            print(f"[Bitget][{func_name}] FALLBACK (Error {e1}). Probando {alt_mode}...")
            try:
                temp_mode = alt_mode 
                ccxt_side_alt = get_action_side(temp_mode)
                p_alt = get_params(temp_mode)
                res = await asyncio.to_thread(exchange.create_order, symbol, 'market' if not price_p else 'limit', ccxt_side_alt, qty_p, price_p, p_alt)
                current_pos_mode = alt_mode
                return {"status": "success", "fallback": True, "result": res}
            except Exception as e2:
                return {"status": "error", "message": f"Fallo en ambos modos: {e2}"}
        return {"status": "error", "message": str(e1)}

@mcp.tool()
async def get_balance() -> Dict:
    try:
        balance = await asyncio.to_thread(exchange.fetch_balance)
        return {"balance": float(balance.get('USDT', {}).get('free', 0.0)), "currency": "USDT"}
    except Exception as e: return {"error": str(e)}

@mcp.tool()
async def get_market_price(symbol: str) -> Dict:
    try:
        if "/" not in symbol: symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
        ticker = await asyncio.to_thread(exchange.fetch_ticker, symbol)
        return {"price": float(ticker['last'])}
    except Exception as e: return {"error": str(e)}

@mcp.tool()
async def get_position(symbol: str) -> Dict:
    try:
        if "/" not in symbol: symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
        positions = await asyncio.to_thread(exchange.fetch_positions, [symbol])
        for pos in positions:
            size = float(pos.get('contracts', pos.get('amount', 0)) or 0)
            if size > 0: return {"symbol": symbol, "size": size, "side": pos.get('side')}
        return {"symbol": symbol, "size": 0.0}
    except Exception as e: return {"error": str(e)}

@mcp.tool()
async def create_order(symbol: str, side: str, order_type: str, qty: float, price: float = None) -> Dict:
    if "/" not in symbol: symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
    pos_side = 'long' if side.lower() in ['long', 'buy', 'buy_long'] else 'short'
    return await safe_execute_with_fallback("OPEN", symbol, side, pos_side, qty, price, {})

@mcp.tool()
async def set_sl_tp(symbol: str, sl_price: float = None, tp_price: float = None) -> Dict:
    if "/" not in symbol: symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
    pos = await get_position(symbol)
    if pos.get("size", 0) == 0:
        for _ in range(3):
            await asyncio.sleep(2.0)
            pos = await get_position(symbol)
            if pos.get("size", 0) > 0: break
    
    if pos.get("size", 0) == 0: return {"status": "error", "message": "No hay posicion activa"}
    
    pos_side = pos['side'] 
    action_side = 'sell' if pos_side == 'long' else 'buy'
    
    results = {}
    if sl_price:
        results["sl"] = await safe_execute_with_fallback("SL", symbol, action_side, pos_side, pos['size'], None, {'stopLossPrice': sl_price})
    if tp_price:
        await asyncio.sleep(0.5)
        results["tp"] = await safe_execute_with_fallback("TP", symbol, action_side, pos_side, pos['size'], None, {'takeProfitPrice': tp_price})
        
    return {"status": "success", "details": results}

@mcp.tool()
async def update_sl(symbol: str, sl_price: float) -> Dict:
    return await set_sl_tp(symbol, sl_price=sl_price)

@mcp.tool()
async def update_tp(symbol: str, tp_price: float) -> Dict:
    return await set_sl_tp(symbol, tp_price=tp_price)

@mcp.tool()
async def close_position_partial(symbol: str, pct: float) -> Dict:
    if "/" not in symbol: symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
    pos = await get_position(symbol)
    if pos.get("size", 0) <= 0: return {"status": "error", "message": "No hay posicion"}
    qty_to_close = pos['size'] * float(pct)
    action_side = 'sell' if pos['side'] in ['long', 'buy'] else 'buy'
    return await safe_execute_with_fallback("PARTIAL_CLOSE", symbol, action_side, pos['side'], qty_to_close, None, {})

@mcp.tool()
async def close_position_full(symbol: str) -> Dict:
    if "/" not in symbol: symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
    pos = await get_position(symbol)
    if pos.get("size", 0) <= 0: return {"status": "error", "message": "No hay posicion"}
    action_side = 'sell' if pos['side'] in ['long', 'buy'] else 'buy'
    return await safe_execute_with_fallback("FULL_CLOSE", symbol, action_side, pos['side'], pos['size'], None, {})

@mcp.tool()
async def get_market_info(symbol: str) -> Dict:
    try:
        if "/" not in symbol: symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
        market = exchange.market(symbol)
        return {"status": "success", "lot_size": market.get("limits", {}).get("amount", {}).get("min", 0.001)}
    except Exception as e: return {"status": "error", "message": str(e)}

@mcp.tool()
async def set_leverage(symbol: str, leverage: int) -> Dict:
    try:
        if "/" not in symbol: symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
        res = await asyncio.to_thread(exchange.set_leverage, int(leverage), symbol)
        return {"status": "success", "result": res}
    except Exception as e: return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    mcp.run()
