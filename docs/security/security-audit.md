# /project:security-audit

Run a full security audit of the Docker submission evaluation pipeline.

Steps:
1. Use the security-reviewer subagent to audit these files:
   - backend/app/services/docker_service.py
   - backend/app/routes/submissions.py
   - docker-compose.yml
   - docker-compose.dev.yml
2. Check all Dockerfiles in the repo for `latest` tags and non-root user setup
3. Check backend/.env.example for any real secrets accidentally committed
4. Summarise findings by severity: CRITICAL → HIGH → MEDIUM
5. List all unresolved issues that must be fixed before any public deployment
