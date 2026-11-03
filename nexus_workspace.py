#!/usr/bin/env python3
"""NEXUS Workspace v0.5: dockable Qt workspace and tmux-over-SSH shared sessions."""
from __future__ import annotations
import os, re, shlex, shutil, socket, subprocess, uuid
from pathlib import Path
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QPoint, QRectF, QVariantAnimation, QEasingCurve, QSettings
from PySide6.QtGui import QIcon, QFont, QColor, QPainter, QPen, QLinearGradient, QPolygonF, QPixmap, QMovie
from PySide6.QtWidgets import (QApplication,QWidget,QMainWindow,QVBoxLayout,QHBoxLayout,
 QGridLayout,QLabel,QPushButton,QComboBox,QMenu,QDialog,QFormLayout,QLineEdit,
 QDialogButtonBox,QMessageBox,QSplitter,QFrame,QPlainTextEdit,QCheckBox,QSpinBox,QSizePolicy,QStyleFactory,QSlider,QInputDialog)
from pyside6_qtermwidget import QTermWidget
from nexus_connections import ConnectionsDialog, SessionDialog, identity, GlassDialog
from nexus_hover import SmartHover
from nexus_quick_commands import Registry, expand, validate_name, RESERVED
from nexus_nova1_style import NovaOneButton, NeonGlassPanel, NovaOneTerminalFrame, NovaOneCloseButton, show_notice

HERE=Path(__file__).resolve().parent
ICONS=HERE/'assets'/'icons'
ACCENT='#13dfff'
STYLE="""
* {font-family:'DejaVu Sans';color:#e3faff;font-size:11px;}
QWidget#root {background:#020b16;}
QWidget#stage {background:rgba(0,58,88,75);border:1px solid rgba(35,205,248,110);}
QWidget#splitSurface {background:rgba(0,64,104,72);}
QWidget#terminalHost {background:#041725;}
QWidget#root QToolTip {color:#eaffff;background:#06283d;border:1px solid #32cfee;}
QWidget#root QTabWidget::pane {background:#041b2c;border:1px solid #137b9c;}
QWidget#root QTabBar::tab {background:#07263b;color:#d9f9ff;padding:6px 10px;}
QWidget#root QTabBar::tab:selected {background:#0b4d68;color:white;}
QWidget#root QScrollArea,QWidget#root QScrollArea > QWidget > QWidget {background:#041b2c;}
QWidget#root QAbstractItemView {background:#061e30;color:#e8ffff;selection-background-color:#08668a;selection-color:#fff;}
QWidget#root QComboBox QAbstractItemView {background:#061e30;color:#e8ffff;}
QWidget#root QCheckBox,QWidget#root QRadioButton {color:#e8ffff;background:transparent;}
QWidget#root QMenuBar {background:#061b2a;color:#e8ffff;}
QWidget#root QMenuBar::item:selected {background:#0b4d68;}
QWidget#root QLabel {background:transparent;}
QWidget#root QSplitter {background:rgba(0,64,104,72);}
QWidget#root QTermWidget {background:#161b20;}
QWidget#root QMenu {background:#061a2b;}
QLabel#title {font-size:21px;font-weight:750;color:#f1ffff;}
QLabel#sub {font-size:10px;letter-spacing:2px;color:#8edbea;}
QLabel#dim {color:#7caebd;}
QPushButton,QComboBox,QSpinBox,QLineEdit {background:#072439;border:1px solid #167c9e;
 border-radius:3px;padding:6px 10px;min-height:22px;}
QPushButton:hover,QComboBox:hover {border:1px solid #61f1ff;background:#0a3a53;}
QPushButton:pressed {background:#0b5268;}
QPushButton#nav {background:transparent;border:0;text-align:left;padding:12px;}
QPushButton#nav:checked {background:#0b5069;border:1px solid #43e6ff;}
QPushButton#add {border:0;background:transparent;color:#31eaff;font-size:18px;font-weight:bold;}
QPushButton#add:hover {color:white;}
QMenu {background:#061a2b;border:1px solid #22a8c9;}
QMenu::item {padding:7px 16px;}
QMenu::item:selected {background:#0a526b;}
QDialog {background:#061725;}
QPlainTextEdit {background:#031321;border:1px solid #1880a3;}
QSplitter::handle {background:rgba(0,155,207,110);border:1px solid rgba(50,230,255,120);}
QSplitter::handle:hover {background:rgba(0,213,255,170);}
QMessageBox {background:#061725;color:#e8ffff;}
QMessageBox QLabel {color:#e8ffff;background:transparent;}
QDialog QLabel {color:#e8ffff;background:transparent;}

/* NOVA 1.0 restored, extra contrast and UX styles */
QWidget#root QFrame#novaOneGlass {background:transparent;border:0;}
QWidget#root QTermWidget {background:#041725;}
QLabel#sessionBadge {font-family:'DejaVu Sans Mono';font-weight:700;font-size:10px;color:#8ff2ff;}
QWidget#stage QLabel {background:transparent;}
QDialogButtonBox QPushButton {min-width:74px;}
QMenu::separator {height:1px;background:#126989;margin:5px 8px;}
QSlider::groove:horizontal {height:4px;background:#10384b;border:1px solid #216c85;}
QSlider::handle:horizontal {width:12px;margin:-6px 0;background:#32dcfa;border:1px solid #a4f7ff;border-radius:4px;}
"""
def icon(name):
    return QIcon(str(ICONS/(name+'.svg')))
