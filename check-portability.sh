#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo '=== NEXUS PORTABILITY CHECK ==='
uname -srm
python3 --version 2>&1 || true
for tool in python3 pip3 git ssh; do command -v "$tool" || true; done
if compgen -G "$ROOT/Dependency/wheels/*.whl" >/dev/null; then echo 'Wheels : présents'; else echo 'Wheels : ABSENTS (kit non autonome hors ligne)'; fi
if [[ -x "$ROOT/Dependency/runtime/bin/python" ]]; then "$ROOT/Dependency/runtime/bin/python" -c 'import PySide6, pyside6_qtermwidget; print("Runtime Qt : OK")' || true; else echo 'Runtime : non préparé'; fi
if [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then echo 'Session graphique : présente'; else echo 'Session graphique : absente'; fi
printf 'Configuration personnelle : %s\n' "${XDG_CONFIG_HOME:-$HOME/.config}"
