#!/usr/bin/env python3
"""
PinScope v1.0 - 主窗口与核心业务逻辑模块 (app.py)
"""

import sys
import glob
import re
import threading
import time

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QScrollArea,
    QFrame, QGridLayout, QMessageBox, QGroupBox, QDialog, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QPainterPath, QPen, QIntValidator

from config import HAS_PYSERIAL, detect_system_is_dark
from styles import get_theme_qss
from widgets import PinCard, WaveformDialog


if HAS_PYSERIAL:
    import serial
    import serial.tools.list_ports


def create_straight_checkmark_pixmap(size=28, bg_color="#27AE60", check_color="#FFFFFF"):
    """使用 QPainter 绘制绝对平直且带抗锯齿的几何勾号徽章"""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing, True)

    # 填充底色圆形
    painter.setBrush(QColor(bg_color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)

    # 绘制矢量平直勾号
    pen = QPen(QColor(check_color), 2.4, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
    painter.setPen(pen)

    path = QPainterPath()
    path.moveTo(7.5, 14.0)
    path.lineTo(11.5, 18.0)
    path.lineTo(20.0, 9.5)
    painter.drawPath(path)
    painter.end()
    return pix


def create_exclamation_pixmap(size=28, bg_color="#E67E22", fg_color="#FFFFFF"):
    """使用 QPainter 绘制带平滑抗锯齿的感叹号警告徽章"""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing, True)

    # 填充底色圆形
    painter.setBrush(QColor(bg_color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)

    # 绘制感叹号
    pen = QPen(QColor(fg_color), 2.8, Qt.SolidLine, Qt.RoundCap)
    painter.setPen(pen)
    painter.drawLine(size // 2, int(size * 0.25), size // 2, int(size * 0.55))

    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(fg_color))
    painter.drawEllipse(size // 2 - 2, int(size * 0.68), 4, 4)
    painter.end()
    return pix


class ModernMessageBox(QDialog):
    """自适应深浅色主题的高颜值弹窗对话框"""
    def __init__(self, title, message, icon_type="warning", is_dark_theme=True, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(380)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(18)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(14)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(28, 28)
        if icon_type == "success" or "成功" in title:
            icon_lbl.setPixmap(create_straight_checkmark_pixmap(28))
        elif icon_type == "error" or "失败" in title:
            icon_lbl.setPixmap(create_exclamation_pixmap(28, bg_color="#C0392B"))
        else:
            icon_lbl.setPixmap(create_exclamation_pixmap(28, bg_color="#E67E22"))
        icon_lbl.setStyleSheet("background: transparent;")
        content_layout.addWidget(icon_lbl)

        text_lbl = QLabel(message)
        text_lbl.setFont(QFont("Noto Sans CJK SC", 12, QFont.Bold))
        text_lbl.setWordWrap(True)
        text_lbl.setStyleSheet("background: transparent;")
        content_layout.addWidget(text_lbl, 1)

        layout.addLayout(content_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("确定")
        btn_ok.setFixedSize(90, 32)
        btn_ok.setFont(QFont("Noto Sans CJK SC", 10, QFont.Bold))
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)

        layout.addLayout(btn_layout)

        bg_color = "#252526" if is_dark_theme else "#FFFFFF"
        text_color = "#E0E0E0" if is_dark_theme else "#24292F"
        btn_bg = "#0E639C" if is_dark_theme else "#0969DA"
        btn_hover = "#1177BB" if is_dark_theme else "#0353E9"
        border_color = "#444444" if is_dark_theme else "#D0D7DE"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QLabel {{
                color: {text_color};
                background: transparent;
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
        """)


class SignalBridge(QObject):
    pin_changed = pyqtSignal(str, int)


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

        # 波形历史记录与时间戳
        self.start_time = time.time()
        self.pin_history = {p: [(self.start_time, 0)] for p in self.pin_names}

        # 默认勾选
        self.selected_pins = set()

        # 信号桥
        self.bridge = SignalBridge()
        self.bridge.pin_changed.connect(self._on_pin_changed)

        self.ser = None
        self.is_connected = False
        self.pulse_response_received = False
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
        self.port_combo.setFixedWidth(220)
        self.port_combo.setFixedHeight(36)
        self.port_combo.setMaxVisibleItems(10)
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
        self.baud_combo.setEditable(True)
        self.baud_combo.setValidator(QIntValidator(1200, 4000000, self))
        self.baud_combo.addItems([
            "9600", "19200", "38400", "57600", "115200",
            "230400", "460800", "921600", "1500000", "2000000"
        ])
        idx = self.baud_combo.findText("115200")
        if idx >= 0:
            self.baud_combo.setCurrentIndex(idx)
        self.baud_combo.setFixedWidth(110)
        self.baud_combo.setFixedHeight(36)
        self.baud_combo.setMaxVisibleItems(10)
        self.baud_combo.editTextChanged.connect(self._on_baud_user_changed)
        top_layout.addWidget(self.baud_combo)

        top_layout.addSpacing(10)
        self.btn_connect = QPushButton("连接串口")
        self.btn_connect.setFont(QFont("Noto Sans CJK SC", 10, QFont.Bold))
        self.btn_connect.setFixedHeight(36)
        self.btn_connect.clicked.connect(self.toggle_connect)
        top_layout.addWidget(self.btn_connect)

        self.btn_reset = QPushButton("清空跳变数据")
        self.btn_reset.setFont(QFont("Noto Sans CJK SC", 10, QFont.Bold))
        self.btn_reset.setFixedHeight(36)
        self.btn_reset.clicked.connect(self.reset_all)
        top_layout.addWidget(self.btn_reset)

        self.btn_waveform = QPushButton("波形时序图")
        self.btn_waveform.setFont(QFont("Noto Sans CJK SC", 10, QFont.Bold))
        self.btn_waveform.setFixedHeight(36)
        self.btn_waveform.clicked.connect(self.open_waveform_dialog)
        top_layout.addWidget(self.btn_waveform)

        top_layout.addStretch()

        # 三档主题模式下拉菜单
        self.lbl_theme_tag = QLabel("主题:")
        self.lbl_theme_tag.setFont(QFont("Noto Sans CJK SC", 11, QFont.Bold))
        top_layout.addWidget(self.lbl_theme_tag)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["跟随系统", "深色模式", "浅色模式"])
        self.theme_combo.setFixedWidth(120)
        self.theme_combo.setFixedHeight(36)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_combo_changed)
        top_layout.addWidget(self.theme_combo)

        self.btn_demo = QPushButton("批量脉冲")
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
            cb.setFocusPolicy(Qt.NoFocus)
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
        """自动侦测端口硬件并刷新列表（过滤 Linux 系统虚拟/空闲母板串口 ttyS*）"""
        self.is_changing_port = True
        self.port_combo.clear()

        port_list = []
        if HAS_PYSERIAL:
            try:
                comports = serial.tools.list_ports.comports()
                for p in comports:
                    # 过滤 Linux 系统默认预留的假串口 /dev/ttyS0 ~ ttyS31
                    if re.search(r"ttyS\d+", p.device):
                        continue
                    name_str = f"{p.device} ({p.description})" if p.description and p.description != "n/a" else p.device
                    port_list.append((p.device, name_str))
            except Exception:
                pass

        # 补全常规 Linux USB 串口节点
        usb_ports = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
        existing_devs = {dev for dev, _ in port_list}
        for u in usb_ports:
            if u not in existing_devs:
                port_list.append((u, u))

        # 增加标准输入模式选项
        if ("STDIN (标准输入)", "STDIN (标准输入)") not in port_list:
            port_list.append(("STDIN (标准输入)", "STDIN (标准输入)"))

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
        if current_dev and new_baud:
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
        """应用解耦的 QSS 样式表与自适应组件色彩"""
        self.setStyleSheet(get_theme_qss(self.is_dark_theme))

        if self.is_dark_theme:
            self.top_frame.setStyleSheet("QFrame { background-color: #252526; border-radius: 8px; }")
            self.lbl_port_tag.setStyleSheet("color: #CCCCCC;")
            self.lbl_baud_tag.setStyleSheet("color: #CCCCCC;")
            self.lbl_theme_tag.setStyleSheet("color: #CCCCCC;")

            self.btn_refresh_port.setStyleSheet("QPushButton { background:#3C3C3C; color:white; border:1px solid #555; border-radius:4px; padding:0 12px; } QPushButton:hover { background:#555; }")
            self.btn_connect.setStyleSheet("QPushButton { background:#0E639C; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#1177BB; }")
            self.btn_reset.setStyleSheet("QPushButton { background:#C0392B; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#E74C3C; }")
            self.btn_waveform.setStyleSheet("QPushButton { background:#8E44AD; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#9B59B6; }")
            self.btn_demo.setStyleSheet("QPushButton { background:#27AE60; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#2ECC71; }")
            
            self.btn_select_all.setStyleSheet("QPushButton { background:#3C3C3C; color:white; border:none; border-radius:4px; } QPushButton:hover { background:#555; }")
            self.btn_clear_all.setStyleSheet("QPushButton { background:#3C3C3C; color:white; border:none; border-radius:4px; } QPushButton:hover { background:#555; }")
            self.pin_list_widget.setStyleSheet("background:#252526;")
            self.cards_widget.setStyleSheet("background:#1E1E1E;")
            # 强制通过 QPalette 设置 viewport 背景色 —— 绕过 QSS 可能被 Fusion 引擎忽略的情况
            pal = QPalette()
            pal.setColor(QPalette.Window, QColor("#252526"))
            pal.setColor(QPalette.Base, QColor("#252526"))
            self.pin_scroll.viewport().setAutoFillBackground(True)
            self.pin_scroll.viewport().setPalette(pal)
            self.pin_scroll.setAutoFillBackground(True)
            self.pin_scroll.setPalette(pal)
        else:
            self.top_frame.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #D0D7DE; border-radius: 8px; }")
            self.lbl_port_tag.setStyleSheet("color: #24292F;")
            self.lbl_baud_tag.setStyleSheet("color: #24292F;")
            self.lbl_theme_tag.setStyleSheet("color: #24292F;")

            self.btn_refresh_port.setStyleSheet("QPushButton { background:#F3F4F6; color:#24292F; border:1px solid #D0D7DE; border-radius:4px; padding:0 12px; } QPushButton:hover { background:#E5E7EB; }")
            self.btn_connect.setStyleSheet("QPushButton { background:#0969DA; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#0353E9; }")
            self.btn_reset.setStyleSheet("QPushButton { background:#CF222E; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#A40E26; }")
            self.btn_waveform.setStyleSheet("QPushButton { background:#8250DF; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#6E40C9; }")
            self.btn_demo.setStyleSheet("QPushButton { background:#1A7F37; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#116327; }")

            self.btn_select_all.setStyleSheet("QPushButton { background:#F3F4F6; color:#24292F; border:1px solid #D0D7DE; border-radius:4px; } QPushButton:hover { background:#E5E7EB; }")
            self.btn_clear_all.setStyleSheet("QPushButton { background:#F3F4F6; color:#24292F; border:1px solid #D0D7DE; border-radius:4px; } QPushButton:hover { background:#E5E7EB; }")
            self.pin_list_widget.setStyleSheet("background:#FFFFFF;")
            self.cards_widget.setStyleSheet("background:#F6F8FA;")
            pal = QPalette()
            pal.setColor(QPalette.Window, QColor("#FFFFFF"))
            pal.setColor(QPalette.Base, QColor("#FFFFFF"))
            self.pin_scroll.viewport().setAutoFillBackground(True)
            self.pin_scroll.viewport().setPalette(pal)
            self.pin_scroll.setAutoFillBackground(True)
            self.pin_scroll.setPalette(pal)

        for card in self.pin_cards.values():
            card.apply_theme(self.is_dark_theme)

    def _on_checkbox_changed(self):
        self.selected_pins = {p for p, cb in self.checkboxes.items() if cb.isChecked()}
        self._refresh_cards()

    def _set_all(self, val):
        self.pin_list_widget.setUpdatesEnabled(False)
        for cb in self.checkboxes.values():
            cb.blockSignals(True)
            cb.setChecked(val)
            cb.blockSignals(False)
        self.pin_list_widget.setUpdatesEnabled(True)
        self._on_checkbox_changed()

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
            card = PinCard(
                p,
                reset_callback=self.reset_single_pin,
                pulse_callback=self.trigger_single_pulse,
                is_dark_theme=self.is_dark_theme
            )
            card.update_state(self.pin_levels[p], self.pin_latched[p], self.pin_counts[p])
            self.cards_grid.addWidget(card, idx // cols, idx % cols)
            self.pin_cards[p] = card

    def send_command(self, cmd_str):
        if self.is_connected and hasattr(self, 'ser') and self.ser and getattr(self.ser, 'is_open', False):
            try:
                if not cmd_str.endswith('\n'):
                    cmd_str += '\n'
                self.ser.write(cmd_str.encode('utf-8'))
            except Exception as e:
                print(f"串口发送错误: {e}")

    def trigger_single_pulse(self, pin_name):
        if pin_name in self.pin_names:
            if self.is_connected and hasattr(self, 'ser') and self.ser and getattr(self.ser, 'is_open', False):
                self.pulse_response_received = False
                self.send_command(f"PULSE:{pin_name}\n")
                QTimer.singleShot(100, lambda: self._check_pulse_response(pin_name))
            else:
                dialog = ModernMessageBox("串口未连接", "请先连接串口。", is_dark_theme=self.is_dark_theme, parent=self)
                dialog.exec_()

    def _on_pin_changed(self, pin_name, level):
        if pin_name not in self.pin_names:
            return

        prev = self.pin_levels[pin_name]
        self.pin_levels[pin_name] = level

        if prev != level:
            self.pin_latched[pin_name] = True
            self.pin_counts[pin_name] += 1
            self.pin_history[pin_name].append((time.time(), level))

        if pin_name in self.pin_cards:
            self.pin_cards[pin_name].update_state(
                level, self.pin_latched[pin_name], self.pin_counts[pin_name]
            )

    def reset_single_pin(self, pin_name):
        if pin_name in self.pin_names:
            self.pin_latched[pin_name] = False
            self.pin_counts[pin_name] = 0
            self.pin_levels[pin_name] = 0
            self.pin_history[pin_name] = [(time.time(), 0)]
            if pin_name in self.pin_cards:
                self.pin_cards[pin_name].reset()

    def reset_all(self):
        now = time.time()
        self.start_time = now
        for p in self.pin_names:
            self.pin_latched[p] = False
            self.pin_counts[p] = 0
            self.pin_levels[p] = 0
            self.pin_history[p] = [(now, 0)]
        for card in self.pin_cards.values():
            card.reset()
        dialog = ModernMessageBox("重置成功", "所有引脚跳变锁存记录与计数器已清零！", is_dark_theme=self.is_dark_theme, parent=self)
        dialog.exec_()

    def get_waveform_data(self):
        return self.selected_pins, self.pin_history, self.start_time

    def clear_waveform_data(self):
        now = time.time()
        self.start_time = now
        for p in self.pin_names:
            self.pin_history[p] = [(now, self.pin_levels[p])]

    def open_waveform_dialog(self):
        if not hasattr(self, 'waveform_dialog') or self.waveform_dialog is None or not self.waveform_dialog.isVisible():
            self.waveform_dialog = WaveformDialog(
                self.get_waveform_data,
                self.clear_waveform_data,
                is_dark_theme=self.is_dark_theme,
                parent=None
            )
            self.waveform_dialog.show()
        else:
            self.waveform_dialog.raise_()
            self.waveform_dialog.activateWindow()

    def trigger_demo(self):
        if not (self.is_connected and hasattr(self, 'ser') and self.ser and getattr(self.ser, 'is_open', False)):
            dialog = ModernMessageBox("串口未连接", "请先连接串口。", is_dark_theme=self.is_dark_theme, parent=self)
            dialog.exec_()
            return
        self.pulse_response_received = False
        target_pins = list(self.selected_pins) if self.selected_pins else self.pin_names
        for p in target_pins:
            self.send_command(f"PULSE:{p}\n")
        QTimer.singleShot(100, lambda: self._check_pulse_response("目标引脚"))

    def toggle_connect(self):
        if not self.is_connected:
            current_dev = self.port_combo.currentData() or self.port_combo.currentText()
            baud_str = self.baud_combo.currentText()
            try:
                baud = int(baud_str)
            except ValueError:
                baud = 115200

            use_real_serial = False
            if current_dev and current_dev != "STDIN (标准输入)":
                try:
                    import serial
                    self.ser = serial.Serial(current_dev, baudrate=baud, timeout=0.1)
                    use_real_serial = True
                except Exception as e:
                    err_msg = str(e)
                    if "Permission" in err_msg or "13" in err_msg:
                        tip = f"权限不足：无法访问 {current_dev}。\n请在终端执行：\nsudo chmod 666 {current_dev}"
                    elif "Input/output error" in err_msg or "5" in err_msg or "ttyS" in current_dev:
                        tip = f"选定的串口不可用或未连接物理硬件 ({current_dev})。\n请确认 USB转TTL 模块（如 CH340）已插入电脑并选择 /dev/ttyUSB0。"
                    else:
                        tip = f"无法打开串口 {current_dev}:\n{err_msg}"

                    dialog = ModernMessageBox("连接失败", tip, icon_type="error", is_dark_theme=self.is_dark_theme, parent=self)
                    dialog.exec_()
                    self.ser = None
                    self.is_connected = False
                    return

            self.is_connected = True
            self.btn_connect.setText("断开连接")
            if self.is_dark_theme:
                self.btn_connect.setStyleSheet("QPushButton { background:#C0392B; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#E74C3C; }")
            else:
                self.btn_connect.setStyleSheet("QPushButton { background:#CF222E; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#A40E26; }")

            if use_real_serial and self.ser:
                t = threading.Thread(target=self._listen_serial, daemon=True)
                t.start()
            else:
                t = threading.Thread(target=self._listen_stdin, daemon=True)
                t.start()
        else:
            self.is_connected = False
            if hasattr(self, 'ser') and self.ser:
                try:
                    self.ser.close()
                except Exception:
                    pass
                self.ser = None
            self.btn_connect.setText("连接串口")
            if self.is_dark_theme:
                self.btn_connect.setStyleSheet("QPushButton { background:#0E639C; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#1177BB; }")
            else:
                self.btn_connect.setStyleSheet("QPushButton { background:#0969DA; color:white; border:none; border-radius:5px; padding: 0 16px; } QPushButton:hover { background:#0353E9; }")

    def _listen_serial(self):
        pattern_hex = re.compile(r"0x([0-9a-fA-F]{4})")
        pattern_pin = re.compile(r"P([AB])(\d+):\s*([01])")

        while self.is_connected and hasattr(self, 'ser') and self.ser and getattr(self.ser, 'is_open', False):
            try:
                line_bytes = self.ser.readline()
                if not line_bytes:
                    continue
                line = line_bytes.decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                self.pulse_response_received = True

                if "PONG" in line:
                    continue

                m_hex = pattern_hex.search(line)
                if m_hex:
                    val = int(m_hex.group(1), 16)
                    for b in range(16):
                        self.bridge.pin_changed.emit(f"PA{b}", (val >> b) & 1)
                    continue

                for port, num, val in pattern_pin.findall(line):
                    self.bridge.pin_changed.emit(f"P{port}{num}", int(val))
            except Exception:
                time.sleep(0.02)

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

    def _check_pulse_response(self, target_name):
        if self.is_connected and not self.pulse_response_received:
            msg = f"对 {target_name} 发送脉冲指令后未收到单片机响应！\n\n请检查：\n1. STM32 main.c 中是否调用了 PinScope_Init();\n2. 串口 TX/RX 杜邦线是否接反 (TX接RX, RX接TX)。"
            dialog = ModernMessageBox("未收到单片机响应", msg, is_dark_theme=self.is_dark_theme, parent=self)
            dialog.exec_()