def button(text,callback,ico=None,name=None):
    b=NovaOneButton(text)
    if ico:
        alternative=ICONS/('hud_'+({'activity':'network','apps':'grid','code':'terminal'}.get(ico,ico))+'.svg')
        b.setIcon(QIcon(str(alternative)) if alternative.is_file() else icon(ico))
        b.setIconSize(QSize(18,18))
    if name:b.setObjectName(name)
    b.clicked.connect(callback)
    return b

class Frame(QFrame):
    def __init__(self,parent=None,cut=13):
        super().__init__(parent);self.cut=cut
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        from PySide6.QtGui import QPainterPath
        r=self.rect().adjusted(3,3,-3,-3);c=self.cut
        path=QPainterPath();path.moveTo(r.left()+c,r.top())
        path.lineTo(r.right()-c,r.top());path.lineTo(r.right(),r.top()+c)
        path.lineTo(r.right(),r.bottom()-c);path.lineTo(r.right()-c,r.bottom())
        path.lineTo(r.left()+c,r.bottom());path.lineTo(r.left(),r.bottom()-c)
        path.lineTo(r.left(),r.top()+c);path.closeSubpath()
        g=QLinearGradient(0,0,0,self.height());g.setColorAt(0,QColor('#09273c'));g.setColorAt(.25,QColor('#041b2b'));g.setColorAt(1,QColor('#020e1d'))
        p.fillPath(path,g);p.setPen(QPen(QColor('#11b9e4'),1.2));p.drawPath(path)
        p.setPen(QPen(QColor('#7dfaff'),1.7))
        p.drawLine(r.left()+c+7,r.top(),r.left()+c+min(110,r.width()//3),r.top())
        p.drawLine(r.right()-c-min(60,r.width()//4),r.bottom(),r.right()-c-5,r.bottom())
        p.end()

class HexWindowButton(QPushButton):
    """Original NOVA 1.0 hex geometry, cyan actions per N3XV5 palette."""
    def __init__(self,kind,parent=None):
        super().__init__(parent)
        self.kind=kind
        self.setFixedSize(37,35)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip({'min':'Minimiser','max':'Maximiser / Restaurer','close':'Fermer'}[kind])
        self.setStyleSheet('background:transparent;border:0;padding:0;')
        self._hover=False
    def enterEvent(self,event):
        self._hover=True;self.update();super().enterEvent(event)
    def leaveEvent(self,event):
        self._hover=False;self.update();super().leaveEvent(event)
    def paintEvent(self,event):
        from PySide6.QtCore import QPointF
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        poly=QPolygonF([QPointF(9,2),QPointF(28,2),QPointF(35,17),
                        QPointF(28,32),QPointF(9,32),QPointF(2,17)])
        p.setPen(QPen(QColor('#69f5ff' if self._hover else '#159cbe'),1.5))
        p.setBrush(QColor('#10506c' if self._hover else '#061929'))
        p.drawPolygon(poly)
        p.setPen(QPen(QColor('#a6fcff' if self._hover else '#51cfe8'),2.2))
        if self.kind=='min':
            p.drawLine(13,20,24,20)
        elif self.kind=='max':
            p.drawRect(13,12,11,10)
        else:
            p.drawLine(14,12,23,22);p.drawLine(23,12,14,22)
        p.end()

class HeaderCircuit(Frame):
    def mouseDoubleClickEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            window=self.window()
            if isinstance(window,MainWindow):window.toggle_maximize()
        super().mouseDoubleClickEvent(event)
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            window=self.window()
            if isinstance(window,MainWindow) and not window.isMaximized():
                handle=window.windowHandle()
                if handle:handle.startSystemMove()
        super().mousePressEvent(event)
    def paintEvent(self,e):
        super().paintEvent(e)
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor('#087aa3'),1.3))
        w=self.width();h=self.height()
        for offset in (0,12,24,36):
            x=int(w*.48)+offset*3
            p.drawLine(x,10,x+55,10);p.drawLine(x+55,10,x+80,30);p.drawLine(x+80,30,x+180,30)
        p.setPen(QPen(QColor('#48efff'),2.2))
        p.drawLine(int(w*.7),10,int(w*.7)+48,10)
        p.end()

class Terminal(QTermWidget):
    """Real QTermWidget PTY, with tmux for durable shared screen and SSH attach."""
    def apply_opacity(self,percent):
        # QTermWidget has its own paint surface; stylesheet alone cannot guarantee alpha.
        # setTerminalOpacity is available in some bindings, fall back to palette.
        value=max(0.35,min(1.0,percent/100.0))
        if callable(getattr(self,"setTerminalOpacity",None)):
            self.setTerminalOpacity(value)
        else:
            from PySide6.QtGui import QPalette
            pal=self.palette();pal.setColor(QPalette.ColorRole.Base,QColor(3,17,29,int(255*value)));self.setPalette(pal)
    def __init__(self,command,parent=None,session_name=None):
        super().__init__(0,parent)
        self.setTerminalFont(QFont('DejaVu Sans Mono',10))
        self.setObjectName('terminalHost')
        self.setHistorySize(8000)
        self.setTerminalSizeHint(False)
        self.setColorScheme('DarkPastels')
        self.apply_opacity(82)
        self.setShellProgram('/bin/bash')
        self.startShellProgram()
        self.smart_hover=SmartHover(self,session_name=session_name)
        self.quick_registry=None
        self._quick_prefix=""
        QTimer.singleShot(350,lambda:self.sendText(command+'\n'))

    def keyPressEvent(self,event):
        # Explicit predictive palette: never intercept normal shell completion / Tab.
        if event.key()==Qt.Key.Key_Space and event.modifiers() & Qt.KeyboardModifier.ControlModifier and self.quick_registry:
            prefix=self._quick_prefix[-60:]
            options=self.quick_registry.suggestions(prefix)
            menu=QMenu(self)
            if not options:menu.addAction('Aucune commande enregistrée').setEnabled(False)
            for item in options:
                action=menu.addAction(item['category']+' / '+item['name'])
                action.triggered.connect(lambda checked=False,c=item:self._insert_quick(c))
            menu.exec(self.mapToGlobal(self.rect().center()))
            return
        if event.key() in (Qt.Key.Key_Return,Qt.Key.Key_Enter):self._quick_prefix=''
        elif event.key()==Qt.Key.Key_Backspace:self._quick_prefix=self._quick_prefix[:-1]
        elif event.text() and event.text().isprintable() and not event.modifiers() & (Qt.KeyboardModifier.ControlModifier|Qt.KeyboardModifier.AltModifier):
            self._quick_prefix=(self._quick_prefix+event.text())[-60:]
        super().keyPressEvent(event)
    def _insert_quick(self,item):
        try:command=expand(item['command'],self.quick_registry.variables)
        except ValueError as exc:
            QMessageBox.warning(self,'Variable manquante',str(exc));return
        # Insert only; Enter remains the user's decision.
        self.sendText(command)

class TerminalTile(NovaOneTerminalFrame):
    closed=Signal()
    def __init__(self,session_name,command,remote=False,parent=None):
        super().__init__(parent)
        self.session_name=session_name
        self.remote=remote
        v=QVBoxLayout(self);v.setContentsMargins(9,9,9,8);v.setSpacing(4)
        self._tile_layout=v
        h=QHBoxLayout()
        status_label=QLabel('●  '+('SSH / '+session_name if remote else 'LOCAL / '+session_name))
        status_label.setObjectName('sessionBadge');h.addWidget(status_label)
        h.addStretch()
        close_button=NovaOneCloseButton(self)
        close_button.clicked.connect(self.closed.emit)
        h.addWidget(close_button)
        v.addLayout(h)
        self.terminal=Terminal(command,self,session_name=None if remote else session_name)
        self.terminal.setMinimumSize(80,65)
        self.setMinimumSize(142,112)
        v.addWidget(self.terminal,1)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        # Keep the frame's beveled SVG visible while maximising usable PTY space.
        if self.width()<340 or self.height()<240:
            self._tile_layout.setContentsMargins(6,7,6,6)
        else:
            self._tile_layout.setContentsMargins(9,9,9,8)

class EmptyTile(Frame):
    requested=Signal()
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setMinimumSize(110,100)
        v=QVBoxLayout(self);v.setContentsMargins(8,8,8,8)
        v.addStretch()
        b=button('⬡  +',lambda:self.requested.emit(),name='add')
        b.setStyleSheet('font-size:31px;color:#2ce7ff;border:0;background:transparent;')
        v.addWidget(b)
        t=QLabel('AJOUTER UN TERMINAL / UNE APPLICATION')
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setWordWrap(True)
        t.setMinimumWidth(0)
        t.setStyleSheet('color:#19cce9;font-weight:bold;letter-spacing:1px;')
        v.addWidget(t);v.addStretch()

class ConnectDialog(GlassDialog):
    def __init__(self,parent=None):
        super().__init__(parent,'NEXUS — Nouvelle session')
        self.setMinimumSize(600,480)
        v=self.body;f=QFormLayout();v.addLayout(f)
        self.mode=QComboBox();self.mode.addItems(['Terminal local partageable','Terminal distant via SSH'])
        f.addRow('Type',self.mode)
        self.name=QLineEdit('nexus-'+uuid.uuid4().hex[:6]);f.addRow('Session tmux',self.name)
        self.host=QLineEdit();self.host.setPlaceholderText('utilisateur@192.168.1.20')
        f.addRow('SSH distant',self.host)
        self.mode.currentIndexChanged.connect(lambda n:self.host.setEnabled(n==1))
        self.host.setEnabled(False)
        v.addWidget(QLabel('Le partage utilise SSH + tmux, sans serveur exposé ni mot de passe enregistré.'))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);v.addWidget(buttons)
    def values(self):
        name=self.name.text().strip()
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,48}',name):
            raise ValueError('Nom de session : lettres, chiffres, _ et - uniquement.')
        remote=self.mode.currentIndex()==1
        host=self.host.text().strip()
        if remote and not re.fullmatch(r'[A-Za-z0-9_.-]+@[A-Za-z0-9_.:-]+',host):
            raise ValueError('Adresse SSH attendue : utilisateur@hôte')
        return name,remote,host

