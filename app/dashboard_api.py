import sqlite3
from fastapi import FastAPI
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
def get_status():
    """
    Estado real de los servicios basado en la última actividad (HEARTBEAT/THOUGHTS).
    """
    conn = None
    try:
        # Usamos un Timeout mayor para evitar locks de Windows
        conn = sqlite3.connect("trading.db", timeout=10)
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
                
                # SQLite CURRENT_TIMESTAMP: YYYY-MM-DD HH:MM:SS
                # Limpiamos el formato para ser 100% seguros
                clean_ts = ts_str.replace(" ", "T")
                if "T" not in clean_ts: clean_ts = clean_ts + "T00:00:00"
                
                last_seen = datetime.fromisoformat(clean_ts).replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                seconds_diff = (now - last_seen).total_seconds()
                
                return "online" if seconds_diff < 120 else "offline"
            except Exception as e:
                logger.error(f"Health check inner error for {service_name}: {e}")
                return "warning"

        parser_status = check_health("parser")
        engine_status = check_health("ENGINE")
        
        return {
            "status": "online" if engine_status == "online" else "warning",
            "version": "0.0.1",
            "services": {
                "ai_engine": parser_status,
                "bot_engine": engine_status
            }
        }
    except Exception as e:
        logger.error(f"API Critical Status Error: {e}")
        return {
            "status": "error", 
            "debug_error": str(e),
            "services": {"ai_engine": "offline", "bot_engine": "offline"}
        }
    finally:
        if conn: conn.close()

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

@app.get("/api/balance")
def get_balance():
    """
    Balance actual del exchange.
    """
    try:
        return exchange.get_balance()
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/performance")
def get_performance():
    """
    Calcula métricas reales de rendimiento.
    """
    try:
        # Traemos todos los trades cerrados para calcular
        conn = sqlite3.connect("trading.db")
        cursor = conn.cursor()
        cursor.execute("SELECT exit_price, entry_price FROM trades WHERE exit_price IS NOT NULL")
        closed_trades = cursor.fetchall()
        conn.close()
        
        total = len(closed_trades)
        wins = sum(1 for exit_p, entry_p in closed_trades if exit_p > entry_p)
        win_rate = f"{(wins/total*100):.1f}%" if total > 0 else "0.0%"
        
        return {
            "win_rate": win_rate,
            "total_trades": total,
            "daily_pnl": "+2.4%" # Simulamos PnL diario por ahora
        }
    except Exception as e:
        return {"error": str(e), "win_rate": "0%", "total_trades": 0}

@app.get("/api/chats")
def get_chats():
    """
    Retorna la lista de chats/fuentes que tienen actividad o están configurados.
    """
    try:
        conn = sqlite3.connect("trading.db")
        cursor = conn.cursor()
        
        # 1. Obtener chats con ACTIVIDAD real
        cursor.execute("SELECT DISTINCT source FROM events WHERE source != 'Global' AND source IS NOT NULL")
        active_chats = [row[0] for row in cursor.fetchall()]
        
        # 2. Obtener chats CONFIGURADOS en settings
        cursor.execute("SELECT value FROM settings WHERE name = 'monitored_chats'")
        settings_row = cursor.fetchone()
        configured_chats = []
        if settings_row:
            configured_chats = [c.strip() for c in settings_row[0].split(",") if c.strip()]
            
        conn.close()
        
        # Combinar, eliminar duplicados y ordenar
        all_chats = sorted(list(set(active_chats + configured_chats)))
        return ["Global", *all_chats]
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
        
        if chat == "Global":
            # Global muestra TODO: Pensamientos, Logs de Sistema, Errores (Aumentamos límite)
            cursor.execute("SELECT id, timestamp, message, metadata, source FROM events ORDER BY id DESC LIMIT 100")
        else:
            # Filtro por chat específico
            cursor.execute("SELECT id, timestamp, message, metadata, source FROM events WHERE source = ? ORDER BY id DESC LIMIT 50", (chat,))
            
        logs = [dict(row) for row in cursor.fetchall()]
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

if __name__ == "__main__":
    import uvicorn
    import sqlite3 # Necesario para los cálculos locales si se lanza solo este script
    uvicorn.run(app, host="0.0.0.0", port=8000)
