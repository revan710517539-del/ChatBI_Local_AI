#!/usr/bin/env bash
set -euo pipefail

BACKEND_SESSION="chatbi_backend"
FRONTEND_SESSION="chatbi_frontend"

if command -v screen >/dev/null 2>&1; then
  screen -S "$BACKEND_SESSION" -X quit >/dev/null 2>&1 || true
  screen -S "$FRONTEND_SESSION" -X quit >/dev/null 2>&1 || true
fi

for port in 8000 8001 8003; do
  pids="$(lsof -ti tcp:$port -sTCP:LISTEN || true)"
  if [ -n "$pids" ]; then
    kill $pids >/dev/null 2>&1 || true
  fi
done

echo "Stopped."
