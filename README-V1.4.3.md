# V1.4.3 — Retour aux vrais visuels NOVA Terminal 1.0 (NeonGlass)

## Source du style

Récupération à partir de **NEXUS-Terminal-v1.0.0-Installateur.zip** (le paquet original V1.0.0 du Terminal), et de ses deux interfaces `nexus_workspace.py` et `nexus_terminal.py`.

- `nexus_terminal.py` V1 : `NeonPanel` Qt vectoriel à huit coins biseautés, dégradé sombre (#051d2f → #03101d → #041a28), halos par traits QPainter, liseré cyan, petit routing décoratif.
- `nexus_workspace.py` V1 : couleurs et QSS de fond (#020b16), barres/cadres/onglets, circuits HeaderCircuit, boutons hexagonaux sans barre XFCE.
- Tous les composants sont des **QWidget réellement actifs**. Aucun grand SVG ne couvre l'espace d'un QTermWidget.

## Adaptation à la structure actuelle

`nexus_nova1_style.py` isole la couche visuelle : `NeonGlassPanel`, `NovaOneTerminalFrame`, `NovaOneButton`, `NovaOneCloseButton`, `show_notice`.

- Fenêtres & panneaux : vrais cadres 1.0 recalculés à toute taille. Marges de terminaux rétablies à 6–9 px ; surface PTY agrandie par rapport aux marges 35 px d'ElectricPulse.
- Menus, popups, gestionnaire SSH, clés Ed25519, appairage LAN : mêmes opérations, nouveaux boutons NeonGlass. Les fonctions de gestion restent dans leurs modules d'origine.
- Animations discrètes : reflet au survol du bouton et trace sur **le terminal actif seulement**, plus un GIF d'origine en en-tête.
- Colonne gauche vide ; navigation/action dans la barre supérieure ; split QSplitter, tmux, Smart Hover, variables de profil, scripts/commandes et saisie prédictive conservés.
- Les 53 ressources NEXUS Electric Carbon et `ElectricPulse.svg` **sont conservées dans le dépôt**, mais ne constituent plus le skin imposé aux terminaux.

## Portée de la validation

Tous les tests unitaires Python exécutables sans Qt, ainsi que syntaxe Python/Bash. **Non testés ici** : rendu graphique réel sous Linux Mint XFCE, Qt/QTermWidget installé, SSH/tmux entre PC, appairage LAN.

## Installer sans écraser l'ancienne version

```bash
sudo apt install -y tmux openssh-client libxcb-cursor0 python3-pip
bash setup-dependency.sh
bash start-nexus.sh
```
