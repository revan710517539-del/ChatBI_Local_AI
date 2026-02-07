#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_SESSION="chatbi_backend"
FRONTEND_SESSION="chatbi_frontend"

if ! command -v screen >/dev/null 2>&1; then
  echo "screen is required"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running"
  exit 1
fi

(
  cd "$ROOT_DIR"
  make docker up
)

screen -S "$BACKEND_SESSION" -X quit >/dev/null 2>&1 || true
screen -S "$FRONTEND_SESSION" -X quit >/dev/null 2>&1 || true

screen -dmS "$BACKEND_SESSION" zsh -lc "cd '$ROOT_DIR' && /Users/revan/.local/bin/uv run fastapi run chatbi/main.py --port 8000"
screen -dmS "$FRONTEND_SESSION" zsh -lc "cd '$ROOT_DIR' && PORT=8001 corepack pnpm -C web dev"

echo "Started."
echo "Frontend: http://localhost:8001"
echo "Backend:  http://localhost:8000"

