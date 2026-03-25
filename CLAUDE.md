# Docker Playground — Agent Instructions

> This file is read by Claude Code, Codex, and Gemini CLI (Antigravity) on every session.
> It is the single source of truth for how to work on this project.

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
├── CLAUDE.md               ← this file
├── AGENTS.md               ← symlink or copy of CLAUDE.md (Codex compatibility)
├── docker-compose.yml      ← production compose
├── docker-compose.dev.yml  ← dev compose with hot reload
├── frontend/               ← Next.js app
│   ├── src/
│   │   ├── app/            ← App Router pages
│   │   ├── components/     ← React components
│   │   └── lib/            ← API client, utils
│   ├── package.json
│   └── Dockerfile
├── backend/                ← FastAPI app
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── services/       ← docker_service.py lives here
│   │   └── models/
│   ├── requirements.txt
│   └── Dockerfile
└── problems/               ← problem bank
    ├── 01-nginx-static/
    │   ├── problem.json
    │   ├── README.md
    │   ├── app/
    │   ├── test.sh
    │   └── solution/Dockerfile
    └── ...
```

---

## Critical Setup — Run This First

```bash
# 1. Install backend deps
cd backend && pip install -r requirements.txt

# 2. Install frontend deps
cd frontend && npm install

# 3. Start dev environment
docker compose -f docker-compose.dev.yml up

# 4. Backend runs on http://localhost:8000
# 5. Frontend runs on http://localhost:3000
```

**IMPORTANT:** The backend container must have the Docker socket mounted:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```
Without this, `docker_service.py` cannot build or run submission containers.

---

## Running Tests

```bash
# Backend unit tests
cd backend && pytest -v

# Frontend type check
cd frontend && npx tsc --noEmit

# Frontend lint
cd frontend && npm run lint

# Test a specific problem's test.sh manually
cd problems/01-nginx-static && bash test.sh
```

Always run `pytest` after touching `backend/app/services/docker_service.py`.
Always run `tsc --noEmit` after touching any TypeScript file.

---

## Architecture Decisions (do not reverse without discussion)

### 1. Docker socket mounting — NOT Docker-in-Docker
The backend talks to the host Docker daemon via `/var/run/docker.sock`.
**Never** use `privileged: true` or `dind` (Docker-in-Docker). The socket approach is safer and simpler.

### 2. Random host port assignment
Submission containers use `ports={"<app_port>/tcp": None}` — Docker picks a random host port.
The backend queries the assigned port via `container.reload()` then runs the health check.
**Never** hardcode a host port for submissions — it causes conflicts.

### 3. Mandatory container cleanup
Every submission container must be run with `remove=True` OR explicitly stopped and removed.
A `cleanup_job` runs every 5 minutes via `asyncio` background task.
**Never** leave containers running after evaluation completes.

### 4. Network isolation for submissions
Submission containers run with `network_disabled=True`.
The health check uses `localhost` with the assigned port — this still works because the port is bound on the host.
**Never** give submission containers internet access.

### 5. Resource limits on submissions
All submission containers get: `mem_limit="256m"`, `cpu_quota=50000` (50% of 1 core).
Build timeout is 60 seconds. Run+test timeout is 30 seconds.
These are non-negotiable for security.

---

## Code Conventions

### Python (backend)
- Python 3.12, type hints everywhere
- Use `async/await` for all FastAPI route handlers
- Use `docker` SDK (not subprocess) for all Docker operations
- Error responses use the pattern: `{"error": "message", "detail": "..."}`
- Environment variables loaded via `pydantic-settings` BaseSettings class
- File: `backend/app/services/docker_service.py` owns ALL Docker interaction — do not put Docker SDK calls anywhere else

### TypeScript (frontend)
- Strict mode enabled (`"strict": true` in tsconfig)
- Use `fetch` with the custom `apiClient` in `src/lib/api.ts` — never raw fetch in components
- Monaco editor is in `src/components/Editor.tsx` — do not import Monaco anywhere else
- Problem types are defined in `src/lib/types.ts` — add new types there only

### File naming
- Python: `snake_case.py`
- TypeScript: `PascalCase.tsx` for components, `camelCase.ts` for utils
- Problem folders: `NN-slug-name/` with zero-padded numbers (01, 02, ...)

---

## Problem Format Contract

Every problem folder MUST have exactly:

```
problems/NN-slug/
├── problem.json     ← metadata
├── README.md        ← shown to user in UI
├── app/             ← pre-written app code (user does NOT modify this)
├── test.sh          ← validator (must exit 0 = pass, 1 = fail)
└── solution/
    └── Dockerfile   ← reference solution (hidden from user)
```

`problem.json` schema:
```json
{
  "id": "01-nginx-static",
  "title": "Static Site with Nginx",
  "difficulty": "easy",
  "concepts": ["FROM", "COPY", "EXPOSE"],
  "appPort": 80,
  "baseImage": "nginx:alpine"
}
```

`test.sh` contract:
- Must accept the container name as `$1` OR use `localhost` with a hardcoded test port
- Must exit 0 on pass, 1 on fail
- Must clean up any containers it creates
- Must not assume internet access

---

## Security Rules — NEVER Violate These

- **No `privileged: true`** on any container, ever
- **No hardcoded secrets** — use `.env` files + `pydantic-settings`
- **No `latest` tags** in production Dockerfiles — pin versions
- **No user input** passed directly to shell commands — use the Docker SDK only
- **Submission containers run as non-root** — enforce via `user="nobody"` in `containers.run()`
- **Build context auto-gets a `.dockerignore`** injected by `docker_service.py` before every build

---

## Environment Variables

```bash
# backend/.env (never commit this)
DATABASE_URL=sqlite:///./playground.db
DOCKER_SOCKET=/var/run/docker.sock
MAX_BUILD_TIMEOUT=60
MAX_RUN_TIMEOUT=30
SUBMISSION_MEMORY_LIMIT=256m
PROBLEMS_DIR=/app/problems

# frontend/.env.local (never commit this)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Common Workflows

### Adding a new problem
1. Create `problems/NN-slug/` folder
2. Write the pre-built app in `app/`
3. Write `problem.json` (follow schema above)
4. Write `README.md` (problem statement + constraints + test criteria)
5. Write `test.sh` (validate with curl, exit 0/1)
6. Write reference `solution/Dockerfile`
7. Test manually: `cd problems/NN-slug && bash test.sh`

### Debugging a broken submission evaluation
1. Check `backend/app/services/docker_service.py` — all Docker logic is here
2. Run `docker ps -a` to see if containers are leaking
3. Run `docker logs <container_name>` to see app startup errors
4. Check that `/var/run/docker.sock` is mounted in the backend container

### Updating frontend problem display
- Problem list: `src/app/page.tsx`
- Problem detail + editor: `src/app/problems/[id]/page.tsx`
- Submission result display: `src/components/ResultPanel.tsx`

---

## What NOT to Do

- Do not add GSAP, Framer Motion, or heavy animation libraries — use CSS transitions only
- Do not add a message queue or Redis for MVP — direct HTTP is fine
- Do not modify files inside `problems/*/app/` — these are the read-only app stubs users containerise
- Do not run `docker system prune` in any automated code — it would nuke unrelated containers
- Do not use `subprocess` or `os.system` anywhere in the backend — use the Docker SDK
