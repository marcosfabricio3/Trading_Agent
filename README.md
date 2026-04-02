# Trading Agent PRO (v0.0.1)

Agente de trading profesional, escalable y seguro diseñado para automatizar señales de Telegram hacia Bitget con interpretación de Inteligencia Artificial (Gemini).

## 🚀 Inicio Rápido

1. **Configura tu .env**: Asegúrate de tener `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE` y `GEMINI_API_KEY`.
2. **Lanza el Agente**: Ejecuta el archivo `Comenzar_Agente.bat`.
3. **Gestiona tus Chats**: Entra al Dashboard, ve a "Gestión Chat" y usa el botón **"REFRESCAR CATÁLOGO"** para añadir fuentes.

## 🏗️ Arquitectura Integrada

El sistema utiliza el **Model Context Protocol (MCP)** para desacoplar responsabilidades:

- **AI Parser**: (Gemini Flash) Traduce texto plano a objetos de señal.
- **Engine**: Orquesta validación, gestión de riesgo y ejecución.
- **Dashboard**: Interfaz React en tiempo real para control total.

## 🛠️ Requisitos Técnicos

- **Python 3.10+**: Corazón del bot y la API.
- **Node.js**: Necesario para el servidor de Bitget.
- **SQLite3**: Persistencia local segura y rápida.

---
> [!IMPORTANT]
> **Modo de Operación**: Por defecto, el sistema opera según las reglas guardadas en la base de datos. Puedes modificarlas en tiempo real desde la pestaña "Configuración" del Dashboard.
