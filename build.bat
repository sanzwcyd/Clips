@echo off
REM Builds a single Clips.exe (no console window). Run from this folder.
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconsole --onefile --name Clips --icon assets\icon.ico --add-data "assets;assets" main.py
echo.
echo Done: dist\Clips.exe
pause
