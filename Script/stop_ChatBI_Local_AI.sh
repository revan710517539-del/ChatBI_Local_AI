#!/usr/bin/env bash
set -euo pipefail

BACKEND_SESSION="chatbi_backend"
FRONTEND_SESSION="chatbi_frontend"

screen -S "$BACKEND_SESSION" -X quit >/dev/null 2>&1 || true
screen -S "$FRONTEND_SESSION" -X quit >/dev/null 2>&1 || true

for port in 8000 8001; do
  pids="$(lsof -ti tcp:$port -sTCP:LISTEN || true)"
  if [ -n "$pids" ]; then
    kill $pids || true
  fi
done

echo "Stopped."

