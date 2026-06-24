@echo off
REM Quick start from the repo folder (same as double-clicking ELYSIUM.py).
cd /d "%~dp0"
python -u ELYSIUM.py
if errorlevel 1 pause
