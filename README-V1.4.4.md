# N3XV5 Terminal HUD V1.4.4 — NOVA 1.0 + Electric Pulse (DEV)

## Périmètre strict

La V1.4.4 est **uniquement une mise à jour esthétique** de la base V1.4.3 :

- On conserve l'interface, la top bar, la colonne gauche vide et la grille `QSplitter` redimensionnable.
- Les vraies instances de `QTermWidget` continuent à gérer le PTY, SSH, tmux, Smart Hover, les scripts, les commandes rapides et la saisie prédictive.
- Chaque `TerminalTile` porte la bordure de l'asset fourni **`assets/theme_nexus/01_Electric_Pulse.svg`**. Le SVG est découpé en neuf zones et seule sa bordure est dessinée : le centre (texte du terminal) n'est pas recouvert par l'artwork.
- Le terminal **actif uniquement** reçoit une petite impulsion lumineuse à 140 ms par image. L'animation est contrôlée par Qt car QtSvg n'anime pas les `animate`/keyframes SVG du fichier source.
- Les boutons `NovaOneButton` utilisent les assets `assets/theme_nexus/Buttons/*.svg` sans leur texte SVG intégré, afin de conserver les vrais libellés, icônes et événements Qt. Leur animation de clic est ponctuelle (~380 ms), pas un effet en boucle. Les trois boutons de fenêtre bénéficient aussi d'une petite réaction au clic.
- Dans `Paramètres → Apparence`, l'opacité du PTY est réglable de **50 % à 100 %**, enregistrée dans les réglages. Le menu `Affichage → Opacité des terminaux` propose 50, 60, 70, 80, 90 et 100 %.

## Transparence et performances

Si le binding QTermWidget propose `setTerminalOpacity`, N3XV5 l'utilise en priorité pour garder les glyphes plus lisibles. Sinon il utilise **`QGraphicsOpacityEffect`** (alpha réel sur la surface, glyphes compris). Dans ce mode de secours, le texte paraît aussi plus transparent : régler 85–100 % pour la meilleure lisibilité. À 100 %, l'effet est supprimé pour conserver les performances. Le seul timer de bordure actif est celui du panneau sélectionné ; les boutons sont animés seulement lors du survol et du clic.

## Test sur Linux Mint XFCE — installation parallèle sans écraser l'ancienne

```bash
sudo apt install -y python3-pip tmux openssh-client libxcb-cursor0
bash setup-dependency.sh
bash start-nexus.sh
```

Contrôles : ouvrir deux sessions, redimensionner les séparateurs, activer une session, modifier l'opacité (50 puis 100 %), cliquer sur Scripts/SSH/Sessions/Paramètres, désactiver les animations. Ne pas tester l'appairage réel avant la phase prévue entre deux PC.

## Validation effectuée

- Tests Python des composants non graphiques et tests structurels.
- `compileall`, `bash -n`, validation XML des SVG, intégrité du ZIP.
- **Non vérifié en environnement réel** : rendu Qt/QTermWidget sur XFCE, transparence native sur le binding local, SSH/tmux, appairage entre PC, performance sur ancien GPU.

Ce n'est pas encore une release stable. Aucune modification du HUB ni d'IATB-CLI.
