"""N3XV5 UI skin: supplied assets + real Qt controls, not an SVG mockup.

QtSvg supports static SVG but not SVG <animate> / CSS keyframes. Artwork is
rendered once with QtSvg; inexpensive Qt timers animate ONLY active surfaces.
This module never launches shell commands or handles credentials.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from xml.etree import ElementTree as ET

from PySide6.QtCore import Qt, QRectF, QSize, QByteArray, QTimer, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QIcon, QPainterPath
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QFrame, QPushButton

BASE = Path(__file__).resolve().parent / 'assets' / 'theme_nexus'
CYAN = QColor('#38e7ff')
BLUE = QColor('#185cfc')
RED = QColor('#ee314e')
ALIASES = {
    'VALIDER': 'OK', 'CONFIRMER': 'OUI', 'ENREGISTRER': 'APPLIQUER',
    'SAUVEGARDER': 'APPLIQUER', 'ANNULÉ': 'ANNULER', 'CANCEL': 'ANNULER',
    'SUPPRIMER': 'NON', 'CONNECTER': 'CONNECTER', 'PARAMÈTRES': 'PARAMETRES',
    'RÉINITIALISER': 'REINITIALISER', 'FERMER': 'FERMER', 'ACTUALISER': 'REINITIALISER',
}


def artwork_path(category: str, name: str) -> Path:
    """Return curated user artwork only; reject traversal / arbitrary paths."""
    valid = re.fullmatch(r'[\w.-]+', category) and re.fullmatch(r'[\w.-]+\.svg', name)
    if not valid:
        raise ValueError('Nom de ressource invalide')
    return BASE / category / name


@lru_cache(maxsize=128)
def _svg_bytes(path_str: str, remove_text: bool = False, electric_only: bool = False) -> bytes:
    """Cache normalized source bytes, not mutable QSvgRenderer instances.

    QtSvg does not execute SVG/SMIL animations; Qt animates the controls instead.
    The supplied originals on disk remain unchanged.
    """
    path = Path(path_str)
    if not path.is_file():
        return b''
    content = path.read_text(encoding='utf-8')
    content = re.sub(r'<animate\b[^>]*(?:/>|>.*?</animate>)', '', content, flags=re.S)
    if remove_text:
        content = re.sub(r'<text\b[^>]*(?:/>|>.*?</text>)', '', content, flags=re.S)
    if electric_only:
        # Keep alerts in red; neutral navigation/action buttons are ElectroBlue.
        content = re.sub(r'#[Ff][Ff]2346|#[Ff]21[Ff]3[Dd]|#[Ff]21[Ff]3[dD]|#[Ff][Ff]2645', '#22DFFF', content)
    return content.encode('utf-8')


def _svg_renderer(path: Path, remove_text=False, electric_only=False) -> QSvgRenderer:
    """A fresh mutable renderer per widget, backed by cached source data."""
    payload = _svg_bytes(str(path), remove_text, electric_only)
    return QSvgRenderer(QByteArray(payload)) if payload else QSvgRenderer()


def _bevel(p: QPainter, rect: QRectF, active=False, warning=False):
    cut = min(13., rect.height() * .27, rect.width() * .13)
    path = QPainterPath()
    path.moveTo(rect.left()+cut,rect.top())
    path.lineTo(rect.right()-cut,rect.top())
    path.lineTo(rect.right(),rect.top()+cut)
    path.lineTo(rect.right(),rect.bottom()-cut)
    path.lineTo(rect.right()-cut,rect.bottom())
    path.lineTo(rect.left()+cut,rect.bottom())
    path.lineTo(rect.left(),rect.bottom()-cut)
    path.lineTo(rect.left(),rect.top()+cut)
    path.closeSubpath()
    p.fillPath(path, QColor(4, 20, 35, 245))
    edge = RED if warning else (CYAN if active else QColor('#176997'))
    p.setPen(QPen(edge, 1.5 if active else 1.1))
    p.drawPath(path)
    if rect.width() > 60:
        p.setPen(QPen(CYAN if active else BLUE, 2.5))
        p.drawLine(int(rect.left()+cut+4),int(rect.top()+1),int(min(rect.right()-cut-3,rect.left()+cut+42)),int(rect.top()+1))


class AssetButton(QPushButton):
    """Real keyboard-accessible QPushButton skinned with source Buttons SVGs."""
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setMinimumSize(48, 34)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet('background:transparent;border:0;padding:0;color:#e9fbff;')
        self._asset = None
        self._asset_key = None
        self._hover = 0.0
        self._animation = QVariantAnimation(self)
        self._animation.setDuration(180)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.valueChanged.connect(self._set_hover)

    def _set_hover(self, value):
        self._hover = float(value)
        self.update()

    def enterEvent(self, event):
        self._motion(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._motion(0.0)
        super().leaveEvent(event)

    def _motion(self, destination):
        self._animation.stop()
        self._animation.setStartValue(self._hover)
        self._animation.setEndValue(destination)
        self._animation.start()

    def _renderer(self):
        original = re.sub(r'^[^\wÀ-ÿ]+\s*', '', self.text()).strip().upper()
        name = ALIASES.get(original, original)
        key = name if (BASE/'Buttons'/(name+'.svg')).is_file() else ''
        if key != self._asset_key:
            self._asset_key = key
            self._asset = _svg_renderer(artwork_path('Buttons',key+'.svg'),remove_text=True,electric_only=True) if key else None
        return self._asset

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1,1,-1,-1)
        art = self._renderer()
        if art is not None and art.isValid():
            art.render(p,rect)
        else:
            _bevel(p,rect, self._hover>.05 or self.isDown(), 'erreur' in self.text().lower())
        if self._hover>.001 or self.isDown():
            strength = .75 if self.isDown() else self._hover
            p.fillRect(rect.adjusted(12,8,-12,-8), QColor(20,207,250,int(22*strength)))
            p.setPen(QPen(QColor(107,244,255,int(170*strength)),1.7))
            p.drawLine(int(rect.left()+19),int(rect.top()+3),int(rect.right()-20),int(rect.top()+3))
        p.setOpacity(1.0 if self.isEnabled() else .44)
        p.setPen(QColor('#edfaff'))
        f=p.font();f.setWeight(QFont.Weight.DemiBold);p.setFont(f)
        text=self.text()
        ico=self.icon()
        metrics=p.fontMetrics()
        text_w=metrics.horizontalAdvance(text)
        if not ico.isNull() and self.width()>text_w+48:
            gap=6;icon_w=17;left=max(12,int((self.width()-text_w-icon_w-gap)/2))
            p.drawPixmap(left,int((self.height()-icon_w)/2),ico.pixmap(QSize(icon_w,icon_w)))
            p.drawText(QRectF(left+icon_w+gap,0,text_w+6,self.height()),Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft,text)
        else:
            p.drawText(rect,Qt.AlignmentFlag.AlignCenter,text)
        p.end()


class TileCloseButton(QPushButton):
    """Compact but accessible close control for narrow split terminal panes."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(30, 27)
        self.setToolTip('Détacher le panneau (session tmux conservée)')
        self.setAccessibleName('Fermer le panneau terminal')
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet('background:transparent;border:0;')
        self._hover = False

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        _bevel(p, rect, self._hover or self.isDown())
        p.setPen(QPen(CYAN if self._hover else QColor('#9CEAF4'), 1.8))
        cx, cy = self.width()/2, self.height()/2
        p.drawLine(int(cx-5), int(cy-5), int(cx+5), int(cy+5))
        p.drawLine(int(cx+5), int(cy-5), int(cx-5), int(cy+5))
        p.end()


