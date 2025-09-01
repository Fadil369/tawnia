@echo off
echo ========================================
echo Tawnia Healthcare Analytics Setup
echo ========================================

:: Check for Node.js in common locations
set NODE_PATH=""
if exist "C:\Program Files\nodejs\node.exe" (
    set NODE_PATH="C:\Program Files\nodejs"
) else if exist "C:\Program Files (x86)\nodejs\node.exe" (
    set NODE_PATH="C:\Program Files (x86)\nodejs"
) else (
    where node >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Node.js not found!
        echo Please install Node.js from https://nodejs.org/
        echo Common installation paths:
        echo - C:\Program Files\nodejs\
        echo - C:\Program Files (x86)\nodejs\
        pause
        exit /b 1
    )
)

:: Add Node.js to PATH if found but not in PATH
if NOT "%NODE_PATH%"=="" (
    echo Found Node.js at %NODE_PATH%
    set PATH=%NODE_PATH%;%PATH%
)

:: Verify Node.js installation
echo Checking Node.js installation...
node --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Could not run Node.js
    pause
    exit /b 1
)

npm --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Could not run npm
    pause
    exit /b 1
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

:: Install dependencies
echo Installing dependencies...
npm install
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

:: Run validation tests
echo Running validation tests...
node test-manual.js
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Some tests failed. Check output above.
    echo You can still continue, but some features may not work correctly.
    pause
)

echo ========================================
echo Setup complete!
echo ========================================
echo.
echo To start the server:
echo   start.bat
echo.
echo To run manual tests:
echo   node test-manual.js
echo.
echo To run automated tests:
echo   npm test
echo.
pause
