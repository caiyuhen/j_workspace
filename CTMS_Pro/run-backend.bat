<<<<<<< HEAD
@echo off
chcp 65001 >nul
cd /d "%~dp0backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8898
=======
@echo off
chcp 65001 >nul
cd /d "%~dp0backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8898
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
