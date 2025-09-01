@echo off
REM Tawnia Healthcare Analytics - Windows Deployment Script
REM Supports multiple deployment targets: Docker, Cloudflare, Netlify

setlocal enabledelayedexpansion

REM Default values
set DEPLOYMENT_TARGET=docker
set ENVIRONMENT=production
set SKIP_TESTS=false
set SKIP_BUILD=false
set VERBOSE=false

echo Tawnia Healthcare Analytics - Deployment Script
echo ===============================================
echo.

REM Show current configuration
echo Configuration:
echo   Target: %DEPLOYMENT_TARGET%
echo   Environment: %ENVIRONMENT%
echo   Skip Tests: %SKIP_TESTS%
echo   Skip Build: %SKIP_BUILD%
echo.

REM Check prerequisites
echo [INFO] Checking prerequisites...

if not exist "main_enhanced.py" (
    echo [ERROR] main_enhanced.py not found. Please run this script from the project root.
    pause
    exit /b 1
)

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is required but not installed.
    pause
    exit /b 1
)

pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is required but not installed.
    pause
    exit /b 1
)

echo [SUCCESS] Prerequisites check completed
echo.

REM Setup environment
echo [INFO] Setting up environment for %ENVIRONMENT%...

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [INFO] Created .env file from .env.example
    ) else (
        echo [WARNING] .env file not found and no .env.example to copy from
    )
)

echo [SUCCESS] Environment setup completed
echo.

REM Install dependencies
echo [INFO] Installing Python dependencies...

if not exist "venv" (
    python -m venv venv
    echo [INFO] Created virtual environment
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul

if exist "requirements.txt" (
    pip install -r requirements.txt >nul
    echo [SUCCESS] Python dependencies installed
) else (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)
echo.

REM Run tests
if "%SKIP_TESTS%"=="false" (
    echo [INFO] Running tests...

    if exist "test_enhanced_system.py" (
        python test_enhanced_system.py
        if errorlevel 1 (
            echo [ERROR] Enhanced system tests failed
            pause
            exit /b 1
        ) else (
            echo [SUCCESS] Enhanced system tests passed
        )
    ) else (
        echo [WARNING] No test files found
    )
    echo.
)

REM Build application
if "%SKIP_BUILD%"=="false" (
    echo [INFO] Building application...

    if not exist "dist" mkdir dist
    copy main_enhanced.py dist\ >nul
    xcopy src dist\src\ /E /I /Y >nul
    copy requirements.txt dist\ >nul
    if exist ".env" copy .env dist\ >nul

    echo BUILD_DATE=%date% %time% > dist\version.txt
    echo ENVIRONMENT=%ENVIRONMENT% >> dist\version.txt

    echo [SUCCESS] Application built successfully
    echo.
)

REM Deployment menu
echo Deployment Options:
echo 1. Docker (Build and run container)
echo 2. Cloudflare Workers
echo 3. Local Development Server
echo 4. All Platforms
echo 5. Exit
echo.
set /p choice="Choose deployment option (1-5): "

if "%choice%"=="1" goto :deploy_docker
if "%choice%"=="2" goto :deploy_cloudflare
if "%choice%"=="3" goto :run_local
if "%choice%"=="4" goto :deploy_all
if "%choice%"=="5" goto :exit
echo [ERROR] Invalid choice. Please select 1-5.
goto :exit

:deploy_docker
echo [INFO] Deploying to Docker...

docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed
    pause
    exit /b 1
)

docker build -t tawnia-analytics:latest .
if errorlevel 1 (
    echo [ERROR] Failed to build Docker image
    pause
    exit /b 1
)

echo [SUCCESS] Docker image built successfully

docker stop tawnia-analytics >nul 2>&1
docker rm tawnia-analytics >nul 2>&1

docker run -d --name tawnia-analytics -p 8000:8000 --env-file .env tawnia-analytics:latest
if errorlevel 1 (
    echo [ERROR] Failed to start Docker container
    pause
    exit /b 1
) else (
    echo [SUCCESS] Docker container deployed successfully
    echo [INFO] Application is running at http://localhost:8000
)
goto :success_exit

:deploy_cloudflare
echo [INFO] Deploying to Cloudflare...

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed
    pause
    exit /b 1
)

wrangler --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Wrangler CLI...
    npm install -g wrangler
)

if exist "wrangler.toml" (
    wrangler deploy
    if errorlevel 1 (
        echo [ERROR] Failed to deploy Cloudflare Worker
        pause
        exit /b 1
    ) else (
        echo [SUCCESS] Cloudflare Worker deployed successfully
        echo [INFO] Check Cloudflare dashboard for deployment URLs
    )
) else (
    echo [ERROR] wrangler.toml not found
    pause
    exit /b 1
)
goto :success_exit

:run_local
echo [INFO] Starting local development server...
echo [INFO] Access the application at: http://localhost:8000
echo [INFO] Press Ctrl+C to stop the server
python main_enhanced.py
goto :exit

:deploy_all
call :deploy_docker
echo.
call :deploy_cloudflare
goto :success_exit

:success_exit
echo.
echo [SUCCESS] Deployment process completed successfully!
echo.
pause
goto :exit

:exit
echo.
echo Deployment script finished.
pause
