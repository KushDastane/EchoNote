@echo off
echo Starting EchoNote Backend API on http://127.0.0.1:8000 ...
cd /d "%~dp0"
set DISABLE_SQLALCHEMY_CEXT=1
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
