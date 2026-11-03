#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
if [[ -x "$ROOT/Dependency/runtime/bin/python" ]]; then
  exec "$ROOT/Dependency/runtime/bin/python" "$ROOT/nexus_workspace.py" "$@"
fi
if [[ -d "$ROOT/Dependency/runtime/PySide6" ]]; then
  export PYTHONPATH="$ROOT/Dependency/runtime${PYTHONPATH:+:$PYTHONPATH}"
  exec python3 "$ROOT/nexus_workspace.py" "$@"
fi
echo 'Dépendances manquantes : exécute bash setup-dependency.sh' >&2
exit 2
