#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux manquant. Installer : sudo apt install tmux" >&2
  exit 1
fi
if [ ! -d .venv ]; then python3 -m venv .venv; fi
. .venv/bin/activate
python -m pip install -r requirements.txt
exec python nexus_workspace.py
