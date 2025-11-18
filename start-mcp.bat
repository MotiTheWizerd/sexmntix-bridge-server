@echo off
cd /d "%~dp0"
poetry run python -m src.modules.xcp_server
