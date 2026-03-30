@echo off
TITLE Trading Agent Controller
COLOR 0B
echo.
echo    =========================================
echo       TRADING AGENT PRO - INICIO RAPIDO
echo    =========================================
echo.
echo    - Iniciando Backend, Monitor y Telegram...
echo    - Iniciando Dashboard UI...
echo.

powershell -ExecutionPolicy Bypass -File start_all.ps1

echo.
echo    [!] El sistema se ha detenido. Pulsa cualquier tecla para salir.
pause > nul
