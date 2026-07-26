#!/usr/bin/env python3
"""
PinScope v1.0 - STM32/嵌入式 GPIO 引脚跳变锁存与计数诊断监视器
路径：/home/jiujiujiur0000/workspace/PinScope/pin_scope_app.py
运行：python3 /home/jiujiujiur0000/workspace/PinScope/pin_scope_app.py
"""

import sys
import os
import re
import glob
import threading
import subprocess

# 强制开启 Qt 高 DPI 自动缩放与自适应显示
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QScrollArea,
    QFrame, QGridLayout, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QPalette

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


class SignalBridge(QObject):
    pin_changed = pyqtSignal(str, int)


class PinCard(QFrame):
    """单个引脚卡片组件 (黄金比例尺寸)"""
    def __init__(self, pin_name, reset_callback=None, is_dark_theme=True, parent=None):
        super().__init__(parent)
        self.pin_name = pin_name
        self.reset_callback = reset_callback
        self.is_dark = is_dark_theme
        self._is_latched = False
        self._count = 0
        self._level = 0
        self._build()
        self.set_idle()

    def _build(self):
        self.setMinimumWidth(230)
        self.setMinimumHeight(140)
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # 头部横向布局：左侧引脚徽章标签，右侧清零按钮
        header_layout = QHBoxLayout()
        
        self.lbl_name = QLabel(self.pin_name)
        self.lbl_name.setFont(QFont("Consolas", 15, QFont.Bold))
        self.lbl_name.setAlignment(Qt.AlignCenter)
        self.lbl_name.setFixedHeight(28)
        header_layout.addWidget(self.lbl_name)

        header_layout.addStretch()

        self.btn_reset_single = QPushButton("清零")
        self.btn_reset_single.setFont(QFont("Noto Sans CJK SC", 9, QFont.Bold))
        self.btn_reset_single.setFixedSize(55, 26)
        self.btn_reset_single.setToolTip("清零该引脚的跳变记录与锁存状态")
        if self.reset_callback:
            self.btn_reset_single.clicked.connect(lambda: self.reset_callback(self.pin_name))
        header_layout.addWidget(self.btn_reset_single)

        self.lbl_level = QLabel("当前电平: LOW (0)")
        self.lbl_level.setFont(QFont("Noto Sans CJK SC", 12))

        # 状态标签（仅触发锁存时动态显示提示）
        self.lbl_status = QLabel("")
        self.lbl_status.setFont(QFont("Noto Sans CJK SC", 11, QFont.Bold))

        self.lbl_count = QLabel("跳变累计: 0 次")
        self.lbl_count.setFont(QFont("Noto Sans CJK SC", 12, QFont.Bold))

        layout.addLayout(header_layout)
        layout.addWidget(self.lbl_level)
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.lbl_count)

    def apply_theme(self, is_dark):
        self.is_dark = is_dark
        if self._is_latched:
            self.set_latched()
        else:
            self.set_idle()

    def set_idle(self):
        self._is_latched = False
        self.lbl_status.hide()
        if self.is_dark:
            self.setStyleSheet("""
                PinCard {
                    background-color: #2D2D30;
                    border: 2px solid #444444;
                    border-radius: 8px;
                }
            """)
            self.lbl_name.setStyleSheet("background-color: #0E639C; color: #FFFFFF; border-radius: 4px; padding: 2px 10px;")
            self.lbl_level.setStyleSheet("background: transparent; color: #E0E0E0;")
            self.lbl_status.setStyleSheet("background: transparent; color: #808080;")
            self.lbl_count.setStyleSheet("background: transparent; color: #4EC9B0;")
            self.btn_reset_single.setStyleSheet("""
                QPushButton { background-color: #3C3C3C; color: #E0E0E0; border: 1px solid #555; border-radius: 4px; }
                QPushButton:hover { background-color: #C0392B; color: #FFF; border: 1px solid #E74C3C; }
            """)
        else:
            self.setStyleSheet("""
                PinCard {
                    background-color: #F8F9FA;
                    border: 2px solid #D0D7DE;
                    border-radius: 8px;
                }
            """)
            self.lbl_name.setStyleSheet("background-color: #005FB8; color: #FFFFFF; border-radius: 4px; padding: 2px 10px;")
            self.lbl_level.setStyleSheet("background: transparent; color: #24292F;")
            self.lbl_status.setStyleSheet("background: transparent; color: #6E7781;")
            self.lbl_count.setStyleSheet("background: transparent; color: #0969DA;")
            self.btn_reset_single.setStyleSheet("""
                QPushButton { background-color: #EAEAEA; color: #24292F; border: 1px solid #D0D7DE; border-radius: 4px; }
                QPushButton:hover { background-color: #CF222E; color: #FFF; border: 1px solid #CF222E; }
            """)

    def set_latched(self):
        self._is_latched = True
        self.lbl_status.show()
        self.lbl_status.setText("[ 🚨 捕捉到跳变锁存! ]")
        if self.is_dark:
            self.setStyleSheet("""
                PinCard {
                    background-color: #6B0000;
                    border: 2px solid #FF4444;
                    border-radius: 8px;
                }
            """)
            self.lbl_name.setStyleSheet("background-color: #D32F2F; color: #FFFFFF; border-radius: 4px; padding: 2px 10px;")
            self.lbl_level.setStyleSheet("background: transparent; color: #FFFFFF;")
            self.lbl_status.setStyleSheet("background: transparent; color: #FFD700; font-weight: bold;")
            self.lbl_count.setStyleSheet("background: transparent; color: #4EC9B0; font-weight: bold;")
            self.btn_reset_single.setStyleSheet("""
                QPushButton { background-color: #800000; color: #FFF; border: 1px solid #FF6666; border-radius: 4px; }
                QPushButton:hover { background-color: #A00000; }
            """)
        else:
            self.setStyleSheet("""
                PinCard {
                    background-color: #FFEBE9;
                    border: 2px solid #CF222E;
                    border-radius: 8px;
                }
            """)
            self.lbl_name.setStyleSheet("background-color: #CF222E; color: #FFFFFF; border-radius: 4px; padding: 2px 10px;")
            self.lbl_level.setStyleSheet("background: transparent; color: #24292F;")
            self.lbl_status.setStyleSheet("background: transparent; color: #D1242F; font-weight: bold;")
            self.lbl_count.setStyleSheet("background: transparent; color: #0969DA; font-weight: bold;")
            self.btn_reset_single.setStyleSheet("""
                QPushButton { background-color: #FFD8D6; color: #82071E; border: 1px solid #CF222E; border-radius: 4px; }
                QPushButton:hover { background-color: #CF222E; color: #FFF; }
            """)

    def update_state(self, level, latched, count):
        self._level = level
        self._count = count
        level_str = "HIGH (1)" if level == 1 else "LOW (0)"
        self.lbl_level.setText(f"当前电平: {level_str}")
        self.lbl_count.setText(f"跳变累计: {count} 次")
        if latched:
            self.set_latched()
        else:
            self.set_idle()

    def reset(self):
        self._count = 0
        self._level = 0
        self.update_state(0, False, 0)


class PinScopeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PinScope v1.0 - 引脚跳变监视器")
        self.setMinimumSize(1180, 700)

        # 主题配置: 'auto' (跟随系统), 'dark', 'light'
        self.theme_mode = "auto"
        self.is_dark_theme = detect_system_is_dark()

        # 波特率相关记录
        self.user_custom_bauds = {}
        self.is_changing_port = False

        # 引脚列表
        self.pin_names = [f"PA{i}" for i in range(16)] + [f"PB{i}" for i in range(16)]
        self.pin_levels  = {p: 0     for p in self.pin_names}
        self.pin_latched = {p: False  for p in self.pin_names}
        self.pin_counts  = {p: 0     for p in self.pin_names}
        self.pin_cards   = {}

        # 默认勾选
        self.selected_pins = {"PA2", "PB8", "PB9"}

        # 信号桥
        self.bridge = SignalBridge()
        self.bridge.pin_changed.connect(self._on_pin_changed)

        self.is_connected = False
        self._build_ui()
        self.apply_theme_mode()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(14, 10, 14, 10)
        main_layout.setSpacing(10)

        # 1. 顶栏控制区（统一高度 36px 黄金比例）
        self.top_frame = QFrame()
        top_layout = QHBoxLayout(self.top_frame)
        top_layout.setContentsMargins(14, 8, 14, 8)
        top_layout.setSpacing(10)

        self.lbl_port_tag = QLabel("串口端口:")
        self.lbl_port_tag.setFont(QFont("Noto Sans CJK SC", 11, QFont.Bold))
        top_layout.addWidget(self.lbl_port_tag)

        self.port_combo = QComboBox()
        self.port_combo.setFixedWidth(200)
        self.port_combo.setFixedHeight(36)
        self.port_combo.currentIndexChanged.connect(self._on_port_changed)
        top_layout.addWidget(self.port_combo)

        # 刷新串口按钮
        self.btn_refresh_port = QPushButton("刷新")
        self.btn_refresh_port.setFont(QFont("Noto Sans CJK SC", 10, QFont.Bold))
        self.btn_refresh_port.setFixedHeight(36)
        self.btn_refresh_port.clicked.connect(self.refresh_ports)
        top_layout.addWidget(self.btn_refresh_port)

        top_layout.addSpacing(10)
        self.lbl_baud_tag = QLabel("波特率:")
        self.lbl_baud_tag.setFont(QFont("Noto Sans CJK SC", 11, QFont.Bold))
        top_layout.addWidget(self.lbl_baud_tag)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems([
            "115200", "9600", "19200", "38400", "57600",
            "230400", "460800", "921600", "1500000", "2000000"
        ])
        self.baud_combo.setFixedWidth(115)
        self.baud_combo.setFixedHeight(36)
        self.baud_combo.currentIndexChanged.connect(self._on_baud_user_changed)
        top_layout.addWidget(self.baud_combo)

        top_layout.addSpacing(10)
        self.btn_connect = QPushButton("连接串口")
        self.btn_connect.setFont(QFont("Noto Sans CJK SC", 10, QFont.Bold))
        self.btn_connect.setFixedHeight(36)
        self.btn_connect.clicked.connect(self.toggle_connect)
        top_layout.addWidget(self.btn_connect)

        self.btn_reset = QPushButton("重置清零所有记录")
        self.btn_reset.setFont(QFont("Noto Sans CJK SC", 10, QFont.Bold))
        self.btn_reset.setFixedHeight(36)
        self.btn_reset.clicked.connect(self.reset_all)
        top_layout.addWidget(self.btn_reset)

        top_layout.addStretch()

        # 三档主题模式下拉菜单 (宽 145px，彻底解决“跟随系统”截断)
        self.lbl_theme_tag = QLabel("主题:")
        self.lbl_theme_tag.setFont(QFont("Noto Sans CJK SC", 11, QFont.Bold))
        top_layout.addWidget(self.lbl_theme_tag)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["跟随系统", "深色模式", "浅色模式"])
        self.theme_combo.setFixedWidth(145)
        self.theme_combo.setFixedHeight(36)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_combo_changed)
        top_layout.addWidget(self.theme_combo)

        self.btn_demo = QPushButton("模拟脉冲测试")
        self.btn_demo.setFont(QFont("Noto Sans CJK SC", 10, QFont.Bold))
        self.btn_demo.setFixedHeight(36)
        self.btn_demo.clicked.connect(self.trigger_demo)
        top_layout.addWidget(self.btn_demo)

        main_layout.addWidget(self.top_frame)

        # 2. 主体：左侧勾选，右侧卡片
        body = QHBoxLayout()
        body.setSpacing(12)

        # 左侧引脚勾选器
        self.left_box = QGroupBox("引脚勾选过滤器")
        self.left_box.setFont(QFont("Noto Sans CJK SC", 11, QFont.Bold))
        self.left_box.setFixedWidth(165)
        left_layout = QVBoxLayout(self.left_box)
        left_layout.setContentsMargins(10, 16, 10, 10)
        left_layout.setSpacing(6)

        btn_row = QHBoxLayout()
        self.btn_select_all = QPushButton("全选")
        self.btn_select_all.setFont(QFont("Noto Sans CJK SC", 9, QFont.Bold))
        self.btn_select_all.setFixedHeight(28)
        self.btn_select_all.clicked.connect(lambda: self._set_all(True))
        self.btn_clear_all = QPushButton("清空")
        self.btn_clear_all.setFont(QFont("Noto Sans CJK SC", 9, QFont.Bold))
        self.btn_clear_all.setFixedHeight(28)
        self.btn_clear_all.clicked.connect(lambda: self._set_all(False))
        btn_row.addWidget(self.btn_select_all)
        btn_row.addWidget(self.btn_clear_all)
        left_layout.addLayout(btn_row)

        self.pin_scroll = QScrollArea()
        self.pin_scroll.setWidgetResizable(True)

        self.pin_list_widget = QWidget()
        pin_list_layout = QVBoxLayout(self.pin_list_widget)
        pin_list_layout.setContentsMargins(6, 6, 6, 6)
        pin_list_layout.setSpacing(4)

        self.checkboxes = {}
        for p in self.pin_names:
            cb = QCheckBox(p)
            cb.setFont(QFont("Consolas", 11, QFont.Bold))
            cb.setChecked(p in self.selected_pins)
            cb.stateChanged.connect(self._on_checkbox_changed)
            pin_list_layout.addWidget(cb)
            self.checkboxes[p] = cb

        pin_list_layout.addStretch()
        self.pin_scroll.setWidget(self.pin_list_widget)
        left_layout.addWidget(self.pin_scroll)
        body.addWidget(self.left_box)

        # 右侧卡片监视大屏
        self.right_box = QGroupBox("GPIO 状态监视")
        self.right_box.setFont(QFont("Noto Sans CJK SC", 11, QFont.Bold))
        self.right_layout_wrap = QVBoxLayout(self.right_box)

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.cards_widget = QWidget()
        self.cards_grid = QGridLayout(self.cards_widget)
        self.cards_grid.setContentsMargins(8, 8, 8, 8)
        self.cards_grid.setSpacing(12)
        self.cards_grid.setAlignment(Qt.AlignTop)

        for col in range(3):
            self.cards_grid.setColumnStretch(col, 1)

        self.cards_scroll.setWidget(self.cards_widget)
        self.right_layout_wrap.addWidget(self.cards_scroll)

        body.addWidget(self.right_box, 1)
        main_layout.addLayout(body, 1)

        self.refresh_ports()
        self._refresh_cards()

    def refresh_ports(self):
        """自动侦测端口硬件并刷新列表"""
        self.is_changing_port = True
        self.port_combo.clear()

        port_list = []
        if HAS_PYSERIAL:
            try:
                comports = serial.tools.list_ports.comports()
                for p in comports:
                    name_str = f"{p.device} ({p.description})" if p.description and p.description != "n/a" else p.device
                    port_list.append((p.device, name_str))
            except Exception:
                pass

        if not port_list:
            raw_ports = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
            for r in raw_ports:
                port_list.append((r, r))

        if not port_list:
            port_list = [("/dev/ttyUSB0", "/dev/ttyUSB0"), ("STDIN (标准输入)", "STDIN (标准输入)")]

        for dev, label in port_list:
            self.port_combo.addItem(label, userData=dev)

        self.is_changing_port = False
        self._on_port_changed()

    def _on_port_changed(self):
        """串口改变时触发默认/记忆波特率转换"""
        if self.is_changing_port:
            return
        
        current_dev = self.port_combo.currentData() or self.port_combo.currentText()
        if current_dev in self.user_custom_bauds:
            target_baud = self.user_custom_bauds[current_dev]
        else:
            target_baud = "115200"

        idx = self.baud_combo.findText(target_baud)
        if idx >= 0:
            self.baud_combo.setCurrentIndex(idx)

    def _on_baud_user_changed(self):
        """用户改变波特率时记录记忆"""
        if self.is_changing_port:
            return
        current_dev = self.port_combo.currentData() or self.port_combo.currentText()
        new_baud = self.baud_combo.currentText()
        if current_dev:
            self.user_custom_bauds[current_dev] = new_baud

    def _on_theme_combo_changed(self, idx):
        if idx == 0:
            self.theme_mode = "auto"
            self.is_dark_theme = detect_system_is_dark()
        elif idx == 1:
            self.theme_mode = "dark"
            self.is_dark_theme = True
        else:
            self.theme_mode = "light"
            self.is_dark_theme = False
        
        self.apply_theme_mode()

    def apply_theme_mode(self):
        """黄金比例控件长宽自适应样式"""
        if self.is_dark_theme:
            self.setStyleSheet(f"""
                QMainWindow {{ background-color: #1E1E1E; }}
                QWidget {{ background-color: #1E1E1E; color: #CCCCCC; font-family: 'Noto Sans CJK SC'; font-size: 13px; }}
                
                QGroupBox {{
                    border: 2px solid #444444;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 14px;
                    color: #CE9178;
                    font-weight: bold;
                    font-size: 13px;
                }}
                QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; }}
                
                QScrollArea {{ border: none; background-color: #252526; }}
                QScrollBar:vertical {{ background: #2D2D30; width: 10px; }}
                QScrollBar::handle:vertical {{ background: #555555; border-radius: 5px; }}
                
                QComboBox {{
                    background-color: #3C3C3C;
                    border: 1px solid #555555;
                    border-radius: 5px;
                    padding: 4px 26px 4px 10px;
                    color: #FFFFFF;
                    font-size: 13px;
                    font-weight: bold;
                }}
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 24px;
                    border-left-width: 0px;
                    border-top-right-radius: 5px;
                    border-bottom-right-radius: 5px;
                    background: transparent;
                }}
                QComboBox::down-arrow {{
                    image: url("data:image/png;base64,{B64_ARROW_WHITE}");
                    width: 12px;
                    height: 8px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: #252526;
                    color: #FFFFFF;
                    font-size: 13px;
                    selection-background-color: #0E639C;
                    border: 1px solid #555555;
                }}
                
                QCheckBox {{
                    color: #E0E0E0;
                    font-size: 12px;
                    font-weight: bold;
                    spacing: 6px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 2px solid #666666;
                    border-radius: 4px;
                    background-color: #2D2D30;
                }}
                QCheckBox::indicator:checked {{
                    border: 2px solid #0E639C;
                    background-color: #0E639C;
                    image: url("data:image/png;base64,{B64_CHECKMARK}");
                }}
            """)

            self.top_frame.setStyleSheet("QFrame { background-color: #252526; border-radius: 8px; }")
            self.lbl_port_tag.setStyleSheet("color: #CCCCCC;")
            self.lbl_baud_tag.setStyleSheet("color: #CCCCCC;")
            self.lbl_theme_tag.setStyleSheet("color: #CCCCCC;")

            self.btn_refresh_port.setStyleSheet("QPushButton { background:#3C3C3C; color:white; border:1px solid #555; border-radius:4px; padding:0 12px; } QPushButton:hover { background:#555; }")
            self.btn_connect.setStyleSheet("QPushButton { background:#0E639C; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#1177BB; }")
            self.btn_reset.setStyleSheet("QPushButton { background:#C0392B; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#E74C3C; }")
            self.btn_demo.setStyleSheet("QPushButton { background:#27AE60; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#2ECC71; }")
            
            self.btn_select_all.setStyleSheet("QPushButton { background:#3C3C3C; color:white; border:none; border-radius:4px; } QPushButton:hover { background:#555; }")
            self.btn_clear_all.setStyleSheet("QPushButton { background:#3C3C3C; color:white; border:none; border-radius:4px; } QPushButton:hover { background:#555; }")
            self.pin_list_widget.setStyleSheet("background:#252526;")
            self.cards_widget.setStyleSheet("background:#1E1E1E;")
        else:
            self.setStyleSheet(f"""
                QMainWindow {{ background-color: #F6F8FA; }}
                QWidget {{ background-color: #F6F8FA; color: #24292F; font-family: 'Noto Sans CJK SC'; font-size: 13px; }}
                
                QGroupBox {{
                    border: 2px solid #D0D7DE;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 14px;
                    color: #0969DA;
                    font-weight: bold;
                    font-size: 13px;
                }}
                QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; }}
                
                QScrollArea {{ border: none; background-color: #FFFFFF; }}
                QScrollBar:vertical {{ background: #F6F8FA; width: 10px; }}
                QScrollBar::handle:vertical {{ background: #D0D7DE; border-radius: 5px; }}
                
                QComboBox {{
                    background-color: #FFFFFF;
                    border: 1px solid #D0D7DE;
                    border-radius: 5px;
                    padding: 4px 26px 4px 10px;
                    color: #24292F;
                    font-size: 13px;
                    font-weight: bold;
                }}
                QComboBox::drop-down {{
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 24px;
                    border-left-width: 0px;
                    border-top-right-radius: 5px;
                    border-bottom-right-radius: 5px;
                    background: transparent;
                }}
                QComboBox::down-arrow {{
                    image: url("data:image/png;base64,{B64_ARROW_DARK}");
                    width: 12px;
                    height: 8px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: #FFFFFF;
                    color: #24292F;
                    font-size: 13px;
                    selection-background-color: #0969DA;
                    selection-color: #FFFFFF;
                    border: 1px solid #D0D7DE;
                }}
                
                QCheckBox {{
                    color: #24292F;
                    font-size: 12px;
                    font-weight: bold;
                    spacing: 6px;
                }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 2px solid #8C959F;
                    border-radius: 4px;
                    background-color: #FFFFFF;
                }}
                QCheckBox::indicator:checked {{
                    border: 2px solid #0969DA;
                    background-color: #0969DA;
                    image: url("data:image/png;base64,{B64_CHECKMARK}");
                }}
            """)

            self.top_frame.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #D0D7DE; border-radius: 8px; }")
            self.lbl_port_tag.setStyleSheet("color: #24292F;")
            self.lbl_baud_tag.setStyleSheet("color: #24292F;")
            self.lbl_theme_tag.setStyleSheet("color: #24292F;")

            self.btn_refresh_port.setStyleSheet("QPushButton { background:#F3F4F6; color:#24292F; border:1px solid #D0D7DE; border-radius:4px; padding:0 12px; } QPushButton:hover { background:#E5E7EB; }")
            self.btn_connect.setStyleSheet("QPushButton { background:#0969DA; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#0353E9; }")
            self.btn_reset.setStyleSheet("QPushButton { background:#CF222E; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#A40E26; }")
            self.btn_demo.setStyleSheet("QPushButton { background:#1A7F37; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#116327; }")

            self.btn_select_all.setStyleSheet("QPushButton { background:#F3F4F6; color:#24292F; border:1px solid #D0D7DE; border-radius:4px; } QPushButton:hover { background:#E5E7EB; }")
            self.btn_clear_all.setStyleSheet("QPushButton { background:#F3F4F6; color:#24292F; border:1px solid #D0D7DE; border-radius:4px; } QPushButton:hover { background:#E5E7EB; }")
            self.pin_list_widget.setStyleSheet("background:#FFFFFF;")
            self.cards_widget.setStyleSheet("background:#F6F8FA;")

        for card in self.pin_cards.values():
            card.apply_theme(self.is_dark_theme)

    def _on_checkbox_changed(self):
        self.selected_pins = {p for p, cb in self.checkboxes.items() if cb.isChecked()}
        self._refresh_cards()

    def _set_all(self, val):
        for cb in self.checkboxes.values():
            cb.setChecked(val)

    def _refresh_cards(self):
        for card in self.pin_cards.values():
            card.setParent(None)
        self.pin_cards.clear()

        pins = [p for p in self.pin_names if p in self.selected_pins]

        if not pins:
            empty_lbl = QLabel("请在左侧勾选您想要监控的引脚")
            empty_lbl.setFont(QFont("Noto Sans CJK SC", 15))
            empty_lbl.setStyleSheet("color: #808080;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.cards_grid.addWidget(empty_lbl, 0, 0)
            return

        cols = 3
        for idx, p in enumerate(pins):
            card = PinCard(p, reset_callback=self.reset_single_pin, is_dark_theme=self.is_dark_theme)
            card.update_state(self.pin_levels[p], self.pin_latched[p], self.pin_counts[p])
            self.cards_grid.addWidget(card, idx // cols, idx % cols)
            self.pin_cards[p] = card

    def _on_pin_changed(self, pin_name, level):
        if pin_name not in self.pin_names:
            return

        prev = self.pin_levels[pin_name]
        self.pin_levels[pin_name] = level

        if prev != level:
            self.pin_latched[pin_name] = True
            self.pin_counts[pin_name] += 1

        if pin_name in self.pin_cards:
            self.pin_cards[pin_name].update_state(
                level, self.pin_latched[pin_name], self.pin_counts[pin_name]
            )

    def reset_single_pin(self, pin_name):
        if pin_name in self.pin_names:
            self.pin_latched[pin_name] = False
            self.pin_counts[pin_name] = 0
            self.pin_levels[pin_name] = 0
            if pin_name in self.pin_cards:
                self.pin_cards[pin_name].reset()

    def reset_all(self):
        for p in self.pin_names:
            self.pin_latched[p] = False
            self.pin_counts[p] = 0
            self.pin_levels[p] = 0
        for card in self.pin_cards.values():
            card.reset()
        QMessageBox.information(self, "重置成功", "所有引脚跳变锁存记录与计数器已清零！")

    def trigger_demo(self):
        self.bridge.pin_changed.emit("PA2", 1)
        QTimer.singleShot(300, lambda: self.bridge.pin_changed.emit("PA2", 0))

    def toggle_connect(self):
        if not self.is_connected:
            self.is_connected = True
            self.btn_connect.setText("断开连接")
            if self.is_dark_theme:
                self.btn_connect.setStyleSheet("QPushButton { background:#C0392B; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#E74C3C; }")
            else:
                self.btn_connect.setStyleSheet("QPushButton { background:#CF222E; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#A40E26; }")
            t = threading.Thread(target=self._listen_stdin, daemon=True)
            t.start()
        else:
            self.is_connected = False
            self.btn_connect.setText("连接串口")
            if self.is_dark_theme:
                self.btn_connect.setStyleSheet("QPushButton { background:#0E639C; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#1177BB; }")
            else:
                self.btn_connect.setStyleSheet("QPushButton { background:#0969DA; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#0353E9; }")

    def _listen_stdin(self):
        pattern_hex = re.compile(r"0x([0-9a-fA-F]{4})")
        pattern_pin = re.compile(r"P([AB])(\d+):\s*([01])")

        for line in sys.stdin:
            if not self.is_connected:
                break

            m_hex = pattern_hex.search(line)
            if m_hex:
                val = int(m_hex.group(1), 16)
                for b in range(16):
                    self.bridge.pin_changed.emit(f"PA{b}", (val >> b) & 1)
                continue

            for port, num, val in pattern_pin.findall(line):
                self.bridge.pin_changed.emit(f"P{port}{num}", int(val))


if __name__ == "__main__":
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
