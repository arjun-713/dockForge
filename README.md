# DockForge

DockForge is a LeetCode-style platform for practicing Dockerfile skills.

## Current Status

This repository currently contains:
- Frontend scaffold (Next.js + TypeScript + Tailwind)
- Backend scaffold (FastAPI + pydantic-settings)
- Docker Compose files for dev and production-style local runs
- CI baseline for lint/type checks and backend tests
- Phase 2 problem-bank APIs:
  - `GET /api/problems`
  - `GET /api/problems/{id}`
- Seed problem bank under `problems/01-*` to `problems/03-*`
- Structured docs under `docs/`

## Quick Start

```bash
# backend deps
cd backend && pip install -r requirements.txt

# frontend deps
cd ../frontend && npm install

# run local dev stack
cd .. && docker compose -f docker-compose.dev.yml up --build
```

Frontend: http://localhost:3000
Backend: http://localhost:8000
