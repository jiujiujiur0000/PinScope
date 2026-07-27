#!/usr/bin/env python3
"""
PinScope v1.0 - 配置与基础常量库 (config.py)
"""

import os
import subprocess

# 强制开启 Qt 高 DPI 自动缩放与自适应显示
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

# 尝试导入 serial list_ports 用于获取串口硬件名称
try:
    import serial.tools.list_ports
    HAS_PYSERIAL = True
except ImportError:
    HAS_PYSERIAL = False

# 64x64 4K Retina 高清 base64 PNG 图标
B64_CHECKMARK = "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAAB2HAAAdhwGP5fFlAAABtElEQVR4nO3ZMU4bQRSAYSRKboAoOAFpuQAS5CbJYbhFqCHnwGdACgoF6YLoYn0pdpFM5F2/gbVnh7yvcoGs9zTe/TViby+llFJKKaWUUmoKjnCFX3joPx/XnmsncNIv/q9HHNWeb6twiPs1y7/4VnvGrcEBFiPLw2PtObcC+7jZsDz8rD3rVuAysPzHfATwNbj8k49WAnzGMrD8H5zXnndS+NSfasSX2vNOyubcrbqsPe+kxHL34hr7tWeejHju4BYHtWeelHjufsCw9ryTEs/db5zserhj3Y3rQXcRuTLhxcOcc6e7eg7dvt59Euaeu/60h9x7x7OohdwNnP6qhTe8jbWSO91zP+mAWsqd8UdgVfgnqqXc6Qow2UvKnHM3BBdimVriYuR75pu7TQpO7mndyZl77iLEn91XedRC7iKUvb0XutS1kbuowoVu8D34t+3c7pT9pCPq566U7j800ZfamPnkrpR4HofML3elxPO4zjxzV0o8j6vmm7tSyvJIC7krJZ7HdnJXSpfH55Hlen55Hlen55Hlen55Hlen55Hl/53fwGLNogirjKh0gAAAABJRU5ErkJggg=="
B64_ARROW_WHITE = "iVBORw0KGgoAAAANSUhEUgAAAA4AAAAKCAYAAACE2W/HAAAACXBIWXMAAB2HAAAdhwGP5fFlAAAALElEQVQokWNgGBDw////hv/EgwZyNDeQYzN2TQQ049eEQzNxmtA0k6aJpgAA0J6hZfDDv5UAAAAASUVORK5CYII="
B64_ARROW_DARK = "iVBORw0KGgoAAAANSUhEUgAAAA4AAAAKCAYAAACE2W/HAAAACXBIWXMAAB2HAAAdhwGP5fFlAAAAW0lEQVQokWNgoDdgZGBgYFDRMmhg+P+/njgdjI13rl1oYGZgYGB49/rFASExSUYGBgYHYjQxMDAwMMPECGpG0oSiEa9mNE0YGrFqxqIJL1DRMmhQ0TIgXgPNAQBrkicqPbl5eQAAAABJRU5ErkJggg=="
B64_ARROW_UP_WHITE = "iVBORw0KGgoAAAANSUhEUgAAAA4AAAAKCAYAAACE2W/HAAAACXBIWXMAAB2HAAAdhwGP5fFlAAAAL0lEQVQokWNgGDTg////Df///28gRxMMEKcZTRNxmnFowq+ZgCbsmonURJqfqQ4As1ShZXtvv5EAAAAASUVORK5CYII="
B64_ARROW_UP_DARK = "iVBORw0KGgoAAAANSUhEUgAAAA4AAAAKCAYAAACE2W/HAAAACXBIWXMAAB2HAAAdhwGP5fFlAAAARUlEQVQokWNgGDRARcugQUXLoAGXPDMuTQz//9czMDA4CIlJMr57/eIAQY1ImmAAq2ZmAppwamYmQhNWzcxEasLrbPoAAE6vJ4Iq1s7QAAAAAElFTkSuQmCC"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CHECKMARK_PATH = os.path.join(ASSETS_DIR, "checkmark_white.png")
ARROW_WHITE_PATH = os.path.join(ASSETS_DIR, "arrow_white.png")
ARROW_DARK_PATH = os.path.join(ASSETS_DIR, "arrow_dark.png")
ARROW_UP_WHITE_PATH = os.path.join(ASSETS_DIR, "arrow_up_white.png")
ARROW_UP_DARK_PATH = os.path.join(ASSETS_DIR, "arrow_up_dark.png")


def ensure_assets():
    import base64
    os.makedirs(ASSETS_DIR, exist_ok=True)
    if not os.path.exists(CHECKMARK_PATH):
        with open(CHECKMARK_PATH, "wb") as f:
            f.write(base64.b64decode(B64_CHECKMARK))
    with open(ARROW_WHITE_PATH, "wb") as f:
        f.write(base64.b64decode(B64_ARROW_WHITE))
    with open(ARROW_DARK_PATH, "wb") as f:
        f.write(base64.b64decode(B64_ARROW_DARK))
    with open(ARROW_UP_WHITE_PATH, "wb") as f:
        f.write(base64.b64decode(B64_ARROW_UP_WHITE))
    with open(ARROW_UP_DARK_PATH, "wb") as f:
        f.write(base64.b64decode(B64_ARROW_UP_DARK))


ensure_assets()


def detect_system_is_dark():
    """自动检测 Linux 系统 GNOME/GTK 是否处于深色模式"""
    try:
        res = subprocess.check_output(
            ['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        if 'dark' in res.lower():
            return True
    except Exception:
        pass

    gtk = os.environ.get('GTK_THEME', '')
    if 'dark' in gtk.lower():
        return True

    return True
