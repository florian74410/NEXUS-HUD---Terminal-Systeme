"""Compact NEXUS NeonGlass context bubble. Pure PySide6, no external browser."""
from PySide6.QtCore import Qt, QPoint, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QLinearGradient, QFont
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsDropShadowEffect, QApplication

class NeonContextBubble(QWidget):
    """150x50 px, frameless translucent mirror-glass and neon beveled border."""
    def __init__(self, parent=None):
        flags=Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint
        super().__init__(parent,flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFixedSize(150,50)
        self.setObjectName('nexusNeonContext')
        self._word=''
        self._meaning=''
        self.word_label=QLabel(self)
        self.word_label.setGeometry(11,5,128,14)
        self.word_label.setStyleSheet('color:#5de9ff;background:transparent;font: bold 9px "DejaVu Sans";')
        self.explanation=QLabel(self)
        self.explanation.setGeometry(11,20,128,25)
        self.explanation.setWordWrap(True)
        self.explanation.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.explanation.setStyleSheet('color:#e2f3fc;background:transparent;font:italic 8px "DejaVu Sans";')
        self.explanation.setToolTip('')
        glow=QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(15);glow.setOffset(0,0);glow.setColor(QColor(30,210,255,115))
        self.setGraphicsEffect(glow)
    def show_context(self,word,meaning,global_pos):
        self._word=str(word).strip()[:32]
        self._meaning=str(meaning).strip()
        self.word_label.setText(self._word)
        metrics=self.explanation.fontMetrics()
        # The complete text is never squeezed to an unreadable font.
        text=self._meaning
        while len(text)>4 and metrics.boundingRect(QRectF(0,0,128,25).toRect(),int(Qt.TextFlag.TextWordWrap),text).height()>25:
            text=text[:-4].rstrip(' .')
        if text!=self._meaning:text=text.rstrip(' .')+'…'
        self.explanation.setText(text)
        self.move(global_pos+QPoint(7,12))
        self.show();self.raise_()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path=QPainterPath()
        path.moveTo(9,1);path.lineTo(139,1);path.lineTo(149,11)
        path.lineTo(149,39);path.lineTo(139,49);path.lineTo(9,49)
        path.lineTo(1,41);path.lineTo(1,9);path.closeSubpath()
        g=QLinearGradient(0,0,0,50)
        g.setColorAt(0,QColor(28,100,137,128))
        g.setColorAt(.23,QColor(9,38,65,113))
        g.setColorAt(.67,QColor(5,22,43,106))
        g.setColorAt(1,QColor(4,12,33,136))
        p.fillPath(path,g)
        # Mirror-like glass reflection, clipped inside the bevel.
        p.save();p.setClipPath(path)
        mirror=QLinearGradient(0,1,0,23)
        mirror.setColorAt(0,QColor(205,248,255,83))
        mirror.setColorAt(.45,QColor(125,221,255,32))
        mirror.setColorAt(1,QColor(125,221,255,0))
        p.fillRect(0,0,150,24,mirror)
        # Secondary slanted reflection, intentionally faint to preserve legibility.
        streak=QPainterPath()
        streak.moveTo(95,2);streak.lineTo(122,2);streak.lineTo(75,49);streak.lineTo(55,49)
        streak.closeSubpath()
        p.fillPath(streak,QColor(180,242,255,10))
        p.restore()
        p.setPen(QPen(QColor(64,226,255,225),1.1));p.drawPath(path)
        p.setPen(QPen(QColor(180,249,255,190),1.2));p.drawLine(14,3,80,3)
        p.setPen(QPen(QColor(119,71,240,190),1.1));p.drawLine(91,47,132,47)
        shine=QPainterPath();shine.moveTo(12,5);shine.lineTo(132,5);shine.lineTo(143,16);shine.lineTo(15,13);shine.closeSubpath()
        p.fillPath(shine,QColor(166,236,255,30))
        p.end()
