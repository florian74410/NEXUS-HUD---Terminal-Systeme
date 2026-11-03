#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -d "$ROOT/Dependency/runtime/PySide6" ]]; then
    echo 'Dépendances manquantes : bash setup-dependency.sh' >&2
    exit 2
fi
PYTHONPATH="$ROOT/Dependency/runtime${PYTHONPATH:+:$PYTHONPATH}" python3 - <<'PYTEST'
from PySide6.QtCore import __version__
from pyside6_qtermwidget import QTermWidget
print('PySide6:', __version__)
print('QTermWidget:', QTermWidget)
print('getText:', hasattr(QTermWidget, 'getText'))
print('selectedText:', hasattr(QTermWidget, 'selectedText'))
PYTEST
