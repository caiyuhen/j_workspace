<<<<<<< HEAD
import psycopg2
conn = psycopg2.connect(dbname='ctms_pro', user='ctms_user', password='ctms2026', host='127.0.0.1')
cur = conn.cursor()
cur.execute("UPDATE roles SET name = '超级管理员' WHERE code = 'SUPER_ADMIN'")
conn.commit()
print("OK")
=======
import psycopg2
conn = psycopg2.connect(dbname='ctms_pro', user='ctms_user', password='ctms2026', host='127.0.0.1')
cur = conn.cursor()
cur.execute("UPDATE roles SET name = '超级管理员' WHERE code = 'SUPER_ADMIN'")
conn.commit()
print("OK")
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
