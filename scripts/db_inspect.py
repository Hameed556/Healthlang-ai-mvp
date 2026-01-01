import psycopg2

HOST = 'database-1.cpswuqk4saqw.eu-north-1.rds.amazonaws.com'
PORT = 5432
DBNAME = 'healthlang'
USER = 'Hameed13'
PASSWORD = 'Abdulhameed123'
SSLMODE = 'require'

conn = None
try:
    conn = psycopg2.connect(host=HOST, port=PORT, dbname=DBNAME, user=USER, password=PASSWORD, sslmode=SSLMODE)
    cur = conn.cursor()

    cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
    tables = cur.fetchall()
    print('TABLES:')
    for t in tables:
        print(f"{t[0]}.{t[1]}")

    try:
        cur.execute("SELECT 'conversations' AS table_name, (SELECT COUNT(*) FROM public.conversations) AS cnt UNION ALL SELECT 'messages', (SELECT COUNT(*) FROM public.messages)")
        counts = cur.fetchall()
        print('\nCOUNTS:')
        for r in counts:
            print(f"{r[0]}: {r[1]}")
    except Exception as e:
        print('\nCOUNTS: error', e)

    cur.close()
except Exception as e:
    print('ERROR connecting or querying:', e)
finally:
    if conn:
        conn.close()
