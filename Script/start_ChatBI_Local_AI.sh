#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_SESSION="${BACKEND_SESSION:-chatbi_backend}"
FRONTEND_SESSION="${FRONTEND_SESSION:-chatbi_frontend}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-8001}"
UV_BIN="${UV_BIN:-$HOME/.local/bin/uv}"

if ! command -v screen >/dev/null 2>&1; then
  echo "Error: screen is required but not installed."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is required but not installed."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Error: Docker daemon is not running."
  exit 1
fi

if ! command -v corepack >/dev/null 2>&1 && ! command -v pnpm >/dev/null 2>&1; then
  echo "Error: corepack or pnpm is required."
  exit 1
fi

if [ ! -x "$UV_BIN" ] && ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv not found. Set UV_BIN or install uv."
  exit 1
fi

wait_port() {
  local port="$1"
  local name="$2"
  for _ in $(seq 1 60); do
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "$name is up on :$port"
      return 0
    fi
    sleep 1
  done
  echo "Error: $name did not start on :$port in time."
  return 1
}

echo "Starting dependencies with Docker Compose..."
(
  cd "$ROOT_DIR"
  make docker up
)

screen -S "$BACKEND_SESSION" -X quit >/dev/null 2>&1 || true
screen -S "$FRONTEND_SESSION" -X quit >/dev/null 2>&1 || true

echo "Starting backend session: $BACKEND_SESSION"
if [ -x "$UV_BIN" ]; then
  screen -dmS "$BACKEND_SESSION" zsh -lc "cd '$ROOT_DIR' && '$UV_BIN' run fastapi run chatbi/main.py --port $BACKEND_PORT"
else
  screen -dmS "$BACKEND_SESSION" zsh -lc "cd '$ROOT_DIR' && uv run fastapi run chatbi/main.py --port $BACKEND_PORT"
fi

echo "Starting frontend session: $FRONTEND_SESSION"
if command -v corepack >/dev/null 2>&1; then
  screen -dmS "$FRONTEND_SESSION" zsh -lc "cd '$ROOT_DIR' && PORT=$FRONTEND_PORT corepack pnpm -C web dev"
else
  screen -dmS "$FRONTEND_SESSION" zsh -lc "cd '$ROOT_DIR' && PORT=$FRONTEND_PORT pnpm -C web dev"
fi

wait_port "$BACKEND_PORT" "Backend"
wait_port "$FRONTEND_PORT" "Frontend"

echo "Started successfully."
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Backend:  http://localhost:$BACKEND_PORT"
echo "Screen sessions:"
screen -ls | grep -E "$BACKEND_SESSION|$FRONTEND_SESSION" || true
