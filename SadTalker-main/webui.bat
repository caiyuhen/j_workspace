@echo on

set HTTP_PROXY=
set HTTPS_PROXY=
set ALL_PROXY=

IF NOT EXIST venv (
"D:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe" -m venv venv
) ELSE (
echo venv folder already exists, skipping creation...
)
call .\venv\Scripts\activate.bat

set PYTHON="venv\Scripts\Python.exe"
echo venv %PYTHON%

%PYTHON% Launcher.py

echo.
echo Launch unsuccessful. Exiting.
pause