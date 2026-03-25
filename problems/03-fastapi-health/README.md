# FastAPI Health Service

## Problem description
Containerize the provided FastAPI app and make `/health` return 200.

## Constraints
- Install dependencies from requirements.txt.
- Run with uvicorn on host 0.0.0.0.
- Expose port 8000.

## Test criteria
- API boots successfully.
- `GET /health` returns HTTP 200.
