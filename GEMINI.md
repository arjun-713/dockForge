# Docker Playground — Gemini / Jules Agent Instructions

> For Claude Code: read CLAUDE.md. For Codex: read AGENTS.md. This file is for Gemini CLI, Jules, and Antigravity.
> All three files contain identical project instructions.

---

## Project Overview

A LeetCode-style platform for practising Docker skills.
Users write Dockerfiles in a browser editor, submit them, and a backend validates whether the containerised app works by running `curl` health checks.

**Stack:**
- Frontend: Next.js (App Router) + TypeScript + Tailwind CSS + Monaco Editor
- Backend: FastAPI (Python 3.12) + Docker SDK for Python
- Storage: SQLite (dev) → PostgreSQL (prod)
- Infrastructure: Docker Compose for local dev, host Docker socket mounted

---

## Repo Structure

```
docker-playground/
├── CLAUDE.md               ← Claude Code instructions
├── AGENTS.md               ← Codex instructions
├── GEMINI.md               ← this file (Gemini / Jules / Antigravity)
├── docker-compose.yml
├── docker-compose.dev.yml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   ├── package.json
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── services/       ← docker_service.py lives here
│   │   └── models/
│   ├── requirements.txt
│   └── Dockerfile
└── problems/
    └── NN-slug/
        ├── problem.json
        ├── README.md
        ├── app/
        ├── test.sh
        └── solution/Dockerfile
```

---

## Critical Setup — Run This First

```bash
cd backend && pip install -r requirements.txt
cd frontend && npm install
docker compose -f docker-compose.dev.yml up
```

Backend: http://localhost:8000 | Frontend: http://localhost:3000

**REQUIRED:** Backend must have Docker socket mounted in docker-compose.dev.yml:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

---

## Running Tests

```bash
cd backend && pytest -v
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
cd problems/01-nginx-static && bash test.sh
```

---

## Non-Negotiable Architecture Rules

1. **Docker socket, not DinD** — mount `/var/run/docker.sock`, never use `privileged: true`
2. **Random ports** — `ports={"80/tcp": None}`, query with `container.reload()`
3. **Always cleanup** — `remove=True` on every submission container + background prune job
4. **Network disabled** — `network_disabled=True` on all submission containers
5. **Resource limits** — `mem_limit="256m"`, `cpu_quota=50000`, build timeout 60s

---

## Code Conventions

### Python
- Type hints everywhere, async/await in all route handlers
- ALL Docker SDK calls in `backend/app/services/docker_service.py` only
- No `subprocess`, no `os.system` — Docker SDK only
- Errors: `{"error": "message", "detail": "..."}`

### TypeScript
- Strict mode on
- API calls via `src/lib/api.ts` only
- Monaco editor only in `src/components/Editor.tsx`
- Types in `src/lib/types.ts`

---

## Problem Format Contract

```
problems/NN-slug/
├── problem.json  → { id, title, difficulty, concepts[], appPort, baseImage }
├── README.md     → problem statement shown to user
├── app/          → pre-written app (DO NOT MODIFY)
├── test.sh       → curl health check, exit 0 = pass
└── solution/Dockerfile
```

---

## Security Rules

- No `privileged: true`, no hardcoded secrets, no `latest` tags
- No user input to shell — Docker SDK only
- Submission containers: non-root user, network disabled, memory capped
- Auto-inject `.dockerignore` before every build

---

## Environment Variables

```bash
# backend/.env
DATABASE_URL=sqlite:///./playground.db
DOCKER_SOCKET=/var/run/docker.sock
MAX_BUILD_TIMEOUT=60
MAX_RUN_TIMEOUT=30
PROBLEMS_DIR=/app/problems

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Do Not

- No `subprocess`/`os.system` in backend
- No `docker system prune` in any automated code
- No modifying `problems/*/app/` files
- No GSAP/Framer Motion — CSS transitions only
- No Redis/queues in MVP
