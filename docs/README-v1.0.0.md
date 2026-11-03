# NEXUS Terminal 1.0.0 — NeonGlass Session Manager

- Fenêtre Qt sans barre de titre XFCE, contrôles hexagonaux.
- Paramètres / Connexions SSH, FTP, TCP, HTTP ; édition, suppression, test.
- Profil utilisateur Linux basé sur UID/pwd, enregistré sous ~/.config/nexus-terminal/connections.json (0600).
- SSH avec clés privées locales dans ~/.ssh ; jamais de copie de clés dans le profil.
- Sessions SSH partagées via tmux sur la machine distante ; même nom tmux pour les deux PC.
- FTP/TCP/HTTP : tests sortants, aucun serveur ni socket entrant lancé.
- La gestion des clés consiste à sélectionner une clé existante : la génération et l'autorisation des clés publiques restent à réaliser via ssh-keygen/ssh-copy-id.
- HTTP Web Inspector / proxy : **prévu ultérieurement**, non livré dans cette version.
- Dépendances Qt/PySide6 installées au premier lancement dans un environnement Python utilisateur.
- Aucune clé ni mot de passe stocké dans les préférences.

## Limites
Le paquet n'a pas été exécuté sur un bureau XFCE réel ici. Le terminal SSH requiert que tmux soit installé sur la cible et que la clé soit déjà autorisée. Le bouton Tester utilise un test synchrone (timeout 5 à 9 s) ; cela peut bloquer brièvement la popup. L'installation ne supprime pas arbitrairement les anciens dossiers de sources ni les données utilisateur.
