@echo off
echo ========================================
echo Resetting Test Database
echo ========================================
echo.

echo Cleaning data\chromadb directory...
if exist "data\chromadb" (
    echo   Deleting all files in data\chromadb...
    del /f /s /q "data\chromadb\*" >nul 2>&1

    echo   Deleting all subdirectories in data\chromadb...
    for /d %%p in ("data\chromadb\*") do rmdir /s /q "%%p" 2>nul

    echo [OK] data\chromadb cleaned
) else (
    mkdir "data\chromadb"
    echo [OK] data\chromadb created
)

echo.
echo Cleaning data\users directory...
if exist "data\users" (
    echo   Deleting all files in data\users...
    del /f /s /q "data\users\*" >nul 2>&1

    echo   Deleting all subdirectories in data\users...
    for /d %%p in ("data\users\*") do rmdir /s /q "%%p" 2>nul

    echo [OK] data\users cleaned
) else (
    mkdir "data\users"
    echo [OK] data\users created
)

echo.
echo ========================================
echo Test database reset completed!
echo ========================================
