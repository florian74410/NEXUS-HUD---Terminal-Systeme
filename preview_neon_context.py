#!/usr/bin/env python3
"""Launch the real Qt tooltip visual to inspect on XFCE."""
import sys
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QLabel,QPushButton
from PySide6.QtCore import QPoint
from nexus_context_bubble import NeonContextBubble
app=QApplication(sys.argv)
w=QWidget();w.setWindowTitle('NEXUS — Neon Context preview');w.setStyleSheet('background:#06121e;color:white;')
w.resize(500,180);layout=QVBoxLayout(w)
label=QLabel('❯ git pull origin main');label.setStyleSheet('font:20px "DejaVu Sans Mono";color:#e2f3fc;')
layout.addWidget(label)
b=QPushButton('Afficher la micro-bulle NeonGlass 150 × 50')
layout.addWidget(b)
bubble=NeonContextBubble(w)
b.clicked.connect(lambda:bubble.show_context('pull','Récupère et fusionne les modifications distantes.',b.mapToGlobal(QPoint(20,b.height()))))
w.show();sys.exit(app.exec())
