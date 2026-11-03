"""NEXUS per-user connection profiles. No passwords or private key material in JSON."""
import json,os,re,socket,subprocess,ftplib,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urlsplit
from PySide6.QtCore import Qt,QTimer,Signal,QObject
from PySide6.QtWidgets import (QDialog,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QLineEdit,QPushButton,QComboBox,QTabWidget,QListWidget,QListWidgetItem,QCheckBox,QSpinBox,QMessageBox,QInputDialog,QPlainTextEdit)
BASE=Path.home()/'.config'/'nexus-terminal'
CONFIG=BASE/'connections.json'
TYPES=('SSH','FTP','TCP','HTTP')
LABEL=re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$')
HOST=re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._:-]{0,252}$')

def identity():
    import pwd
    u=pwd.getpwuid(os.getuid())
    return {'uid':os.getuid(),'user':u.pw_name,'home':u.pw_dir,'computer':socket.gethostname()}

def load():
    try:
        if CONFIG.is_symlink():raise ValueError('Refus de suivre un lien symbolique de configuration')
        data=json.loads(CONFIG.read_text())
        if not isinstance(data,dict):raise ValueError('Format incorrect')
        if data.get('user')!=identity()['user']:raise ValueError('Profil d’un autre utilisateur')
        data.setdefault('connections',[])
        return data
    except FileNotFoundError:return {'user':identity()['user'],'connections':[]}

def save(data):
    BASE.mkdir(mode=0o700,parents=True,exist_ok=True)
    BASE.chmod(0o700)
    import tempfile
    fd,name=tempfile.mkstemp(prefix='.connections-',dir=BASE)
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(data,f,indent=2,ensure_ascii=False);f.flush();os.fsync(f.fileno())
        os.chmod(name,0o600);os.replace(name,CONFIG)
    finally:
        if os.path.exists(name):os.unlink(name)

def validate(c):
    if c['type'] not in TYPES:raise ValueError('Protocole inconnu')
    if not LABEL.fullmatch(c['name']):raise ValueError('Nom : lettres, chiffres, - et _ (64 max)')
    if not HOST.fullmatch(c['host']):raise ValueError('Hôte invalide')
    if not 1<=int(c['port'])<=65535:raise ValueError('Port invalide')
    if c['type']=='SSH':
        if not LABEL.fullmatch(c['login']):raise ValueError('Login SSH invalide')
        key=c['key']
        if key and (not Path(key).is_absolute() or not Path(key).is_file()):raise ValueError('Clé privée introuvable')
    if c['type']=='HTTP' and c.get('scheme') not in ('http','https'):raise ValueError('Schéma HTTP invalide')

def ssh_command(c,session=None):
    import shlex
    validate(c)
    cmd=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=ask','-p',str(c['port'])]
    if c.get('key'):cmd+=['-i',c['key'],'-o','IdentitiesOnly=yes']
    cmd+=['-t',c['login']+'@'+c['host']]
    if session:
        if not LABEL.fullmatch(session):raise ValueError('Nom tmux invalide')
        cmd+=['tmux','new-session','-A','-s',session]
    return shlex.join(cmd)

def test_connection(c):
    validate(c)
    if c['type']=='SSH':
        cmd=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','StrictHostKeyChecking=yes','-p',str(c['port'])]
        if c.get('key'):cmd+=['-i',c['key'],'-o','IdentitiesOnly=yes']
        cmd+=[c['login']+'@'+c['host'],'true']
        p=subprocess.run(cmd,timeout=9,capture_output=True,text=True)
        return p.returncode==0,('SSH authentifié' if p.returncode==0 else (p.stderr.strip() or 'Échec SSH')[:250])
    if c['type']=='FTP':
        with ftplib.FTP() as ftp:
            ftp.connect(c['host'],int(c['port']),timeout=5)
            banner=ftp.getwelcome()
            return True,'Serveur FTP joignable : '+str(banner)[:160]+' (sans authentification)'
    if c['type']=='TCP':
        with socket.create_connection((c['host'],int(c['port'])),timeout=5):return True,'Connexion TCP établie'
    url=c.get('scheme','https')+'://'+c['host']+':'+str(c['port'])+'/'
    req=urllib.request.Request(url,method='HEAD',headers={'User-Agent':'NEXUS-Terminal/1.0'})
    try:
        with urllib.request.urlopen(req,timeout=5) as response:return True,'HTTP '+str(response.status)
    except urllib.error.HTTPError as e:return True,'HTTP '+str(e.code)+' (serveur joignable)'

