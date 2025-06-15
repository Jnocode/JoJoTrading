@echo off
cd /d "d:\AI_Park\Workspace\dev_projects\web\jojo_trading"
echo Starting JoJo Trading Enhanced DCF Analysis System...
echo Port: 8508
echo URL: http://localhost:8508
python -m streamlit run main_app.py --server.port 8508
pause
