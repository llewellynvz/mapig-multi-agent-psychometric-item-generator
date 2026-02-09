#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

BACKEND_CMD=${BACKEND_CMD:-"uvicorn app.main:app --reload --host ${BACKEND_HOST} --port ${BACKEND_PORT}"}
FRONTEND_CMD=${FRONTEND_CMD:-"npm run dev -- --port ${FRONTEND_PORT}"}

cleanup() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${FRONTEND_PID:-}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

(
  cd "$ROOT_DIR"
  echo "Starting backend: $BACKEND_CMD"
  eval "$BACKEND_CMD"
) &
BACKEND_PID=$!

(
  cd "$ROOT_DIR/frontend"
  echo "Starting frontend: $FRONTEND_CMD"
  eval "$FRONTEND_CMD"
) &
FRONTEND_PID=$!

wait -n "$BACKEND_PID" "$FRONTEND_PID"
