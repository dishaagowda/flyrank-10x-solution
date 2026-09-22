# My 10x Solution

## What is the problem you are solving?

During a fast-paced backend internship, I completed multiple technical assignments 
quickly, but had no simple way to track what I'd built, summarize it professionally, 
or produce something shareable — I was writing project summaries and reports manually 
from scratch every time. Anyone juggling multiple fast-moving technical projects faces 
the same friction: the work gets done, but documenting and presenting it eats real time.

## How did you implement your solution?

I built the Internship Assignment Tracker: a small backend service where you log an 
assignment (title + description), and the system stores it, generates a one-sentence 
AI summary of it, and produces a downloadable PDF report of everything tracked so far.

The 5 concepts implemented (no swaps):
1. **API endpoints** — FastAPI routes with input validation and correct status codes
2. **Database** — Postgres, running in Docker, data survives restarts
3. **Authentication** — Supabase login/signup, protected routes via bearer tokens
4. **LLM integration** — OpenRouter-based summary generation with schema-validated 
   JSON output
5. **PDF report** — ReportLab-generated report of all tracked assignments

To run it: git clone https://github.com/dishaagowda/flyrank-10x-solution.git
cd flyrank-10x-solution
cp .env.example .env # fill in your own Supabase + OpenRouter keys
docker compose up
python3 seed.py # in a separate terminal

Full demo steps are in the repo's README