class AssetSurface(QFrame):
    """Scalable original electronic frame; children remain fully functional Qt widgets."""
    def __init__(self,parent=None,category='Windows',name='Console.svg',animated=False):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
        self.setStyleSheet('background:transparent;border:0;')
        self._source=artwork_path(category,name)
        self._svg=_svg_renderer(self._source)
        self._phase=0
        self._animated=False
        self._timer=QTimer(self)
        self._timer.setInterval(130)
        self._timer.timeout.connect(self._tick)
        self.set_animated(animated)

    def set_artwork(self, category: str, name: str):
        self._source=artwork_path(category,name)
        self._svg=_svg_renderer(self._source)
        self.update()

    def _tick(self):
        if self.isVisible():
            self._phase=(self._phase+1)%100
            self.update()

    def set_animated(self,enabled):
        self._animated=bool(enabled)
        if self._animated:self._timer.start()
        else:self._timer.stop()
        self.update()

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._svg.isValid(): self._svg.render(p,QRectF(self.rect()))
        else: _bevel(p,QRectF(self.rect()).adjusted(1,1,-1,-1))
        # Qt-generated pulse: SVG CSS animation does not work in QtSvg.
        if self._animated and self.width()>130:
            x=int(26+(self.width()-85)*self._phase/100)
            p.setPen(QPen(QColor(68,229,255,170),2))
            p.drawLine(x,8,x+37,8)
        p.end()


