@echo off
echo Starting Label Management System...

:: Set the project directory
set PROJECT_DIR=C:\Users\Bartender3\brady_label_automation

:: Create a log file
set LOG_FILE=%PROJECT_DIR%\server.log

:: Log start time
echo [%date% %time%] Starting server... >> %LOG_FILE%

:: Change to the project directory
cd /d %PROJECT_DIR%
if %errorlevel% neq 0 (
    echo Error: Could not change to project directory >> %LOG_FILE%
    pause
    exit /b 1
)

:: Activate the virtual environment
call env\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Could not activate virtual environment >> %LOG_FILE%
    pause
    exit /b 1
)

:: Start the Django server
echo [%date% %time%] Running Django server... >> %LOG_FILE%
python manage.py runserver 0.0.0.0:8000 >> %LOG_FILE% 2>&1

:: If the server stops, log it
echo [%date% %time%] Server stopped >> %LOG_FILE%

:: Wait before closing
pause