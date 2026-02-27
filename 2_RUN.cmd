@echo off
setlocal

call .venv\Scripts\activate
python main.py --check-input

echo.
echo Exit code: %ERRORLEVEL%
pause
