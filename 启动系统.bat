@echo off
title 分单系统启动
cd /d %~dp0

echo ========================================
echo          Fen Dan System Start
echo ========================================
echo.

echo [1/3] Check Python deps...
pip install -r backend\requirements.txt -q -i https://pypi.tuna.tsinghua.edu.cn/simple 2>nul

echo [2/3] Start backend (port 5000)...
start /B python backend\app.py >nul 2>&1
ping -n 3 127.0.0.1 >nul

echo [3/3] Start frontend (port 5173)...
cd /d %~dp0frontend
if not exist node_modules (
    echo Installing frontend deps first time...
    call npm install
)
start /B npm run dev >nul 2>&1
cd /d %~dp0

ping -n 4 127.0.0.1 >nul
echo.
echo ========================================
echo   System Ready!
echo   Open: http://localhost:5173
echo.
echo   Admin:  admin / admin123
echo   User1:  employee1 / 123456
echo   User2:  employee2 / 123456
echo ========================================
echo.
pause
