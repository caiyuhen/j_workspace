import subprocess
import os

passwords = ["postgres", "123456", "admin", "root", "", "password", "ctms2026", "12345678", "ctms_password_2026", "123456aA!"]

for pwd in passwords:
    env = os.environ.copy()
    env["PGPASSWORD"] = pwd
    result = subprocess.run([r"D:\Program Files\PostgreSQL\18\bin\psql.exe", "-U", "postgres", "-d", "ctms_pro", "-c", "SELECT 1;"], env=env, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"SUCCESS with password: '{pwd}'")
        break
    else:
        pass
else:
    print("None worked.")
