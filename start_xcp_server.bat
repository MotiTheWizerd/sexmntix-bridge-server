@echo off
REM === FORCE execution via real CMD session (IDE compatibility fix) ===
if "%COMSPEC%"=="" (
    set COMSPEC=%SystemRoot%\System32\cmd.exe
)

REM === Re-run this script inside a real CMD instance if needed ===
if not "%_INSIDE_CMD%"=="1" (
    set _INSIDE_CMD=1
    "%COMSPEC%" /c "%~f0" %*
    goto :EOF
)

REM === Set runtime environment variables ===
set XCP_USER_ID=84e17260-ff03-409b-bf30-0b5ba52a2ab4
set XCP_PROJECT_ID=bc2b08e5-a603-43fc-b15c-b572f56b55b8

REM === Move to directory of the script ===
cd /d "%~dp0"

REM === Use the project’s venv Python ===
"C:\Users\Moti\AppData\Local\pypoetry\Cache\virtualenvs\semantic-bridge-server-ZVw9XJ58-py3.11\Scripts\python.exe" ^
  -m src.modules.xcp_server