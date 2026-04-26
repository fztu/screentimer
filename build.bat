@echo off
pyinstaller --onefile --windowed --name screentimer screentimer/main.py
echo.
echo Build complete: dist\screentimer.exe
pause
