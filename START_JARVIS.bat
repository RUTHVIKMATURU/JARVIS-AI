@echo off
title JARVIS AI Assistant
echo.
echo  ============================================
echo   J.A.R.V.I.S  -  AI Voice Assistant v2.0
echo  ============================================
echo.

:: Force UTF-8 output so Unicode characters display correctly
set PYTHONIOENCODING=utf-8
chcp 65001 > nul

:: Use the explicit Python installation to avoid venv/PATH issues
set PYTHON="C:\Users\ruthv\AppData\Local\Programs\Python\Python311\python.exe"

:: Check if Python exists at that path
if not exist %PYTHON% (
    echo [ERROR] Python 3.11 not found at expected path.
    echo Trying system 'python' instead...
    set PYTHON=python
)

:: Install any missing packages silently
echo [*] Checking dependencies...
%PYTHON% -m pip install -q -r requirements.txt

echo [*] Starting JARVIS...
echo.
%PYTHON% jarvis.py

echo.
echo [JARVIS] Session ended.
pause
