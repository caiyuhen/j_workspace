import os

schema_file = r"D:\workspace\CTMS_Pro\database\init\01_schema.sql"

with open(schema_file, "r", encoding="utf-8") as f:
    content = f.read()

header = """-- ================================================================
-- CTMS Pro 数据库初始化脚本
-- 临床试验管理系统 (Clinical Trial Management System)
-- (基于本地数据库 pg_dump 自动生成)
-- ================================================================

-- 启用核心扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

"""

if "CREATE EXTENSION" not in content:
    with open(schema_file, "w", encoding="utf-8") as f:
        f.write(header + content)
    print("Added header and extensions to 01_schema.sql")
else:
    print("Already has extensions.")
