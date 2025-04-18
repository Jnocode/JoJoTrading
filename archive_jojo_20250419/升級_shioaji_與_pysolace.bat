@echo off
REM 升級 shioaji 與 pysolace 至最新版，解決合約同步 IndexError 問題

cd /d %~dp0
call venv\Scripts\activate

pip install --upgrade shioaji
pip install --upgrade pysolace

pause
