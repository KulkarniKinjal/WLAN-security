#!/usr/bin/env bash
# Stops any backend/frontend dev processes left running from start-dev.sh
# if you started it with '&' directly instead of through the script.
set -uo pipefail

pkill -f "uvicorn app.main:app" 2>/dev/null && echo "Stopped backend (uvicorn)." || echo "No backend process found."
pkill -f "vite" 2>/dev/null && echo "Stopped frontend (vite)." || echo "No frontend process found."
