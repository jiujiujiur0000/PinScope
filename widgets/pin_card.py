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
        self.setMinimumHeight(125)
        self.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # 头部横向布局：左侧引脚徽章标签，右侧脉冲按钮与清零按钮
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        
        self.lbl_name = QLabel(self.pin_name)
        self.lbl_name.setFont(QFont("Consolas", 11, QFont.Bold))
        self.lbl_name.setAlignment(Qt.AlignCenter)
        self.lbl_name.setFixedHeight(26)
        header_layout.addWidget(self.lbl_name, 0, Qt.AlignVCenter)

        header_layout.addStretch()

        self.btn_pulse_single = QPushButton("脉冲")
        self.btn_pulse_single.setFont(QFont("Noto Sans CJK SC", 9, QFont.Bold))
        self.btn_pulse_single.setFixedSize(50, 26)
        self.btn_pulse_single.setCursor(Qt.PointingHandCursor)
        self.btn_pulse_single.setToolTip("对该引脚单独触发 1 次模拟高低电平跳变")
        if self.pulse_callback:
            self.btn_pulse_single.clicked.connect(lambda: self.pulse_callback(self.pin_name))
        header_layout.addWidget(self.btn_pulse_single, 0, Qt.AlignVCenter)

        self.btn_reset_single = QPushButton("清零")
        self.btn_reset_single.setFont(QFont("Noto Sans CJK SC", 9, QFont.Bold))
        self.btn_reset_single.setFixedSize(50, 26)
        self.btn_reset_single.setCursor(Qt.PointingHandCursor)
        self.btn_reset_single.setToolTip("清零该引脚的跳变记录与锁存状态")
        if self.reset_callback:
            self.btn_reset_single.clicked.connect(lambda: self.reset_callback(self.pin_name))
        header_layout.addWidget(self.btn_reset_single, 0, Qt.AlignVCenter)

        # 电平状态 Key-Value 横向布局
        level_layout = QHBoxLayout()
        self.lbl_level_key = QLabel("当前电平:")
        self.lbl_level_key.setFont(QFont("Noto Sans CJK SC", 10))
        
        self.lbl_level_val = QLabel("LOW (0)")
        self.lbl_level_val.setFont(QFont("Consolas", 9, QFont.Bold))
        self.lbl_level_val.setAlignment(Qt.AlignCenter)
        self.lbl_level_val.setFixedHeight(22)

        level_layout.addWidget(self.lbl_level_key, 0, Qt.AlignVCenter)
        level_layout.addStretch()
        level_layout.addWidget(self.lbl_level_val, 0, Qt.AlignVCenter)

        # 跳变累计 Key-Value 横向布局
        count_layout = QHBoxLayout()
        self.lbl_count_key = QLabel("跳变累计:")
        self.lbl_count_key.setFont(QFont("Noto Sans CJK SC", 10))
        
        self.lbl_count_val = QLabel("0 次")
        self.lbl_count_val.setFont(QFont("Noto Sans CJK SC", 10, QFont.Bold))
        self.lbl_count_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        count_layout.addWidget(self.lbl_count_key, 0, Qt.AlignVCenter)
        count_layout.addStretch()
        count_layout.addWidget(self.lbl_count_val, 0, Qt.AlignVCenter)

        layout.addLayout(header_layout)
        layout.addLayout(level_layout)
        layout.addLayout(count_layout)

    def apply_theme(self, is_dark):
        self.is_dark = is_dark
        self._update_styles()

    def set_idle(self):
        self._is_latched = False
        self._update_styles()

    def set_latched(self):
        self._is_latched = True
        self._update_styles()

    def _update_styles(self):
        if self.is_dark:
            self.setStyleSheet("""
                PinCard {
                    background-color: #2D2D30;
                    border: 2px solid #444444;
                    border-radius: 8px;
                }
            """)
            self.lbl_name.setStyleSheet("background-color: #0E639C; color: #FFFFFF; border-radius: 4px; padding: 2px 10px;")
            self.lbl_level_key.setStyleSheet("background: transparent; color: #CCCCCC;")
            self.lbl_count_key.setStyleSheet("background: transparent; color: #CCCCCC;")
            
            # Level value badge
            if self._level == 1:
                self.lbl_level_val.setStyleSheet("background-color: #27AE60; color: #FFFFFF; border-radius: 4px; padding: 2px 8px; font-weight: bold;")
            else:
                self.lbl_level_val.setStyleSheet("background-color: #383838; color: #AAAAAA; border-radius: 4px; padding: 2px 8px;")

            # Count value style
            if self._is_latched or self._count > 0:
                self.lbl_count_val.setStyleSheet("background: transparent; color: #4EC9B0; font-weight: bold;")
            else:
                self.lbl_count_val.setStyleSheet("background: transparent; color: #808080;")

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
                    background-color: #FFFFFF;
                    border: 2px solid #D0D7DE;
                    border-radius: 8px;
                }
            """)
            self.lbl_name.setStyleSheet("background-color: #005FB8; color: #FFFFFF; border-radius: 4px; padding: 2px 10px;")
            self.lbl_level_key.setStyleSheet("background: transparent; color: #24292F;")
            self.lbl_count_key.setStyleSheet("background: transparent; color: #24292F;")

            # Level value badge
            if self._level == 1:
                self.lbl_level_val.setStyleSheet("background-color: #1A7F37; color: #FFFFFF; border-radius: 4px; padding: 2px 8px; font-weight: bold;")
            else:
                self.lbl_level_val.setStyleSheet("background-color: #EFF2F5; color: #6E7781; border-radius: 4px; padding: 2px 8px;")

            # Count value style
            if self._is_latched or self._count > 0:
                self.lbl_count_val.setStyleSheet("background: transparent; color: #0969DA; font-weight: bold;")
            else:
                self.lbl_count_val.setStyleSheet("background: transparent; color: #6E7781;")

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
        self._is_latched = latched
        level_str = "HIGH (1)" if level == 1 else "LOW (0)"
        self.lbl_level_val.setText(level_str)
        self.lbl_count_val.setText(f"{count} 次")
        self._update_styles()

    def reset(self):
        self._count = 0
        self._level = 0
        self.update_state(0, False, 0)
