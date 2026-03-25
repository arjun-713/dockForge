# project_overview.md

Quick reference for any AI agent or new contributor.
Full instructions → CLAUDE.md / AGENTS.md / GEMINI.md

---

## What This Is

Docker Playground = LeetCode for Docker.

User opens a problem → reads what the app does → writes a Dockerfile in the browser editor → clicks Submit → backend builds + runs the container → curls the health endpoint → returns pass/fail.

No app code writing. Only Dockerfile writing.

---

## The Core Loop (one sentence each)

1. **Frontend** serves the problem list and Monaco editor
2. **User** writes a Dockerfile
3. **Frontend** POSTs `{ problem_id, dockerfile_content }` to `/api/submit`
4. **Backend** writes Dockerfile to a temp dir alongside the problem's app files
5. **Backend** calls Docker SDK to build the image (60s timeout)
6. **Backend** runs the container with random port, network disabled, memory capped
7. **Backend** curls `localhost:<random_port>/<health_path>` and checks for HTTP 200
8. **Backend** tears down the container and returns `{ passed: bool, logs: str }`
9. **Frontend** shows pass/fail + build logs

---

## Five Starter Problems (SOLO Dockerfile category)

| # | Problem | Port | Health endpoint | New concept |
|---|---------|------|-----------------|-------------|
| 01 | Static HTML → Nginx | 80 | `/` | FROM, COPY, EXPOSE |
| 02 | Node.js Express API | 3000 | `/health` | WORKDIR, npm install, CMD |
| 03 | FastAPI (Python) | 8000 | `/health` | pip install, uvicorn |
| 04 | Python CLI tool | none | stdout check | ENTRYPOINT, no port |
| 05 | File upload service (Node) | 3000 | `/health` | VOLUME, persistent data |

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `backend/app/services/docker_service.py` | All Docker SDK interaction |
| `backend/app/routes/submissions.py` | POST /api/submit handler |
| `frontend/src/components/Editor.tsx` | Monaco editor wrapper |
| `frontend/src/app/problems/[id]/page.tsx` | Problem detail page |
| `problems/NN-slug/test.sh` | Curl validator per problem |

---

## Gotchas (highest signal, read these first)

- Backend needs `/var/run/docker.sock` mounted — check docker-compose first if submissions fail
- Submission containers get `network_disabled=True` — health check uses host port, not container network
- Port is random — always `container.reload()` before reading `container.ports`
- Temp dirs are cleaned by `tempfile.TemporaryDirectory()` context manager — don't fight it
- `.dockerignore` is auto-injected — never rely on the user providing one
