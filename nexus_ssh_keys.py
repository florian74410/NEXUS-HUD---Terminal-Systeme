"""Local SSH key manager. Never uploads or displays private key material."""
from nexus_skin import AssetButton
from pathlib import Path
import os,subprocess
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,QMessageBox,QPlainTextEdit,QApplication
from PySide6.QtCore import Qt

class SSHKeysDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent);self.setWindowTitle('N3XV5 — Clés SSH Ed25519');self.resize(550,340)
        lay=QVBoxLayout(self)
        lay.addWidget(QLabel('Générer une clé SSH locale Ed25519 (jamais envoyée à un serveur).'))
        self.name=QLineEdit('id_n3xv5_ed25519');lay.addWidget(QLabel('Nom de fichier dans ~/.ssh/'));lay.addWidget(self.name)
        self.passphrase=QLineEdit();self.passphrase.setEchoMode(QLineEdit.EchoMode.Password)
        self.passphrase.setPlaceholderText('Phrase secrète (recommandée)');lay.addWidget(self.passphrase)
        row=QHBoxLayout();lay.addLayout(row)
        generate=AssetButton('Générer');generate.clicked.connect(self.generate);row.addWidget(generate)
        copy=AssetButton('Copier clé publique');copy.clicked.connect(self.copy_public);row.addWidget(copy)
        self.result=QPlainTextEdit();self.result.setReadOnly(True);lay.addWidget(self.result)
        lay.addWidget(QLabel('La clé privée reste dans ~/.ssh/ (permissions 600). Ne la partage jamais.'))
    def _key_path(self):
        name=self.name.text().strip()
        import re
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',name):raise ValueError('Nom invalide : lettres, chiffres, _ et - uniquement.')
        return Path.home()/'.ssh'/name
    def generate(self):
        try:
            path=self._key_path();path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
            os.chmod(path.parent,0o700)
            if path.exists() or Path(str(path)+'.pub').exists():raise ValueError('Une clé de ce nom existe déjà. Aucune clé ne sera écrasée.')
            # Passphrase is passed through a private temporary fd, not argv, to avoid process-list disclosure.
            # ssh-keygen -N requires an argument: use a private file descriptor via SSH_ASKPASS instead.
            from tempfile import TemporaryDirectory
            with TemporaryDirectory(prefix='n3xv5-askpass-') as d:
                helper=Path(d)/'askpass.sh';secret=Path(d)/'secret'
                secret.write_text(self.passphrase.text());os.chmod(secret,0o600)
                helper.write_text('#!/bin/sh\nexec cat "'+str(secret)+'"\n');os.chmod(helper,0o700)
                env=os.environ.copy();env.update({'SSH_ASKPASS':str(helper),'SSH_ASKPASS_REQUIRE':'force','DISPLAY':env.get('DISPLAY',':0')})
                result=subprocess.run(['ssh-keygen','-q','-t','ed25519','-a','64','-f',str(path),' -C'.strip(),'n3xv5-terminal'],stdin=subprocess.DEVNULL,text=True,capture_output=True,env=env,timeout=30,start_new_session=True)
                # Some ssh-keygen versions demand interactive passphrase input even with askpass.
                if result.returncode:raise RuntimeError('ssh-keygen : '+(result.stderr or 'échec de génération'))
            os.chmod(path,0o600)
            self.result.setPlainText('Clé créée : '+str(path)+'\n\n'+Path(str(path)+'.pub').read_text())
            self.passphrase.clear()
        except Exception as e:QMessageBox.warning(self,'Génération SSH',str(e))
    def copy_public(self):
        try:
            data=Path(str(self._key_path())+'.pub').read_text()
            QApplication.clipboard().setText(data);self.result.setPlainText('Clé publique copiée.\n\n'+data)
        except Exception as e:QMessageBox.warning(self,'Clé publique',str(e))