def local_cmd(name):
    return 'tmux new-session -A -s '+shlex.quote(name)
def remote_cmd(name,host):
    # SSH performs its own host key verification. No StrictHostKeyChecking=no.
    return 'ssh -t '+shlex.quote(host)+' '+shlex.quote('tmux new-session -A -s '+shlex.quote(name))

class SettingsHub(GlassDialog):
    def __init__(self,parent):
        super().__init__(parent,'PARAMÈTRES NEXUS')
        self.setMinimumSize(660,480)
        from PySide6.QtWidgets import QTabWidget,QFileDialog
        tabs=QTabWidget(self);self.body.addWidget(tabs,1)
        connection=QWidget();cl=QVBoxLayout(connection)
        cl.addWidget(QLabel('Connexions SSH / FTP / TCP / HTTP'))
        b=NovaOneButton('Connexions SSH');b.clicked.connect(lambda:ConnectionsDialog(self).exec());cl.addWidget(b);cl.addStretch()
        from PySide6.QtWidgets import QCheckBox
        from nexus_pairing import enabled,set_enabled
        pair=QCheckBox('Autoriser la découverte N3XV5 sur le réseau local')
        pair.setChecked(enabled())
        pair.setToolTip('Émet une annonce UDP locale. Aucune clé privée n’est transmise.')
        pair.toggled.connect(lambda checked:(set_enabled(checked),QMessageBox.information(self,'Appairage N3XV5','Redémarre le Terminal pour appliquer le changement.')))
        cl.addWidget(pair)
        cl.addWidget(QLabel('Appairage : SSH ▾ → Appareils du réseau. Confirmation obligatoire sur les deux PC.'))
        tabs.addTab(connection,'Connexions')
        appearance=QWidget();ap=QVBoxLayout(appearance)
        ap.addWidget(QLabel('NOVA 1.0 NEONGLASS  /  EFFETS VISUELS'))
        animation=QCheckBox('Reflets électriques discrets (terminal actif seulement)')
        animation.setChecked(parent.animations_enabled)
        animation.toggled.connect(parent.set_animations_enabled)
        ap.addWidget(animation)
        op_label=QLabel(f'Opacité des terminaux : {parent.terminal_opacity} %')
        ap.addWidget(op_label)
        opacity=QSlider(Qt.Orientation.Horizontal)
        opacity.setRange(65,100);opacity.setSingleStep(1)
        opacity.setValue(parent.terminal_opacity)
        opacity.valueChanged.connect(lambda value:(op_label.setText(f'Opacité des terminaux : {value} %'),parent.set_terminal_opacity(value)))
        ap.addWidget(opacity)
        ap.addWidget(QLabel('Le contenu des terminaux reste lisible : seule la surface du terminal est ajustée.'))
        ap.addStretch()
        tabs.addTab(appearance,'Apparence')
        updates=QWidget();ul=QVBoxLayout(updates)
        ul.addWidget(QLabel('NEXUS Update — canal stable'))
        ul.addWidget(QLabel('Importer une archive .deb locale ou rechercher une version sur le serveur.'))
        ul.addWidget(QLabel('Les mises à jour demandent confirmation et sont installées via apt.'))
        self.result=QPlainTextEdit();self.result.setReadOnly(True);self.result.setMaximumHeight(155)
        ul.addWidget(self.result)
        local=NovaOneButton('Importer .deb…');local.clicked.connect(self.local_update);ul.addWidget(local)
        check=NovaOneButton('Rechercher sur le serveur');check.clicked.connect(self.server_check);ul.addWidget(check)
        update=NovaOneButton('Installer la mise à jour serveur…');update.clicked.connect(self.server_update);ul.addWidget(update)
        ul.addStretch();tabs.addTab(updates,'Mise à jour')
        close=NovaOneButton('Fermer');close.clicked.connect(self.accept);self.body.addWidget(close)
    def cli(self,*args):
        import sys
        return [sys.executable,str(HERE/'nexus_updater.py'),*args]
    def local_update(self):
        from PySide6.QtWidgets import QFileDialog
        file,_=QFileDialog.getOpenFileName(self,'Choisir un paquet NEXUS',str(Path.home()/'Téléchargements'),'Paquets Debian (*.deb)')
        if not file:return
        self.result.setPlainText('Paquet sélectionné : '+file)
        if QMessageBox.question(self,'Confirmer','Vérifier et installer ce paquet NEXUS ?')!=QMessageBox.StandardButton.Yes:return
        self.launch_installer('install-file','--file',file)
    def server_check(self):
        import subprocess
        p=subprocess.run(self.cli('check'),capture_output=True,text=True,timeout=20)
        self.result.setPlainText((p.stdout+'\n'+p.stderr).strip() or 'Aucune réponse')
    def server_update(self):
        if QMessageBox.question(self,'Confirmer','Télécharger et installer une mise à jour NEXUS depuis le serveur ?')!=QMessageBox.StandardButton.Yes:return
        self.launch_installer('update')
    def launch_installer(self,*args):
        import subprocess
        # Polkit requests authentication through the desktop; never run a shell from an update manifest.
        cmd=['pkexec',*self.cli(*args)] if shutil.which('pkexec') else None
        if not cmd:
            self.result.setPlainText('pkexec indisponible : installe policykit-1 ou utilise le CLI dans un terminal.')
            return
        try:
            subprocess.Popen(cmd,start_new_session=True)
            self.result.setPlainText('Installation demandée. Le dialogue d’autorisation système peut apparaître.\nRelance NEXUS après mise à jour.')
        except OSError as e:self.result.setPlainText(str(e))

