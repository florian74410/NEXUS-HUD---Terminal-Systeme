# N3XV5 Terminal HUD — NOVA 1.0 NeonGlass (V1.4.3 DEV)

**Même moteur multi-terminal Qt + tmux que la V1.4.2, nouveau skin tiré des vrais sources du Terminal NOVA/NEXUS 1.0.0.**

Style actif : NeonGlass original peint avec `QPainter`. Les sources Electric Pulse restent conservées à titre d'archives dans `nexus_skin.py` et `assets/theme_nexus`, mais ne sont plus utilisées comme grands fonds SVG.

Fonctionnalités : panneaux redimensionnables, SSH et gestion de clés, scripts/variables et prédiction Ctrl+Espace, sessions tmux, Smart Hover, appairage LAN confirmé sur les deux machines (à tester), colonne gauche vide et commandes de gestion en haut.

Voir [README-V1.4.3.md](README-V1.4.3.md) pour la correspondance précise avec NOVA 1.0, l'installation et les limites de validation.

```bash
bash setup-dependency.sh
bash start-nexus.sh
```

Le Terminal reste indépendant de N3XV5 HUB et d'IATB-CLI.
