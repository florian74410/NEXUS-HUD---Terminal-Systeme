#!/usr/bin/env bash
set -euo pipefail
# Construire uniquement sur une machine Debian/Ubuntu dédiée à la compilation.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:---check}"
if [[ "$MODE" != "--build" && "$MODE" != "--check" ]]; then echo "Usage: $0 --check | --build"; exit 2; fi
for tool in lb mksquashfs xorriso; do command -v "$tool" >/dev/null || { echo "Manquant: $tool (installer live-build squashfs-tools xorriso)"; exit 1; }; done
if [[ "$MODE" == "--check" ]]; then echo "Outils ISO disponibles. Vérifier les wheels et les pilotes via ./check-portability.sh"; exit 0; fi
[[ "$(id -u)" == 0 ]] || { echo "Exécuter avec sudo uniquement dans une VM de build dédiée"; exit 1; }
[[ -d "$ROOT/Dependency/wheels" ]] && compgen -G "$ROOT/Dependency/wheels/*.whl" >/dev/null || { echo "Dependency/wheels est vide. Construire les wheels avant l'ISO."; exit 1; }
BUILD="$ROOT/ISO/work"
mkdir -p "$BUILD"
cd "$BUILD"
lb config --mode debian --distribution trixie --architectures amd64 --binary-images iso-hybrid --debian-installer none --archive-areas 'main non-free-firmware' --bootappend-live 'boot=live components quiet'
mkdir -p config/package-lists config/includes.chroot/opt/nexus-terminal config/includes.chroot/etc/xdg/autostart
printf '%s\n' 'live-boot' 'live-config' 'task-xfce-desktop' 'lightdm' 'python3' 'python3-venv' 'python3-pip' 'openssh-client' 'ca-certificates' 'libgl1' 'libegl1' 'libxkbcommon-x11-0' 'libxcb-cursor0' > config/package-lists/nexus.list.chroot
# Exclure runtime et fichiers temporaires : venv non portable entre versions Python.
tar -C "$ROOT" --exclude=Dependency/runtime --exclude=ISO --exclude='*.pyc' --exclude=__pycache__ -cf - . | tar -C config/includes.chroot/opt/nexus-terminal -xf -
cat > config/includes.chroot/etc/xdg/autostart/nexus-terminal.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=NEXUS Terminal
Exec=/opt/nexus-terminal/ISO/start-live.sh
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
cat > config/includes.chroot/opt/nexus-terminal/ISO/start-live.sh <<'EOF'
#!/bin/sh
cd /opt/nexus-terminal
if [ ! -x Dependency/runtime/bin/python ]; then
  ./setup-dependency.sh || { echo 'NEXUS: dépendances locales incomplètes' >&2; exit 1; }
fi
exec ./start-nexus.sh
EOF
chmod +x config/includes.chroot/opt/nexus-terminal/ISO/start-live.sh
lb build
printf 'ISO créée : %s\n' "$BUILD"
