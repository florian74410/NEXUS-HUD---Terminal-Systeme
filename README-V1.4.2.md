# N3XV5 Terminal HUD v1.4.2 — Electric Pulse refined (DEV)

Reprise ciblée des sources v1.4.1, architecture inchangée.

- Le bouton de fermeture de chaque terminal est un contrôle compact, accessible et dessiné en cyan par Qt. La session tmux est conservée au détachement.
- Le menu **Affichage** apparaît sous son véritable bouton, au lieu du centre de la fenêtre.
- Les commandes SSH vers tmux utilisent `new-session -A -s` : ouvrir une session distante existante ou la créer.
- Cache LRU du contenu SVG normalisé, **sans partager les renderers mutables** entre terminaux.
- Les SVG de boutons non critiques ont leurs segments rouges convertis en bleu à l'affichage seulement ; les SVG originaux ne sont pas modifiés.
- Tous les modules SSH, Scripts, Sessions, Smart Hover et appairage LAN de la v1.4.1 sont conservés.
- La colonne de gauche reste sans contrôles.

## Validation
Tests automatiques et contrôle de syntaxe ; rendu Qt/XFCE, comportement SSH, tmux, appairage LAN et paquet .deb non validés sur machines physiques.

## Installation isolée
```bash
bash setup-dependency.sh
bash start-nexus.sh
```

Le dépôt est encore en développement ; ne remplace pas une version installée sans validation manuelle.
