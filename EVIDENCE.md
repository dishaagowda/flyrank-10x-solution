# Evidence

## Ingestion / API endpoints
`POST /assignments` accepts title + description, stores it, returns 201.
curl -i -X POST http://localhost:8001/assignments -H "Authorization: Bearer $TOKEN" -d '{"title":"Database assignment","description":"SQLite to Postgres swap"}'
HTTP/1.1 201 Created
{"id":1,"title":"Database assignment","description":"SQLite to Postgres swap","status":"not_started","created_at":"2026-09-22T11:10:49.318813+00:00"}


## Database persistence
`GET /assignments` after a server restart still returns the same records — confirmed 
across multiple sessions during this project's build.

## Authentication
Without a token: curl -i -X POST http://localhost:8001/assignments -d '{"title":"Test"}'
HTTP/1.1 401 Unauthorized

With a valid token: curl -i -X POST http://localhost:8001/assignments -H "Authorization: Bearer $TOKEN" -d '{"title":"Test"}'
HTTP/1.1 201 Created

## LLM integration

curl -i -X POST http://localhost:8001/assignments/1/summarize -H "Authorization: Bearer $TOKEN"
HTTP/1.1 200 OK
{"assignment_id":1,"summary":"Migrated application data layer from SQLite to PostgreSQL, ensuring schema compatibility and performance improvements."}

## PDF report

curl -o report.pdf http://localhost:8001/assignments/report -H "Authorization: Bearer $TOKEN"
Produced a 1806-byte valid PDF opening in Preview, showing all tracked assignments with 
title, status, description, and created date.

## Full stack, one command

docker compose up

Builds the app image, starts Postgres with a healthcheck, waits for the database to be 
healthy before starting the API, and both come up cleanly with no manual steps — 
confirmed working end to end.
