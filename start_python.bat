@echo off
echo ========================================
echo Tawnia Healthcare Analytics - Python Version
echo ========================================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

:: Display Python version
echo Python version:
python --version
echo.

:: Check Python version (must be 3.8+)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Checking Python version...
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if %errorlevel% neq 0 (
    echo ERROR: Python 3.8 or higher is required
    echo Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install requirements
if exist "requirements.txt" (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo WARNING: requirements.txt not found
)

:: Create required directories
echo Creating required directories...
if not exist "uploads" mkdir "uploads"
if not exist "data" mkdir "data"
if not exist "reports" mkdir "reports"
if not exist "logs" mkdir "logs"

:: Copy environment file if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env file from template...
        copy ".env.example" ".env"
    )
)

:: Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found
    echo Please ensure all Python files are in place
    pause
    exit /b 1
)

echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Virtual environment is activated.
echo.
echo To start the server:
echo   python main.py
echo.
echo Or use uvicorn directly:
echo   uvicorn main:app --reload --host 127.0.0.1 --port 3000
echo.
echo The application will be available at:
echo   - Main interface: http://localhost:3000
echo   - API documentation: http://localhost:3000/docs
echo   - Alternative docs: http://localhost:3000/redoc
echo   - Health check: http://localhost:3000/health
echo.

:: Ask if user wants to start the server
set /p START_SERVER="Start the server now? (y/n): "
if /i "%START_SERVER%"=="y" (
    echo Starting server...
    echo Press Ctrl+C to stop the server
    echo.
    python main.py
) else (
    echo Server not started. You can start it manually with: python main.py
)

pause
