# Node.js Express Health API

## Problem description
Containerize the provided Express API so its `/health` endpoint is reachable.

## Constraints
- Install production dependencies.
- Start the server with a deterministic command.
- Expose port 3000.

## Test criteria
- Container starts within a few seconds.
- `GET /health` returns HTTP 200 and JSON body.
