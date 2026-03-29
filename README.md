# Trading Agent 🚀

Agente de trading profesional, escalable y seguro diseñado para automatizar señales de trading (ej. Telegram) hacia Bitget.

## Arquitectura

El sistema sigue una arquitectura de microservicios desacoplados usando el **Model Context Protocol (MCP)**:

- **Parser**: Traduce texto plano a objetos de señal estructurados.
- **Validator**: Filtra señales que no cumplen con los parámetros de calidad o R:R.
- **Risk**: Calcula el tamaño de la posición basándose en el capital disponible y la distancia al SL.
- **Bitget**: Interfaz con el exchange para ejecución de órdenes.
- **DB**: Persistencia de señales, trades, órdenes y eventos.

## Requisitos

- Python 3.10+
- Node.js (para el servidor de Bitget)
- SQLite3

## Instalación

1. Clona el repositorio.
2. Crea un entorno virtual: `python -m venv venv`.
3. Instala dependencias: `pip install fastmcp`.
4. Copia `.env.example` a `.env` y completa tus credenciales.

## Estructura de Carpetas

- `opencode/mcp/`: Servidores MCP individuales.
- `opencode/context/`: Documentación técnica y reglas de negocio.
- `opencode/skills/`: Orquestación de flujos de trabajo.
- `opencode/environments/`: Configuraciones por entorno.

## Seguridad

- Nunca subas el archivo `.env` al repositorio.
- Usa el modo `dev` para pruebas sin ejecución real en el exchange.