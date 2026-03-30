Write-Host "🤖 Iniciando AI ENGINE (Gemini Parser)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { `$Host.UI.RawUI.WindowTitle = '🤖 AI ENGINE - Trading Agent'; `$env:PYTHONPATH = '.'; python opencode/mcp/parser_server.py }"

Write-Host "🚀 Iniciando CEREBRO Principal (Bot Engine)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& { `$Host.UI.RawUI.WindowTitle = '🚀 ENGINE - Trading Agent'; `$env:PYTHONPATH = '.'; python -m app.main }"

Write-Host "🖥️ Iniciando DASHBOARD UI..." -ForegroundColor Yellow
Set-Location dashboard
npm run dev -- --port 5173 --host 0.0.0.0
