#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$ROOT/Dependency/runtime/bin/python" - <<'PYTEST'
from PySide6.QtCore import __version__
from pyside6_qtermwidget import QTermWidget
print('PySide6:', __version__)
print('QTermWidget:', QTermWidget)
print('getText:', hasattr(QTermWidget, 'getText'))
print('selectedText:', hasattr(QTermWidget, 'selectedText'))
PYTEST
