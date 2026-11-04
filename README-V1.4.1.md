# N3XV5 Terminal HUD — V1.4.1 NEXUS Asset Rework (DEV)

## Périmètre
Refonte réelle de la couche visuelle Qt **sans aucune dépendance au HUB**.
QTermWidget/tmux, SSH, scripts, profils/variables, Smart Hover, appairage LAN restent dans les modules existants.
La colonne gauche est **réservée et vide**. Sessions, SSH (clés et connexions dans un même menu), Paramètres et Scripts sont en haut.

## Audit des défauts corrigés
- **Animations SVG non interprétées par QtSvg** : rendu vectoriel statique, avec animations Qt dédiées et activables dans Paramètres.
- **Boutons partiellement déconnectés de leurs SVG** : `AssetButton` rend le fond issu de l'archive source et peint une étiquette Qt mise à jour dynamiquement ; les boutons inconnus reçoivent un vrai cadre biseauté.
- **Classes painter anciennes redondantes** retirées de `nexus_workspace.py`.
- **Fenêtres d'ajout de session incohérentes** : création de session utilisant désormais `GlassDialog`/Popups/Connection.svg.
- **Cadre ElectricPulse non responsive** : marges adaptatives par instance QTermWidget, aucune surface d'illustration remplaçant le PTY.
- **Notifications** : `NexusNotice` dessiné avec les SVG fournis ; utilisé pour les erreurs de console courantes. Confirmations de commandes sensibles maintenues explicitement.

## Asset mapping
| Zone Qt | SVG/GIF fourni |
|---|---|
| Chaque terminal réel | `assets/theme_nexus/Boxes/Electric_Pulse_Original.svg` |
| Panneau principal 2×2 | `assets/theme_nexus/Windows/Console.svg` |
| Panneau principal autres grilles | `assets/theme_nexus/Windows/SplitView.svg` |
| Colonne gauche vide | `assets/theme_nexus/Boxes/Performance_Tall.svg` |
| Modal Paramètres | `assets/theme_nexus/Popups/Settings.svg` |
| Modal de connexion | `assets/theme_nexus/Popups/Connection.svg` |
| Autres modales | `assets/theme_nexus/Popups/Details.svg` |
| Notifications | `assets/theme_nexus/Notifications/{Info,Warning,Error,...}.svg` |
| Boutons dont l'intitulé est fourni | `assets/theme_nexus/Buttons/*.svg` |
| Barre supérieure | `assets/theme_nexus/ElectroBlueNEON_pcb_signal.gif` (QMovie) |

Le pack source est **réellement embarqué** : 48 SVG et 5 GIF, pas les grandes captures JPEG/PNG de référence.
Le texte des commandes reste du vrai texte Qt; pas de labels SVG impossibles à changer.
Les GIF peuvent être désactivés dans Paramètres → Apparence.

## Dépendances / lancement Linux Mint XFCE
`PySide6==6.11.2`, `pyside6_qtermwidget`, `tmux`, `openssh-client` et les wheels adaptées à la version Python sont nécessaires. 
Ne pas lancer pip sur chaque démarrage. Avec wheels présentes dans `Dependency/wheels/` :

```bash
bash setup-dependency.sh
bash start-nexus.sh
```

Les wheels ne sont pas redistribuées. `setup-dependency.sh` cherche d’abord les wheels locales, puis télécharge celles qui manquent dans `Dependency/wheels/` (connexion Internet requise). `bash setup-dependency.sh --offline` interdit tout téléchargement. Aucun pip au démarrage de l’application.

## Validation & limites
- Unit tests + parse AST + `bash -n` + validation SVG sont effectués dans le conteneur.
- La **GUI Qt / XFCE**, SSH réel et l'appairage entre deux PC **ne sont pas testés** dans cet environnement.
- La transparence de QTermWidget dépend du binding; son mode palette est de secours et peut n'offrir qu'une opacité partielle.
- Ce package ne valide pas à lui seul un `.deb` autonome sur Linux Mint; ne remplace pas ta version fonctionnelle avant un test visuel.
