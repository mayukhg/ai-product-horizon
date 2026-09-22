#!/usr/bin/env bash
# Starts HorizonAI (FastAPI backend + TanStack Start frontend).
# Usage: ./start.sh [--host 127.0.0.1] [--port 5173] [--api-port 8000] [--skip-seed]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-5173}"
API_PORT="${API_PORT:-8000}"
SKIP_SEED=false

API_PID_FILE=".horizon-ai-api.pid"
WEB_PID_FILE=".horizon-ai-web.pid"
API_LOG_FILE=".horizon-ai-api.log"
WEB_LOG_FILE=".horizon-ai-web.log"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --host) HOST="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --api-port) API_PORT="$2"; shift 2 ;;
    --skip-seed) SKIP_SEED=true; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

is_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null
}

if is_running "$API_PID_FILE" || is_running "$WEB_PID_FILE"; then
  echo "HorizonAI is already running."
  [[ -f "$API_PID_FILE" ]] && echo "  API PID: $(cat "$API_PID_FILE")"
  [[ -f "$WEB_PID_FILE" ]] && echo "  Web PID: $(cat "$WEB_PID_FILE")"
  echo "Run ./stop.sh first if you want to restart."
  exit 0
fi

rm -f "$API_PID_FILE" "$WEB_PID_FILE"

port_listener_pid() {
  local port="$1"
  local pid=""
  if command -v lsof >/dev/null 2>&1; then
    pid="$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | head -1 || true)"
  elif command -v fuser >/dev/null 2>&1; then
    pid="$(fuser -n tcp "$port" 2>/dev/null | awk '{print $1}' | head -1 || true)"
  fi
  printf '%s' "$pid"
}

for check_port in "$API_PORT" "$PORT"; do
  existing_pid="$(port_listener_pid "$check_port")"
  if [[ -n "$existing_pid" ]]; then
    echo "Port $check_port is already in use (PID $existing_pid). Stop it first or run ./stop.sh." >&2
    exit 1
  fi
done

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required but was not found on PATH. Install Node.js 18+." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required but was not found on PATH." >&2
  exit 1
fi

PKG_RUNNER="npm"
if command -v bun >/dev/null 2>&1 && [[ -f "bun.lock" ]]; then
  PKG_RUNNER="bun"
fi

if [[ ! -d "node_modules" ]]; then
  echo "Installing frontend dependencies with $PKG_RUNNER..."
  if [[ "$PKG_RUNNER" == "bun" ]]; then bun install; else npm install; fi
fi

if [[ ! -f "backend/.venv/bin/uvicorn" ]]; then
  echo "Creating Python virtual environment..."
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install -r backend/requirements.txt
fi

if [[ ! -f "backend/.env" ]]; then
  cp backend/.env.example backend/.env
fi

if [[ ! -f ".env" ]]; then
  cp .env.example .env
fi

echo "Ensuring PostgreSQL is configured..."
bash scripts/setup-postgres.sh

if [[ "$SKIP_SEED" == false ]]; then
  echo "Seeding database and golden dataset..."
  backend/.venv/bin/python backend/scripts/seed_data.py
fi

echo "Starting FastAPI on http://$HOST:$API_PORT ..."
nohup backend/.venv/bin/uvicorn app.main:app --host "$HOST" --port "$API_PORT" --app-dir backend > "$API_LOG_FILE" 2>&1 &
API_PID=$!
echo "$API_PID" > "$API_PID_FILE"

for _ in $(seq 1 30); do
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "API failed to start. Last log lines:" >&2
    tail -n 30 "$API_LOG_FILE" >&2 || true
    rm -f "$API_PID_FILE"
    exit 1
  fi
  if curl -fsS "http://$HOST:$API_PORT/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "http://$HOST:$API_PORT/health" >/dev/null 2>&1; then
  echo "API did not become healthy in time. Last log lines:" >&2
  tail -n 30 "$API_LOG_FILE" >&2 || true
  kill "$API_PID" 2>/dev/null || true
  rm -f "$API_PID_FILE"
  exit 1
fi

if ! kill -0 "$API_PID" 2>/dev/null; then
  echo "API process exited during startup (port $API_PORT may already be in use). Last log lines:" >&2
  tail -n 30 "$API_LOG_FILE" >&2 || true
  rm -f "$API_PID_FILE"
  exit 1
fi

echo "Starting frontend on http://$HOST:$PORT ..."
if [[ "$PKG_RUNNER" == "bun" ]]; then
  nohup bun run dev --host "$HOST" --port "$PORT" > "$WEB_LOG_FILE" 2>&1 &
else
  nohup npm run dev -- --host "$HOST" --port "$PORT" > "$WEB_LOG_FILE" 2>&1 &
fi
WEB_PID=$!
echo "$WEB_PID" > "$WEB_PID_FILE"

for _ in $(seq 1 30); do
  if ! kill -0 "$WEB_PID" 2>/dev/null; then
    echo "Frontend failed to start. Last log lines:" >&2
    tail -n 30 "$WEB_LOG_FILE" >&2 || true
    kill "$API_PID" 2>/dev/null || true
    rm -f "$API_PID_FILE" "$WEB_PID_FILE"
    exit 1
  fi
  if grep -q "ready in\|Local:" "$WEB_LOG_FILE" 2>/dev/null; then
    break
  fi
  sleep 1
done

echo ""
echo "HorizonAI is running."
echo "  Cockpit:  http://$HOST:$PORT"
echo "  API:      http://$HOST:$API_PORT/health"
echo "  API PID:  $API_PID (log: $API_LOG_FILE)"
echo "  Web PID:  $WEB_PID (log: $WEB_LOG_FILE)"
echo "Stop with: ./stop.sh"
echo "Guide:     docs/HOW_TO_USE.md"
