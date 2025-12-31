import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv('bemo/.env')

try:
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    print("Successfully connected to the database!")
    
    with conn.cursor() as cur:
        cur.execute("SELECT now()")
        res = cur.fetchall()
        conn.commit()
        print(f"Current time from DB: {res[0][0]}")
        
except Exception as e:
    print(f"Connection failed: {e}")
