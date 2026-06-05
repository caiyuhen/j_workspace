import psycopg2
conn = psycopg2.connect(dbname='ctms_pro', user='ctms_user', password='ctms2026', host='127.0.0.1')
cur = conn.cursor()
try:
    cur.execute("UPDATE users SET last_login_ip = CAST('127.0.0.1' AS INET)")
    print("OK")
except Exception as e:
    print(e)
