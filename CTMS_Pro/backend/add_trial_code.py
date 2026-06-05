import subprocess
import os

env = os.environ.copy()
env["PGPASSWORD"] = ""
result = subprocess.run([
    r"D:\Program Files\PostgreSQL\18\bin\psql.exe", 
    "-U", "postgres", 
    "-d", "ctms_pro", 
    "-c", "ALTER TABLE trials ADD COLUMN IF NOT EXISTS trial_code VARCHAR(100);"
], env=env, capture_output=True, text=True)

if result.returncode == 0:
    print("SUCCESS:", result.stdout)
else:
    print("ERROR:", result.stderr)
