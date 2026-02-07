#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_SESSION="${BACKEND_SESSION:-chatbi_backend}"
FRONTEND_SESSION="${FRONTEND_SESSION:-chatbi_frontend}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-8001}"
WITH_DOCKER="${1:-}"

stop_session() {
  local session="$1"
  if screen -ls | grep -q "[.]${session}[[:space:]]"; then
    screen -S "$session" -X quit || true
    echo "Stopped screen session: $session"
  else
    echo "Screen session not found: $session"
  fi
}

kill_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti tcp:"$port" -sTCP:LISTEN || true)"
  if [ -n "$pids" ]; then
    kill $pids || true
    sleep 1
    pids="$(lsof -ti tcp:"$port" -sTCP:LISTEN || true)"
    if [ -n "$pids" ]; then
      kill -9 $pids || true
    fi
    echo "Released port: $port"
  else
    echo "Port already free: $port"
  fi
}

stop_session "$BACKEND_SESSION"
stop_session "$FRONTEND_SESSION"

kill_port "$BACKEND_PORT"
kill_port "$FRONTEND_PORT"

if [ "$WITH_DOCKER" = "--with-docker" ]; then
  echo "Stopping Docker dependencies..."
  (
    cd "$ROOT_DIR/docker"
    COMPOSE_PROJECT_NAME=chatbi docker compose down
  )
fi

echo "Stopped."
