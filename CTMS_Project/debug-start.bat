@echo off

echo Starting CTMS/EDC System Debug Environment...

echo Starting Backend Service...
cd server
start "" npm run dev

timeout /t 5 /nobreak >nul

echo Starting Frontend Service...
cd ..\client
start "" npm run dev

echo.
echo Debug Environment Started!
echo Backend: http://localhost:3666
echo Frontend: http://localhost:5779
echo.
echo Press any key to exit...
pause