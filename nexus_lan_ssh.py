"""Opt-in LAN SSH onboarding; never enables sshd or trusts another host silently."""
from nexus_skin import AssetButton
from pathlib import Path
import os
import re
import shutil
import socket
import subprocess
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,
    QLineEdit,QPlainTextEdit,QMessageBox,QApplication)

KEY_NAME='id_n3xv5_lan_ed25519'

def key_path(home=None):
    return Path(home or Path.home())/'.ssh'/KEY_NAME

def generate_lan_key(home=None):
    path=key_path(home)
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    if path.parent.is_symlink():raise ValueError('Dossier ~/.ssh symbolique refusé')
    path.parent.chmod(0o700)
    if path.exists() or path.with_suffix(path.suffix+'.pub').exists():
        raise FileExistsError('Clé déjà présente : aucune clé écrasée')
    if not shutil.which('ssh-keygen'):raise RuntimeError('ssh-keygen non installé')
    # Dedicated passwordless key for LAN convenience. Host authorization remains opt-in.
    proc=subprocess.run(['ssh-keygen','-q','-t','ed25519','-a','64','-N','','-C','n3xv5-lan','-f',str(path)],
        capture_output=True,text=True,timeout=30,stdin=subprocess.DEVNULL)
    if proc.returncode:raise RuntimeError(proc.stderr.strip() or 'Échec ssh-keygen')
    path.chmod(0o600)
    return path

class LANSSHDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle('N3XV5 — SSH local et réseau LAN')
        self.resize(630,490)
        self.setStyleSheet('QDialog{background:#061b2b;color:#dcfaff} QLabel{color:#c9f4ff} QLineEdit,QPlainTextEdit{background:#09283a;color:#e7ffff;border:1px solid #1598bf} QPushButton{background:#103e54;color:#eaffff;border:1px solid #29d6ff;padding:8px} QPushButton:hover{background:#155a78}')
        v=QVBoxLayout(self)
        v.addWidget(QLabel('◈  IDENTITÉ SSH N3XV5 / RÉSEAU LOCAL'))
        v.addWidget(QLabel('Une identité propre à ce PC. La clé privée ne quitte jamais la machine.'))
        self.info=QPlainTextEdit();self.info.setReadOnly(True);self.info.setMaximumHeight(135);v.addWidget(self.info)
        row=QHBoxLayout();v.addLayout(row)
        gen=AssetButton('Créer la clé N3XV5');gen.clicked.connect(self.generate);row.addWidget(gen)
        copy=AssetButton('Copier la clé publique');copy.clicked.connect(self.copy_public);row.addWidget(copy)
        v.addWidget(QLabel('Autoriser ce PC sur un autre PC N3XV5 :'))
        v.addWidget(QLabel('1. Sur le PC distant : installer et activer openssh-server volontairement.'))
        v.addWidget(QLabel('2. Sur le PC distant : ajouter cette clé publique à ~/.ssh/authorized_keys.'))
        v.addWidget(QLabel('3. Vérifier l’empreinte du serveur à la première connexion.'))
        v.addWidget(QLabel('4. Dans SSH ▾ → Connexions, enregistrer son IP, utilisateur et clé.'))
        from nexus_pairing import enabled
        self.discovery=QLabel('Découverte LAN : '+('activée' if enabled() else 'désactivée (Paramètres → Connexions)'))
        v.addWidget(self.discovery)
        v.addWidget(QLabel('L’appairage automatique des clés nécessite encore une validation mutuelle sécurisée.'))
        v.addWidget(QLabel('IP locale indicative : '+self.local_ips()))
        v.addWidget(QLabel('Commande de test (après autorisation sur le PC distant) :'))
        self.target=QLineEdit();self.target.setPlaceholderText('utilisateur@192.168.1.25');v.addWidget(self.target)
        self.example=QPlainTextEdit();self.example.setReadOnly(True);self.example.setMaximumHeight(75);v.addWidget(self.example)
        self.target.textChanged.connect(self.refresh)
        v.addWidget(QLabel('⚠ L’accès SSH donne accès au compte distant : n’autorise que des appareils de confiance.'))
        close=AssetButton('Fermer');close.clicked.connect(self.accept);v.addWidget(close)
        self.refresh()
    @staticmethod
    def local_ips():
        try:
            ips=sorted({x[4][0] for x in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET) if not x[4][0].startswith('127.')})
            return ', '.join(ips) if ips else 'à vérifier avec ip -4 addr'
        except OSError:return 'à vérifier avec ip -4 addr'
    def refresh(self):
        path=key_path()
        pub=Path(str(path)+'.pub')
        self.info.setPlainText(('Clé existante : '+str(path)+'\n\n'+pub.read_text() if pub.exists() else 'Aucune clé N3XV5 LAN générée.\nClique sur « Créer la clé N3XV5 ».'))
        target=self.target.text().strip()
        if re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_-]*@[a-zA-Z0-9][a-zA-Z0-9.:-]*',target):
            self.example.setPlainText('ssh -i '+str(path)+' -o IdentitiesOnly=yes '+target)
        else:self.example.setPlainText('Saisis utilisateur@IP pour obtenir la commande SSH.')
    def generate(self):
        try:
            path=generate_lan_key()
            self.refresh()
            QMessageBox.information(self,'Clé N3XV5','Identité SSH créée : '+str(path)+'\n\nElle n’autorise encore aucune connexion distante.')
        except FileExistsError:self.refresh();QMessageBox.information(self,'Clé existante','Identité N3XV5 déjà créée. Aucune modification.')
        except Exception as e:QMessageBox.warning(self,'SSH',str(e))
    def copy_public(self):
        try:
            data=Path(str(key_path())+'.pub').read_text()
            QApplication.clipboard().setText(data)
            QMessageBox.information(self,'Clé publique','Clé publique copiée. Colle-la uniquement sur un PC que tu souhaites autoriser.')
        except OSError:QMessageBox.warning(self,'SSH','Génère d’abord la clé N3XV5.')
