N3XV5 V1.3.7 — Première étape d’appairage LAN
- Paramètres > Connexions : activation/désactivation persistante de la découverte LAN.
- Désactivée par défaut ; annonce UDP 43871 toutes les 5 secondes lorsque activée.
- Service réseau démarré seulement au lancement si activé ; redémarrer pour appliquer.
- Aucune ouverture automatique de sshd, aucune autorisation de clé sans validation.
- Moteur de validation et ajout explicite de clé Ed25519 préparé, non relié à un flux d’appairage automatique.
- Les appareils découverts ne sont pas encore affichés dans l’interface.
- IMPORTANT : ceci n’est PAS encore l’appairage complet demandé ; protocole de confirmation mutuelle à finaliser.
