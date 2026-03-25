#!/usr/bin/env bash
set -euo pipefail

name="dockforge-test-node"

docker rm -f "$name" >/dev/null 2>&1 || true
docker build -t "$name" app
container_id=$(docker run -d --rm -p 13000:3000 --name "$name" "$name")
trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT

sleep 2
if curl -fsS http://localhost:13000/health >/dev/null; then
  exit 0
fi

docker logs "$container_id" || true
exit 1
