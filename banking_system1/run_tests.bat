@echo off
REM Quick Test Runner for Windows
REM Run this from your project root directory

echo.
echo ========================================
echo   BANKING SYSTEM - QUICK TEST
echo ========================================
echo.

REM Test 1: Intent Parser
echo [1/2] Testing Intent Parser...
python tests\quick_test.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Intent parser test failed!
    pause
    exit /b 1
)

echo.
echo [2/2] Checking if database exists...
if exist banking_system.db (
    echo Database found! Running viewer...
    python view_database.py --overview
) else (
    echo.
    echo No database found yet.
    echo Run 'python chat.py' first to create data.
)

echo.
echo ========================================
echo   Tests Complete!
echo ========================================
echo.
echo What you can do next:
echo   - python chat.py          (Create data)
echo   - python view_database.py (View all data)
echo   - python web_app.py       (Start web interface)
echo.
pause
