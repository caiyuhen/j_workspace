import sqlite3

db_path = r'd:\workspace\dataPlaform\omop-platform\backend\data\omop_platform.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print('Tables in database:', tables)

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"Table {table} has {cursor.fetchone()[0]} rows")

conn.close()