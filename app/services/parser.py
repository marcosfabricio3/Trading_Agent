from opencode.mcp.parser_server import parse_signal as core_parse, interpret_with_ai
from app.logger import logger

class SignalParser:
    """
    Wrapper para el parseo central con soporte de Inteligencia Artificial (Gemini).
    """
    def __init__(self):
        # El AIEngine ahora vive dentro del parser_server.py como un servicio MCP
        pass

    async def parse_signal(self, text: str):
        """
        Intenta parsear mediante Regex (Rápido) -> Si falla o es incompleto -> Llama a IA.
        """
        # 1. Intento rápido con Regex (Soporte Async ahora)
        result = await core_parse(text)
        
        # Si el resultado ya tiene una categoría clara (IA o Regex avanzado), lo devolvemos tal cual
        if "category" in result and result["category"] != "ERROR":
            return result
            
        # Si el resultado es síncrono/viejo o incompleto, intentamos IA de nuevo (redundancia)
        if (
            "error" in result or 
            result.get("symbol") == "UNKNOWN" or 
            result.get("is_incomplete", False)
        ):
            logger.info("[Parser] Datos incompletos. Re-evaluando con Motor de IA...")
            return await interpret_with_ai(text)
        
        # Fallback para compatibilidad
        return {
            "category": "NEW_SIGNAL",
            "data": result,
            "reason": "legacy_fallback"
        }
