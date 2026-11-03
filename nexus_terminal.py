#!/usr/bin/env python3
"""NEXUS Terminal • ElectroBlueNEON v0.3 • standalone / embedded Qt widget.

Genuine PTY consoles provided by pyside6-qtermwidget. Each live shell is kept
when rearranging panes. Success/error toasts are based on supervised QProcess
scripts, never regex-matched from arbitrary terminal output.
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QPoint, QProcess, QTimer, Signal, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QLinearGradient, QKeySequence, QShortcut, QMovie, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton, QToolButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSplitter, QTabWidget, QComboBox,
    QScrollArea, QMessageBox, QMenu, QFileDialog, QDialog, QDialogButtonBox,
    QLineEdit, QCheckBox, QPlainTextEdit, QSizePolicy, QStackedWidget,
)
from pyside6_qtermwidget import QTermWidget

VERSION = '0.4.0-dev'
HERE = Path(__file__).resolve().parent
FX = HERE / 'assets' / 'animations'
ICONS = HERE / 'assets' / 'icons'
MACROS = Path.home() / '.config' / 'nexus-terminal' / 'macros'
LAYOUTS = [('grid','Quad (2×2)',4), ('one','Focus (1)',1),
           ('two-columns','Horizontal (1×2)',2), ('two-rows','Vertical (2×1)',2),
           ('two-plus-one','2 + 1',3), ('one-plus-two','1 + 2',3)]
MODES = {key:count for key,_,count in LAYOUTS}
C = {'cyan':'#00dfff','bright':'#80f3ff','dark':'#04111d','ink':'#061723',
     'success':'#34e79c','error':'#ff566d','warning':'#ffc960','text':'#e7faff'}

QSS = '''
* {font-family:"DejaVu Sans";font-size:11px;color:#d7f5ff;outline:none;}
QWidget#nexusRoot,QWidget#mainBackground,QMainWindow{background:#020a13;}
QLabel#brand {font-size:19px;font-weight:700;color:#f1fdff;}
QLabel#overline{font-size:9px;letter-spacing:2px;color:#94cbdd;}
QLabel#section {font-size:11px;font-weight:700;color:#e9fcff;}
QLabel#muted {color:#83afc3;}
QLabel#statusGreen{color:#3df4ac;font-weight:700;}
QLabel#statusCyan{color:#78eaff;font-weight:700;}
QLabel#metric{font-size:15px;font-weight:bold;color:#effdff;}
QPushButton,QToolButton,QComboBox{background:#07283a;border:1px solid #187da2;
 border-radius:4px;min-height:19px;padding:5px 8px;color:#d4f5ff;}
QPushButton:hover,QToolButton:hover,QComboBox:hover{background:#0e425c;border:1px solid #41e9ff;}
QPushButton:pressed,QToolButton:pressed{background:#156682;}
QPushButton:checked{background:#12475f;border:1px solid #7bf5ff;color:white;}
QPushButton#danger:hover{border-color:#ed566e;color:#ff9dac;}
QPushButton#nav{background:transparent;border:0;border-bottom:1px solid #0b3049;
 text-align:left;padding:12px 13px;font-size:12px;}
QPushButton#nav:hover{background:#0d344b;border-left:2px solid #30dfff;}
QPushButton#nav:checked{background:#10516c;border:1px solid #48dfff;
 color:white;font-weight:bold;}
QPushButton#layout{padding:8px 4px;min-height:43px;}
QTabWidget::pane{border:0;background:transparent;}
QTabBar::tab{background:#062235;border:1px solid #146f8c;padding:8px 17px;
 min-width:62px;color:#b2dbe8;margin-right:3px;}
QTabBar::tab:selected{background:#0b4b62;border:1px solid #69e7ff;border-bottom:2px solid #48e9ff;color:#fff;}
QTabBar::tab:hover{background:#15546c;}
QSplitter::handle{background:#0b4d68;}
QSplitter::handle:hover{background:#28c8e9;}
QMenu{background:#061d2d;border:1px solid #18a2c8;padding:4px;}
QMenu::item{padding:7px 14px;}
QMenu::item:selected{background:#0b5975;}
QLineEdit,QPlainTextEdit{background:#031723;border:1px solid #157e9b;border-radius:4px;
 selection-background-color:#0d789a;padding:5px;}
QDialog{background:#061522;}
QScrollArea{background:transparent;border:0;}
QScrollBar:vertical{background:#051723;width:9px;}
QScrollBar::handle:vertical{background:#167996;border-radius:3px;min-height:20px;}
'''


def lbl(text, name=None, parent=None):
    out = QLabel(text, parent)
    if name: out.setObjectName(name)
    return out


def svg_icon(name):
    path = ICONS / (name + '.svg')
    return QIcon(str(path)) if path.is_file() else QIcon()


def btn(text, fn, name=None, tip=None, check=False, icon=None):
    w = QPushButton(text)
    if icon:
        w.setIcon(svg_icon(icon))
        w.setIconSize(QSize(19,19))
    if name: w.setObjectName(name)
    if tip: w.setToolTip(tip)
    w.setCheckable(check)
    w.clicked.connect(fn)
    return w


class NeonPanel(QFrame):
    """Responsive beveled glass frame; no raster stretching or blur filters."""
    def __init__(self, parent=None, accent='#10c7f4', cut=13, fill=True):
        super().__init__(parent)
        self.accent = QColor(accent)
        self.cut = cut
        self.fill_panel = fill
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w,h = self.width()-1,self.height()-1
        if w < 26 or h < 26: return
        k = min(self.cut,w//8,h//8)
        path = QPainterPath()
        path.moveTo(4+k,3);path.lineTo(w-4-k,3);path.lineTo(w-3,3+k)
        path.lineTo(w-3,h-4-k);path.lineTo(w-4-k,h-3)
        path.lineTo(4+k,h-3);path.lineTo(3,h-4-k);path.lineTo(3,3+k)
        path.closeSubpath()
        if self.fill_panel:
            grad = QLinearGradient(0,0,w,h)
            grad.setColorAt(0,QColor(5,29,47,245))
            grad.setColorAt(0.45,QColor(3,16,29,242))
            grad.setColorAt(1,QColor(4,26,40,245))
            p.fillPath(path,grad)
        for width,alpha in [(8,14),(4,28),(2,85)]:
            tone = QColor(self.accent);tone.setAlpha(alpha)
            p.setPen(QPen(tone,width));p.drawPath(path)
        p.setPen(QPen(self.accent,1.1));p.drawPath(path)
        p.setPen(QPen(QColor('#a1f7ff'),1.7))
        p.drawLine(19,3,min(w//3,115),3)
        p.drawLine(max(12,w-98),h-3,w-24,h-3)
        p.setPen(QPen(QColor('#135f80'),1))
        for shift in (0,7,14):
            p.drawLine(w-58+shift,11,w-47+shift,11)
        p.end()


class NeonButton(NeonPanel):
    clicked = Signal()
    def __init__(self, text, icon='▣', parent=None):
        super().__init__(parent,cut=7)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)
        h=QHBoxLayout(self);h.setContentsMargins(12,2,6,2);h.setSpacing(8)
        h.addWidget(lbl(icon,'statusCyan'))
        h.addWidget(lbl(text));h.addStretch()
    def mouseReleaseEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class Shell(QTermWidget):
    """Real Bash/QTermWidget console, never replaced with a mock editor."""
    def __init__(self,parent=None):
        super().__init__(0,parent)
        self.setTerminalFont(QFont('DejaVu Sans Mono',10))
        self.setHistorySize(6500)
        self.setTerminalSizeHint(False)
        self.setShellProgram('/bin/bash')
        self.setColorScheme('DarkPastels')
        self.startShellProgram()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.menu)
        self.shortcuts=[]
        for key,handler in [('Ctrl+Shift+C',self.copyClipboard),('Ctrl+Shift+V',self.pasteClipboard)]:
            sc=QShortcut(QKeySequence(key),self)
            sc.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            sc.activated.connect(handler);self.shortcuts.append(sc)
    def menu(self,pos):
        m=QMenu(self);m.addAction('Copier',self.copyClipboard);m.addAction('Coller',self.pasteClipboard)
        m.exec(self.mapToGlobal(pos))


class ConsoleFrame(NeonPanel):
    def __init__(self, shell, title, close_callback, focus_callback):
        super().__init__(accent='#1addfa',cut=13)
        self.shell = shell
        v=QVBoxLayout(self);v.setContentsMargins(7,8,7,7);v.setSpacing(3)
        hdr=QHBoxLayout();hdr.setSpacing(5)
        name=lbl('▣  ●  '+title,'section');hdr.addWidget(name);hdr.addStretch()
        b=btn('□',focus_callback,tip='Agrandir ce panneau')
        b.setFixedSize(27,25);hdr.addWidget(b)
        x=btn('×',close_callback,'danger',tip='Fermer le panneau')
        x.setFixedSize(27,25);hdr.addWidget(x)
        v.addLayout(hdr)
        underline=QFrame();underline.setFixedHeight(1);underline.setStyleSheet('background:#158db7;')
        v.addWidget(underline)
        v.addWidget(shell,1)


def splitter(orientation, children):
    w=QSplitter(orientation);w.setChildrenCollapsible(False);w.setHandleWidth(5)
    for child in children: w.addWidget(child)
    w.setSizes([100]*len(children))
    return w


class TerminalPage(QWidget):
    """Keep every live PTY when switching among layouts; no silent session loss."""
    sessionsChanged=Signal()
    def __init__(self, mode='grid', parent=None):
        super().__init__(parent)
        self.mode=mode
        self.shells=[Shell() for _ in range(MODES[mode])]
        self.focused=None
        self.outer=QVBoxLayout(self);self.outer.setContentsMargins(1,1,1,1);self.outer.setSpacing(1)
        self.widget=None
        self.build()
    def build(self):
        if self.widget:
            previous=self.widget
            self.outer.removeWidget(previous)
            for s in self.shells: s.setParent(self)
            previous.hide();previous.deleteLater()
        widgets=[]
        for i,shell in enumerate(self.shells):
            widgets.append(ConsoleFrame(shell,
                    ['Local bash','Scripts / Bash','SSH / VPS','Logs / Shell'][i] if i<4 else f'Console {i+1}',
                    lambda checked=False,index=i:self.close_pane(index),
                    lambda checked=False,index=i:self.focus_pane(index)))
        h,v=Qt.Orientation.Horizontal,Qt.Orientation.Vertical
        m=self.mode
        if m=='grid':root=splitter(v,[splitter(h,widgets[:2]),splitter(h,widgets[2:4])])
        elif m=='two-columns':root=splitter(h,widgets)
        elif m=='two-rows':root=splitter(v,widgets)
        elif m=='two-plus-one':root=splitter(h,[splitter(v,widgets[:2]),widgets[2]])
        elif m=='one-plus-two':root=splitter(h,[widgets[0],splitter(v,widgets[1:])])
        else:root=widgets[0]
        self.widget=root;self.outer.addWidget(root)
    def mode_change(self,mode):
        if mode==self.mode:return True
        count=MODES[mode]
        if count<len(self.shells):return False
        while len(self.shells)<count:self.shells.append(Shell())
        self.mode=mode;self.build();self.sessionsChanged.emit();return True
    def close_pane(self,index):
        if len(self.shells)<=1: return
        r=QMessageBox.question(self,'Fermer une session','Terminer cette session Bash ?',
             QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if r!=QMessageBox.StandardButton.Yes:return
        old=self.shells.pop(index);old.setParent(None);old.close();old.deleteLater()
        new_mode=next((m for m,_,num in LAYOUTS if num==len(self.shells)), 'one')
        self.mode=new_mode;self.build();self.sessionsChanged.emit()
    def focus_pane(self,index):
        # True focus: safely hide other console wrappers without touching their PTYs.
        if self.focused==index:self.focused=None
        else:self.focused=index
        frames=self.findChildren(ConsoleFrame)
        for frame in frames:
            if frame.shell in self.shells:
                frame.setVisible(self.focused is None or self.shells.index(frame.shell)==self.focused)
    def total(self):return len(self.shells)


class Toast(NeonPanel):
    def __init__(self,title,detail,kind,close, parent=None):
        palette={'success':('#2beb95','✓'), 'error':('#ff526a','⚠'),
                 'info':('#39dfff','ⓘ'), 'warning':('#ffc458','!')}
        color,glyph=palette.get(kind,palette['info'])
        super().__init__(parent,accent=color,cut=9)
        self.setFixedHeight(66)
        h=QHBoxLayout(self);h.setContentsMargins(13,7,9,7);h.setSpacing(8)
        ico=lbl(glyph);ico.setStyleSheet(f'font-size:21px;font-weight:bold;color:{color};')
        h.addWidget(ico)
        v=QVBoxLayout();v.setSpacing(1)
        title_lbl=lbl(title);title_lbl.setStyleSheet('font-weight:bold;color:white;')
        v.addWidget(title_lbl)
        detail_lbl=lbl(detail[:120],'muted');detail_lbl.setWordWrap(True);v.addWidget(detail_lbl)
        h.addLayout(v,1)
        close_btn=btn('×',close);close_btn.setFixedSize(22,24);h.addWidget(close_btn)


class SecretDialog(QDialog):
    """A protected entry field for application-controlled actions only."""
    def __init__(self,parent=None,reason='Saisir une donnée confidentielle'):
        super().__init__(parent);self.setModal(True)
        self.setWindowTitle('NEXUS • ENTER SECRET')
        self.setMinimumWidth(420)
        v=QVBoxLayout(self);v.setContentsMargins(20,18,20,18);v.setSpacing(11)
        v.addWidget(lbl('♙  ENTER SECRET','brand'))
        v.addWidget(lbl(reason))
        self.input=QLineEdit();self.input.setEchoMode(QLineEdit.EchoMode.Password)
        self.input.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        v.addWidget(self.input)
        reveal=QCheckBox('Afficher temporairement')
        reveal.toggled.connect(lambda show:self.input.setEchoMode(
            QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password))
        v.addWidget(reveal)
        controls=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        controls.accepted.connect(self.accept);controls.rejected.connect(self.reject)
        v.addWidget(controls)
        self.setStyleSheet(QSS)


class MacroManager(NeonPanel):
    """User-approved script execution: reliable exit codes and bounded output."""
    event=Signal(str,object)
    notification=Signal(str,str,str)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.proc=QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self.gather)
        self.proc.finished.connect(self.finished)
        self.proc.errorOccurred.connect(lambda _: self.notification.emit('Erreur de lancement',self.proc.errorString(),'error'))
        self.path=None
        v=QVBoxLayout(self);v.setContentsMargins(9,8,9,8)
        v.addWidget(lbl('SCRIPTS & MACROS','section'))
        self.script=lbl('Aucun script sélectionné','muted');v.addWidget(self.script)
        self.script_list=QComboBox()
        self.script_list.currentIndexChanged.connect(self.select_listed)
        v.addWidget(self.script_list)
        v.addWidget(btn('↻  Actualiser les macros',self.refresh_scripts,icon='refresh'))
        v.addWidget(btn('+  Sélectionner .sh',self.choose,icon='folder'))
        v.addWidget(btn('▶  Exécuter le script',self.execute))
        v.addWidget(btn('■  Arrêter',self.stop,'danger'))
        self.output=QPlainTextEdit();self.output.setReadOnly(True)
        self.output.setMaximumBlockCount(350)
        self.output.setPlaceholderText('Sortie du script exécuté…')
        self.output.setMaximumHeight(135)
        v.addWidget(self.output)
        self.refresh_scripts()
    def refresh_scripts(self):
        MACROS.mkdir(parents=True,exist_ok=True)
        self.script_list.blockSignals(True)
        self.script_list.clear()
        self.script_list.addItem('Choisir un script…',None)
        for path in sorted(MACROS.glob('*.sh')):
            if path.is_file():self.script_list.addItem(path.name,str(path))
        self.script_list.blockSignals(False)
    def select_listed(self,index):
        value=self.script_list.itemData(index)
        if value:
            self.path=Path(value)
            self.script.setText(self.path.name)
    def choose(self):
        MACROS.mkdir(parents=True,exist_ok=True)
        path,_=QFileDialog.getOpenFileName(self,'Choisir une macro .sh',str(MACROS),'Scripts (*.sh)')
        if path:
            self.path=Path(path)
            self.script.setText(self.path.name)
    def execute(self):
        if self.proc.state()!=QProcess.ProcessState.NotRunning:
            self.notification.emit('Script actif','Une exécution est déjà en cours.','warning');return
        if not self.path or not self.path.is_file() or self.path.suffix!='.sh':
            self.notification.emit('Aucun script','Sélectionne un fichier .sh.','warning');return
        confirm=QMessageBox.question(self,'Confirmation • Exécution',
            f'Exécuter ce script local avec tes permissions ?\n\n{self.path}',
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if confirm!=QMessageBox.StandardButton.Yes:return
        self.output.clear();self.proc.setProgram('/bin/bash');self.proc.setArguments([str(self.path)])
        self.proc.setWorkingDirectory(str(self.path.parent));self.proc.start()
        self.notification.emit('Script lancé',self.path.name,'info')
        self.event.emit('terminal.script.started',{'script':self.path.name})
    def gather(self):
        data=bytes(self.proc.readAllStandardOutput()).decode('utf-8',errors='replace')
        if data:self.output.insertPlainText(data[-10000:])
    def finished(self,code,status):
        self.gather()
        ok=(code==0 and status==QProcess.ExitStatus.NormalExit)
        self.notification.emit('Exécution réussie' if ok else 'Échec de la commande',
            f'{self.path.name if self.path else "Script"} • EXIT {code}', 'success' if ok else 'error')
        self.event.emit('terminal.script.finished',{'script':self.path.name if self.path else '',
                                                 'exit_code':code,'success':ok})
    def stop(self):
        if self.proc.state()==QProcess.ProcessState.NotRunning:return
        ans=QMessageBox.question(self,'Arrêter le script','Interrompre le processus en cours ?',
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if ans==QMessageBox.StandardButton.Yes:
            self.proc.terminate()
            QTimer.singleShot(1700,lambda:self.proc.kill() if self.proc.state()!=QProcess.ProcessState.NotRunning else None)


class MonitorStrip(NeonPanel):
    """Slow poll of local, real Linux metrics; no fake numbers."""
    def __init__(self,parent=None):
        super().__init__(parent,accent='#18aeda',cut=11)
        self.fields={}
        h=QHBoxLayout(self);h.setContentsMargins(11,7,11,7);h.setSpacing(13)
        for key,title in [('cpu','⚙  CPU'),('ram','▣  RAM'),('disk','▱  DISQUE'),('net','⌁  RÉSEAU'),('sessions','▤  SESSIONS')]:
            col=QVBoxLayout();col.setSpacing(1)
            col.addWidget(lbl(title,'muted'))
            value=lbl('—','metric');col.addWidget(value);self.fields[key]=value
            h.addLayout(col,1)
        self.last_cpu=None;self.last_net=None
        self.timer=QTimer(self);self.timer.timeout.connect(self.update_metrics)
        self.timer.start(2500);self.update_metrics()
    def update_metrics(self):
        try:
            vals=Path('/proc/stat').read_text().splitlines()[0].split()[1:]
            ns=[int(x) for x in vals];idle=ns[3]+(ns[4] if len(ns)>4 else 0);total=sum(ns)
            if self.last_cpu:
                dt=total-self.last_cpu[0];di=idle-self.last_cpu[1]
                if dt>0:self.fields['cpu'].setText(f'{max(0,min(100,100*(1-di/dt))):.0f}%')
            self.last_cpu=(total,idle)
        except (OSError,ValueError,IndexError):pass
        try:
            metrics={x.split(':')[0]:int(x.split()[1]) for x in Path('/proc/meminfo').read_text().splitlines() if ':' in x}
            total=metrics.get('MemTotal',0);free=metrics.get('MemAvailable',0)
            if total:self.fields['ram'].setText(f'{100*(total-free)/total:.0f}%')
        except (OSError,ValueError,IndexError):pass
        try:
            disk=shutil.disk_usage(Path.home());self.fields['disk'].setText(f'{100*disk.used/disk.total:.0f}%')
        except OSError:pass
        try:
            lines=Path('/proc/net/dev').read_text().splitlines()[2:]
            rx=tx=0
            for line in lines:
                interface,stats=line.split(':',1)
                if interface.strip()=='lo':continue
                cols=stats.split();rx+=int(cols[0]);tx+=int(cols[8])
            now=__import__('time').monotonic()
            if self.last_net:
                last_t,last_rx,last_tx=self.last_net;dt=max(0.001,now-last_t)
                self.fields['net'].setText(f'↓{(rx-last_rx)/dt/1024:.0f} ↑{(tx-last_tx)/dt/1024:.0f} KiB/s')
            self.last_net=(now,rx,tx)
        except (OSError,IndexError,ValueError):pass
    def set_sessions(self,n):self.fields['sessions'].setText(str(n))


class NexusTerminalWidget(QWidget):
    """Embed directly in NOVA Control Center QMdiSubWindow, no extra QApplication."""
    event=Signal(str,object)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setObjectName('nexusRoot');self.setStyleSheet(QSS)
        self.setMinimumSize(920,610)
        self._movies=[];self._toasts=[]
        outer=QVBoxLayout(self);outer.setContentsMargins(7,5,7,6);outer.setSpacing(6)
        outer.addWidget(self.build_header())
        body=QHBoxLayout();body.setSpacing(7);outer.addLayout(body,1)
        body.addWidget(self.build_nav())
        mid=QVBoxLayout();mid.setSpacing(5);body.addLayout(mid,1)
        mid.addLayout(self.build_toolbar())
        self.tabs=QTabWidget();self.tabs.setDocumentMode(True);self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_state)
        mid.addWidget(self.tabs,1)
        body.addWidget(self.build_right())
        self.toast_row=QHBoxLayout();self.toast_row.setSpacing(5)
        mid.addLayout(self.toast_row)
        self.monitor=MonitorStrip();outer.addWidget(self.monitor)
        self.new_tab()
        self.change_layout('grid')
        self.shortcut=QShortcut(QKeySequence('Ctrl+Shift+T'),self)
        self.shortcut.activated.connect(self.new_tab)

    def build_header(self):
        root=NeonPanel(accent='#35e6ff',cut=18)
        root.setFixedHeight(79)
        h=QHBoxLayout(root);h.setContentsMargins(21,10,15,10);h.setSpacing(10)
        mark=QLabel()
        mark.setPixmap(svg_icon('nexus').pixmap(QSize(55,55)))
        mark.setFixedSize(60,58)
        h.addWidget(mark)
        col=QVBoxLayout();col.setSpacing(1)
        col.addWidget(lbl('NEXUS Terminal — Multi Console','brand'))
        col.addWidget(lbl('M U L T I - T E R M I N A L    /    R E M O T E    /    S C R I P T S    /    A U T O M A T I O N','overline'))
        h.addLayout(col,1)
        scan=FX/'ElectroBlueNEON_pcb_signal.gif'
        if scan.exists():
            label=QLabel();label.setFixedSize(63,25)
            movie=QMovie(str(scan));movie.setScaledSize(label.size());label.setMovie(movie)
            movie.start();self._movies.append(movie);h.addWidget(label)
        self.sessions_lbl=lbl('SESSIONS: 0','statusCyan');h.addWidget(self.sessions_lbl)
        self.picker=QComboBox();self.picker.setMinimumWidth(150)
        for key,name,_ in LAYOUTS:self.picker.addItem(name,key)
        self.picker.currentIndexChanged.connect(self.pick_layout);h.addWidget(self.picker)
        online=lbl('●  ONLINE','statusGreen');h.addWidget(online)
        return root

    def build_nav(self):
        side=NeonPanel(accent='#0fa8d0',cut=12);side.setFixedWidth(206)
        v=QVBoxLayout(side);v.setContentsMargins(5,11,5,8);v.setSpacing(2)
        nav_items=[('home','Dashboard'),('apps','Applications'),('terminal','NEXUS Terminal'),
                   ('folder','Explorer'),('activity','Monitoring'),('code','Scripts & Macros'),
                   ('settings','Settings'),('palette','Themes')]
        for icon,name in nav_items:
            w=btn(name,lambda checked=False,n=name:self.nav_click(n),'nav',
                  check=True,icon=icon)
            if name=='NEXUS Terminal':w.setChecked(True)
            if name not in ('NEXUS Terminal','Scripts & Macros','Settings'):
                w.setToolTip('Disponible avec le futur NOVA Control Center')
            v.addWidget(w)
            if name=='NEXUS Terminal':self.active_nav=w
        v.addStretch()
        v.addWidget(lbl('◈    ELECTROBLUE', 'statusCyan'))
        v.addWidget(lbl('NEXUS SYSTEM SUITE','overline'))
        return side

    def nav_click(self,name):
        if name=='Scripts & Macros':self.macros.choose()
        elif name=='Settings':self.dialog_settings()
        elif name!='NEXUS Terminal':self.notify('Application externe',
                f'{name} sera proposé par le NOVA Control Center.','info')
        self.active_nav.setChecked(True)

    def build_toolbar(self):
        h=QHBoxLayout();h.setSpacing(5)
        for name,icon,fn in [('Terminals','▣',lambda:self.notify('Mode terminal','Consoles actives','info')),
             ('Sessions','▤',lambda:self.notify('Sessions',str(self.count_sessions())+' consoles Bash','info')),
             ('Scripts','⌘',lambda:self.macros.choose()),
             ('Logs','≡',lambda:self.show_logs())]:
            w=btn(icon+'  '+name,fn)
            h.addWidget(w)
        h.addWidget(btn('＋',self.new_tab));h.addStretch()
        return h

    def build_right(self):
        side=QWidget();side.setFixedWidth(305)
        v=QVBoxLayout(side);v.setContentsMargins(0,0,0,0);v.setSpacing(6)
        sessions=NeonPanel();ss=QVBoxLayout(sessions);ss.setContentsMargins(10,10,10,9);ss.setSpacing(5)
        ss.addWidget(lbl('◈  SESSIONS','section'))
        self.session_rows=[]
        for i in range(4):
            b=btn(f'●  Console {i+1}',lambda checked=False,index=i:self.focus_session(index),
                  icon='terminal')
            b.setMinimumHeight(27)
            ss.addWidget(b)
            self.session_rows.append(b)
        v.addWidget(sessions)
        self.macros=MacroManager();self.macros.notification.connect(self.notify)
        self.macros.event.connect(self.event.emit)
        v.addWidget(self.macros,1)
        actions=NeonPanel();ac=QVBoxLayout(actions);ac.setContentsMargins(10,9,10,10)
        ac.addWidget(lbl('⚡  ACTIONS RAPIDES','section'))
        for row in [[('＋  Nouveau',self.new_tab),('▶  Script',self.macros.choose)],
                    [('⌘  SSH',self.ssh_help),('▱  Dossier',self.open_explorer)],
                    [('≡  Logs',self.show_logs),('■  Arrêter',self.macros.stop)]]:
            wrap=QHBoxLayout();wrap.setSpacing(5)
            for title,fn in row:wrap.addWidget(btn(title,fn))
            ac.addLayout(wrap)
        v.addWidget(actions)
        layouts=NeonPanel();ll=QVBoxLayout(layouts);ll.setContentsMargins(8,8,8,8)
        ll.addWidget(lbl('▦  LAYOUT PRESETS','section'))
        grid=QGridLayout();grid.setSpacing(4)
        for i,(mode,name,_) in enumerate(LAYOUTS[:4]):
            w=btn('▣\n'+name,lambda checked=False,m=mode:self.change_layout(m),'layout')
            grid.addWidget(w,i//2,i%2)
        ll.addLayout(grid);v.addWidget(layouts)
        return side

    def focus_session(self,index):
        page=self.tabs.currentWidget()
        if page and index<len(page.shells):
            page.shells[index].setFocus()
            self.notify('Console active',f'Console {index+1} sélectionnée','info')

    def count_sessions(self):return sum(self.tabs.widget(i).total() for i in range(self.tabs.count()))
    def update_state(self,*args):
        total=self.count_sessions()
        self.sessions_lbl.setText(f'SESSIONS: {total}')
        self.monitor.set_sessions(total)
        page=self.tabs.currentWidget()
        if page:
            pos=self.picker.findData(page.mode)
            self.picker.blockSignals(True);self.picker.setCurrentIndex(pos);self.picker.blockSignals(False)
        for i,widget in enumerate(self.session_rows):
            widget.setEnabled(bool(page and i<len(page.shells)))
            widget.setText(f'●  Console {i+1}' if page and i<len(page.shells) else f'○  Console {i+1}')

    def new_tab(self):
        page=TerminalPage('grid');page.sessionsChanged.connect(self.update_state)
        idx=self.tabs.addTab(page,f'◈  Console {self.tabs.count()+1}')
        self.tabs.setCurrentIndex(idx);self.update_state()
        self.event.emit('terminal.session.created',{'sessions':self.count_sessions()})

    def pick_layout(self,index):
        mode=self.picker.itemData(index)
        if mode:self.change_layout(mode)

    def change_layout(self,mode):
        page=self.tabs.currentWidget()
        if page and not page.mode_change(mode):
            self.notify('Sessions protégées','Ce format supprimerait des consoles actives. Ouvre un nouvel onglet.','warning')
        elif page:
            self.event.emit('terminal.layout.changed',{'mode':mode})
        self.update_state()

    def close_tab(self,index):
        page=self.tabs.widget(index)
        if not page:return
        r=QMessageBox.question(self,'Fermer cet onglet',f'Terminer {page.total()} session(s) Bash ?',
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if r!=QMessageBox.StandardButton.Yes:return
        self.tabs.removeTab(index);page.deleteLater()
        if not self.tabs.count():self.new_tab()
        self.update_state()

    def notify(self,title,detail='',kind='info'):
        if len(self._toasts)>=3:
            old=self._toasts.pop(0);self.toast_row.removeWidget(old);old.deleteLater()
        card=None
        def dismiss():
            if card in self._toasts:self._toasts.remove(card)
            self.toast_row.removeWidget(card);card.deleteLater()
        card=Toast(title,detail,kind,dismiss)
        self.toast_row.addWidget(card);self._toasts.append(card)
        QTimer.singleShot(6500,lambda:dismiss() if card in self._toasts else None)
        self.event.emit('terminal.notification',{'title':title,'detail':detail,'kind':kind})

    def ssh_help(self):self.notify('SSH','Dans une console Bash : ssh utilisateur@serveur','info')
    def open_explorer(self):
        path=Path.home()
        import subprocess
        try:subprocess.Popen(['xdg-open',str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except OSError:self.notify('Explorer indisponible',str(path),'error')
    def show_logs(self):
        dlg=QDialog(self);dlg.setWindowTitle('NEXUS • Logs scripts');dlg.resize(780,450)
        v=QVBoxLayout(dlg);edit=QPlainTextEdit();edit.setReadOnly(True)
        edit.setPlainText(self.macros.output.toPlainText());v.addWidget(edit)
        v.addWidget(btn('Fermer',dlg.accept));dlg.setStyleSheet(QSS);dlg.exec()
    def dialog_settings(self):
        dlg=QDialog(self);dlg.setWindowTitle('NEXUS • Paramètres');dlg.resize(420,190)
        v=QVBoxLayout(dlg);v.addWidget(lbl('ELECTROBLUE NEON / PERFORMANCE','section'))
        v.addWidget(lbl('Animations : uniquement éléments sélectionnés, sans rafraîchissement global.'))
        v.addWidget(lbl('Échecs : signalés sur codes de sortie des macros supervisées.'))
        v.addWidget(btn('Fermer',dlg.accept));dlg.setStyleSheet(QSS);dlg.exec()
    def secret_dialog(self,reason='Saisie privée'):
        dlg=SecretDialog(self,reason)
        return dlg.input.text() if dlg.exec()==QDialog.DialogCode.Accepted else None
    def confirm_close(self):
        return QMessageBox.question(self,'Quitter NEXUS Terminal',
            'Fermer toutes les consoles Bash et les scripts en cours ?',
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes


class NexusTerminalWindow(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('NEXUS Terminal — ElectroBlueNEON 0.3')
        self.resize(1648,928);self.setMinimumSize(980,650)
        self.terminal=NexusTerminalWidget(self);self.setCentralWidget(self.terminal)
    def closeEvent(self,event):
        if self.terminal.confirm_close():event.accept()
        else:event.ignore()


def create_widget(context=None,parent=None):
    """Factory compatible with Control Center AppSpec('terminal',...,factory)."""
    w=NexusTerminalWidget(parent)
    if context is not None and callable(getattr(context,'publish',None)):
        w.event.connect(lambda name,payload:context.publish(name,payload))
    return w


def main():
    app=QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName('NEXUS Terminal')
    window=NexusTerminalWindow();window.show()
    return app.exec()

if __name__=='__main__':sys.exit(main())
