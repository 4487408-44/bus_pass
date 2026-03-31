@echo off

cd /d C:\Project

echo Starting server...
start cmd /k py -3.12 server.py

timeout /t 2 >nul

echo Opening browser...
start http://localhost:8082