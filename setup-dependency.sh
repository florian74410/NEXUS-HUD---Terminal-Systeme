#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$ROOT/Dependency/wheels" "$ROOT/Dependency/runtime"
python3 -m pip install --no-index --find-links="$ROOT/Dependency/wheels" --target="$ROOT/Dependency/runtime" -r "$ROOT/requirements.txt"
PYTHONPATH="$ROOT/Dependency/runtime" python3 -c 'from PySide6.QtCore import __version__; from pyside6_qtermwidget import QTermWidget; print("PySide6",__version__,"QTermWidget OK")'
