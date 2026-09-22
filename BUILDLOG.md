# Build Log

## Where AI helped
- Scaffolding each endpoint's structure (FastAPI routes, Pydantic models) following 
  patterns I'd already built by hand in earlier internship assignments.
- Writing the ReportLab PDF generation code, since this was new to me.
- Debugging several real mistakes I made while pasting code — including a missing 
  return statement that caused /summarize to return null, and a load_dotenv() 
  call positioned after code that needed the environment variables it loads.

## Where AI was wrong or I had to fix things myself
- Several code-paste errors happened where blocks landed in the wrong place in the 
  file (before functions they depended on were defined). I had to trace these by 
  reading tracebacks and file contents carefully.
- A Postgres image version mismatch caused an early container crash (fixed by pinning 
  to postgres:16 instead of latest).

## What I changed after reviewing AI output
- Removed a no-op database update line in the summarize endpoint that didn't actually 
  do anything useful.
- Simplified the PDF report layout after the first version.

I understand every line of this code — the database queries, the auth flow, the LLM 
call and its JSON parsing, and the PDF generation — because I reused patterns I'd 
already built by hand in three prior internship assignments (database, auth, LLM 
triage endpoint).