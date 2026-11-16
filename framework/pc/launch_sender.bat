@echo off
setlocal
cd /d "%~dp0\..\.."
echo === AirQR PC Sender (Mobile: PC -^> Phone) ===
echo Your phone does NOT run Python. This PC shows QR codes, phone scans them.
echo.
set /p SRC=Enter source file or folder path:
if "%SRC%"=="" echo No path entered. & pause & exit /b 1
echo.
echo Checking Python deps (only opencv+qrcode needed for --web --broadcast)...
py -c "import cv2, qrcode" 2>nul
if errorlevel 1 (
  echo Installing minimal mobile deps...
  py -m pip install opencv-python "qrcode[pil]" Pillow numpy
)
echo.
echo Starting broadcast. On phone open http://192.168.1.3:8765/index.html -^> Receive -^> Enable Camera
echo If page not reachable, run in a 2nd terminal: python framework/run.py
echo Press ENTER on this PC to start QR loop, Ctrl+C to stop.
echo.
py -m airqr send "%SRC%" --web --broadcast --qr-scale 0.9
pause
