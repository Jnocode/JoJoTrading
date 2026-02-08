@echo off
echo 🚀 Launching JoJo Trader...

:: Ensure Data Directory Exists
if not exist "dist\JoJoTrader\data" mkdir "dist\JoJoTrader\data"

:: Copy Database if exists in root but not in dist
if exist "stocks.db" (
    if not exist "dist\JoJoTrader\stocks.db" (
        echo 📦 Copying existing database...
        copy "stocks.db" "dist\JoJoTrader\stocks.db"
    )
)

:: Copy .env if exists (for legacy support)
if exist ".env" (
    if not exist "dist\JoJoTrader\.env" (
        echo 🔑 Copying environment variables...
        copy ".env" "dist\JoJoTrader\.env"
    )
)

echo ▶️ Starting Application...
cd dist\JoJoTrader
start JoJoTrader.exe
