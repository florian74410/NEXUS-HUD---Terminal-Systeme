# NEXUS Terminal — ElectroBlueNEON

Application Linux Qt/PySide6 de gestion de terminaux et de profils de connexions SSH, FTP, TCP et HTTP.

## Installation Linux Mint / XFCE

Télécharger `nexus-terminal_1.0.0-1_all.deb` depuis ce dépôt, puis :

```bash
sudo apt install ./nexus-terminal_1.0.0-1_all.deb
/usr/bin/nexus-terminal
```

Les dépendances Python `PySide6` et `pyside6_qtermwidget` sont installées dans un environnement virtuel utilisateur au premier lancement (connexion Internet nécessaire).

**Statut :** version 1.0.0 en validation sur Linux Mint/XFCE. Les connexions réseau nécessitent une configuration explicite ; l'ouverture d'un profil n'ouvre pas automatiquement des ports entrants.

**Sécurité :** ne jamais publier de clé SSH privée, d'identifiants FTP ou de secrets API dans le dépôt.
