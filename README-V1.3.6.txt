N3XV5 Terminal HUD V1.3.6 — SSH LAN / interface simplifiée

- Colonne gauche laissée vide, réservée à une fonction future.
- Barre supérieure : bouton SSH unique, avec Connexions, Clés, SSH local / réseau LAN.
- Nouveau panneau SSH LAN : identité Ed25519 dédiée créée sur demande, copie de clé publique, instructions pour autoriser un autre PC, exemple de commande de connexion.
- Aucune installation ni activation automatique de sshd, aucune clé ajoutée automatiquement à authorized_keys, aucun échange de clé privée.
- La clé LAN sans phrase secrète est un compromis pour l'accès simplifié. Elle ne doit être utilisée qu'avec des machines de confiance. Pour les environnements sensibles, préférer une clé protégée par phrase secrète et ssh-agent.
- Les sessions distantes continuent de s'appuyer sur SSH + tmux ; la gestion des connexions est conservée.

TESTS : 15 tests unitaires existants passés, syntaxe Python validée. Pas de validation GUI réelle sur Linux Mint.
LANCEMENT : depuis le dossier extrait, copier les wheels compatibles dans Dependency/wheels/, puis bash setup-dependency.sh et bash start-nexus.sh.
