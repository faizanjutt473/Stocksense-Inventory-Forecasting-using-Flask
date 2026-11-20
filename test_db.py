import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
url = os.getenv("DATABASE_URL")
print("DATABASE_URL:", "mil gaya" if url else "NAHI mila (.env check karein)")

try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("SELECT current_database(), version();")
    row = cur.fetchone()
    if row is None:
        raise RuntimeError("Query returned no rows")
    db, ver = row
    print("Connection successful!")
    print("Database:", db)
    print(ver)
    conn.close()
except Exception as e:
    print("Connection fail:", e)