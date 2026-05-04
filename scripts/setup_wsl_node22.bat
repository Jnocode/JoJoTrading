@echo off
echo ===============================================
echo   Setup: Node.js 22 + OpenClaw in WSL
echo ===============================================
echo.
echo [1/5] Removing old Node.js (v20)...
wsl sudo apt remove -y nodejs npm
wsl sudo apt autoremove -y
echo.

echo [2/5] Adding Node.js 22 Source...
wsl sudo apt update
wsl sudo apt install -y curl
wsl /bin/bash -c "curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -"
echo.

echo [3/5] Installing Node.js 22...
wsl sudo apt install -y nodejs build-essential git
echo.

echo [4/5] Verifying Node Version...
wsl node -v
echo.

echo [5/5] Re-installing OpenClaw...
wsl sudo npm install -g openclaw
echo.

echo [6/6] Verifying OpenClaw...
wsl openclaw --version
echo.

echo ===============================================
echo   Setup Complete!
echo   Please run 'wsl openclaw onboard' to configure.
echo ===============================================
pause
