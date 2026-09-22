from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import psycopg
import os

load_dotenv()

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
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
    conn.commit()
    cursor.close()
    conn.close()


init_db()
print("Server running and connected to Postgres (capstone)")


class AssignmentCreate(BaseModel):
    title: str
    description: str | None = None


@app.get("/")
def root():
    return {
        "name": "Internship Assignment Tracker",
        "version": "1.0",
        "endpoints": ["/assignments"]
    }


@app.post("/assignments", status_code=201)
def create_assignment(assignment: AssignmentCreate):
    if not assignment.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO assignments (title, description) VALUES (%s, %s) RETURNING id, title, description, status, created_at",
        (assignment.title, assignment.description)
    )
    row = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "status": row[3],
        "created_at": row[4].isoformat()
    }


@app.get("/assignments")
def list_assignments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, status, created_at FROM assignments ORDER BY id")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "status": r[3],
            "created_at": r[4].isoformat()
        }
        for r in rows
    ]