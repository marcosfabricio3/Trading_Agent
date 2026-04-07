import sqlite3
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.services import db, exchange
from app.logger import logger

app = FastAPI(title="Trading Agent API")

# Habilitar CORS para que el frontend (Vite) pueda consultar la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/status")
async def get_status():
    """
    Estado real de los servicios con manejo de errores robusto.
    """
    services = {
        "ai_engine": "offline",
        "bot_engine": "offline",
        "bitget": "offline"
    }
    
    conn = None
    try:
        # 1. Intentar conectar a la DB para estados de salud locales
        try:
            conn = sqlite3.connect("trading.db", timeout=5)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            def check_health(service_name):
                try:
                    cursor.execute("""
                        SELECT timestamp FROM events 
                        WHERE (message LIKE ? OR metadata LIKE ?) 
                        ORDER BY id DESC LIMIT 1
                    """, (f"%{service_name}%", f"%{service_name}%"))
                    row = cursor.fetchone()
                    if not row: return "offline"
                    
                    from datetime import datetime, timezone
                    ts_str = row['timestamp']
                    clean_ts = ts_str.replace(" ", "T")
                    if "T" not in clean_ts: clean_ts = clean_ts + "T00:00:00"
                    
                    last_seen = datetime.fromisoformat(clean_ts).replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    seconds_diff = (now - last_seen).total_seconds()
                    
                    return "online" if seconds_diff < 120 else "offline"
                except Exception as e:
                    logger.error(f"Health check inner error for {service_name}: {e}")
                    return "warning"

            services["ai_engine"] = check_health("parser")
            services["bot_engine"] = check_health("ENGINE")
        except Exception as db_err:
            logger.error(f"Status API DB Error: {db_err}")
            # Si falla la DB, los servicios locales quedan como offline/warning
        
        # 2. Comprobación real de Bitget (Independiente de la DB)
        try:
            # Fallback check simple: si el motor está online, al menos hay pulso
            # Pero intentamos llamar al exchange para ver si las API keys responden
            bitget_status = "offline"
            try:
                # Usar un timeout muy corto para no penalizar la UI
                # Nota: exchange ya es una instancia global del singleton
                balance_task = asyncio.wait_for(exchange.get_balance(), timeout=2.0)
                balance = await balance_task
                
                if isinstance(balance, dict) and 'error' in balance:
                    # Si hay error (ej: permisos), probamos market que es público
                    market = await asyncio.wait_for(exchange.get_market_price("BTCUSDT"), timeout=1.5)
                    if market and 'error' not in market:
                        bitget_status = "online"
                elif balance:
                    bitget_status = "online"
            except asyncio.TimeoutError:
                # Si el exchange tarda mucho, lo marcamos como warning pero no offline si el motor vive
                bitget_status = "online" if services["bot_engine"] == "online" else "warning"
            except Exception as ex_err:
                logger.error(f"Bitget specific check error: {ex_err}")
                bitget_status = "offline"
            
            services["bitget"] = bitget_status
        except Exception as bitget_err:
            logger.error(f"Global Bitget check error: {bitget_err}")
            services["bitget"] = "offline"

        # 3. Determinar estado global
        all_online = all(v == "online" for v in services.values())
        return {
            "status": "online" if all_online else "warning",
            "version": "0.0.1",
            "services": services
        }

    except Exception as global_err:
        logger.error(f"API Critical Status Error: {global_err}")
        return {
            "status": "error", 
            "debug_error": str(global_err),
            "services": services # Devuelve lo que tengamos (probablemente offline por defecto)
        }
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

@app.get("/api/trades")
def get_trades():
    """
    Lista de trades (Activos e Históricos).
    """
    try:
        active = db.get_active_trades()
        # En una versión extendida, db_server traería también los históricos
        return {
            "active": active,
            "historical": [] 
        }
    except Exception as e:
        logger.error(f"API Error (trades): {e}")
        return {"error": str(e)}

@app.post("/api/trades/{trade_id}/close")
async def close_trade(trade_id: int):
    """
    Cierre de emergencia manual de un trade activo.
    """
    try:
        # Recuperamos la instancia del motor desde el estado global del app
        engine = getattr(app.state, "engine", None)
        if not engine:
            return {"status": "error", "message": "Trading Engine no inyectado en API."}
            
        result = await engine.close_trade_by_id(trade_id)
        return result
    except Exception as e:
        logger.error(f"API Error (close_trade): {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/trades/{trade_id}/params")
async def update_trade_params(trade_id: int, data: dict):
    """
    Modificación manual de SL y TP desde el Dashboard.
    """
    try:
        engine = getattr(app.state, "engine", None)
        if not engine:
            return {"status": "error", "message": "Trading Engine no inyectado en API."}
        
        sl = data.get("sl")
        tp = data.get("tp")
        
        if sl is not None: sl = float(sl)
        if tp is not None: tp = float(tp)
        
        result = await engine.update_trade_params(trade_id, sl=sl, tp=tp)
        return result
    except Exception as e:
        logger.error(f"API Error (update_trade_params): {e}")
        return {"status": "error", "message": str(e)}


@app.get("/api/balance")
async def get_balance():
    """
    Balance actual del exchange.
    """
    try:
        return await exchange.get_balance()
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/performance")
def get_performance():
    """
    Calcula métricas de posiciones abiertas (Longs vs Shorts).
    """
    try:
        active = db.get_active_trades()
        longs = sum(1 for t in active if t.get('side', '').lower() == 'long')
        shorts = sum(1 for t in active if t.get('side', '').lower() == 'short')
        
        return {
            "longs_open": longs,
            "shorts_open": shorts,
            "daily_pnl": "+2.4%" # Simulamos PnL diario por ahora
        }
    except Exception as e:
        logger.error(f"API Performance Error: {e}")
        return {"error": str(e), "longs_open": 0, "shorts_open": 0, "daily_pnl": "0.0%"}

