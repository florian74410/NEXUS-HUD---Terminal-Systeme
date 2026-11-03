N3XV5 Terminal HUD v1.3.4 — ElectroBlue

Changements : contrôles hexagonaux bleu électrique avec transition de survol animée; dock latéral SSH / clés / sessions; génération Ed25519 via ssh-keygen; réglage opacité par terminal (65-100%).

Installation locale : copier les wheels Linux déjà téléchargés dans Dependency/wheels, puis bash setup-dependency.sh et bash start-nexus.sh.
Dépendances Python : PySide6 >=6.7,<7 ; pyside6-qtermwidget ==0.6.6.11.2 ; versions résolues sur Mint : PySide6 6.11.2, shiboken6 6.11.2, PySide6_Essentials 6.11.2, PySide6_Addons 6.11.2.
Système : python3.12, tmux, openssh-client, bibliothèques graphiques Qt.

ATTENTION : l'opacité dépend de la prise en charge du backend QTermWidget et du compositeur XFCE. La solution palette peut être opaque selon le rendu natif. Tests graphiques Linux Mint non effectués. La génération SSH nécessite une vérification interactive locale.
