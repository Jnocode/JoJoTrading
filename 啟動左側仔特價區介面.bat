@echo off
chcp 65001 > nul
cd /d "%~dp0modules"
call ..\venv\Scripts\activate
python left_value_zone_gui.py
pause
