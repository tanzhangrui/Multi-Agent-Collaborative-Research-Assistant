@echo off
chcp 65001 >nul
echo ========================================
echo   多智能体协作研究助手 - 启动脚本
echo ========================================
echo.
echo 正在启动服务器...
echo 启动后请在浏览器中访问: http://localhost:8000
echo.
cd /d "%~dp0"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
