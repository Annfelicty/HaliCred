import json
import psycopg2

CREDS = [
    {"label": "env_credentials", "user": "halicred_user", "password": "HaliCred2024!Secure"},
    {"label": "user_hint_password", "user": "halicred_user", "password": "AKariuki@2006"},
    {"label": "default_user_hint", "user": "user", "password": "AKariuki@2006"},
]

RESULTS = []

for item in CREDS:
    info = {
        "host": "localhost",
        "port": 5432,
        "user": item["user"],
        "password": item["password"],
        "dbname": "halicred_db",
    }
    try:
        conn = psycopg2.connect(**info)
        cur = conn.cursor()
        cur.execute("SELECT CURRENT_DATABASE(), CURRENT_USER")
        result = cur.fetchone()
        cur.close()
        conn.close()
        RESULTS.append({
            "label": item["label"],
            "status": "success",
            "details": {
                "database": result[0],
                "user": result[1],
            }
        })
    except Exception as exc:
        RESULTS.append({
            "label": item["label"],
            "status": "error",
            "error": str(exc),
        })

print(json.dumps(RESULTS, indent=2))