class Workspace(QWidget):
    event=Signal(str,object)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setObjectName('root')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        self.setAutoFillBackground(True)
        self.setStyleSheet(STYLE)
        self.setMinimumSize(680,455)
        self.ui_settings=QSettings('N3XV5', 'TerminalHUD')
        self.mode='quad';self.tiles=[None]*4;self._layout_root=None
        self.terminal_opacity=max(65,min(100,int(self.ui_settings.value('opacity',82))))
        self.animations_enabled=self.ui_settings.value('animations',True,type=bool)
        self.registry=Registry()
        self.active_tile=None
        self.outer=QVBoxLayout(self);self.outer.setContentsMargins(5,5,5,5);self.outer.setSpacing(5)
        self.header=HeaderCircuit();self.header.setFixedHeight(72)
        hh=QHBoxLayout(self.header);hh.setContentsMargins(16,8,15,8)
        logo=QLabel();logo.setPixmap(icon('nexus').pixmap(QSize(49,49)));hh.addWidget(logo)
        titlecol=QVBoxLayout()
        self.title_label=self.label('N3XV5 Terminal — NOVA 1.0','title')
        self.subtitle_label=self.label('M U L T I - T E R M I N A L   /   S S H   /   S C R I P T S','sub')
        titlecol.addWidget(self.title_label);titlecol.addWidget(self.subtitle_label)
        hh.addLayout(titlecol);hh.addStretch()
        self.status=self.label('SESSIONS : 0','dim');hh.addWidget(self.status)
        self.online_label=self.label('●  LOCAL / READY','dim');hh.addWidget(self.online_label)
        # Actual QMovie (not unsupported SVG-CSS animation), only one subtle moving signal.
        self.signal_label=QLabel();self.signal_label.setFixedSize(65,25)
        self.signal_movie=QMovie(str(HERE/'assets'/'animations'/'ElectroBlueNEON_pcb_signal.gif'))
        if self.signal_movie.isValid():
            self.signal_movie.setScaledSize(QSize(65,25))
            self.signal_label.setMovie(self.signal_movie)
            if self.animations_enabled:self.signal_movie.start()
            hh.addWidget(self.signal_label)
        self.window_controls=QWidget()
        controls=QHBoxLayout(self.window_controls)
        controls.setContentsMargins(10,0,0,0);controls.setSpacing(4)
        self.min_btn=HexWindowButton('min')
        self.max_btn=HexWindowButton('max')
        self.close_btn=HexWindowButton('close')
        controls.addWidget(self.min_btn);controls.addWidget(self.max_btn);controls.addWidget(self.close_btn)
        self.window_controls.hide()  # Standalone only; embedded QWidget never owns the host window.
        hh.addWidget(self.window_controls)
        self.outer.addWidget(self.header)
        bar=QHBoxLayout();bar.setSpacing(5)
        self.bar=bar
        # Terminal workspace is already visible; no dead 'Terminals' action.
        bar.addWidget(button('Sessions',self.show_sessions,'apps'))
        self.ssh_btn=button('SSH ▾',self.show_ssh_menu,'activity');bar.addWidget(self.ssh_btn)
        bar.addWidget(button('Paramètres',self.show_settings,'settings'))
        self.scripts_btn=button('Scripts ▾',self.show_scripts,'code');bar.addWidget(self.scripts_btn)
        self.display_btn=button('Affichage ▾',self.show_display,'settings');bar.addWidget(self.display_btn)
        bar.addStretch()
        bar.addWidget(button('+ Terminal',self.add_session,'terminal'))
        from nexus_pairing import PairingService
        self.pairing_service=PairingService()
        self.pairing_service.start()
        self.outer.addLayout(bar)
        body=QHBoxLayout();body.setSpacing(5);self.outer.addLayout(body,1)
        # Reserved blank left column: no duplicate or placeholder controls.
        self.nav=NeonGlassPanel(accent='#0fa8d0',cut=12);self.nav.setFixedWidth(148)
        self.nav.setToolTip('')
        body.addWidget(self.nav)
        self.stage=NeonGlassPanel(accent='#0ea8d4',cut=16);self.stage.setObjectName('stage')
        # Draw bevel/glass natively; keep user-supplied SVG assets optional, not forced.
        self.stage.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self.stage_layout=QVBoxLayout(self.stage)
        self.stage_layout.setContentsMargins(9,10,9,9);body.addWidget(self.stage,1)
        self.rebuild()
        QTimer.singleShot(0,self.apply_responsive)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.apply_responsive()
    def apply_responsive(self):
        w=self.width()
        self.nav.setVisible(w>=1020)
        self.subtitle_label.setVisible(w>=1040)
        self.online_label.setVisible(w>=1160)
        self.title_label.setText('N3XV5 Terminal' if w<790 else 'N3XV5 Terminal — NOVA 1.0')
    @staticmethod
    def label(text,name=None):
        l=QLabel(text)
        if name:l.setObjectName(name)
        return l
    def show_ssh_menu(self):
        menu=QMenu(self)
        menu.addAction('Connexions SSH…',lambda:ConnectionsDialog(self,'SSH').exec())
        menu.addAction('Clés SSH…',self.show_ssh_keys)
        menu.addSeparator()
        menu.addAction('SSH local / réseau LAN…',self.show_lan_ssh)
        menu.addAction('Appareils du réseau / Appairage…',self.show_pairing)
        menu.exec(self.ssh_btn.mapToGlobal(self.ssh_btn.rect().bottomLeft()))

    def show_pairing(self):
        from nexus_pairing_dialog import PairingDialog
        PairingDialog(self.pairing_service,self).exec()

    def show_lan_ssh(self):
        from nexus_lan_ssh import LANSSHDialog
        LANSSHDialog(self).exec()

    def closeEvent(self,event):
        if hasattr(self,'signal_movie'):self.signal_movie.stop()
        if hasattr(self,'pairing_service'):self.pairing_service.shutdown()
        super().closeEvent(event)

    def emit_status(self):
        self.status.setText('SESSIONS : '+str(sum(x is not None for x in self.tiles)))
    def rebuild(self):
        # Detach the live terminal widgets before destroying old splitter wrappers.
        old=self._layout_root
        if old:
            for tile in self.tiles:
                if tile is not None:tile.setParent(self.stage)
            self.stage_layout.removeWidget(old);old.hide();old.deleteLater()
        slots=4 if self.mode=='quad' else 3
        frames=[]
        for i in range(slots):
            tile=self.tiles[i]
            if tile is None:
                tile=EmptyTile()
                tile.requested.connect(lambda index=i:self.add_session(index))
            frames.append(tile)
        def split(orientation,items):
            w=QSplitter(orientation)
            w.setObjectName('splitSurface')
            w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
            w.setHandleWidth(5);w.setChildrenCollapsible(False)
            for item in items:w.addWidget(item)
            w.setSizes([100]*len(items))
            return w
        h=Qt.Orientation.Horizontal;v=Qt.Orientation.Vertical
        if self.mode=='quad':
            root=split(v,[split(h,frames[:2]),split(h,frames[2:])])
        elif self.mode=='left':
            root=split(h,[frames[0],split(v,frames[1:])])
        else:
            root=split(h,[split(v,frames[:2]),frames[2]])
        self._layout_root=root;self.stage_layout.addWidget(root)
        self.emit_status()
    def change_layout(self,mode):
        if mode==self.mode:return
        if mode!='quad' and self.tiles[3] is not None:
            QMessageBox.information(self,'Disposition','Ferme ou déplace le quatrième terminal avant de passer à trois panneaux.')
            return
        self.mode=mode;self.rebuild();self.event.emit('terminal.layout.changed',{'layout':mode})
    def add_session(self,index=None):
        if not shutil.which('tmux'):
            show_notice(self,'TMUX ABSENT','Installe tmux : sudo apt install tmux','Warning')
            return
        d=ConnectDialog(self)
        if d.exec()!=QDialog.DialogCode.Accepted:return
        try:name,remote,host=d.values()
        except ValueError as e:show_notice(self,'PARAMÈTRES INVALIDES',str(e),'Warning');return
        max_slots=4 if self.mode=='quad' else 3
        if index is None:index=next((i for i in range(max_slots) if self.tiles[i] is None),None)
        if index is None or self.tiles[index] is not None:
            show_notice(self,'PANNEAUX OCCUPÉS','Choisis un panneau vide.','Info');return
        command=remote_cmd(name,host) if remote else local_cmd(name)
        tile=TerminalTile(name,command,remote)
        tile.closed.connect(lambda t=tile:self.close_tile(t))
        tile.terminal.apply_opacity(self.terminal_opacity)
        self.tiles[index]=tile
        self._wire_tile(tile)
        self.rebuild()
        self.event.emit('terminal.session.created',{'name':name,'remote':remote,'slot':index})
        if not remote:self.share_dialog(name)
    def close_tile(self,tile):
        i=self.tiles.index(tile)
        self.tiles[i]=None;self.rebuild();tile.close();tile.deleteLater()
        self.event.emit('terminal.session.detached',{'name':tile.session_name})
    def share_dialog(self,name):
        user=os.environ.get('USER','utilisateur')
        host=socket.gethostname()
        command='ssh -t '+shlex.quote(user+'@'+host)+' '+shlex.quote('tmux attach -t '+shlex.quote(name))
        d=QDialog(self);d.setWindowTitle('Partager la session NEXUS')
        v=QVBoxLayout(d)
        v.addWidget(QLabel('Depuis le PC ASUS, via SSH (clé SSH autorisée) :'))
        output=QPlainTextEdit(command);output.setReadOnly(True);output.setMaximumHeight(85);v.addWidget(output)
        v.addWidget(QLabel('La session tmux est partagée : affichage ET saisie collaborative.\n'
                           'Utilise un compte SSH dédié si nécessaire. Fermer le panneau ne tue pas tmux.\n'
                           'La résolution peut varier entre les deux machines.'))
        v.addWidget(button('Fermer',d.accept));d.exec()
    def open_command(self,name,command,remote=True):
        max_slots=4 if self.mode=='quad' else 3
        index=next((i for i in range(max_slots) if self.tiles[i] is None),None)
        if index is None:
            show_notice(self,'PANNEAUX OCCUPÉS','Aucun emplacement disponible.','Info');return False
        tile=TerminalTile(name,command,remote)
        tile.closed.connect(lambda t=tile:self.close_tile(t))
        tile.terminal.apply_opacity(self.terminal_opacity)
        self.tiles[index]=tile;self._wire_tile(tile);self.rebuild()
        self.event.emit('terminal.session.created',{'name':name,'remote':remote,'slot':index})
        return True
    def show_ssh_keys(self):
        from nexus_ssh_keys import SSHKeysDialog
        SSHKeysDialog(self).exec()
    def set_terminal_opacity(self,value):
        self.terminal_opacity=int(value)
        self.ui_settings.setValue('opacity',self.terminal_opacity)
        for tile in self.tiles:
            if tile:tile.terminal.apply_opacity(self.terminal_opacity)
    def set_animations_enabled(self, enabled):
        self.animations_enabled=bool(enabled)
        self.ui_settings.setValue('animations',self.animations_enabled)
        self.stage.set_animated(self.animations_enabled)
        if self.signal_movie.isValid():
            if self.animations_enabled:self.signal_movie.start()
            else:self.signal_movie.stop()
        for tile in self.tiles:
            if tile:
                tile.set_animated(self.animations_enabled and tile is self.active_tile)
    def show_sessions(self):
        SessionDialog(self,self).exec()
    def show_settings(self):
        SettingsHub(self).exec()
    def _wire_tile(self,tile):
        tile.terminal.quick_registry=self.registry
        tile.terminal.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tile.terminal.customContextMenuRequested.connect(lambda pos,t=tile:self.terminal_menu(t,pos))
        tile.terminal.installEventFilter(self)
        self.active_tile=tile
        for other in self.tiles:
            if other:
                other.set_animated(self.animations_enabled)
                other.set_active(other is tile)
    def eventFilter(self,obj,event):
        from PySide6.QtCore import QEvent
        if event.type()==QEvent.Type.FocusIn:
            for tile in self.tiles:
                if tile and tile.terminal is obj:
                    self.active_tile=tile
                    for other in self.tiles:
                        if other:other.set_active(other is tile)
                    break
        return super().eventFilter(obj,event)
    def _target(self):
        if self.active_tile in self.tiles:return self.active_tile
        return next((t for t in self.tiles if t),None)
    def _commands_menu(self,menu):
        add=menu.addAction('＋ Ajouter une commande…')
        add.triggered.connect(self.add_quick_command)
        menu.addSeparator()
        for category in sorted({c['category'] for c in self.registry.commands}):
            group=menu.addMenu(category)
            for item in self.registry.commands:
                if item['category']==category:
                    action=group.addAction(item['name'])
                    action.triggered.connect(lambda checked=False,c=item:self.run_quick(c))
        if not self.registry.commands:menu.addAction('Aucune commande enregistrée').setEnabled(False)
    def show_scripts(self):
        menu=QMenu(self);self._commands_menu(menu)
        menu.exec(self.scripts_btn.mapToGlobal(self.scripts_btn.rect().bottomLeft()))
    def terminal_menu(self,tile,pos):
        self.active_tile=tile
        menu=QMenu(tile.terminal)
        sub=menu.addMenu('Commandes rapides');self._commands_menu(sub)
        menu.addSeparator()
        menu.addAction('Copier la sélection',lambda:QApplication.clipboard().setText(tile.terminal.selectedText()))
        menu.addAction('Coller',lambda:tile.terminal.pasteClipboard())
        menu.exec(tile.terminal.mapToGlobal(pos))
    def run_quick(self,item):
        tile=self._target()
        if tile is None:show_notice(self,'TERMINAL REQUIS','Sélectionne ou ouvre un terminal.','Info');return
        try:command=expand(item['command'],self.registry.variables)
        except ValueError as e:show_notice(self,'VARIABLE MANQUANTE',str(e),'Warning');return
        if len(command)>4096:show_notice(self,'COMMANDE TROP LONGUE','Limite de 4096 caractères.','Warning');return
        # Explicit confirmation for all commands; never silently execute arbitrary shell.
        if QMessageBox.question(self,'Exécuter dans '+tile.session_name,command, QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        tile.terminal.sendText(command+'\n')
    def add_quick_command(self):
        dlg=GlassDialog(self,'N3XV5 — Ajouter une commande')
        dlg.setMinimumSize(620,560)
        # Artwork is translucent already; don't overwrite its skin with a flat fill.
        layout=dlg.body;form=QFormLayout();layout.addLayout(form)
        name=QLineEdit();category=QComboBox();category.setEditable(True);category.addItems(['SSH','Git','Docker','Système','Personnalisé'])
        shell=QPlainTextEdit();shell.setPlaceholderText('ssh -p ${SSH_PORT} ${SSH_USER}@${SSH_HOST}');shell.setMaximumHeight(85)
        form.addRow('Nom',name);form.addRow('Type / Application',category);form.addRow('Commande shell',shell)
        layout.addWidget(QLabel('Variables du profil : ${NOM_VARIABLE}'))
        vn=QLineEdit();vv=QLineEdit();feedback=QLabel('');feedback.setStyleSheet('font-size:9px;color:#54e3a0;')
        form.addRow('Nouvelle variable',vn);form.addRow('Valeur',vv);layout.addWidget(feedback)
        def check(text):
            if not text:return feedback.setText('')
            try:validate_name(text)
            except ValueError:feedback.setStyleSheet('font-size:9px;color:#ff5265;');feedback.setText('Rouge : nom interdit');return
            if text in self.registry.variables:
                feedback.setStyleSheet('font-size:9px;color:#ffab46;');feedback.setText('Orange : variable existante');return
            feedback.setStyleSheet('font-size:9px;color:#52ef9c;');feedback.setText('Vert : nouveau nom disponible')
        vn.textChanged.connect(check)
        def add_var():
            try:self.registry.add_variable(vn.text().strip(),vv.text());vn.clear();vv.clear();feedback.setText('Variable ajoutée')
            except ValueError as e:QMessageBox.warning(dlg,'Variable',str(e))
        layout.addWidget(button('＋ Ajouter la variable',add_var))
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept);buttons.rejected.connect(dlg.reject);layout.addWidget(buttons)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            try:self.registry.add_command(name.text(),category.currentText(),shell.toPlainText())
            except ValueError as e:QMessageBox.warning(self,'Commande',str(e))

    def show_display(self):
        m=QMenu(self)
        layouts=m.addMenu('Disposition des panneaux')
        for text,key in [('2 × 2','quad'),('2 × 1 + 1 + 1','left'),('1 + 1 + 1 × 2','right')]:
            action=layouts.addAction(text)
            action.setCheckable(True);action.setChecked(key==self.mode)
            action.triggered.connect(lambda checked=False,k=key:self.change_layout(k))
        m.addSeparator()
        opacity=m.addMenu('Opacité des terminaux')
        for value in (65,75,82,90,100):
            action=opacity.addAction(f'{value} %')
            action.setCheckable(True);action.setChecked(value==self.terminal_opacity)
            action.triggered.connect(lambda checked=False,v=value:self.set_terminal_opacity(v))
        m.addAction('Sans grille — espace libre').setEnabled(False)
        m.exec(self.display_btn.mapToGlobal(self.display_btn.rect().bottomLeft()))
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('N3XV5 Terminal HUD — NOVA 1.0 NeonGlass v1.4.3')
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.resize(1250,760);self.setMinimumSize(710,490)
        self.workspace=Workspace()
        self.setCentralWidget(self.workspace)
        self.workspace.window_controls.show()
        self.workspace.min_btn.clicked.connect(self.showMinimized)
        self.workspace.max_btn.clicked.connect(self.toggle_maximize)
        self.workspace.close_btn.clicked.connect(self.close)
        self.setMouseTracking(True)
        self._edge=7
    def toggle_maximize(self):
        if self.isMaximized():self.showNormal()
        else:self.showMaximized()
        self.workspace.max_btn.setToolTip('Restaurer' if self.isMaximized() else 'Maximiser')
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and not self.isMaximized():
            x,y=event.position().x(),event.position().y()
            edges=Qt.Edge(0)
            if x<self._edge:edges|=Qt.Edge.LeftEdge
            elif x>=self.width()-self._edge:edges|=Qt.Edge.RightEdge
            if y<self._edge:edges|=Qt.Edge.TopEdge
            elif y>=self.height()-self._edge:edges|=Qt.Edge.BottomEdge
            if edges:
                handle=self.windowHandle()
                if handle and handle.startSystemResize(edges):
                    event.accept();return
        super().mousePressEvent(event)
