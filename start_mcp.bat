@echo off
set PYTHONUNBUFFERED=1
cd /d "%~dp0"
"C:\Users\Moti\AppData\Local\pypoetry\Cache\virtualenvs\semantic-bridge-server-ZVw9XJ58-py3.11\Scripts\python.exe" -m src.modules.xcp_server 2>server_error.log
