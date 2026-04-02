from mcp.server.fastmcp import FastMCP
from opencode.mcp.db_server import log_event
import google.generativeai as genai
import os
import json
import threading
import time
from dotenv import load_dotenv

load_dotenv()

# Inicializar FastMCP
mcp = FastMCP("AI Signal Parser")

# Configurar Gemini (Usando el modelo disponible en tu cuenta avanzada)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

PROMPT_SISTEMA = """
Eres un experto en trading. Tu tarea es extraer datos de señales de Telegram.
Categorías: 
1. NEW_SIGNAL: Nueva operación (requiere símbolo, side, entrada, TP, SL).
2. PARTIAL_CLOSE: Cerrar parte de la posición (ej: "tomamos tp1", "cerramos 50%").
3. MOVE_BE: Mover Stop Loss al precio de entrada (ej: "SL a BE", "aseguramos entrada").
4. CLOSE_FULL: Cerrar toda la operación (ej: "cerramos XRP", "fuera de BTC").
5. DISCARD: Mensajes irrelevantes o saludos.

Responde ÚNICAMENTE en JSON:
{
  "category": "CATEGORIA",
  "reason": "breve explicación",
  "data": { "symbol": "BTCUSDT", "side": "long/short", "entry": 123.4, "tp": 130, "sl": 110, "percent": 50 }
}
"""

async def parse_signal(text: str):
    """Función de compatibilidad/core para el Engine."""
    try:
        # Solo logueamos si el texto es sustancial
        if len(text) > 3:
            log_event("AI_THOUGHT", f"Analizando intención del mensaje: '{text[:25]}...'", {"service": "parser"})
        
        response = model.generate_content(f"{PROMPT_SISTEMA}\n\nMensaje: {text}")
        raw_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_json)
        
        log_event("AI_THOUGHT", f"IA interpretó como {data.get('category')}: {data.get('reason')}", {"category": data.get('category')})
        return data
    except Exception as e:
        return {"category": "ERROR", "reason": str(e)}

    except Exception as e:
        return {"category": "ERROR", "reason": str(e)}

@mcp.tool()
async def interpret_with_ai(text: str):
    """Analiza un mensaje de trading con Gemini."""
    return await parse_signal(text)

if __name__ == "__main__":
    # Si se ejecuta directamente, actúa como un servidor MCP estándar
    mcp.run()
