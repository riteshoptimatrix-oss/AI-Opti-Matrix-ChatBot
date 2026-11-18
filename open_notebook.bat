@echo off
title Gemini Notebook - Persistent Session
cls
echo ===================================================================
echo   OPT MATRIX - OPEN GEMINI NOTEBOOK (PERSISTENT SESSION)
echo ===================================================================
echo.
echo [1] Reusing persistent session...
echo [2] Navigating to Gemini Notebook...
echo.
cd /d "%~dp0backend"
myenv\Scripts\python.exe gemini_session.py notebook
echo.
echo ===================================================================
pause
