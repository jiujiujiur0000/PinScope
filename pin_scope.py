#!/usr/bin/env python3
"""
PinScope v1.0 - 极简应用程序启动入口 (pin_scope.py)
运行：python3 pin_scope.py
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app import PinScopeApp


def main():
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    global_font = QFont("Noto Sans CJK SC", 13)
    app.setFont(global_font)

    window = PinScopeApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
