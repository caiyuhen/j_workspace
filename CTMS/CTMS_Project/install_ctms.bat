<<<<<<< HEAD
<<<<<<< HEAD
@echo off
cd /d "%~dp0"
if not exist ".venv" (
  py -3 -m venv .venv
)
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if not exist "runtime_db" mkdir runtime_db
echo Install completed
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
@echo off
cd /d "%~dp0"
if not exist ".venv" (
  py -3 -m venv .venv
)
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if not exist "runtime_db" mkdir runtime_db
echo Install completed
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
