@echo off
title AI Opti Matrix - Python Backend
cd /d "%~dp0"
echo ========================================================
echo Starting AI Opti Matrix API Backend (Gemini Flash Engine)...
echo URL: http://localhost:8000
echo ========================================================
.\backend\myenv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --app-dir backend
pause
