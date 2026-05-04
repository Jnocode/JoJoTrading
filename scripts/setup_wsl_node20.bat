@echo off
echo ===============================================
echo   Setup: Node.js 20 + OpenClaw in WSL
echo ===============================================
echo.
echo [1/5] Removing old Node.js (if any)...
wsl sudo apt remove -y nodejs npm
wsl sudo apt autoremove -y
echo.

echo [2/5] Adding Node.js 20 Source...
wsl sudo apt update
wsl sudo apt install -y curl
wsl /bin/bash -c "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
echo.

echo [3/5] Installing Node.js 20...
wsl sudo apt install -y nodejs build-essential git
echo.

echo [4/5] Installing Homebrew (If not installed)...
wsl /bin/bash -c "if ! command -v brew &> /dev/null; then NONINTERACTIVE=1 /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"; fi"
echo.

echo [5/5] Configuring Path & Installing OpenClaw...
wsl /bin/bash -c "(echo; echo 'eval \"$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)\"') >> /home/jun/.bashrc"
wsl /bin/bash -c "eval \"$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)\" && sudo npm install -g openclaw"
echo.

echo ===============================================
echo   Setup Complete!
echo   Please run 'wsl openclaw onboard' to configure.
echo ===============================================
pause
