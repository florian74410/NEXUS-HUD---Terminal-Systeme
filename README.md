# N3XV5 Terminal HUD — NOVA 1.0 NeonGlass (V1.4.4 DEV)

**Même moteur multi-terminal Qt + tmux que la V1.4.2, nouveau skin tiré des vrais sources du Terminal NOVA/NEXUS 1.0.0.**

Style actif : NeonGlass NOVA 1.0 peint avec `QPainter` et décoré avec les assets Electric Pulse **autour de chaque instance de terminal**. Le centre du terminal reste entièrement libre pour QTermWidget.

Fonctionnalités : panneaux redimensionnables, SSH et gestion de clés, scripts/variables et prédiction Ctrl+Espace, sessions tmux, Smart Hover, appairage LAN confirmé sur les deux machines (à tester), colonne gauche vide et commandes de gestion en haut.

Voir [README-V1.4.4.md](README-V1.4.4.md) pour les assets utilisés, les clics animés et les limites de validation.

```bash
bash setup-dependency.sh
bash start-nexus.sh
```

Le Terminal reste indépendant de N3XV5 HUB et d'IATB-CLI.


La V1.4.4 ajoute les cadres de terminal issus des assets (9-slice), opacité 50–100 % et impulsion Qt au clic des boutons. Voir [README-V1.4.4.md](README-V1.4.4.md).