def create_widget(context=None,parent=None):
    widget=Workspace(parent)
    if context is not None and callable(getattr(context,'publish',None)):
        widget.event.connect(context.publish)
    return widget
def create_shared_terminal_widget(host,session,parent=None):
    """Control Center 2.1 can embed a real SSH-attached QTermWidget directly."""
    if not re.fullmatch(r'[A-Za-z0-9_.-]+@[A-Za-z0-9_.:-]+',host):
        raise ValueError('Invalid SSH user@host')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,48}',session):
        raise ValueError('Invalid tmux session name')
    return Terminal(remote_cmd(session,host),parent)
def main():
    app=QApplication.instance() or QApplication([])
    app.setStyle('Fusion')
    app.setStyleSheet('''QMessageBox,QInputDialog,QDialog {background:#061827;color:#e7faff;}
        QMessageBox QLabel {color:#e3f9ff;background:transparent;}
        QMessageBox QPushButton,QDialogButtonBox QPushButton {
            background:#092b43;color:#eaffff;border:1px solid #269cc8;
            padding:7px 18px;min-height:24px;}
        QMessageBox QPushButton:hover,QDialogButtonBox QPushButton:hover {
            background:#104d69;border:1px solid #51eeff;}
        QToolTip {background:#082638;color:#f5ffff;border:1px solid #26caf5;}''')
    w=MainWindow();w.show()
    return app.exec()
if __name__=='__main__':raise SystemExit(main())
