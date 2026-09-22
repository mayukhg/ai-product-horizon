#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ ! -f backend/.venv/bin/uvicorn ]]; then
  python3 -m venv backend/.venv
  backend/.venv/bin/pip install -r backend/requirements.txt
fi

if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
fi

bash scripts/setup-postgres.sh
backend/.venv/bin/python backend/scripts/seed_data.py

export PATH="${HOME}/.bun/bin:${PATH}"
if command -v bun >/dev/null 2>&1; then
  bun install
  bun run dev --host 0.0.0.0 --port 5173 &
else
  npm install
  npm run dev -- --host 0.0.0.0 --port 5173 &
fi

backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
