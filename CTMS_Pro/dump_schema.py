import subprocess
import os

env = os.environ.copy()
env['PGPASSWORD'] = 'ctms2026'
pg_dump_path = r"D:\Program Files\PostgreSQL\18\bin\pg_dump.exe"
args = [
    pg_dump_path,
    "-U", "ctms_user",
    "-h", "127.0.0.1",
    "-p", "5432",
    "-d", "ctms_pro",
    "--schema-only",
    "--no-owner",
    "--no-privileges"
]

result = subprocess.run(args, env=env, capture_output=True, text=True, encoding='utf-8')
if result.returncode != 0:
    print("Error:", result.stderr)
else:
    lines = result.stdout.splitlines()
    filtered_lines = [line for line in lines if not line.startswith(r'\restrict')]
    with open(r"D:\workspace\CTMS_Pro\database\init\01_schema.sql", "w", encoding="utf-8") as f:
        f.write("\n".join(filtered_lines) + "\n")
    print("Dump completed.")
