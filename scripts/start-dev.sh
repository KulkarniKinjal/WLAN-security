#!/usr/bin/env bash
# Starts backend (uvicorn) and frontend (vite) together. Ctrl+C stops both.
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

cleanup() {
  echo
  echo "Stopping..."
  [ -n "${BACKEND_PID:-}" ] && kill "$BACKEND_PID" 2>/dev/null
  [ -n "${FRONTEND_PID:-}" ] && kill "$FRONTEND_PID" 2>/dev/null
  wait 2>/dev/null
  exit 0
}
trap cleanup INT TERM

if [ ! -f "$BACKEND_DIR/.env" ]; then
  echo "backend/.env not found. Run scripts/setup-kali.sh first (or cp backend/.env.example backend/.env)."
  exit 1
fi

cd "$BACKEND_DIR"
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend started (PID $BACKEND_PID) -- http://0.0.0.0:8000"

cd "$FRONTEND_DIR"
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!
echo "Frontend started (PID $FRONTEND_PID) -- http://0.0.0.0:5173"

echo "Press Ctrl+C to stop both."
wait
