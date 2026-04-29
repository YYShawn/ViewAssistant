@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 正在启动 ViewAssistant...

:: 释放 8000 端口（如已被占用）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: 后台启动服务器
start "" /b python server.py

:: 等待服务器就绪（最多 10 秒）
set /a count=0
:wait
timeout /t 1 /nobreak >nul
curl -s http://127.0.0.1:8000 >nul 2>&1
if errorlevel 1 (
    set /a count+=1
    if %count% lss 10 goto wait
    echo.
    echo [错误] 服务器启动失败，请确认已安装 Python 并执行过 pip install -r requirements.txt
    pause
    exit /b 1
)

echo 服务器已启动，正在打开浏览器...
start http://127.0.0.1:8000

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo   ViewAssistant 运行中
echo   配置页面：http://127.0.0.1:8000
echo   按任意键停止服务器并退出
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pause >nul

:: 退出时停止服务器
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo 服务器已停止
