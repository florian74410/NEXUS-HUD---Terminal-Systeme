#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/nexus-terminal-v13.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=NEXUS Terminal V1.3
Exec=$ROOT/start-nexus.sh
Path=$ROOT
Terminal=false
Categories=System;TerminalEmulator;
EOF
chmod +x "$HOME/.local/share/applications/nexus-terminal-v13.desktop"
echo "Raccourci XFCE installé"
