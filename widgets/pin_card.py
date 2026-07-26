#!/usr/bin/env python3
"""
PinScope v1.0 - 单个引脚胶囊徽章卡片组件 (widgets/pin_card.py)
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class PinCard(QFrame):
    """单个引脚卡片组件 (黄金比例尺寸与无缝状态切换)"""
    def __init__(self, pin_name, reset_callback=None, pulse_callback=None, is_dark_theme=True, parent=None):
        super().__init__(parent)
        self.pin_name = pin_name
        self.reset_callback = reset_callback
        self.pulse_callback = pulse_callback
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

        # 头部横向布局：左侧引脚徽章标签，右侧脉冲按钮与清零按钮
        header_layout = QHBoxLayout()
        
        self.lbl_name = QLabel(self.pin_name)
        self.lbl_name.setFont(QFont("Consolas", 15, QFont.Bold))
        self.lbl_name.setAlignment(Qt.AlignCenter)
        self.lbl_name.setFixedHeight(28)
        header_layout.addWidget(self.lbl_name)

        header_layout.addStretch()

        self.btn_pulse_single = QPushButton("脉冲")
        self.btn_pulse_single.setFont(QFont("Noto Sans CJK SC", 9, QFont.Bold))
        self.btn_pulse_single.setFixedSize(50, 26)
        self.btn_pulse_single.setToolTip("对该引脚单独触发 1 次模拟高低电平跳变")
        if self.pulse_callback:
            self.btn_pulse_single.clicked.connect(lambda: self.pulse_callback(self.pin_name))
        header_layout.addWidget(self.btn_pulse_single)

        self.btn_reset_single = QPushButton("清零")
        self.btn_reset_single.setFont(QFont("Noto Sans CJK SC", 9, QFont.Bold))
        self.btn_reset_single.setFixedSize(50, 26)
        self.btn_reset_single.setToolTip("清零该引脚的跳变记录与锁存状态")
        if self.reset_callback:
            self.btn_reset_single.clicked.connect(lambda: self.reset_callback(self.pin_name))
        header_layout.addWidget(self.btn_reset_single)

        self.lbl_level = QLabel("当前电平: LOW (0)")
        self.lbl_level.setFont(QFont("Noto Sans CJK SC", 12))

        self.lbl_count = QLabel("跳变累计: 0 次")
        self.lbl_count.setFont(QFont("Noto Sans CJK SC", 12, QFont.Bold))

        layout.addLayout(header_layout)
        layout.addWidget(self.lbl_level)
        layout.addWidget(self.lbl_count)

    def apply_theme(self, is_dark):
        self.is_dark = is_dark
        if self._is_latched:
            self.set_latched()
        else:
            self.set_idle()

    def set_idle(self):
        self._is_latched = False
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
            self.lbl_count.setStyleSheet("background: transparent; color: #808080;")
            self.btn_pulse_single.setStyleSheet("""
                QPushButton { background-color: #27AE60; color: #FFFFFF; border: none; border-radius: 4px; }
                QPushButton:hover { background-color: #2ECC71; }
            """)
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
            self.lbl_count.setStyleSheet("background: transparent; color: #6E7781;")
            self.btn_pulse_single.setStyleSheet("""
                QPushButton { background-color: #1A7F37; color: #FFFFFF; border: none; border-radius: 4px; }
                QPushButton:hover { background-color: #116327; }
            """)
            self.btn_reset_single.setStyleSheet("""
                QPushButton { background-color: #EAEAEA; color: #24292F; border: 1px solid #D0D7DE; border-radius: 4px; }
                QPushButton:hover { background-color: #CF222E; color: #FFF; border: 1px solid #CF222E; }
            """)

    def set_latched(self):
        self._is_latched = True
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
            self.lbl_count.setStyleSheet("background: transparent; color: #4EC9B0; font-weight: bold;")
            self.btn_pulse_single.setStyleSheet("""
                QPushButton { background-color: #27AE60; color: #FFFFFF; border: none; border-radius: 4px; }
                QPushButton:hover { background-color: #2ECC71; }
            """)
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
            self.lbl_count.setStyleSheet("background: transparent; color: #0969DA; font-weight: bold;")
            self.btn_pulse_single.setStyleSheet("""
                QPushButton { background-color: #1A7F37; color: #FFFFFF; border: none; border-radius: 4px; }
                QPushButton:hover { background-color: #116327; }
            """)
            self.btn_reset_single.setStyleSheet("""
                QPushButton { background-color: #EAEAEA; color: #24292F; border: 1px solid #D0D7DE; border-radius: 4px; }
                QPushButton:hover { background-color: #CF222E; color: #FFF; border: 1px solid #CF222E; }
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
