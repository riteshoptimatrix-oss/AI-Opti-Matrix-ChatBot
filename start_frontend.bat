@echo off
title AI Opti Matrix - PHP Frontend
cd /d "%~dp0"
echo ========================================================
echo Starting AI Opti Matrix PHP Frontend on port 3000...
echo Open in your browser: http://localhost:3000
echo ========================================================
php -S localhost:3000 -t frontend
pause
