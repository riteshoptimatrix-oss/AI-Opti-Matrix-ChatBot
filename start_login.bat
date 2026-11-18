@echo off
title Google Login - Playwright Session
cls
echo ===================================================================
echo   OPT MATRIX - GOOGLE PERSISTENT LOGIN SETUP
echo ===================================================================
echo.
echo [1] Launching visible Chromium browser for Google Login...
echo.
cd /d "%~dp0backend"
myenv\Scripts\python.exe gemini_session.py login
echo.
echo ===================================================================
pause
