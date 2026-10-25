#!/usr/bin/env bash
# Checks prerequisites for running WLAN AttackLab inside Kali.
# Safe to rerun; makes no changes to the system.
set -uo pipefail

ok=0
warn=0

check_cmd() {
  local name="$1" hint="$2"
  if command -v "$name" >/dev/null 2>&1; then
    echo "[OK]      $name found ($(command -v "$name"))"
    ok=$((ok+1))
  else
    echo "[WARNING] $name not found. $hint"
    warn=$((warn+1))
  fi
}

echo "== WLAN AttackLab environment check =="
check_cmd python3 "Install with: sudo apt install -y python3 python3-venv python3-pip"
check_cmd node "Install with: sudo apt install -y nodejs npm"
check_cmd npm "Install with: sudo apt install -y npm"
check_cmd aircrack-ng "Install with: sudo apt install -y aircrack-ng (wireless experiments will use demonstration mode until installed)"
check_cmd tshark "Install with: sudo apt install -y tshark (WPA handshake pre-check will use demonstration mode until installed)"
check_cmd capinfos "Install with: sudo apt install -y wireshark-common"
check_cmd msfconsole "Install with: sudo apt install -y metasploit-framework (Metasploit experiment will use demonstration mode until installed)"

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
if [ -f "$BACKEND_DIR/.env" ]; then
  echo "[OK]      backend/.env present"
  ok=$((ok+1))
else
  echo "[WARNING] backend/.env missing. Run: cp backend/.env.example backend/.env"
  warn=$((warn+1))
fi

echo
echo "Summary: $ok OK, $warn warning(s)."
echo "Warnings do not block the app -- missing tools fall back to demonstration mode."
exit 0
