"""NOVA 1.0 NeonGlass + original NEXUS asset skin for N3XV5 v1.4.4.

Source of visual grammar: the genuine NOVA 1.0 `nexus_terminal.py`,
`NeonPanel` + QSS, and the original `nexus_workspace.py` (Frame/HeaderCircuit).

The painter scales to live QWidget dimensions.  No SVG is stretched across a
PTY, and no I/O, shell execution, profile handling or socket logic lives here.
ElectricPulse.svg is nine-sliced around each terminal, while original button SVGs
provide static skins and Qt adds a limited click animation. PTY remains real.
"""
from __future__ import annotations

from math import sin
from pathlib import Path
from functools import lru_cache
import re
from PySide6.QtCore import Qt, QTimer, QVariantAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QFontMetrics
from PySide6.QtWidgets import QFrame, QPushButton, QDialog, QVBoxLayout, QHBoxLayout, QLabel

# Static SVGs from the user-supplied NEXUS asset pack. Animation is rendered by Qt,
# because QtSvg does not execute SVG/CSS keyframe animations.
from nexus_skin import _svg_renderer

THEME_ASSETS = Path(__file__).resolve().parent / 'assets' / 'theme_nexus'


@lru_cache(maxsize=24)
def _raster_asset(relative_path: str, strip_text: bool = False) -> QPixmap:
    """Lazy Qt pixmap cache; only called after QApplication has been initialized."""
    path = THEME_ASSETS / relative_path
    renderer = _svg_renderer(path, remove_text=strip_text, electric_only=True)
    if not renderer.isValid():
        return QPixmap()
    size = renderer.defaultSize()
    if size.width() < 1 or size.height() < 1:
        return QPixmap()
    image = QPixmap(size)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return image


def _asset_border(painter: QPainter, sprite: QPixmap, width: int, height: int):
    """Nine-slice only the perimeter; the PTY content is never covered.

    Original Electric Pulse artwork is retained and sliced using its transparent
    outer bounds. The center panel is omitted so it cannot tint terminal text.
    """
    if sprite.isNull() or width < 80 or height < 85:
        return
    source = QRectF(40, 52, 880, 428)
    sx = [source.left(), source.left() + 126, source.right() - 126, source.right()]
    sy = [source.top(), source.top() + 115, source.bottom() - 88, source.bottom()]
    inset_x = min(24.0, max(11.0, width * .075))
    inset_top = min(26.0, max(18.0, height * .13))
    inset_bottom = min(19.0, max(10.0, height * .09))
    dx = [0.0, inset_x, width - inset_x, float(width)]
    dy = [0.0, inset_top, height - inset_bottom, float(height)]
    # Avoid drawing the asset's opaque carbon center over the live QTermWidget.
    for row in range(3):
        for col in range(3):
            if row == 1 and col == 1:
                continue
            src = QRectF(sx[col], sy[row], sx[col+1]-sx[col], sy[row+1]-sy[row])
            dst = QRectF(dx[col], dy[row], dx[col+1]-dx[col], dy[row+1]-dy[row])
            if dst.width() > 0 and dst.height() > 0:
                painter.drawPixmap(dst, sprite, src)


def _button_asset(text: str) -> QPixmap:
    """Map real action labels to an SVG button; keep Qt's dynamic label."""
    key = re.sub(r'^[^\wÀ-ÿ]+', '', text).strip().upper()
    key = re.sub(r'\s*[▾▼].*$', '', key)
    substitutions = {'PARAMÈTRES':'PARAMETRES', 'SETTINGS':'PARAMETRES',
                     'FERMER':'FERMER', 'ANNULER':'ANNULER', 'ENREGISTRER':'APPLIQUER',
                     'REINITIALISER':'REINITIALISER', 'AJOUTER':'CONNECTER',
                     'CONNEXION':'CONNECTER', 'OUI':'OUI', 'NON':'NON'}
    key = substitutions.get(key, key)
    path = f'Buttons/{key}.svg' if (THEME_ASSETS/'Buttons'/f'{key}.svg').is_file() else 'Buttons/CONNECTER.svg'
    return _raster_asset(path, strip_text=True)


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
    """NOVA 1.0 glass + the actual ElectricPulse asset, nine-sliced per PTY."""
    def __init__(self, parent=None):
        super().__init__(parent, accent='#1addfa', cut=13, fill=True)
        self.setMinimumSize(142, 112)
        self._terminal_art = None

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._terminal_art is None:
            self._terminal_art = _raster_asset('01_Electric_Pulse.svg')
        if self._terminal_art.isNull():
            return  # NOVA 1.0 painted fallback, no missing-resource crash
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setOpacity(.94 if self._active else .78)
        _asset_border(painter, self._terminal_art, self.width(), self.height())
        # Qt-controlled animated spark on the active tile only, never on text.
        if self._active and self._animated:
            progress = self._phase / 120.0
            left, right = 32.0, max(40.0, self.width() - 30.0)
            pos = left + progress * max(1.0, right - left)
            glow = QLinearGradient(pos - 28, 4, pos + 28, 4)
            glow.setColorAt(0, QColor(16, 219, 255, 0))
            glow.setColorAt(.5, QColor(114, 246, 255, 225))
            glow.setColorAt(1, QColor(16, 219, 255, 0))
            painter.setPen(QPen(glow, 3))
            painter.drawLine(int(pos - 28), 5, int(min(right, pos + 28)), 5)
        painter.end()


