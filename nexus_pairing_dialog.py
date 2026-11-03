"""Qt pairing assistant. UI approval always runs on the GUI thread."""
from nexus_nova1_style import NovaOneButton
import queue
import threading
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QListWidget, QMessageBox)
from nexus_pairing import enabled
from nexus_pairing_secure import PairingServer, pair_with
from nexus_lan_ssh import key_path, generate_lan_key


class PairingDialog(QDialog):
    def __init__(self, discovery, parent=None):
        super().__init__(parent)
        self.discovery = discovery
        self.server = PairingServer()
        self.answers = queue.Queue()
        self.setWindowTitle('N3XV5 — Appairage sécurisé LAN')
        self.resize(590, 460)
        self.setStyleSheet('QDialog{background:#061827;color:#e2faff} QLabel{color:#b9edfa} '
            'QListWidget,QLineEdit{background:#092b3e;color:#ecffff;border:1px solid #1786ac;padding:7px} '
            'QPushButton{background:#0b3a53;color:#ecffff;border:1px solid #21cfff;padding:8px}')
        v=QVBoxLayout(self)
        v.addWidget(QLabel('◈  N3XV5 / APPAREILS DU RÉSEAU'))
        v.addWidget(QLabel('Chaque PC doit ouvrir cette fenêtre et activer la découverte dans Paramètres.'))
        self.status=QLabel('Initialisation…');v.addWidget(self.status)
        self.devices=QListWidget();v.addWidget(self.devices)
        row=QHBoxLayout();v.addLayout(row)
        refresh=NovaOneButton('Actualiser');refresh.clicked.connect(self.refresh);row.addWidget(refresh)
        self.ip=QLineEdit();self.ip.setPlaceholderText('IP locale du PC distant (facultatif)');v.addWidget(self.ip)
        self.connect=NovaOneButton('Appairer le PC sélectionné');self.connect.clicked.connect(self.connect_peer);v.addWidget(self.connect)
        v.addWidget(QLabel('Compare le code sur les deux écrans avant de confirmer.'))
        v.addWidget(QLabel('Les clés privées ne sont jamais échangées. SSH serveur doit être activé séparément.'))
        close=NovaOneButton('Fermer');close.clicked.connect(self.accept);v.addWidget(close)
        self.timer=QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(250)
        if not enabled():
            self.status.setText('Découverte désactivée : active-la dans Paramètres → Connexions.')
            self.connect.setEnabled(False)
        else:
            try:
                if not key_path().exists():
                    generate_lan_key()
                self.server.start()
                self.status.setText('Prêt : demandes entrantes autorisées avec confirmation.')
            except Exception as e:
                self.status.setText('Service indisponible : '+str(e))
                self.connect.setEnabled(False)
        self.refresh()

    def refresh(self):
        self.devices.clear()
        if self.discovery:
            for ip, meta in sorted(self.discovery.peers.items()):
                self.devices.addItem(f"{meta.get('name','PC')}  —  {ip}")

    def connect_peer(self):
        host=self.ip.text().strip()
        if not host and self.devices.currentItem():
            host=self.devices.currentItem().text().rsplit(' — ',1)[-1]
        if not host:
            QMessageBox.information(self,'N3XV5','Sélectionne un PC ou saisis son IP.');return
        self.connect.setEnabled(False)
        self.status.setText('Demande envoyée à '+host)
        def approve(code, peer):
            answer=threading.Event()
            result={'ok':False}
            self.answers.put(('confirm',code,peer,answer,result))
            if not answer.wait(85):return False
            return result['ok']
        def worker():
            try:self.answers.put(('result',pair_with(host,approve),host))
            except Exception as e:self.answers.put(('error',str(e)))
        threading.Thread(target=worker,daemon=True).start()

    def poll(self):
        while True:
            try:pending=self.server.incoming.get_nowait()
            except queue.Empty:break
            accepted=QMessageBox.question(self,'Demande SSH N3XV5',
                f"PC demandeur : {pending.peer}\n\nCODE DE COMPARAISON : {pending.code}\n\n"
                'Vérifie que ce code est IDENTIQUE sur le PC demandeur.\n'
                'Autoriser sa clé publique à accéder à ton compte SSH ?',
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            pending.decide(accepted==QMessageBox.StandardButton.Yes)
        while True:
            try:msg=self.answers.get_nowait()
            except queue.Empty:break
            if msg[0]=='confirm':
                _,code,peer,event,result=msg
                result['ok']=QMessageBox.question(self,'Vérification mutuelle',
                    f'PC : {peer}\n\nCODE : {code}\n\n'
                    'Compare ce code sur les DEUX PC avant de confirmer.\n'
                    'Autoriser sa clé publique dans authorized_keys ?',
                    QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes
                event.set()
            elif msg[0]=='result':
                self.status.setText('Appairage réussi' if msg[1] else 'Appairage annulé')
                self.connect.setEnabled(True)
                if msg[1]:QMessageBox.information(self,'N3XV5','Clés publiques autorisées des deux côtés.\nVérifie maintenant le serveur SSH et sa clé hôte avant connexion.')
            elif msg[0]=='error':
                self.status.setText('Échec : '+msg[1]);self.connect.setEnabled(True)
        while True:
            try:error=self.server.errors.get_nowait()
            except queue.Empty:break
            self.status.setText('Connexion entrante : '+error)

    def closeEvent(self,event):
        self.server.stop()
        super().closeEvent(event)

    def done(self,result):
        self.server.stop()
        super().done(result)
