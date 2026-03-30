import os
import json
import google.generativeai as genai
from app.logger import logger
from dotenv import load_dotenv

load_dotenv()

class AIEngine:
    """
    Motor de IA para interpretar, normalizar y filtrar mensajes de trading.
    """
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            logger.error("[AI] No se ha configurado la GEMINI_API_KEY en el .env")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            # Usamos los nombres exactos que tu cuenta confirmó en el diagnóstico
            self.model = genai.GenerativeModel('models/gemini-flash-latest')
            logger.info("[AI] Motor de razonamiento (Gemini Flash Latest) inicializado con éxito.")

    async def interpret_message(self, text: str):
        """
        Analiza el texto y devuelve la categoría y datos estructurados.
        """
        if not self.model:
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
        5. DISCARD: Saludos, noticias, memes o charla que NO requiere acción del bot (ej: "buenos dias", "cafe", etc).

        REGLAS:
        - Si es NEW_SIGNAL, extrae: symbol, side, entry, tp, sl, risk_pct.
        - Si es PARTIAL_CLOSE, extrae: symbol (si existe), percent (20, 30 o 50).
        - Devuelve ÚNICAMENTE un JSON puro con este formato:
          {{ "category": "XXX", "data": {{...}}, "reason": "breve explicación" }}
        """

        try:
            # Intentamos llamar al modelo flash
            response = self.model.generate_content(prompt)
            # Limpiamos el texto de posibles formatos de markdown
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except Exception as e:
            logger.error(f"[AI] Error interpretando mensaje: {e}")
            # Si el error es 404, puede ser que el modelo tenga otro nombre o el SDK sea antiguo
            if "404" in str(e):
                logger.warning("[AI] Reintentando con modelo alternativo 'gemini-pro'...")
                try:
                    alt_model = genai.GenerativeModel('gemini-pro')
                    response = alt_model.generate_content(prompt)
                    clean_text = response.text.replace("```json", "").replace("```", "").strip()
                    return json.loads(clean_text)
                except Exception as e2:
                    return {"category": "ERROR", "reason": f"Models flash/pro fail: {e2}"}
            return {"category": "ERROR", "reason": str(e)}
