import logging
import sys
from app.config import config

def setup_logging():
    """
    Configura el sistema de logs profesional.
    - Consola: Nivel INFO
    - Archivo (agent.log): Nivel DEBUG
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Formato de los logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Handler de Consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Handler de Archivo
    file_handler = logging.FileHandler("agent.log", encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()
