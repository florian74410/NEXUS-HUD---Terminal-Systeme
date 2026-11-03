N3XV5 TERMINAL HUD 1.3.2 — ETAT DE LIVRAISON
=============================================
Linux : source + paquet .deb installable ; PySide6 et QTermWidget NON inclus.
Windows : EXE NON DISPONIBLE. QTermWidget utilise un pseudo-terminal Unix ; backend ConPTY a developper.

DEPENDANCES PYTHON (seulement sous Dependency/)
PySide6 >=6.7,<7
pyside6-qtermwidget ==0.6.6.11.2
shiboken6, PySide6_Essentials, PySide6_Addons : versions resolues par PySide6.
Placer tous les .whl compatibles Python/architecture dans Dependency/wheels/.
Installer avec ./setup-dependency.sh, cree Dependency/runtime/.
Le lanceur ./start-nexus.sh ne telecharge jamais rien.

DEPENDANCES SYSTEME LINUX (hors de notre controle, gerees par OS)
Python 3 + python3-venv, bibliotheques Qt/X11/Wayland, glibc, libstdc++,
SSH, tmux pour certaines fonctionnalites. Un .deb n'est pas autonome sans OS.

LINUX .DEB : sudo apt install ./N3XV5-Terminal-HUD_1.3.2_amd64.deb
Les fichiers sont dans /opt/n3xv5-terminal/ ; lancer n3xv5-terminal.
Pour preparer Dependency, cd /opt/n3xv5-terminal && sudo ./setup-dependency.sh
Attention : l'installation du .deb ne configure pas le runtime si les wheels sont absents.

LIMITES : aucun test graphique Linux Mint, aucune validation de getText() QTermWidget.
Le SmartHover peut ne pas detecter les mots ; menu de selection disponible en secours.
Ne pas considerer cette version comme finale/stable ni Windows-ready.
