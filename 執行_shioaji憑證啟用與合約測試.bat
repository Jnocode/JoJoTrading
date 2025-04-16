@echo off
REM 啟動 JoJoTrading venv 虛擬環境並執行憑證啟用與合約測試

cd /d %~dp0
call venv\Scripts\activate

REM 安裝 shioaji（如已安裝會自動略過）
pip install shioaji

REM 提示用戶輸入憑證路徑與密碼
set /p CAPATH=請輸入你的憑證檔案完整路徑（如 C:\Users\你的帳號\Downloads\sinopac.pfx）:
set /p CAPASS=請輸入你的憑證密碼（通常是身分證字號）:

REM 產生臨時 Python 檔案
echo import shioaji as sj > temp_ca_test.py
echo api = sj.Shioaji() >> temp_ca_test.py
echo api.activate_ca(ca_path=r"%CAPATH%", ca_passwd=r"%CAPASS%") >> temp_ca_test.py
echo print("憑證啟用完成，開始下載合約...") >> temp_ca_test.py
echo api.login(api_key="你的API_KEY", secret_key="你的SECRET_KEY") >> temp_ca_test.py
echo api.fetch_contracts(api.Contracts.Stocks) >> temp_ca_test.py
echo print("合約型態:", type(api.Contracts.Stocks)) >> temp_ca_test.py
echo print("合約長度:", len(list(api.Contracts.Stocks))) >> temp_ca_test.py
echo for i, contract in enumerate(api.Contracts.Stocks): >> temp_ca_test.py
echo.    print("code:", getattr(contract, "code", None), "name:", getattr(contract, "name", None), "category:", getattr(contract, "category", None)) >> temp_ca_test.py
echo.    if i > 20: break >> temp_ca_test.py

REM 執行臨時 Python 檔案
python temp_ca_test.py

REM 刪除臨時檔
del temp_ca_test.py

pause
