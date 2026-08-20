@echo off
title Desinstalador de Menu SmartBundle
cd /d "%~dp0"
echo ==================================================
echo   Desinstalando menu contextual de SmartBundle...
echo ==================================================
python sb_context_menu.py uninstall
pause
