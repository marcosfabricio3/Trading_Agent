import os
from dotenv import load_dotenv

# Explicación: Cargamos las variables de entorno desde el archivo .env
# Si no existe, usamos valores por defecto para desarrollo local.
load_dotenv()

class Config:
    # API Keys (Mocked defaults for safety)
    BITGET_API_KEY = os.getenv("BITGET_API_KEY", "mock_key")
    BITGET_SECRET_KEY = os.getenv("BITGET_SECRET_KEY", "mock_secret")
    BITGET_PASSPHRASE = os.getenv("BITGET_PASSPHRASE", "mock_passphrase")
    
    # Database
    DB_PATH = os.getenv("DB_PATH", "trading_agent.db")
    
    # Risk settings
    DEFAULT_RISK_PCT = float(os.getenv("DEFAULT_RISK_PCT", "1.0"))
    MAX_CAPITAL_EXPOSURE = float(os.getenv("MAX_CAPITAL_EXPOSURE", "0.30"))
    
    # Validation settings
    MAX_MARKET_DISTANCE_PCT = float(os.getenv("MAX_MARKET_DISTANCE_PCT", "1.0"))

config = Config()
