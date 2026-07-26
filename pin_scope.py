#!/usr/bin/env python3
"""
PinScope v1.0 - 极简应用程序启动入口 (pin_scope.py)
运行：python3 pin_scope.py
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor

from app import PinScopeApp


def make_dark_palette():
    """构建全局深色调色板，让 Fusion 引擎原生绘制全部使用深色"""
    p = QPalette()
    dark      = QColor("#1E1E1E")
    mid_dark  = QColor("#252526")
    panel     = QColor("#2D2D30")
    text      = QColor("#CCCCCC")
    bright    = QColor("#FFFFFF")
    accent    = QColor("#0E639C")
    disabled  = QColor("#666666")

    p.setColor(QPalette.Window,          dark)
    p.setColor(QPalette.WindowText,      text)
    p.setColor(QPalette.Base,            mid_dark)
    p.setColor(QPalette.AlternateBase,   panel)
    p.setColor(QPalette.ToolTipBase,     panel)
    p.setColor(QPalette.ToolTipText,     text)
    p.setColor(QPalette.Text,            text)
    p.setColor(QPalette.Button,          panel)
    p.setColor(QPalette.ButtonText,      bright)
    p.setColor(QPalette.BrightText,      bright)
    p.setColor(QPalette.Link,            accent)
    p.setColor(QPalette.Highlight,       accent)
    p.setColor(QPalette.HighlightedText, bright)
    p.setColor(QPalette.Disabled, QPalette.Text,       disabled)
    p.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
    p.setColor(QPalette.Disabled, QPalette.WindowText, disabled)
    return p


def make_light_palette():
    """构建全局浅色调色板"""
    p = QPalette()
    bg       = QColor("#F6F8FA")
    base     = QColor("#FFFFFF")
    text     = QColor("#24292F")
    accent   = QColor("#0969DA")
    disabled = QColor("#8C959F")

    p.setColor(QPalette.Window,          bg)
    p.setColor(QPalette.WindowText,      text)
    p.setColor(QPalette.Base,            base)
    p.setColor(QPalette.AlternateBase,   bg)
    p.setColor(QPalette.ToolTipBase,     base)
    p.setColor(QPalette.ToolTipText,     text)
    p.setColor(QPalette.Text,            text)
    p.setColor(QPalette.Button,          bg)
    p.setColor(QPalette.ButtonText,      text)
    p.setColor(QPalette.BrightText,      QColor("#FFFFFF"))
    p.setColor(QPalette.Link,            accent)
    p.setColor(QPalette.Highlight,       accent)
    p.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    p.setColor(QPalette.Disabled, QPalette.Text,       disabled)
    p.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
    p.setColor(QPalette.Disabled, QPalette.WindowText, disabled)
    return p


def main():
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    global_font = QFont("Noto Sans CJK SC", 13)
    app.setFont(global_font)

    # 初始默认深色全局调色板——彻底消除 Fusion 原生绘制的白色控件背景
    app.setPalette(make_dark_palette())

    window = PinScopeApp()

    # 主题切换时同步更新全局调色板
    original_apply = window.apply_theme_mode
    def patched_apply():
        original_apply()
        if window.is_dark_theme:
            app.setPalette(make_dark_palette())
        else:
            app.setPalette(make_light_palette())
    window.apply_theme_mode = patched_apply

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