class NovaOneButton(QPushButton):
    """Real NOVA QPushButton with supplied SVG skin and click-triggered pulse.

    The button stays interactive, focusable, keyboard accessible and retains
    its real text and icon. Qt animations are finite, not a permanent GIF loop.
    """
    def __init__(self, text='', parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(29)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet('background:transparent;border:0;padding:4px 9px;color:#d4f5ff;')
        self._hover = 0.0
        self._click = 0.0
        self._effects_enabled = True
        self._motion = QVariantAnimation(self)
        self._motion.setDuration(190)
        self._motion.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._motion.valueChanged.connect(self._update_glow)
        self._click_animation = QVariantAnimation(self)
        self._click_animation.setDuration(380)
        self._click_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._click_animation.valueChanged.connect(self._update_click)
        self.pressed.connect(self._pulse)

    def set_animated(self, enabled):
        self._effects_enabled = bool(enabled)
        if not enabled:
            self._motion.stop()
            self._click_animation.stop()
            self._hover = 0.0
            self._click = 0.0
            self.update()

    def _update_glow(self, value):
        self._hover = float(value)
        self.update()

    def _update_click(self, value):
        self._click = float(value)
        self.update()

    def _animate(self, dest):
        if not self._effects_enabled:
            return
        self._motion.stop()
        self._motion.setStartValue(self._hover)
        self._motion.setEndValue(float(dest))
        self._motion.start()

    def _pulse(self):
        if not self._effects_enabled:
            return
        self._click_animation.stop()
        self._click_animation.setStartValue(1.0)
        self._click_animation.setEndValue(0.0)
        self._click_animation.start()

    def enterEvent(self, event):
        self._animate(1)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate(0)
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect()
        compact = self.text() == '×'
        art = QPixmap() if compact else _button_asset(self.text())
        painter.setOpacity(1.0 if self.isEnabled() else .48)
        if not art.isNull():
            painter.drawPixmap(QRectF(rect), art, QRectF(art.rect()))
        else:
            painter.setPen(QPen(QColor('#1f9cbe'), 1.2))
            painter.setBrush(QColor('#07283a'))
            painter.drawRoundedRect(QRectF(rect).adjusted(1, 1, -1, -1), 4, 4)
        painter.setOpacity(1.0)
        if self.isDown():
            painter.fillRect(rect.adjusted(6, 6, -6, -6), QColor(25, 207, 250, 45))
        if self._hover > .01 or self._click > .01:
            opacity = min(1.0, .38 * self._hover + .9 * self._click)
            painter.setPen(QPen(QColor(105, 237, 255, int(210 * opacity)), 2.0))
            painter.drawLine(12, self.height() - 3, max(12, self.width() - 12), self.height() - 3)
            if self._click > .01:
                progress = 1.0 - self._click
                x = int(10 + progress * max(0, self.width() - 22))
                painter.setPen(QPen(QColor(189, 252, 255, int(255 * self._click)), 2.5))
                painter.drawLine(x, 3, x, max(3, self.height() - 4))
        painter.setPen(QColor('#e8fcff' if self.isEnabled() else '#688b9a'))
        metrics = QFontMetrics(self.font())
        label_rect = rect.adjusted(8, 1, -8, -1)
        button_icon = self.icon()
        if not button_icon.isNull():
            icon_size = min(18, max(12, self.height() - 11))
            painter.drawPixmap(9, (self.height() - icon_size)//2,
                               button_icon.pixmap(icon_size, icon_size))
            label_rect.adjust(icon_size + 5, 0, 0, 0)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter,
                         metrics.elidedText(self.text(), Qt.TextElideMode.ElideRight,
                                            max(0, label_rect.width())))
        if self.hasFocus():
            painter.setPen(QPen(QColor('#8df5ff'), 1.0, Qt.PenStyle.DashLine))
            painter.drawRect(QRectF(rect).adjusted(4, 4, -4, -4))
        painter.end()


class NovaOneCloseButton(NovaOneButton):
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