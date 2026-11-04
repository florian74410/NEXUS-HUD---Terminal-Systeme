"""QTermWidget hover adapter. Uses only readable screen APIs, never types into PTY."""
from __future__ import annotations
import os, re
from nexus_screen_adapter import TmuxScreenAdapter
from PySide6.QtCore import QObject, QEvent, QTimer, Qt, QPoint, QThread, Signal
from PySide6.QtWidgets import QApplication, QMenu, QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from nexus_context_bubble import NeonContextBubble
from nexus_smart_context import safe_query, ContextLookup

class LookupWorker(QThread):
    finished_text=Signal(str)
    def __init__(self,context,parent=None):
        super().__init__(parent);self.context=context
    def run(self):
        try:result=ContextLookup().lookup(self.context)
        except Exception:result='Recherche HTTPS indisponible.'
        self.finished_text.emit(result)

class UnderlineOverlay(QWidget):
    """Mouse-transparent paint overlay; never changes PTY text or selection."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.line_rect = None
        self.hide()

    def show_word(self, rect):
        self.setGeometry(self.parentWidget().rect())
        self.line_rect = rect
        self.show()
        self.raise_()
        self.update()

    def clear(self):
        self.line_rect = None
        self.hide()

    def paintEvent(self, event):
        if not self.line_rect:
            return
        x1, y, x2 = self.line_rect
        painter = QPainter(self)
        painter.setPen(QPen(QColor('#55E6FF'), 1.4))
        painter.drawLine(x1, y, x2, y)
        painter.end()

class SmartHover(QObject):
    """Hover underline after 2 s, click to show a 150x50 glass explanation.

    QTermWidget bindings differ: screen word lookup requires a compatible
    getText(row, column, length) method. If unavailable, no synthetic mouse
    selection or clipboard changes are attempted. Selection context-menu
    lookup remains available as an explicit fallback.
    """
    def __init__(self,terminal,session_name=None):
        super().__init__(terminal);self.terminal=terminal
        self.reader=TmuxScreenAdapter(session_name) if session_name else None
        self.bubble=NeonContextBubble(terminal)
        self.overlay=UnderlineOverlay(terminal)
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(2000)
        self.timer.timeout.connect(self._activate)
        self.target=None;self.active=None;self.worker=None;self.pending_pos=None
        terminal.setMouseTracking(True)
        terminal.installEventFilter(self)
        # Qt terminal libraries sometimes deliver mouse events to a child viewport.
        for child in terminal.findChildren(QWidget):
            if child is not self.overlay and child is not self.bubble:
                child.setMouseTracking(True)
                child.installEventFilter(self)
        terminal.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        terminal.customContextMenuRequested.connect(self._menu)
    def _reset(self):
        self.timer.stop();self.target=None;self.active=None;self.pending_pos=None
        self.overlay.clear()
        self.terminal.setCursor(Qt.CursorShape.IBeamCursor)
    def _read_at(self,pos):
        """Read-only local tmux snapshot; never changes selection or PTY input."""
        if not self.reader:return None
        font=self.terminal.fontMetrics()
        cw=max(1,font.horizontalAdvance('M'));ch=max(1,font.height())
        # QTermWidget has internal margins; this mapping is approximate until
        # the native terminal viewport exposes exact cell coordinates.
        row=max(0,pos.y()//ch);col=max(0,pos.x()//cw)
        return self.reader.word_at(row,col,pos)
    def eventFilter(self,obj,event):
        if obj is not self.terminal and obj not in self.terminal.findChildren(QWidget):return False
        typ=event.type()
        if typ==QEvent.Type.MouseMove:
            pos=event.position().toPoint()
            if obj is not self.terminal:pos=obj.mapTo(self.terminal,pos)
            # No subprocess on each mouse movement: debounce 2 seconds.
            self._reset()
            self.pending_pos=pos
            if self.reader:self.timer.start()
        elif typ==QEvent.Type.Leave and obj is self.terminal:self._reset()
        elif typ==QEvent.Type.Resize and obj is self.terminal:
            self.overlay.setGeometry(self.terminal.rect())
        elif typ==QEvent.Type.MouseButtonPress and event.button()==Qt.MouseButton.LeftButton:
            if self.active:
                context=safe_query(*self.active[:4],known_identities=(os.environ.get('USER',''),))
                if context:self._lookup(context,event.globalPosition().toPoint())
                self._reset();return True
        return False
    def _activate(self):
        if self.pending_pos is None:return
        found=self._read_at(self.pending_pos)
        if not found:return
        if not safe_query(*found[:4],known_identities=(os.environ.get('USER',''),)):
            return
        self.target=found;self.active=found
        self.terminal.setCursor(Qt.CursorShape.PointingHandCursor)
        word,line,start,end,pos=found
        fm=self.terminal.fontMetrics();cw=max(1,fm.horizontalAdvance('M'))
        ch=max(1,fm.height());row=max(0,pos.y()//ch)
        self.overlay.show_word((start*cw,(row+1)*ch-2,end*cw))
    def _lookup(self,context,pos):
        self.bubble.show_context(context.word,'Recherche…',pos)
        if self.worker and self.worker.isRunning():return
        self.worker=LookupWorker(context,self)
        self.worker.finished_text.connect(lambda text:self.bubble.show_context(context.word,text,pos))
        self.worker.start()
    def _menu(self,pos):
        menu=QMenu(self.terminal)
        copy=menu.addAction('Copier la sélection')
        action=menu.addAction('NEXUS · Expliquer la sélection')
        chosen=menu.exec(self.terminal.mapToGlobal(pos))
        selection=getattr(self.terminal,'selectedText',None)
        value=selection() if callable(selection) else ''
        if chosen==copy and value:QApplication.clipboard().setText(value)
        if chosen==action and value:
            word=value.strip()
            context=safe_query(word,known_identities=(os.environ.get('USER',''),))
            if context:self._lookup(context,self.terminal.mapToGlobal(pos))
