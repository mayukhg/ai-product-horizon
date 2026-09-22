#!/usr/bin/env bash
# Stops HorizonAI processes started by start.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

API_PID_FILE=".horizon-ai-api.pid"
WEB_PID_FILE=".horizon-ai-web.pid"

stop_pid_file() {
  local label="$1"
  local pid_file="$2"

  if [[ ! -f "$pid_file" ]]; then
    return 0
  fi

  local pid
  pid="$(cat "$pid_file")"

  if ! kill -0 "$pid" 2>/dev/null; then
    echo "$label process $pid is not running. Cleaning stale PID file."
    rm -f "$pid_file"
    return 0
  fi

  echo "Stopping $label (PID $pid)..."
  kill "$pid" 2>/dev/null || true

  for _ in $(seq 1 10); do
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$pid_file"
      echo "$label stopped."
      return 0
    fi
    sleep 1
  done

  echo "$label did not exit in time, forcing..."
  kill -9 "$pid" 2>/dev/null || true
  rm -f "$pid_file"
  echo "$label stopped."
}

if [[ ! -f "$API_PID_FILE" && ! -f "$WEB_PID_FILE" ]]; then
  echo "No PID files found — HorizonAI doesn't look like it's running via start.sh."
  exit 0
fi

stop_pid_file "API" "$API_PID_FILE"
stop_pid_file "Web" "$WEB_PID_FILE"
echo "Done."