class ElectricPulseSurface(AssetSurface):
    """Each terminal has a standalone, resizable instance of ElectricPulse art."""
    def __init__(self,parent=None):
        super().__init__(parent,category='Boxes',name='Electric_Pulse_Original.svg')
        if not self._svg.isValid():
            self._svg=_svg_renderer(BASE/'01_Electric_Pulse.svg')
        if self._svg.isValid():
            # Huge transparent margins in user SVG; keep its border proportions.
            self._svg.setViewBox(QRectF(47,88,866,393))
        self.setMinimumSize(180,140)
        self._active=False

    def set_active(self,value):
        self._active=bool(value)
        self.set_animated(self._active)

    def paintEvent(self,event):
        super().paintEvent(event)
        if self._active:
            p=QPainter(self)
            p.setPen(QPen(QColor(86,231,255,120),1.4))
            p.drawLine(35,self.height()-18,min(self.width()-35,135),self.height()-18)
            p.end()


class NexusNotice(QFrame):
    """A live Qt notification widget using the supplied Notifications artworks."""
    def __init__(self, title, detail='', kind='Info', parent=None):
        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel
        super().__init__(parent)
        if kind not in ('Info','Warning','Error','Success','Network'):
            kind='Info'
        self.setObjectName('nexusNotice')
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
        v=QVBoxLayout(self);v.setContentsMargins(0,0,0,0)
        self.surface=AssetSurface(category='Notifications',name=kind+'.svg')
        v.addWidget(self.surface)
        inner=QVBoxLayout(self.surface);inner.setContentsMargins(32,36,32,24)
        row=QHBoxLayout()
        heading=QLabel(title);heading.setStyleSheet('font-size:14px;font-weight:700;color:#c6f7ff;background:transparent;')
        row.addWidget(heading);row.addStretch()
        inner.addLayout(row)
        self.detail=QLabel(detail);self.detail.setWordWrap(True)
        self.detail.setStyleSheet('color:#d9eef6;background:transparent;')
        inner.addWidget(self.detail)
        self.setMinimumHeight(145)


def show_notice(parent, title, detail='', kind='Info'):
    """Show an action-free notification; never auto-runs a remote command."""
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout
    dialog=QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
    dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground,True)
    dialog.resize(550,190)
    outer=QVBoxLayout(dialog);outer.setContentsMargins(9,9,9,9)
    surface=NexusNotice(title, detail, kind, dialog)
    outer.addWidget(surface)
    button=AssetButton('OK', dialog)
    button.clicked.connect(dialog.accept)
    button.setMaximumWidth(105)
    footer=QHBoxLayout();footer.addStretch();footer.addWidget(button)
    outer.addLayout(footer)
    return dialog.exec()
