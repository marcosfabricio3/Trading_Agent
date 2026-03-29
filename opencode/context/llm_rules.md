# Reglas de Comportamiento para el LLM 🤖

Estas reglas son **obligatorias** para cualquier Inteligencia Artificial que colabore en este proyecto. Su objetivo es garantizar la máxima transparencia, aprendizaje y calidad técnica.

## 1. Explicación Paso a Paso (Obligatorio)
Antes, durante o después de cada implementación o cambio, el LLM **debe**:
- **Explicar el "Qué"**: Qué problema se está resolviendo o qué funcionalidad se está añadiendo.
- **Explicar el "Cómo"**: La lógica técnica detrás del cambio, incluyendo algoritmos, patrones de diseño o librerías utilizadas.
- **Explicar el "Por qué"**: La justificación de por qué se eligió esa solución y no otra (ventajas en seguridad, escalabilidad o rendimiento).

## 2. Transparencia Algorítmica
Si se implementa un cálculo (ej: modelo de riesgo, lógica de órdenes), se debe:
- Desglosar la fórmula matemática o lógica.
- Explicar las variables involucradas.
- Indicar los límites o restricciones aplicadas.

## 3. Seguridad Primero
- Cualquier cambio que afecte a claves API, manejo de fondos o ejecución de órdenes debe ser resaltado con una advertencia `> [!WARNING]`.
- Se debe explicar cómo se están protegiendo los datos sensibles en cada paso.

## 4. Estilo de Comunicación
- La comunicación debe ser clara, didáctica y profesional.
- Se deben usar bloques de código y diagramas cuando sea necesario para facilitar la comprensión.

---
> [!IMPORTANT]
> El incumplimiento de estas reglas de explicación se considera un fallo en la entrega del componente. El usuario debe entender exactamente qué hace cada línea de código añadida.
