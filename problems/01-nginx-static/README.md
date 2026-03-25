# Static Site with Nginx

## Problem description
Containerize the provided static website using Nginx.

## Constraints
- Use an Nginx base image.
- Copy site files into the correct served directory.
- Expose port 80.

## Test criteria
- Container starts successfully.
- `GET /` returns HTTP 200.
