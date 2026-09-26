@echo off
REM ===== CaughtBot one-time setup for Windows =====
echo Setting up CaughtBot... this takes a few minutes.
echo.
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo ============================================================
echo  Setup done!
echo  1. Create a file named  .env  in this folder with:
echo         GROQ_API_KEY=your_key_from_console.groq.com
echo  2. Then double-click  run_windows.bat  to start the app.
echo ============================================================
pause
