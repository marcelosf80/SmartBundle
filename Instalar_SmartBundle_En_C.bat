@echo off
title Instalador de SmartBundle Pro (C:\Program Files)
cd /d "%~dp0"

:: Verificar privilegios de Administrador y autoelevar si es necesario
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Solicitando permisos de Administrador para instalar en C:\Program Files...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Ejecutar instalador PowerShell
powershell -ExecutionPolicy Bypass -File "%~dp0install_to_program_files.ps1"

pause
