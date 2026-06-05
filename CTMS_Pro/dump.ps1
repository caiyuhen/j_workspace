$env:PGPASSWORD="ctms2026"
pg_dump.exe -U ctms_user -h 127.0.0.1 -p 5432 -d ctms_pro --schema-only --no-owner --no-privileges -f "D:\workspace\CTMS_Pro\database\init\01_schema.sql"
