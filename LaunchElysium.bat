@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher\LaunchElysium.ps1"
if errorlevel 1 pause
