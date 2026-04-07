@echo off
TITLE Trading Agent Controller
SETLOCAL
SET PYTHONPATH=.

:: Colores y Estética
COLOR 0B
echo.
echo    =========================================
echo       TRADING AGENT PRO - INICIO RAPIDO
echo    =========================================
echo.
echo    [1/2] Levantando BACKEND (Engine + API + AI + Monitor)...
start "TRADING AGENT: BACKEND" powershell -NoExit -Command "python -m app.main"

echo    [2/2] Levantando DASHBOARD UI (Frontend)...
timeout /t 3 > nul
start "TRADING AGENT: DASHBOARD" powershell -NoExit -Command "cd dashboard; npm run dev -- --port 5173 --host 0.0.0.0"

echo.
echo    [OK] ¡Ambos servicios se están iniciando en ventanas separadas!
echo    [!] Si hay algún error, revisa las ventanas abiertas.
echo.
echo    Pulsa cualquier tecla para completar el inicio.
pause > nul
ENDLOCAL
EXIT
