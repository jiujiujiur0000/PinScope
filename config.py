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

# 高清 base64 PNG 图标
B64_CHECKMARK = "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAA9hAAAPYQGoP6dpAAAA4ElEQVQ4jZXTMUoEMRiG4TjuilgKglZewcbewso7WHkBQbQQPIOdFxCL7byAYiNeYAtBEEHC1kYQxX0sHPFjdkdm/mqS/3vfJENSSs9CleOqLdgCz5dSrnFcf/de/cRfXWGuD7yJjxAc9YGXcB/wTfNf/AZnbglnAb9ivRkY4hC3GDR6O5iEYHdqVdxFYD96K3iJ3qjtjAeNLa7W85cx/4zlNsEA4wifYy/GX9ieCYdkK846wVsITv+FQ3JhusZY7CpYw3vAn9joBNeCCg8heOwMh2QBT35u3rC3IESdHso34tZeO6m1m/YAAAAASUVORK5CYII="
B64_ARROW_WHITE = "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAICAYAAADN5B7xAAAACXBIWXMAAA9hAAAPYQGoP6dpAAAAeUlEQVQYlX2MwQ3CMBAE10guIa4BlC7oG4ogkZUaaCDS3GP5mMiKMPe8mdlku0hSSumtP3d4wCpJOef7KLJdIuIpyZf2myPi8V0ZyLMky3YBFsDAYnvqZWBt7HWwX9FQ7tamLqrANpRPUW2igTqUu+gWETuw276e+QftLamoo//0z"
B64_ARROW_DARK = "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAICAYAAADN5B7xAAAACXBIWXMAAA9hAAAPYQGoP6dpAAAAqElEQVQYlX3M0WnDQBCE4X+P3RLkFoyREJwaMMh1S5ACZIFicGpIShBi/OIzJom9jzPfrLVtuwNYluWbN1dciogxIsYSvMIRMbr7kAAk1e4+/DcqWFINKK3r2gMXoHH3IedcvcCfkk5WCncfgAa4SOq3bbPfeJ7nHyvfcs6VmY1AI+maUkqS9s8Y4DEoI+DDzA736CrpWPCfAUDXdQfgDGBmeZqmr+f+BtaRU42Glacy"


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
