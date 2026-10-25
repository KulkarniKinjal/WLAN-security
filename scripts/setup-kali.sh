#!/usr/bin/env bash
# One-time setup inside Kali. Safe to rerun (idempotent where possible).
# Does NOT run as root for the app itself -- only apt install needs sudo.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "== Installing system packages (requires sudo) =="
sudo apt update
sudo apt install -y python3-venv python3-pip nodejs npm aircrack-ng wireshark-common tshark metasploit-framework || {
  echo "One or more packages failed to install. The app still runs in demonstration mode for any missing tool.";
}

echo "== Setting up backend virtual environment =="
cd "$BACKEND_DIR"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created backend/.env from the example -- edit LAB_TARGET_HOST before running the Metasploit module."
fi

mkdir -p data/uploads data/reports fixtures/wordlists fixtures/captures

echo "== Setting up frontend =="
cd "$FRONTEND_DIR"
npm install

echo
echo "Setup complete. Next: run scripts/doctor.sh, then scripts/start-dev.sh"
