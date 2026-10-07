# AgentFlow AI

**Autonomous AI agents for real-world workflows.**

A multi-agent platform that takes a high-level objective, plans it as a task graph, picks and runs
tools, observes results, retries and recovers from failures, asks a human before risky actions,
and returns a structured, traceable result.

> **Status: Phase 1 of 13 (project foundation).**
> Implemented: backend skeleton, config, structured logging with request IDs, error envelope,
> health/readiness endpoints, PostgreSQL connection, Alembic migrations, React status page, Docker.
> Everything else (agents, tools, workflow engine, approvals, evaluation) is **NOT IMPLEMENTED YET**
> and arrives in later phases. See [architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md).

## Quick start (Windows PowerShell)

Run all of these from the **project root** (the folder containing `docker-compose.yml`):

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }   # then edit the password in .env (2 places)
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
docker compose up -d db
.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
.venv\Scripts\python.exe -m pytest backend\tests -v
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir backend --app-dir backend --host 127.0.0.1 --port 8000
```

Frontend, in a second terminal inside `frontend`:

```powershell
npm.cmd install
npm.cmd run dev
```

- API health: http://127.0.0.1:8000/api/v1/health
- API docs: http://127.0.0.1:8000/docs
- UI: http://localhost:5173

Everything in Docker instead: `docker compose up --build` from the project root.
