#!/usr/bin/env bash
set -euo pipefail
DEB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/nexus-terminal_1.0.0-1_all.deb"
if [ ! -f "$DEB" ]; then
  echo "Place le fichier .deb à côté de ce script." >&2; exit 1
fi
sudo apt install "$DEB"
backup="$HOME/.local/share/nexus-terminal/legacy-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup"
for shortcut in "$HOME/.local/share/applications/nexus-terminal.desktop" "$HOME/Bureau/nexus-terminal.desktop" "$HOME/Desktop/nexus-terminal.desktop"; do
  if [ -f "$shortcut" ] && grep -Eq '^Exec=.*nexus-terminal' "$shortcut"; then
    cp -p "$shortcut" "$backup/$(basename "$(dirname "$shortcut")")-nexus-terminal.desktop"
    sed -i 's|^Exec=.*|Exec=/usr/bin/nexus-terminal|' "$shortcut"
    sed -i 's|^Name=.*|Name=NEXUS Terminal v1.0|' "$shortcut"
  fi
done
# Preserve old executable as a backup only if it is a regular user-owned file.
legacy="$HOME/.local/bin/nexus-terminal"
if [ -f "$legacy" ] && [ ! -L "$legacy" ] && [ -O "$legacy" ]; then
  mv "$legacy" "$backup/nexus-terminal-legacy"
fi
hash -r
command -v update-desktop-database >/dev/null && update-desktop-database "$HOME/.local/share/applications" || true
printf 'Installation OK. Raccourcis corrigés, sauvegarde : %s\n' "$backup"
printf 'Lancer : /usr/bin/nexus-terminal\n'
