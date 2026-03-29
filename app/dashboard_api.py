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
    Estado general del bot.
    """
    return {
        "bot_name": "Trading Agent PRO",
        "version": "1.0",
        "status": "online"
    }

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
    Métricas de rendimiento.
    """
    return {
        "win_rate": "0%", # Placeholder hasta tener datos reales
        "total_trades": 0,
        "daily_pnl": 0.0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
