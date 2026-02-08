#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/.run-logs"
BACKEND_SESSION="chatbi_backend"
FRONTEND_SESSION="chatbi_frontend"
BACKEND_LOG="$LOG_DIR/chatbi_backend.log"
FRONTEND_LOG="$LOG_DIR/chatbi_frontend.log"

mkdir -p "$LOG_DIR"

if ! command -v screen >/dev/null 2>&1; then
  echo "screen is required"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running"
  exit 1
fi

# cleanup old listeners/sessions
for port in 8000 8001 8003; do
  pids="$(lsof -ti tcp:$port -sTCP:LISTEN || true)"
  if [ -n "$pids" ]; then
    kill $pids >/dev/null 2>&1 || true
  fi
done

screen -S "$BACKEND_SESSION" -X quit >/dev/null 2>&1 || true
screen -S "$FRONTEND_SESSION" -X quit >/dev/null 2>&1 || true

(
  cd "$ROOT_DIR"
  make docker up
)

if [ -x "/Users/revan/.local/bin/uv" ]; then
  BACKEND_CMD="/Users/revan/.local/bin/uv run fastapi run chatbi/main.py --port 8000"
else
  BACKEND_CMD="python3 -m uvicorn chatbi.main:app --host 0.0.0.0 --port 8000"
fi

: >"$BACKEND_LOG"
: >"$FRONTEND_LOG"

screen -dmS "$BACKEND_SESSION" zsh -lc "cd '$ROOT_DIR' && $BACKEND_CMD >> '$BACKEND_LOG' 2>&1"

# wait backend bind ok before starting frontend (avoid port race)
for _ in {1..40}; do
  if lsof -iTCP:8000 -sTCP:LISTEN -n -P >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! lsof -iTCP:8000 -sTCP:LISTEN -n -P >/dev/null 2>&1; then
  echo "Backend failed to start on 8000"
  tail -n 120 "$BACKEND_LOG" || true
  exit 1
fi

# force frontend on 8001
screen -dmS "$FRONTEND_SESSION" zsh -lc "cd '$ROOT_DIR' && env PORT=8001 corepack pnpm -C web dev >> '$FRONTEND_LOG' 2>&1"

for _ in {1..50}; do
  if lsof -iTCP:8001 -sTCP:LISTEN -n -P >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! lsof -iTCP:8001 -sTCP:LISTEN -n -P >/dev/null 2>&1; then
  echo "Frontend failed to start on 8001"
  tail -n 120 "$FRONTEND_LOG" || true
  exit 1
fi

echo "Started."
echo "Frontend: http://localhost:8001"
echo "Backend:  http://localhost:8000"
echo "Backend log:  $BACKEND_LOG"
echo "Frontend log: $FRONTEND_LOG"
