# Internship Assignment Tracker

## The Problem

During a fast-paced backend internship, I completed multiple technical assignments 
quickly, but had no simple way to track what I'd built, summarize it professionally, 
or produce something shareable — I was writing project summaries and reports 
manually from scratch every time.

## My 10x Claim

Turns "manually writing a project summary and report" (30-60 minutes per project) 
into "log the assignment, get an AI summary and a PDF report in under 2 minutes."

## Architecture

[client]
|
v
FastAPI (auth + assignments + summary + PDF endpoints)
|
+---> Supabase Auth (login/signup, protects all assignment routes)
|
+---> Postgres (stores assignments — title, description, status)
|
+---> OpenRouter LLM (generates a one-sentence professional summary)
|
+---> ReportLab (generates a PDF report of all tracked assignments)


## The 5 Concepts

| Concept | Where it lives |
|---|---|
| API endpoints | `src/main.py` — FastAPI routes with validation and status codes |
| Database | Postgres (via Docker), `src/main.py` — assignments table, survives restarts |
| Authentication | `src/main.py` — Supabase login/signup, protected routes via `verify_token` |
| LLM integration | `src/main.py` `/assignments/{id}/summarize`, `prompts/summarize-v1.md` |
| PDF report | `src/main.py` `/assignments/report`, built with ReportLab |

## Run it (one command)

**Requirements:** Docker Desktop

1. Clone the repo:
```bash
git clone https://github.com/dishaagowda/flyrank-10x-solution.git
cd flyrank-10x-solution
```

2. Copy `.env.example` to `.env` and fill in your own Supabase and OpenRouter keys:
```bash
cp .env.example .env
```

3. Start everything:
```bash
docker compose up
```

4. In a separate terminal, seed demo data:
```bash
python3 seed.py
```

## 5-Minute Demo Path

1. Sign up a user:
```bash
curl -X POST http://localhost:8001/auth/signup -H "Content-Type: application/json" -d '{"email":"demo@example.com","password":"password123"}'
```

2. Log in and save the token:
```bash
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login -H "Content-Type: application/json" -d '{"email":"demo@example.com","password":"password123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

3. List assignments (seeded data should appear):
```bash
curl http://localhost:8001/assignments -H "Authorization: Bearer $TOKEN"
```

4. Get an AI summary for assignment #1:
```bash
curl -X POST http://localhost:8001/assignments/1/summarize -H "Authorization: Bearer $TOKEN"
```

5. Download the PDF report:
```bash
curl -o report.pdf http://localhost:8001/assignments/report -H "Authorization: Bearer $TOKEN"
open report.pdf
```

## Known Limitations

- No edit/delete endpoints for assignments yet — create and list only.
- The PDF report includes all assignments with no filtering by status or date.
- Single-user model — no per-user assignment isolation (any logged-in user sees all assignments).

## Future Ideas

- Filter the PDF report by status or date range.
- Per-user assignment isolation.
- A simple frontend instead of curl-only interaction.