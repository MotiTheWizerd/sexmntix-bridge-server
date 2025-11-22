@echo off
set XCP_USER_ID=84e17260-ff03-409b-bf30-0b5ba52a2ab4
set XCP_PROJECT_ID=bc2b08e5-a603-43fc-b15c-b572f56b55b8
cd /d "%~dp0"
"C:\Users\Moti\AppData\Local\pypoetry\Cache\virtualenvs\semantic-bridge-server-ZVw9XJ58-py3.11\Scripts\python.exe" -m src.modules.xcp_server
