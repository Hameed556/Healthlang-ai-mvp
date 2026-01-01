import psycopg2
import sys

HOST = 'database-1.cpswuqk4saqw.eu-north-1.rds.amazonaws.com'
PORT = 5432
DBNAME = 'healthlang'
USER = 'Hameed13'
PASSWORD = 'Abdulhameed123'
SSLMODE = 'require'

try:
    conn = psycopg2.connect(host=HOST, port=PORT, dbname=DBNAME, user=USER, password=PASSWORD, sslmode=SSLMODE)
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, is_active, created_at FROM public.users ORDER BY created_at DESC LIMIT 20")
    rows = cur.fetchall()
    print('USERS:')
    if not rows:
        print('(no rows)')
    for r in rows:
        print(r)
    cur.close()
    conn.close()
except Exception as e:
    print('ERROR connecting or querying:', e)
    sys.exit(1)