@app.get("/api/chats")
def get_chats():
    """
    Retorna la lista de chats/fuentes ACTIVAS (configuradas por el usuario).
    """
    try:
        conn = sqlite3.connect("trading.db")
        cursor = conn.cursor()
        
        # Obtener chats CONFIGURADOS en settings únicamente
        cursor.execute("SELECT value FROM settings WHERE name = 'monitored_chats'")
        settings_row = cursor.fetchone()
        configured_chats = []
        if settings_row:
            # Dividir por coma y limpiar espacios
            configured_chats = [c.strip() for c in settings_row[0].split(",") if c.strip()]
            
        conn.close()
        
        # Siempre incluimos Global al principio
        return ["Global", *sorted(configured_chats)]
    except Exception as e:
        logger.error(f"API Error (chats): {e}")
        return ["Global"]

@app.get("/api/logs")
def get_logs(chat: str = "Global"):
    """
    Retorna los logs filtrados. Global muestra todo, otros filtran por source.
    """
    try:
        conn = sqlite3.connect("trading.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Búsqueda Robusta: Normalizamos tanto lo que entra como lo que hay en DB
        if chat == "Global":
            cursor.execute("SELECT id, timestamp, message, metadata, source FROM events ORDER BY id DESC LIMIT 100")
        else:
            # Búsqueda Insensible a Mayúsculas y Espacios
            clean_chat = chat.strip().upper()
            cursor.execute("""
                SELECT id, timestamp, message, metadata, source 
                FROM events 
                WHERE UPPER(TRIM(source)) = ? 
                ORDER BY id DESC LIMIT 50
            """, (clean_chat,))
            
        logs = []
        for row in cursor.fetchall():
            d = dict(row)
            # SQLite stores as YYYY-MM-DD HH:MM:SS (UTC). 
            # Appending 'Z' tells the frontend it's UTC so it converts to local time.
            if d.get('timestamp') and 'Z' not in d['timestamp']:
                d['timestamp'] = d['timestamp'].replace(" ", "T") + "Z"
            logs.append(d)
        conn.close()
        return logs
    except Exception as e:
        logger.error(f"API Error (logs): {e}")
        return []

@app.get("/api/discover")
async def discover_chats():
    """
    Lista todos los chats y temas disponibles en la cuenta de Telegram.
    """
    try:
        telegram_service = app.state.telegram
        chats = await telegram_service.get_discoverable_chats()
        return chats
    except Exception as e:
        logger.error(f"API Error (discover): {e}")
        return []

@app.get("/api/settings")
def get_settings():
    """Retorna la configuración actual."""
    try:
        return db.get_settings()
    except Exception as e:
        logger.error(f"API Error (get_settings): {e}")
        return {"error": str(e)}

@app.post("/api/settings")
def update_settings(settings: dict):
    """Actualiza la configuración (acepta un dict con múltiples cambios)."""
    try:
        for name, value in settings.items():
            db.update_setting(name, str(value))
        return {"status": "success", "updated_keys": list(settings.keys())}
    except Exception as e:
        logger.error(f"API Error (update_settings): {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/telegram/dialogs")
async def get_telegram_dialogs(request: Request):
    telegram = getattr(request.app.state, 'telegram', None)
    if not telegram:
        return {"error": "Servicio de Telegram no disponible"}
    
    dialogs = await telegram.get_all_dialogs()
    return dialogs

@app.post("/api/telegram/toggle")
async def toggle_telegram_chat(request: Request, data: dict):
    telegram = getattr(request.app.state, 'telegram', None)
    chat_id = data.get("id")
    chat_name = data.get("name")
    action = data.get("action") # "add" or "remove"
    
    if not telegram or not chat_id:
        return {"error": "Datos insuficientes"}
    
    try:
        conn = sqlite3.connect("trading.db")
        cursor = conn.cursor()
        
        # Obtener configuración actual
        cursor.execute("SELECT value FROM settings WHERE name = 'monitored_chats'")
        row = cursor.fetchone()
        current_chats = [c.strip() for c in row[0].split(",") if c.strip()] if row else []
        
        # Identificadores potenciales (Nombre e ID)
        name_id = chat_name.strip() if chat_name and not chat_name.startswith("Sin Nombre") else None
        str_id = str(chat_id)
        
        if action == "add":
            # Usar Nombre si existe, si no ID
            to_add = name_id or str_id
            if to_add not in current_chats:
                current_chats.append(to_add)
        else:
            # Acción "remove": Ser muy flexible
            new_list = []
            for c in current_chats:
                # Si coincide con el nombre (case-insensitive) o con el ID, lo saltamos (borramos)
                is_match = (
                    (name_id and c.lower() == name_id.lower()) or 
                    (c == str_id) or
                    (c == name_id)
                )
                if not is_match:
                    new_list.append(c)
            current_chats = new_list
        
        new_chats_str = ", ".join(current_chats)
        cursor.execute("INSERT OR REPLACE INTO settings (name, value) VALUES (?, ?)", ("monitored_chats", new_chats_str))
        conn.commit()
        conn.close()
        
        # Notificar al bot de la actualización en caliente
        await telegram.refresh_monitored_chats(new_chats_str)
        
        return {"status": "success", "monitored_chats": current_chats}
    except Exception as e:
        logger.error(f"Error toggling chat: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    import sqlite3 # Necesario para los cálculos locales si se lanza solo este script
    uvicorn.run(app, host="0.0.0.0", port=8000)