class GlassDialog(QDialog):
    def __init__(self,parent,title):
        super().__init__(parent)
        self.setWindowTitle(title);self.setWindowFlags(Qt.WindowType.Dialog|Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
        self.setMinimumSize(650,520)
        self.setStyleSheet("""QWidget#glass {background:rgba(3,21,37,245);border:2px solid #24c7ed;border-radius:12px;}
        QLabel {color:#dffaff;background:transparent;border:0;} QLineEdit,QComboBox,QSpinBox,QListWidget,QPlainTextEdit {background:#061b2b;color:#e9ffff;border:1px solid #176e91;padding:5px;}
        QPushButton {background:#082f46;color:#e6ffff;border:1px solid #1badd4;padding:7px 12px;}
        QPushButton:hover {background:#115574;border-color:#66f7ff;}
        QTabWidget::pane {background:rgba(2,20,35,230);border:1px solid #168aab;}
        QTabBar::tab {background:#09283d;color:#aeeeff;padding:9px 12px;}
        QTabBar::tab:selected {background:#116481;color:white;}
        QCheckBox {color:#e6ffff;}""")
        outside=QVBoxLayout(self);outside.setContentsMargins(12,12,12,12)
        self.panel=QWidget();self.panel.setObjectName('glass');outside.addWidget(self.panel)
        self.body=QVBoxLayout(self.panel);self.body.setContentsMargins(20,18,20,20)
        top=QHBoxLayout();heading=QLabel('⬡  '+title);heading.setStyleSheet('font-size:17px;color:#6ef3ff;font-weight:bold;')
        top.addWidget(heading);top.addStretch();x=QPushButton('✕');x.clicked.connect(self.reject);top.addWidget(x);self.body.addLayout(top)
    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton and e.position().y()<70:
            if self.windowHandle():self.windowHandle().startSystemMove()
        super().mousePressEvent(e)

class ConnectionsDialog(GlassDialog):
    def __init__(self,parent,initial='SSH'):
        super().__init__(parent,'PARAMÈTRES  /  CONNEXIONS')
        self.data=load();self.tabs=QTabWidget();self.body.addWidget(self.tabs,1)
        self.lists={}
        for typ in TYPES:
            page=QWidget();v=QVBoxLayout(page)
            info=QLabel({'SSH':'Clés SSH locales, connexions sécurisées et terminaux tmux distants.',
              'FTP':'Connexion FTP classique (non chiffrée) : privilégier SFTP via SSH pour les fichiers sensibles.',
              'TCP':'Tests de connexions sortantes vers des ports TCP. Aucun port entrant ouvert.',
              'HTTP':'Tests HTTP/HTTPS sortants, sans stockage de jetons API.'}[typ]);info.setWordWrap(True);v.addWidget(info)
            lst=QListWidget();self.lists[typ]=lst;v.addWidget(lst,1)
            row=QHBoxLayout()
            for title,cb in [('＋ Ajouter',lambda checked=False,t=typ:self.edit(t)),('Modifier',lambda checked=False,t=typ:self.edit(t,True)),('Supprimer',lambda checked=False,t=typ:self.remove(t)),('Tester',lambda checked=False,t=typ:self.test(t))]:
                b=QPushButton(title);b.clicked.connect(cb);row.addWidget(b)
            v.addLayout(row);self.tabs.addTab(page,typ)
        self.tabs.setCurrentIndex(TYPES.index(initial) if initial in TYPES else 0)
        self.refresh()
        foot=QHBoxLayout();foot.addStretch();close=QPushButton('Fermer');close.clicked.connect(self.accept);foot.addWidget(close);self.body.addLayout(foot)
    def refresh(self):
        for typ,lst in self.lists.items():
            lst.clear()
            for c in self.data['connections']:
                if c['type']==typ:
                    item=QListWidgetItem(('● ' if c.get('enabled') else '○ ')+c['name']+'    '+c['host']+':'+str(c['port']))
                    item.setData(Qt.ItemDataRole.UserRole,c['name']);lst.addItem(item)
    def selected(self,typ):
        item=self.lists[typ].currentItem()
        if not item:return None
        return next((c for c in self.data['connections'] if c['type']==typ and c['name']==item.data(Qt.ItemDataRole.UserRole)),None)
    def edit(self,typ,existing=False):
        c=self.selected(typ) if existing else None
        if existing and not c:return
        d=GlassDialog(self,'CONNEXION  /  '+typ);d.setMinimumSize(580,480)
        f=QFormLayout();d.body.addLayout(f)
        def field(label,value=''):
            w=QLineEdit(str(value));f.addRow(label,w);return w
        name=field('Nom métier-rôle-utilisateur',c['name'] if c else '')
        host=field('Hôte / adresse IP',c['host'] if c else '')
        port=QSpinBox();port.setRange(1,65535);port.setValue(int(c['port']) if c else {'SSH':22,'FTP':21,'TCP':8080,'HTTP':443}[typ]);f.addRow('Port',port)
        login=field('Utilisateur distant',c.get('login','') if c else identity()['user']) if typ=='SSH' else None
        key=field('Chemin de clé privée (~/.ssh/...)',c.get('key','') if c else '') if typ=='SSH' else None
        scheme=QComboBox() if typ=='HTTP' else None
        if scheme:
            scheme.addItems(['https','http']);scheme.setCurrentText(c.get('scheme','https') if c else 'https');f.addRow('Protocole',scheme)
        enabled=QCheckBox('Activer dans le profil');enabled.setChecked(c.get('enabled',True) if c else True);f.addRow('',enabled)
        row=QHBoxLayout();row.addStretch();ok=QPushButton('Enregistrer');cancel=QPushButton('Annuler');row.addWidget(cancel);row.addWidget(ok);d.body.addLayout(row);cancel.clicked.connect(d.reject)
        def commit():
            record={'type':typ,'name':name.text().strip(),'host':host.text().strip(),'port':port.value(),'enabled':enabled.isChecked()}
            if login:record.update(login=login.text().strip(),key=os.path.expanduser(key.text().strip()))
            if scheme:record['scheme']=scheme.currentText()
            try:
                validate(record)
                if any(x['name']==record['name'] and x['type']==typ and x is not c for x in self.data['connections']):raise ValueError('Ce nom existe déjà')
                if c:self.data['connections'].remove(c)
                self.data['connections'].append(record);save(self.data);self.refresh();d.accept()
            except Exception as e:QMessageBox.warning(d,'Connexion invalide',str(e))
        ok.clicked.connect(commit);d.exec()
    def remove(self,typ):
        c=self.selected(typ)
        if c and QMessageBox.question(self,'Supprimer','Supprimer '+c['name']+' ?')==QMessageBox.StandardButton.Yes:
            self.data['connections'].remove(c);save(self.data);self.refresh()
    def test(self,typ):
        c=self.selected(typ)
        if not c:return
        QApplication=__import__('PySide6.QtWidgets',fromlist=['QApplication']).QApplication
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:ok,msg=test_connection(c)
        except Exception as e:ok,msg=False,str(e)
        finally:QApplication.restoreOverrideCursor()
        (QMessageBox.information if ok else QMessageBox.warning)(self,'Test '+typ,msg)

class SessionDialog(GlassDialog):
    def __init__(self,parent,workspace):
        super().__init__(parent,'SESSIONS  /  PROFIL LOCAL')
        self.workspace=workspace;self.data=load();i=identity()
        self.body.addWidget(QLabel('◉  '+i['user']+'@'+i['computer']+'     UID '+str(i['uid'])))
        self.body.addWidget(QLabel('Profil rattaché au compte Linux connecté. Les clés privées restent dans ~/.ssh.'))
        self.items=QListWidget();self.body.addWidget(self.items,1)
        self.refresh()
        row=QHBoxLayout()
        for text,callback in [('Ouvrir terminal SSH',self.open_ssh),('Tester connexion',self.test),('Paramètres connexions',self.settings)]:
            b=QPushButton(text);b.clicked.connect(callback);row.addWidget(b)
        self.body.addLayout(row)
        self.body.addWidget(QLabel('Macro ↔ ASUS : configurer SSH sur les deux PC, autoriser la clé publique, puis rejoindre le même nom tmux.'))
    def refresh(self):
        self.data=load();self.items.clear()
        for c in self.data['connections']:
            if c.get('enabled'):
                item=QListWidgetItem('◈ '+c['type']+'  /  '+c['name']+'   →  '+c['host']+':'+str(c['port']))
                item.setData(Qt.ItemDataRole.UserRole,c);self.items.addItem(item)
    def selected(self):
        item=self.items.currentItem();return item.data(Qt.ItemDataRole.UserRole) if item else None
    def settings(self):
        ConnectionsDialog(self).exec();self.refresh()
    def test(self):
        c=self.selected()
        if c:
            try:ok,msg=test_connection(c)
            except Exception as e:ok,msg=False,str(e)
            (QMessageBox.information if ok else QMessageBox.warning)(self,'Test '+c['type'],msg)
    def open_ssh(self):
        c=self.selected()
        if not c or c['type']!='SSH':QMessageBox.information(self,'Session','Sélectionne une connexion SSH.');return
        name,ok=QInputDialog.getText(self,'Session tmux','Nom partagé sur le serveur distant :',text='nexus-shared')
        if not ok:return
        try:command=ssh_command(c,name)
        except Exception as e:QMessageBox.warning(self,'SSH',str(e));return
        if self.workspace.open_command(name,command,True):self.accept()
