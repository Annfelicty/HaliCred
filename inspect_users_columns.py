import psycopg2
import json

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="halicred_user",
    password="HaliCred2024!Secure",
    dbname="halicred_db",
)
try:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users'
            ORDER BY ordinal_position
            """
        )
        columns = [row[0] for row in cur.fetchall()]
    print(json.dumps(columns, indent=2))
finally:
    conn.close()
