#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/DEBIAN" "$STAGE/opt/n3xv5-terminal" "$STAGE/usr/bin" "$STAGE/usr/share/applications"
cp -a "$ROOT"/. "$STAGE/opt/n3xv5-terminal/"
rm -f "$STAGE/opt/n3xv5-terminal/"*.deb
cat > "$STAGE/DEBIAN/control" <<'EOF'
Package: n3xv5-terminal-hud
Version: 1.4.1~dev1
Section: utils
Priority: optional
Architecture: amd64
Maintainer: N3XV5 Development <noreply@example.invalid>
Depends: python3 (>= 3.10), python3-venv, tmux, openssh-client
Description: N3XV5 Terminal HUD source runtime launcher
 Neon Qt terminal workspace. Requires local wheels in Dependency/wheels.
EOF
cat > "$STAGE/usr/bin/n3xv5-terminal" <<'EOF'
#!/usr/bin/env bash
exec /opt/n3xv5-terminal/start-nexus.sh "$@"
EOF
chmod 755 "$STAGE/usr/bin/n3xv5-terminal"
cat > "$STAGE/usr/share/applications/n3xv5-terminal.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=N3XV5 Terminal HUD
Exec=n3xv5-terminal
Terminal=false
Categories=System;TerminalEmulator;
EOF
chmod 755 "$STAGE/opt/n3xv5-terminal/"*.sh
OUT="${1:-$ROOT/N3XV5-Terminal-HUD_1.4.1~dev1_amd64.deb}"
dpkg-deb --build --root-owner-group "$STAGE" "$OUT"
echo "Paquet cree: $OUT"
