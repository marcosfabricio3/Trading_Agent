from fastmcp import FastMCP
import re
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("parser")

# --- AI Engine Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Usamos el modelo estable confirmado en el diagnóstico
    AI_MODEL = genai.GenerativeModel('models/gemini-flash-latest')
else:
    AI_MODEL = None

@mcp.tool()
def interpret_with_ai(text: str):
    """
    Usa Inteligencia Artificial (Gemini) para interpretar un mensaje complejo.
    """
    if not AI_MODEL:
        return {"category": "ERROR", "reason": "No API Key"}

    prompt = f"""
    Actúa como un experto analista de señales de trading institucional.
    Tu tarea es identificar si el siguiente mensaje es una SEÑAL, una ORDEN DE GESTIÓN o RUIDO.

    MENSAJE: "{text}"

    CATEGORÍAS:
    1. NEW_SIGNAL: Una señal de entrada con símbolo, lado (Long/Short), TP y SL.
    2. PARTIAL_CLOSE: Orden de tomar ganancias parciales. 
       Identifica el tamaño: "grande/importante" -> 50%, "pequenia/ligera" -> 20%, el resto -> 30%.
    3. MOVE_BE: Orden de mover el Stop Loss al precio de entrada (Break-Even).
    4. CLOSE_FULL: Orden de cerrar toda la posición.
    5. DISCARD: Saludos, noticias, memes o charla que NO requiere acción del bot.

    REGLAS:
    - Si es NEW_SIGNAL, extrae: symbol, side (long/short), entry, tp, sl, risk_pct (número, default 1), leverage (número, default 10).
    - Si es PARTIAL_CLOSE, extrae: symbol y percent (20, 30 o 50).
    - Devuelve ÚNICAMENTE un JSON puro con este formato:
      {{ "category": "XXX", "data": {{ "symbol": "...", "side": "...", "entry": 1.2, "tp": 1.5, "sl": 1.1, "risk_pct": 1.0, "leverage": 10 }}, "reason": "..." }}
    """

    try:
        response = AI_MODEL.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean_text)
        
        # Post-procesamiento para asegurar que 'data' tenga campos por defecto y símbolos normalizados
        if result.get("category") == "NEW_SIGNAL":
            d = result.get("data", {})
            d.setdefault("risk_pct", 1.0)
            d.setdefault("leverage", 10)
            
            # Normalización de Símbolo (añadir USDT si falta)
            symbol = d.get("symbol", "UNKNOWN").upper()
            if symbol != "UNKNOWN" and not symbol.endswith("USDT"):
                symbol = symbol + "USDT"
            d["symbol"] = symbol
            
            result["data"] = d
            
        return result
    except Exception as e:
        return {"category": "ERROR", "reason": str(e)}

@mcp.tool()
def parse_signal(text: str):
    """
    Parses a trading signal using Regex (Deterministic).
    """
    try:
        text_upper = text.upper()
        # (Lógica Regex existente...)
        side = "long" if "LONG" in text_upper else "short" if "SHORT" in text_upper else "unknown"
        if side == "unknown" and "ENTRADA" not in text_upper:
            return {"symbol": "UNKNOWN", "error": "No trading indicators found"}

        BLACKLIST = ["EQUIPO", "BUENOS", "HOLA", "ATENCION", "NUEVA", "URGENTE"]
        symbol = "UNKNOWN"
        all_words = re.findall(r"\b([A-Z]{3,5})\b", text_upper)
        for word in all_words:
            if word not in BLACKLIST:
                symbol = word
                break
        
        def find_value(key):
            match = re.search(rf"{key}:\s*([\d\.]+)", text_upper)
            return float(match.group(1)) if match else 0.0

        entry = find_value("ENTRADA")
        tp = find_value("TP")
        sl = find_value("SL")
        
        # Si el regex es incompleto para una nueva señal, indicamos que se requiere IA
        is_incomplete = (entry == 0 or tp == 0) and side != "unknown"

        if symbol != "UNKNOWN" and not symbol.endswith("USDT"):
            symbol = symbol + "USDT"

        # Leverage: Buscamos X20, X10, etc.
        leverage_match = re.search(r"X(\d+)", text_upper)
        leverage = int(leverage_match.group(1)) if leverage_match else 10 # Default 10x

        # Riesgo: Buscamos "RIESGO: 1", "1%", etc.
        risk_match = re.search(r"RIESGO:\s*([\d\.]+)", text_upper)
        risk = float(risk_match.group(1)) if risk_match else 1.0 # Default 1%

        return {
            "symbol": symbol,
            "side": side,
            "leverage": leverage,
            "entry": entry,
            "tp": tp,
            "sl": sl,
            "risk_pct": risk,
            "is_incomplete": is_incomplete,
            "type": "new_signal" if entry > 0 else "update"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()
