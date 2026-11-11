@echo off
setlocal
cd /d "%~dp0\..\.."
echo === AirQR PC Sender ===
set /p SRC=Enter source file or folder path:
py airqr send "%SRC%"
pause