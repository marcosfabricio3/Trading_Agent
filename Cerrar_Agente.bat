@echo off
title TRADING AGENT - CLEANUP
echo ==========================================
echo       CERRANDO TRADING AGENT (PRO)        
echo ==========================================
echo.

echo [1/3] Finalizando procesos de Python (Backend)...
taskkill /F /IM python.exe /T 2>nul

echo [2/3] Finalizando procesos de Node/Vite (Frontend)...
taskkill /F /IM node.exe /T 2>nul

echo [3/3] Limpiando memorias residuales...
echo.
echo ==========================================
echo    ¡SISTEMA CERRADO CORRECTAMENTE!       
echo ==========================================
echo Ya puedes iniciar denuevo con Comenzar_Agente.bat
pause
