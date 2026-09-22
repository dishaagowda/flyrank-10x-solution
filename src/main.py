from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client
import psycopg
import os

load_dotenv()

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
security = HTTPBearer()


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


class AuthRequest(BaseModel):
    email: str
    password: str


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        return user_response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.get("/")
def root():
    return {
        "name": "Internship Assignment Tracker",
        "version": "1.0",
        "endpoints": ["/assignments", "/auth/signup", "/auth/login"]
    }


# ---------- AUTH ROUTES ----------

@app.post("/auth/signup", status_code=201)
def signup(auth: AuthRequest):
    if not auth.email or not auth.password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    try:
        result = supabase.auth.sign_up({"email": auth.email, "password": auth.password})
        return {"user": result.user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login")
def login(auth: AuthRequest):
    if not auth.email or not auth.password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    try:
        result = supabase.auth.sign_in_with_password({"email": auth.email, "password": auth.password})
        return {"access_token": result.session.access_token}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")


# ---------- ASSIGNMENT ROUTES (PROTECTED) ----------

@app.post("/assignments", status_code=201)
def create_assignment(assignment: AssignmentCreate, user=Depends(verify_token)):
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
def list_assignments(user=Depends(verify_token)):
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