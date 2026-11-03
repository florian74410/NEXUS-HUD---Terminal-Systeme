"""NOVA 1.0 NeonGlass restored for N3XV5 Terminal HUD v1.4.3.

Source of visual grammar: the genuine NOVA 1.0 `nexus_terminal.py`,
`NeonPanel` + QSS, and the original `nexus_workspace.py` (Frame/HeaderCircuit).

The painter scales to live QWidget dimensions.  No SVG is stretched across a
PTY, and no I/O, shell execution, profile handling or socket logic lives here.
The ElectricPulse / ElectricCarbon assets remain preserved in `nexus_skin.py`
as an optional legacy style, not the active default.
"""
from __future__ import annotations

from math import sin
from PySide6.QtCore import Qt, QTimer, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QFrame, QPushButton, QDialog, QVBoxLayout, QHBoxLayout, QLabel

# Original NOVA v1.0 NeonPanel palette / glass fills.
CYAN = QColor('#10c7f4')
BRIGHT = QColor('#a1f7ff')
SUCCESS = QColor('#34e79c')
ERROR = QColor('#ff566d')
WARNING = QColor('#ffc960')


class NeonGlassPanel(QFrame):
    """Exact v1.0 beveled QPainter glass grammar, made size-aware and optional-active.

    `category` / `name` are accepted to simplify migration of v1.4.2 dialogs;
    they do not select artwork in NOVA 1.0's native painted style.
    """
    def __init__(self, parent=None, accent='#10c7f4', cut=13, fill=True,
                 animated=False, category=None, name=None):
        super().__init__(parent)
        self.accent = QColor(accent)
        self.cut = int(cut)
        self.fill_panel = bool(fill)
        self._active = False
        self._animated = bool(animated)
        self._phase = 0
        self._timer = QTimer(self)
        self._timer.setInterval(140)
        self._timer.timeout.connect(self._advance)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

    def _advance(self):
        if self.isVisible():
            self._phase = (self._phase + 1) % 120
            self.update()

    def _update_timer(self):
        if self._active and self._animated:
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def set_active(self, active):
        self._active = bool(active)
        self._update_timer()

    def set_animated(self, enabled):
        self._animated = bool(enabled)
        self._update_timer()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width() - 1, self.height() - 1
        if w < 26 or h < 26:
            p.end()
            return
        k = min(self.cut, w // 8, h // 8)
        path = QPainterPath()
        path.moveTo(4 + k, 3)
        path.lineTo(w - 4 - k, 3)
        path.lineTo(w - 3, 3 + k)
        path.lineTo(w - 3, h - 4 - k)
        path.lineTo(w - 4 - k, h - 3)
        path.lineTo(4 + k, h - 3)
        path.lineTo(3, h - 4 - k)
        path.lineTo(3, 3 + k)
        path.closeSubpath()

        if self.fill_panel:
            grad = QLinearGradient(0, 0, w, h)
            grad.setColorAt(0, QColor(5, 29, 47, 245))
            grad.setColorAt(.45, QColor(3, 16, 29, 242))
            grad.setColorAt(1, QColor(4, 26, 40, 245))
            p.fillPath(path, grad)
        # Original v1 multi-stroke halo (fast, no raster blur).
        for width, alpha in ((8, 14), (4, 28), (2, 85)):
            tone = QColor(self.accent)
            tone.setAlpha(alpha)
            p.setPen(QPen(tone, width))
            p.drawPath(path)
        p.setPen(QPen(self.accent, 1.1))
        p.drawPath(path)
        p.setPen(QPen(BRIGHT, 1.7))
        p.drawLine(19, 3, min(w // 3, 115), 3)
        p.drawLine(max(12, w - 98), h - 3, w - 24, h - 3)
        p.setPen(QPen(QColor('#135f80'), 1))
        for shift in (0, 7, 14):
            p.drawLine(w - 58 + shift, 11, w - 47 + shift, 11)
        # Motion only on the currently selected live terminal pane.
        if self._active:
            self._paint_active_trace(p, w, h)
        p.end()

    def _paint_active_trace(self, painter, w, h):
        progress = self._phase / 120 if self._animated else .3
        bright = QColor('#66f1ff')
        bright.setAlpha(165 if self._animated else 105)
        painter.setPen(QPen(bright, 2.0))
        span = max(20, w - 105)
        start = 33 + int(progress * span)
        painter.drawLine(start, 3, min(start + 37, w - 17), 3)


class NovaOneTerminalFrame(NeonGlassPanel):
    """Original v1 ConsoleFrame shape around a real QTermWidget instance."""
    def __init__(self, parent=None):
        super().__init__(parent, accent='#1addfa', cut=13, fill=True)
        self.setMinimumSize(142, 112)


class NovaOneButton(QPushButton):
    """Original v1 QPushButton treatment; never replace a real clickable widget."""
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(29)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet('''
            QPushButton {background:#07283a;border:1px solid #187da2;
                border-radius:4px;padding:5px 9px;color:#d4f5ff;}
            QPushButton:hover {background:#0e425c;border:1px solid #41e9ff;}
            QPushButton:pressed {background:#156682;}
            QPushButton:checked {background:#12475f;border:1px solid #7bf5ff;color:white;}
            QPushButton:disabled {background:#051724;border-color:#12384b;color:#648294;}
        ''')
        self._hover = 0.0
        self._motion = QVariantAnimation(self)
        self._motion.setDuration(190)
        self._motion.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._motion.valueChanged.connect(self._update_glow)

    def _update_glow(self, value):
        self._hover = float(value)
        self.update()

    def _animate(self, dest):
        self._motion.stop()
        self._motion.setStartValue(self._hover)
        self._motion.setEndValue(float(dest))
        self._motion.start()

    def enterEvent(self, event):
        self._animate(1)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate(0)
        super().leaveEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._hover > .01 and self.isEnabled():
            p = QPainter(self)
            edge = QColor('#71eeff')
            edge.setAlpha(round(200 * self._hover))
            p.setPen(QPen(edge, 1.5))
            p.drawLine(11, self.height() - 2, max(12, self.width() - 11), self.height() - 2)
            p.end()


class NovaOneCloseButton(QPushButton):
    """Small 27 x 25 close control copied from NOVA v1 ConsoleFrame UX."""
    def __init__(self, parent=None):
        super().__init__('×', parent)
        self.setFixedSize(27, 25)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName('Détacher ce terminal')
        self.setToolTip('Détacher le panneau ; la session tmux reste active')
        self.setStyleSheet('''
            QPushButton {background:#07283a;border:1px solid #187da2;
                padding:0;color:#d4f5ff;border-radius:3px;font-size:17px;}
            QPushButton:hover {background:#32202c;border:1px solid #ed566e;color:#ff9dac;}
        ''')


def show_notice(parent, title, detail='', kind='Info'):
    """A native v1 NeonGlass modal: real text, accessible OK, no SVG-only UI."""
    accents = {'Info':'#10c7f4', 'Network':'#10c7f4',
               'Success':'#34e79c', 'Warning':'#ffc960', 'Error':'#ff566d'}
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setMinimumWidth(420)
    dlg.setStyleSheet('QDialog {background:#020a13;color:#e7faff;} QLabel {background:transparent;color:#e7faff;}')
    outer = QVBoxLayout(dlg)
    outer.setContentsMargins(9,9,9,9)
    panel = NeonGlassPanel(accent=accents.get(kind, '#10c7f4'), cut=11)
    inner = QVBoxLayout(panel)
    inner.setContentsMargins(18,16,18,13)
    inner.setSpacing(8)
    caption = QLabel(title)
    caption.setStyleSheet('font-size:14px;font-weight:700;color:#a1f7ff;')
    inner.addWidget(caption)
    message = QLabel(detail)
    message.setWordWrap(True)
    inner.addWidget(message)
    row = QHBoxLayout()
    row.addStretch()
    ok = NovaOneButton('OK')
    ok.clicked.connect(dlg.accept)
    ok.setMinimumWidth(88)
    row.addWidget(ok)
    inner.addLayout(row)
    outer.addWidget(panel)
    return dlg.exec()
