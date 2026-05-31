@echo off
cls
echo.
echo ============================================
echo  Clase Analytics Platform Startup
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Python is not installed
    exit /b 1
)

REM Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Node.js is not installed
    exit /b 1
)

REM Setup backend
echo Setting up backend...
cd backend

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

if not exist "installed_deps" (
    echo Installing Python dependencies...
    pip install -q -r requirements.txt
    type nul > installed_deps
)

cd ..

REM Setup frontend
echo Setting up frontend...
cd frontend

if not exist "node_modules" (
    echo Installing Node dependencies...
    call npm install -q
)

cd ..

echo.
echo Setup complete!
echo.
echo Starting services...
echo.

REM Start backend
echo Backend: Starting FastAPI on http://localhost:8000
cd backend
call venv\Scripts\activate.bat
start "Clase Analytics Backend" python main.py

REM Start frontend
cd ..\frontend
echo Frontend: Starting Next.js on http://localhost:3000
start "Clase Analytics Frontend" cmd /k "npm run dev"

echo.
echo Services started!
echo.
echo Access the application:
echo   - http://localhost:3000
echo.
echo API:
echo   - http://localhost:8000/api/clases
echo.
echo Close the command windows to stop the services.
pause
