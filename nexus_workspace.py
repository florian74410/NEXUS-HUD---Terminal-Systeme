#!/usr/bin/env python3
"""NEXUS Workspace v0.5: dockable Qt workspace and tmux-over-SSH shared sessions."""
from __future__ import annotations
import os, re, shlex, shutil, socket, subprocess, uuid
from pathlib import Path
from PySide6.QtCore import Qt, QSize, QTimer, Signal, QPoint
from PySide6.QtGui import QIcon, QFont, QColor, QPainter, QPen, QLinearGradient, QPolygonF
from PySide6.QtWidgets import (QApplication,QWidget,QMainWindow,QVBoxLayout,QHBoxLayout,
 QGridLayout,QLabel,QPushButton,QComboBox,QMenu,QDialog,QFormLayout,QLineEdit,
 QDialogButtonBox,QMessageBox,QSplitter,QFrame,QPlainTextEdit,QCheckBox,QSpinBox,QSizePolicy,QStyleFactory)
from pyside6_qtermwidget import QTermWidget
from nexus_connections import ConnectionsDialog, SessionDialog, identity

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
"""
def icon(name):
    return QIcon(str(ICONS/(name+'.svg')))
def button(text,callback,ico=None,name=None):
    b=QPushButton(text)
    if ico:b.setIcon(icon(ico));b.setIconSize(QSize(20,20))
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
    """Painted hexagonal window control: no stock titlebar icons."""
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
        p.setPen(QPen(QColor('#ff747a' if self._hover else '#bb3746'),1.5))
        p.setBrush(QColor('#51202b' if self._hover else '#140d1a'))
        p.drawPolygon(poly)
        p.setPen(QPen(QColor('#ff858b' if self._hover else '#f04b5c'),2.2))
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
    def __init__(self,command,parent=None):
        super().__init__(0,parent)
        self.setTerminalFont(QFont('DejaVu Sans Mono',10))
        self.setObjectName('terminalHost')
        self.setHistorySize(8000)
        self.setTerminalSizeHint(False)
        self.setColorScheme('DarkPastels')
        self.setShellProgram('/bin/bash')
        self.startShellProgram()
        QTimer.singleShot(350,lambda:self.sendText(command+'\n'))

class TerminalTile(Frame):
    closed=Signal()
    def __init__(self,session_name,command,remote=False,parent=None):
        super().__init__(parent)
        self.session_name=session_name
        self.remote=remote
        v=QVBoxLayout(self);v.setContentsMargins(9,9,9,8);v.setSpacing(5)
        h=QHBoxLayout()
        h.addWidget(QLabel('●  '+('SSH / '+session_name if remote else 'Bash / '+session_name)))
        h.addStretch()
        h.addWidget(button('×',lambda:self.closed.emit()))
        v.addLayout(h)
        self.terminal=Terminal(command,self)
        self.terminal.setMinimumSize(80,70)
        self.setMinimumSize(140,110)
        v.addWidget(self.terminal,1)

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

class ConnectDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent);self.setWindowTitle('NEXUS — Nouvelle session')
        v=QVBoxLayout(self);f=QFormLayout();v.addLayout(f)
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
    return 'ssh -t '+shlex.quote(host)+' '+shlex.quote('tmux attach-session -t '+shlex.quote(name))

class Workspace(QWidget):
    event=Signal(str,object)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setObjectName('root')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        self.setAutoFillBackground(True)
        self.setStyleSheet(STYLE)
        self.setMinimumSize(580,420)
        self.mode='quad';self.tiles=[None]*4;self._layout_root=None
        self.outer=QVBoxLayout(self);self.outer.setContentsMargins(5,5,5,5);self.outer.setSpacing(5)
        self.header=HeaderCircuit();self.header.setFixedHeight(72)
        hh=QHBoxLayout(self.header);hh.setContentsMargins(16,8,15,8)
        logo=QLabel();logo.setPixmap(icon('nexus').pixmap(QSize(49,49)));hh.addWidget(logo)
        titlecol=QVBoxLayout()
        self.title_label=self.label('NEXUS Terminal — ElectroBlueNEON','title')
        self.subtitle_label=self.label('MULTI-TERMINAL  /  REMOTE  /  SCRIPTS  /  AUTOMATION','sub')
        titlecol.addWidget(self.title_label);titlecol.addWidget(self.subtitle_label)
        hh.addLayout(titlecol);hh.addStretch()
        self.status=self.label('SESSIONS : 0','dim');hh.addWidget(self.status)
        self.online_label=self.label('●  ONLINE','dim');hh.addWidget(self.online_label)
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
        bar.addWidget(button('Terminals',lambda:None,'terminal'))
        bar.addWidget(button('Sessions',self.show_sessions,'apps'))
        bar.addWidget(button('Paramètres',self.show_settings,'settings'))
        bar.addWidget(button('Scripts',self.show_scripts,'code'))
        bar.addWidget(button('Affichage ▾',self.show_display,'settings'))
        bar.addStretch()
        bar.addWidget(button('+ Terminal',self.add_session,'terminal'))
        self.outer.addLayout(bar)
        body=QHBoxLayout();body.setSpacing(5);self.outer.addLayout(body,1)
        self.nav=Frame();self.nav.setFixedWidth(158)
        nv=QVBoxLayout(self.nav);nv.setContentsMargins(6,12,6,8)
        for text,ico in [('NEXUS Terminal','terminal'),('Applications','apps'),('Settings','settings')]:
            b=button(text,lambda t=text:self.nav_action(t),ico,'nav')
            if text=='NEXUS Terminal':b.setCheckable(True);b.setChecked(True)
            nv.addWidget(b)
        nv.addStretch();nv.addWidget(self.label('◈  ELECTROBLUE','dim'))
        body.addWidget(self.nav)
        self.stage=QWidget();self.stage.setObjectName('stage')
        self.stage.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        self.stage.setAutoFillBackground(True)
        self.stage.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self.stage_layout=QVBoxLayout(self.stage)
        self.stage_layout.setContentsMargins(0,0,0,0);body.addWidget(self.stage,1)
        self.rebuild()
        QTimer.singleShot(0,self.apply_responsive)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.apply_responsive()
    def apply_responsive(self):
        w=self.width()
        self.nav.setVisible(w>=940)
        self.subtitle_label.setVisible(w>=1040)
        self.online_label.setVisible(w>=1160)
        self.title_label.setText('NEXUS Terminal' if w<790 else 'NEXUS Terminal — ElectroBlueNEON')
    @staticmethod
    def label(text,name=None):
        l=QLabel(text)
        if name:l.setObjectName(name)
        return l
    def nav_action(self,text):
        if text=='Settings':self.show_settings()
        elif text=='Applications':self.add_session()
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
            QMessageBox.warning(self,'tmux absent','Installe tmux : sudo apt install tmux')
            return
        d=ConnectDialog(self)
        if d.exec()!=QDialog.DialogCode.Accepted:return
        try:name,remote,host=d.values()
        except ValueError as e:QMessageBox.warning(self,'Paramètres invalides',str(e));return
        max_slots=4 if self.mode=='quad' else 3
        if index is None:index=next((i for i in range(max_slots) if self.tiles[i] is None),None)
        if index is None or self.tiles[index] is not None:
            QMessageBox.information(self,'Panneaux occupés','Choisis un panneau vide.');return
        command=remote_cmd(name,host) if remote else local_cmd(name)
        tile=TerminalTile(name,command,remote)
        tile.closed.connect(lambda t=tile:self.close_tile(t))
        self.tiles[index]=tile
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
            QMessageBox.information(self,'Panneaux occupés','Aucun emplacement disponible.');return False
        tile=TerminalTile(name,command,remote)
        tile.closed.connect(lambda t=tile:self.close_tile(t))
        self.tiles[index]=tile;self.rebuild()
        self.event.emit('terminal.session.created',{'name':name,'remote':remote,'slot':index})
        return True
    def show_sessions(self):
        SessionDialog(self,self).exec()
    def show_settings(self):
        ConnectionsDialog(self).exec()
    def show_scripts(self):
        QMessageBox.information(self,'Scripts & macros','Le gestionnaire de macros v0.4 reste disponible dans nexus_terminal.py.\n'
                                'Cette interface v0.5 démarre volontairement sans application.')
    def show_display(self):
        m=QMenu(self)
        layouts=m.addMenu('Disposition des panneaux')
        for text,key in [('2 × 2','quad'),('2 × 1 + 1 + 1','left'),('1 + 1 + 1 × 2','right')]:
            action=layouts.addAction(text)
            action.setCheckable(True);action.setChecked(key==self.mode)
            action.triggered.connect(lambda checked=False,k=key:self.change_layout(k))
        m.addSeparator();m.addAction('Sans grille — espace libre').setEnabled(False)
        m.exec(self.mapToGlobal(self.rect().center()))
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('NEXUS Terminal — ElectroBlueNEON v1.0.0')
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.resize(1250,760);self.setMinimumSize(600,460)
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
    w=MainWindow();w.show()
    return app.exec()
if __name__=='__main__':raise SystemExit(main())
