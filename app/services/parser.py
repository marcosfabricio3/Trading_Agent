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
        # 1. Intento rápido con Regex (Síncrono)
        deterministic = core_parse(text)
        
        # Si el regex falla o le faltan datos críticos (is_incomplete), delegamos a la IA
        if (
            "error" in deterministic or 
            deterministic.get("symbol") == "UNKNOWN" or 
            deterministic.get("is_incomplete", False)
        ):
            logger.info("[Parser] Regex incompleto o mensaje humano. Consultando Motor de IA...")
            # Simulamos el comportamiento del Engine de IA unificado
            return interpret_with_ai(text)
        
        # Si el regex funcionó perfectamente (nuevas señales con formato estricto)
        return {
            "category": "NEW_SIGNAL",
            "data": deterministic,
            "reason": "regex_matched"
        }
