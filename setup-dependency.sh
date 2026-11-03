#!/usr/bin/env bash
# Portable and repeatable runtime: never install PySide6 globally.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEELS="$ROOT/Dependency/wheels"
RUNTIME="$ROOT/Dependency/runtime"
mkdir -p "$WHEELS" "$ROOT/Dependency"
OFFLINE=0
case "${1:-}" in
  '') ;;
  --offline) OFFLINE=1 ;;
  *) printf 'Usage: bash setup-dependency.sh [--offline]\n' >&2; exit 2 ;;
esac
python3 -m pip --version >/dev/null || {
  echo 'Python pip absent : installe python3-pip sans modifier Python système.' >&2
  exit 2
}
STAGING="$(mktemp -d "$ROOT/Dependency/.runtime-new.XXXXXXXX")"
cleanup() { rm -rf "$STAGING"; }
trap cleanup EXIT
# Prefer cached wheels. Fallback to a single download (unless --offline).
if ! python3 -m pip install --disable-pip-version-check --no-index \
  --find-links="$WHEELS" --target="$STAGING" -r "$ROOT/requirements.txt"; then
  if [[ "$OFFLINE" == 1 ]]; then
    echo 'Wheels locales insuffisantes. Copie les fichiers .whl dans Dependency/wheels.' >&2
    exit 3
  fi
  echo 'Téléchargement des wheels manquantes vers Dependency/wheels (aucune installation globale)…'
  python3 -m pip download --disable-pip-version-check --only-binary=:all: \
    --dest "$WHEELS" -r "$ROOT/requirements.txt"
  rm -rf "$STAGING"; mkdir -p "$STAGING"
  python3 -m pip install --disable-pip-version-check --no-index \
    --find-links="$WHEELS" --target="$STAGING" -r "$ROOT/requirements.txt"
fi
PYTHONPATH="$STAGING" python3 -c \
  'from PySide6.QtCore import __version__; from pyside6_qtermwidget import QTermWidget; print("PySide6",__version__,"QTermWidget OK")'
# Preserve the previously running runtime until the new one passes import checks.
OLD="$ROOT/Dependency/.runtime-previous"
rm -rf "$OLD"
if [[ -d "$RUNTIME" ]]; then mv "$RUNTIME" "$OLD"; fi
mv "$STAGING" "$RUNTIME"
rm -rf "$OLD"
trap - EXIT
printf 'Dépendances prêtes sous : %s\n' "$RUNTIME"
