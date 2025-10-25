@echo off
REM Misty Manufacturing - Desktop App Builder for Windows
REM This script builds the Windows installer

echo ========================================
echo   Misty Manufacturing Desktop Builder
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

REM Check if Yarn is installed
where yarn >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing Yarn...
    npm install -g yarn
)

echo.
echo Step 1: Get NAS IP Address
set /p NAS_IP="Enter your NAS IP address (e.g., 192.168.1.100): "

echo.
echo Step 2: Updating configuration...
cd frontend
echo REACT_APP_BACKEND_URL=http://%NAS_IP%:8001 > .env
echo Configuration updated!

echo.
echo Step 3: Installing dependencies...
call yarn install
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 4: Building React app...
call yarn build
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build React app
    pause
    exit /b 1
)

echo.
echo Step 5: Building Windows installer...
call yarn electron:build --win
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build Windows installer
    pause
    exit /b 1
)

echo.
echo ========================================
echo   BUILD COMPLETE!
echo ========================================
echo.
echo Installer location: frontend\dist\Misty Manufacturing Setup 1.0.0.exe
echo.
echo Next steps:
echo   1. Copy the installer to your client computers
echo   2. Run the installer on each computer
echo   3. Launch the app and login
echo.
pause
