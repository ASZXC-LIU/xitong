@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
echo ========================================
echo          Fen Dan System Starting...
echo ========================================
echo.
echo [1/3] Installing Python dependencies...
pip install -r backend\requirements.txt -q -i https://pypi.tuna.tsinghua.edu.cn/simple
echo [2/3] Starting backend (port 5000)...
start /B python backend\app.py
timeout /t 3 /nobreak >nul
echo [3/3] Starting frontend (port 5173)...
cd frontend
if not exist node_modules (
    echo First run - installing frontend deps...
    call npm install
)
start /B npm run dev
cd ..
timeout /t 4 /nobreak >nul
echo.
echo ========================================
echo   System is ready!
echo   Open: http://localhost:5173
echo.
echo   Admin:  admin / admin123
echo   User1:  employee1 / 123456
echo   User2:  employee2 / 123456
echo ========================================
echo.
pause