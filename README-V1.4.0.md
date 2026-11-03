# N3XV5 Terminal HUD — V1.4.0 Electric Pulse (DEV)

## Objectif
Refonte de la **couche visuelle Qt**, sans modifier le modèle des sessions, les commandes SSH, tmux, le registre de variables et l’appairage LAN existants. Projet indépendant de N3XV5 HUB.

## Éléments fournis réutilisés
- `assets/electric_pulse/01_Electric_Pulse.svg` : **une instance par terminal** (`ElectricPulseSurface`) ; rendu QtSvg avec vue recadrée, sans flouter ni substituer le terminal QTermWidget.
- `assets/electric_pulse/new/Windows/Console.svg` : surface des panneaux redimensionnables via `QSplitter`.
- `assets/electric_pulse/new/Boxes/Performance_Tall.svg` : colonne gauche réservée, sans raccourcis.
- `assets/electric_pulse/new/Popups/Settings.svg` : contenu des fenêtres avec cadres Carbon.
- `assets/electric_pulse/new/Buttons/*.svg` et `assets/electric_pulse/controls/01_CIRCUIT_CORE/...` : boutons Qt interactifs, sans texte SVG en double.
- Animation Qt légère : rail supérieur du panneau et **terminal actif uniquement**. Pas d'animation continue sur tous les terminaux ni sur tous les boutons.

## Fonctions conservées
Gestionnaire multi-format QSplitter, plusieurs PTY, SSH / tmux, connexions HTTP/FTP/TCP de test, scripts et variables par profil, saisie prédictive Ctrl+Espace, menus contextuels, SmartHover, appairage LAN, opacité et installateur portable.

## Installation
Conserver les wheels PySide6 compatibles avec votre Python dans `Dependency/wheels/` :
```bash
bash setup-dependency.sh
bash start-nexus.sh
```
Les wheels ne sont pas distribuées dans cette archive. Il faut `ssh`, `ssh-keygen`, `tmux` et un système Linux compatible QTermWidget.

## Validation
23 tests Python sans GUI réussis et vérification des scripts effectués. Les rendus SVG, le focus multi-session, l'appairage entre deux machines et le `.deb` restent à valider sur Linux Mint XFCE.

## Sécurité
Aucune découverte LAN n'est activée par cette mise à jour si désactivée dans le profil. Les secrets SSH ne sont pas intégrés aux assets. Aucun changement du HUB ni d'IATB-CLI.
