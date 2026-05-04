@echo off
echo ==========================================
echo   Setting up OpenClaw in WSL (Linux)
echo ==========================================
echo.
echo [1/4] Updating Package Lists...
wsl sudo apt update
echo.

echo [2/4] Installing Node.js and npm...
wsl sudo apt install -y nodejs npm
echo.

echo [3/4] Installing OpenClaw CLI...
wsl sudo npm install -g openclaw
echo.

echo [4/4] Verifying Installation...
wsl openclaw --version
echo.

echo Setup Complete! You can now run 'wsl openclaw onboard' to configure.
echo.
pause
