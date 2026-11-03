NEXUS Terminal — préparation ISO (prototype, pas ISO prête)
=========================================================
OBJECTIF 1 : archive Linux portable (même architecture + ABI + bibliothèques système compatibles).
OBJECTIF 2 : ISO Live Linux bootable, utilisable dans une VM ou depuis une clé USB sans OS préinstallé.

IMPORTANT : une application Qt/Python ne peut PAS démarrer sur un PC nu sans noyau Linux, pilotes, gestion mémoire et affichage. Une ISO Live EMBARQUE son propre système d'exploitation Linux. Ce n'est pas un programme bare-metal.

ARCHITECTURE :
  Dependency/wheels/    Wheels Python téléchargés pour la distribution cible
  Dependency/runtime/   Environnement virtuel construit sur la machine cible (ne pas copier un venv entre OS)
  ISO/build-iso.sh      Script live-build Debian, compilation dans une VM Linux avec accès réseau
  ISO/work/             Dossier de compilation temporaire
  check-portability.sh  Vérifications locales

PRÉPARATION SUR DEBIAN (VM DE BUILD) :
  sudo apt install live-build squashfs-tools xorriso debootstrap
  bash check-portability.sh
  bash ISO/build-iso.sh --check
  sudo bash ISO/build-iso.sh --build

LIMITES ACTUELLES :
  * Le script ISO est un prototype non exécuté : la compilation complète, le démarrage en VM, le réseau et les dépendances Qt restent à valider.
  * La construction exige un accès Internet pour Debian et des wheels locaux compatibles Debian/Python cible.
  * Le répertoire Dependency/runtime/ reste le seul emplacement Python propre à l'application. Les dépendances Linux système sont gérées par l'OS de l'ISO.
  * La configuration et les clés SSH doivent rester hors de l'ISO distribuée (profil utilisateur), jamais embarquées.
  * L'ISO live est non persistante par défaut : prévoir stockage persistant chiffré pour conserver paramètres et clés.
  * L'application n'est pas un environnement de bureau complet ; XFCE est inclus dans l'ISO pour l'affichage.
  * Tester avec QEMU/KVM avant publication ; vérifier la licence et la redistribution des binaires.
