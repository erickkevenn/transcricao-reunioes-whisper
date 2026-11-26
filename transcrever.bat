@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title Transcrever reuniões
python "%~dp0sistema\transcrever.py" %*
echo.
pause
