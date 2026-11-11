@echo off
setlocal
cd /d "%~dp0\..\.."
echo === AirQR PC Receiver ===
set /p DEST=Enter destination folder (default .\received):
if "%DEST%"=="" set DEST=.\received
py airqr receive --dest "%DEST%"
pause