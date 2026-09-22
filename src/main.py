from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from supabase import create_client, Client
from openai import OpenAI
import psycopg
import os
import json
import re
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

load_dotenv()

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
security = HTTPBearer()

llm_client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
    timeout=30.0,
)

with open("prompts/summarize-v1.md", "r") as f:
    SUMMARY_PROMPT = f.read()


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


def extract_json(raw_text):
    text = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            text = brace_match.group(0)
    return json.loads(text)


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


# ---------- LLM SUMMARY ROUTE ----------

@app.post("/assignments/{assignment_id}/summarize")
def summarize_assignment(assignment_id: int, user=Depends(verify_token)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title, description FROM assignments WHERE id = %s", (assignment_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Assignment {assignment_id} not found")

    title, description = row
    user_content = f"Title: {title}\nDescription: {description or 'No description provided'}"

    response = llm_client.chat.completions.create(
        model=os.getenv("LLM_MODEL"),
        temperature=0.3,
        messages=[
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": user_content}
        ]
    )

    raw_text = response.choices[0].message.content
    print("RAW SUMMARY OUTPUT:", raw_text)
    try:
        data = extract_json(raw_text)
        summary = data.get("summary")
        if not summary:
            raise ValueError("No summary field in response")
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=422, detail="Could not generate a valid summary")

    return {"assignment_id": assignment_id, "summary": summary}

@app.get("/assignments/report")
def generate_report(user=Depends(verify_token)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, status, created_at FROM assignments ORDER BY id")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    output_path = "output/assignment_report.pdf"
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Internship Assignment Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    if not rows:
        elements.append(Paragraph("No assignments recorded yet.", styles["Normal"]))
    else:
        for row in rows:
            assignment_id, title, description, status, created_at = row
            elements.append(Paragraph(f"<b>{title}</b>", styles["Heading2"]))
            elements.append(Paragraph(f"Status: {status}", styles["Normal"]))
            elements.append(Paragraph(f"Description: {description or 'No description'}", styles["Normal"]))
            elements.append(Paragraph(f"Created: {created_at.strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
            elements.append(Spacer(1, 16))

    doc.build(elements)

    return FileResponse(output_path, media_type="application/pdf", filename="assignment_report.pdf")