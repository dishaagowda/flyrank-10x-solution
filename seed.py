import psycopg
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT NOT NULL DEFAULT 'not_started',
        created_at TIMESTAMPTZ DEFAULT now()
    )
""")

cursor.execute("SELECT COUNT(*) FROM assignments")
count = cursor.fetchone()[0]

if count == 0:
    cursor.executemany(
        "INSERT INTO assignments (title, description, status) VALUES (%s, %s, %s)",
        [
            ("Database assignment", "SQLite to Postgres swap", "not_started"),
            ("Docker containerization", "Ran Postgres and the API together with docker compose", "not_started"),
            ("Auth integration", "Added Supabase login, signup, and protected routes", "not_started"),
        ]
    )
    conn.commit()
    print("Seeded 3 demo assignments")
else:
    print(f"Database already has {count} assignments, skipping seed")

cursor.close()
conn.close()
