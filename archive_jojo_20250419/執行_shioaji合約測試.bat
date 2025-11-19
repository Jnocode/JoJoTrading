@echo off
REM 啟動 JoJoTrading venv 虛擬環境並執行 test_shioaji_contracts.py

cd /d %~dp0
call venv\Scripts\activate

REM 安裝 shioaji（如已安裝會自動略過）
pip install shioaji

REM 執行測試程式
python test_shioaji_contracts.py

pause
