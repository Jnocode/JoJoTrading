@echo off
echo ===============================================
echo   FULL Setup: OpenClaw + Homebrew in WSL
echo ===============================================
echo.
echo [1/5] Installing System Dependencies (Node, Git, Build Tools)...
wsl sudo apt update
wsl sudo apt install -y nodejs npm build-essential curl git
echo.

echo [2/5] Installing Homebrew (Required for OpenClaw Skills)...
echo NOTE: You may need to press ENTER if prompted by Homebrew.
wsl /bin/bash -c "NONINTERACTIVE=1 /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
echo.

echo [3/5] Configuring Homebrew Path...
wsl /bin/bash -c "(echo; echo 'eval \"$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)\"') >> /home/jun/.bashrc"
wsl /bin/bash -c "eval \"$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)\""
echo.

echo [4/5] Installing OpenClaw CLI...
wsl sudo npm install -g openclaw
echo.

echo [5/5] Launching OpenClaw Onboard...
echo This will now install skills using the newly installed tools.
wsl /bin/bash -c "eval \"$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)\" && openclaw onboard --install-daemon"
echo.

echo ===============================================
echo   Setup Complete!
echo   If you see 'brew not found' errors, restart your terminal.
echo ===============================================
pause
