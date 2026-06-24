import sqlite3

db_path = 'd:/workspace/dataPlaform/omop-platform/backend/app/data/omop_platform.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
tables = [row[0] for row in cursor.fetchall()]

print("========== SQLite 数据库概览 ==========")
for table in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"\n📦 表: {table} (共 {count} 条数据)")
    
    if count > 0:
        row = conn.execute(f"SELECT * FROM {table} LIMIT 1").fetchone()
        print("示例数据 (第1条):")
        for key in row.keys():
            val = str(row[key])
            if len(val) > 80:
                val = val[:77] + "..."
            print(f"  - {key}: {val}")

conn.close()
