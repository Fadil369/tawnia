@echo off
echo Starting Tawnia Healthcare Analytics System...
echo.

@echo off
echo Starting Tawnia Healthcare Analytics System...
echo.

:: Check for Node.js in PATH first
node --version >nul 2>&1
if %errorlevel% equ 0 goto :nodejs_found

:: Check for Node.js in common installation locations
if exist "C:\Program Files\nodejs\node.exe" (
    echo Found Node.js in Program Files, adding to PATH...
    set PATH=C:\Program Files\nodejs;%PATH%
    goto :nodejs_found
)

if exist "C:\Program Files (x86)\nodejs\node.exe" (
    echo Found Node.js in Program Files (x86), adding to PATH...
    set PATH=C:\Program Files (x86)\nodejs;%PATH%
    goto :nodejs_found
)

:: Node.js not found
echo ERROR: Node.js is not installed or not found
echo Please install Node.js from https://nodejs.org/
echo Or run setup.bat to configure your environment
pause
exit /b 1

:nodejs_found
:: Display Node.js version
echo Node.js version:
node --version
echo.

:: Check if dependencies are installed
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo.
)

:: Create required directories
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
if not exist "data" mkdir data
if not exist "reports" mkdir reports

echo Starting server...
echo.
echo The application will be available at:
echo   - Main interface: http://localhost:3000
echo   - Enhanced UI:    http://localhost:3000/brainsait
echo   - Health check:   http://localhost:3000/health
echo.
echo Press Ctrl+C to stop the server
echo.

:: Start the server
npm start
