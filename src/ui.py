from pathlib import Path

import moderngl_window
import moderngl_window.context.pyqt5.window as qtw

from PyQt5 import QtOpenGL, QtWidgets
from PyQt5.QtCore import QSize, Qt, QTimer
from PyQt5.QtGui import QScreen, QColor

_g_ui_widget = None

class QUIBarWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setMinimumSize(200, 100)
        self.resize(self.minimumSize())

        path = Path(__file__).parent.resolve() / "qt_style_sheet.css"

        self.setStyleSheet(path.read_text())

        self.setAttribute(Qt.WA_StyledBackground)
        self.setAutoFillBackground(True)

        self.text_label = QtWidgets.QLabel("...")
        vbox = QtWidgets.QFormLayout()
        vbox.addWidget(self.text_label)
        self.setLayout(vbox)

        global _g_ui_widget
        _g_ui_widget = self

    def set_text(self, text: str):
        self.text_label.setText(text)

def get_ui() -> QUIBarWidget:
    return _g_ui_widget