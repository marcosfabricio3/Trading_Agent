# Roadmap Detallado: Trading Agent Profesional 🚀

Este roadmap define el flujo ordenado y detallado para la construcción del agente de trading, diseñado para ser escalable, seguro y profesional.

## Fase 1: Cimientos y Herramientas (Contexto LLM) 🏗️
*En esta fase, preparamos el terreno para que el programador (LLM) tenga todas las herramientas necesarias.*

1.  **Definición de Protocolos (MCP)**:
    *   [x] `Parser`: Extracción de señales de texto.
    *   [x] `Validator`: Filtro de calidad y reglas de negocio.
    *   [x] `Risk`: Motor de cálculo de lotaje y gestión monetaria.
    *   [x] `DB`: Persistencia de todo el ciclo de vida.
    *   [x] `Bitget`: Interfaz de ejecución.
2.  **Configuración de Entornos**:
    *   [x] Definir `dev`, `testnet` y `prod` en `opencode/environments/`.
    *   [x] Crear `.env.example` con los secretos requeridos.
3.  **Refinamiento de Reglas**:
    *   [ ] Establecer umbrales de seguridad (Drawdown máximo, exposición por símbolo).

## Fase 2: Desarrollo del Núcleo (Engine) 🧠
*Construcción del orquestador central que ejecutará los "Skills".*

1.  **Diseño del Ciclo de Vida del Trade**:
    *   Implementar `Engine.py`: El servicio principal que escucha eventos (o simula escucha).
    *   Flujo de Ejecución: Invocación secuencial de los servicios MCP.
2.  **Mquina de Estados Robusta**:
    *   `IDLE` -> `PARSING` -> `VALIDATING` -> `CALCULATING_RISK` -> `PLACING_ORDER` -> `MONITORING`.
3.  **Gestión de Errores y Retries**:
    *   Puntos de falla críticos: Tiempo de espera agotado en API del exchange, errores de red, fallos en la DB.

## Fase 3: Seguridad y Validaciones Profundas 🛡️
*Asegurar que el bot nunca ponga en riesgo el capital de forma innecesaria.*

1.  **Validación de Capital (Hard Limits)**:
    *   No permitir operaciones si el balance es menor al calculado por el `risk_server`.
    *   Verificación de margen libre antes de cada orden.
2.  **Reglas de Anti-Sobrecarga**:
    *   Evitar la apertura de múltiples posiciones del mismo símbolo simultáneamente.
3.  **Validación de Precios de Mercado**:
    *   Verificar que el precio de entrada de la señal no esté a más de un % de distancia del precio actual de mercado.

## Fase 4: Integración de Datos (Ingestion) 📡
*Conexión del agente con el mundo exterior.*

1.  **Listener de Telegram**:
    *   Uso de `Telethon` o `python-telegram-bot` para la captura de mensajes.
2.  **Filtrado de Canales**:
    *   Limitar la escucha solo a IDs de canales autorizados.

## Fase 5: Ejecución Real y Exchange 💹
1.  **Sustitución de Mocks**: Implementar la clase `BitgetConnector` real.
2.  **Sincronización de Precios**: Mantener un cache de precios locales para cálculos de balance rápidos.

## Fase 6: Monitoreo y Escalabilidad 📊
1.  **Dashboard de Telemetría**: Ver el estado del bot en tiempo real.
2.  **Sistema de Notificaciones Reales**: Alertas al móvil ante ejecuciones exitosas o fallidas.

## Fase 7: Gestión Avanzada de Trades 📈
1.  **Cierres Parciales Automatizados**:
    *   Lógica para cerrar el 25% de la posición al alcanzar el TP1 (definido en `skills/close_partial.skill.json`).
    *   Mantenimiento de la posición persistente en DB.
2.  **Trailing Stop / Break Even**:
    *   Mover el SL al precio de entrada después del primer parcial (definido en `skills/move_sl.skill.json`).
3.  **Gestión de Expiración**:
    *   Cancelar señales que no se activan en un tiempo determinado.

## Fase 8: Despliegue y Mantenimiento 🚀
1.  **Docker Compose**: Orquestar el Bot, SQLite/PostgreSQL y Redis.
2.  **CI/CD**: Github Actions para correr los tests automáticamente en cada commit.
1.  **Simulador de Señales**:
    *   Herramienta para inyectar señales históricas y ver cómo habría reaccionado el bot.
2.  **Refinamiento del Parser**:
    *   Soporte para múltiples formatos de canales (emojis, tablas).

---
> [!NOTE]
> Este roadmap es un documento vivo que se actualizará según avancemos en el desarrollo y descubramos nuevas necesidades.
