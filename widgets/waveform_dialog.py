#!/usr/bin/env python3
"""
PinScope v1.0 - 多路 GPIO 方波时序对比图窗口 (widgets/waveform_dialog.py)
"""

import time
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QScrollArea
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QPainter, QPainterPath, QPen


class WaveformCanvas(QWidget):
    """纯 QPainter 高性能逻辑方波绘制画布"""
    MIN_CHAN_H = 50

    def __init__(self, get_data_func, is_dark_theme=True, parent=None):
        super().__init__(parent)
        self.get_data_func = get_data_func
        self.is_dark = is_dark_theme
        self.setMinimumHeight(380)

    def adjust_height(self):
        selected_pins, _, _ = self.get_data_func()
        num_pins = len(selected_pins)
        needed_h = max(380, num_pins * self.MIN_CHAN_H + 30 + 48) if num_pins else 380
        if self.height() != needed_h:
            self.setFixedHeight(needed_h)

    def paintEvent(self, event):
        selected_pins, pin_history, start_time = self.get_data_func()
        pins = sorted(list(selected_pins))

        margin_left = 70
        margin_right = 30
        margin_top = 30
        margin_bottom = 48

        width = self.width()
        height = self.height()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        bg_color = QColor("#1E1E1E") if self.is_dark else QColor("#FFFFFF")
        grid_color = QColor("#333333") if self.is_dark else QColor("#E1E4E8")
        text_color = QColor("#D4D4D4") if self.is_dark else QColor("#57606A")
        wave_color = QColor("#4EC9B0") if self.is_dark else QColor("#0969DA")
        pin_bg_color = QColor("#0E639C") if self.is_dark else QColor("#005FB8")

        painter.fillRect(0, 0, width, height, bg_color)

        if not pins:
            painter.setPen(QPen(text_color))
            painter.setFont(QFont("Noto Sans CJK SC", 14))
            painter.drawText(self.rect(), Qt.AlignCenter, "暂无已勾选监视的引脚，请在主窗口勾选引脚")
            return

        plot_w = width - margin_left - margin_right
        plot_h = height - margin_top - margin_bottom

        now = time.time()
        window_duration = 15.0
        abs_end = now
        abs_start = now - window_duration

        num_pins = len(pins)
        chan_h = plot_h / num_pins

        # 绘制工业级固定相对时间刻度 (-15.0s ~ 0s (Now))
        labels = ["-15.0s", "-12.0s", "-9.0s", "-6.0s", "-3.0s", "0s (Now)"]
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        for step in range(6):
            x_pos = margin_left + (step / 5.0) * plot_w
            painter.setPen(QPen(grid_color, 1, Qt.DashLine))
            painter.drawLine(int(x_pos), margin_top, int(x_pos), height - margin_bottom)
            
            painter.setPen(QPen(text_color))
            painter.drawText(int(x_pos) - 35, height - 38, 70, 25, Qt.AlignCenter, labels[step])

        # 逐通道绘制方波
        for idx, pin in enumerate(pins):
            chan_top = margin_top + idx * chan_h
            chan_bot = chan_top + chan_h * 0.75
            wave_high_y = chan_top + chan_h * 0.15
            wave_low_y  = chan_bot

            # 通道分隔线
            painter.setPen(QPen(grid_color, 1, Qt.SolidLine))
            painter.drawLine(margin_left, int(chan_top), width - margin_right, int(chan_top))

            # 绘制引脚标签 Badge
            painter.setPen(Qt.NoPen)
            painter.setBrush(pin_bg_color)
            painter.drawRoundedRect(10, int(chan_top + 6), 50, 22, 4, 4)
            painter.setPen(QPen(QColor("#FFFFFF")))
            painter.setFont(QFont("Consolas", 10, QFont.Bold))
            painter.drawText(10, int(chan_top + 6), 50, 22, Qt.AlignCenter, pin)

            # 获取该引脚事件序列
            events = pin_history.get(pin, [(start_time, 0)])
            
            # 构建渲染点序列
            points = []
            curr_level = 0
            
            for ev_t, ev_level in events:
                if ev_t < abs_start:
                    curr_level = ev_level
                    continue
                if ev_t > abs_end:
                    break
                points.append((ev_t, ev_level))

            # 绘制方波 Path
            path = QPainterPath()
            start_x = margin_left
            curr_y = wave_high_y if curr_level == 1 else wave_low_y
            path.moveTo(start_x, curr_y)

            for ev_t, next_level in points:
                x_pos = margin_left + ((ev_t - abs_start) / window_duration) * plot_w
                next_y = wave_high_y if next_level == 1 else wave_low_y
                
                path.lineTo(x_pos, curr_y)   # 维持原电平水平延伸
                path.lineTo(x_pos, next_y)   # 垂直跳变
                curr_y = next_y

            # 延伸至右边界
            path.lineTo(margin_left + plot_w, curr_y)

            # 绘制波形线条
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(wave_color, 2.2, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))
            painter.drawPath(path)


class WaveformDialog(QDialog):
    """多路 GPIO 时序波形对比分析窗口"""
    def __init__(self, get_data_func, clear_func, is_dark_theme=True, parent=None):
        super().__init__(parent)
        self.get_data_func = get_data_func
        self.clear_func = clear_func
        self.is_dark = is_dark_theme

        self.setWindowTitle("PinScope - GPIO 多路波形时序对比图")
        self.resize(850, 520)
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        # 顶栏控制
        top_bar = QHBoxLayout()

        lbl_title = QLabel("📈 波形分析")
        lbl_title.setFont(QFont("Noto Sans CJK SC", 12, QFont.Bold))
        top_bar.addWidget(lbl_title)

        top_bar.addStretch()

        self.lbl_clock = QLabel()
        self.lbl_clock.setFont(QFont("Consolas", 11, QFont.Bold))
        clock_color = "#4EC9B0" if is_dark_theme else "#0969DA"
        self.lbl_clock.setStyleSheet(f"color: {clock_color};")
        top_bar.addWidget(self.lbl_clock)

        top_bar.addStretch()

        btn_clear = QPushButton("清空波形")
        btn_clear.setFont(QFont("Noto Sans CJK SC", 9, QFont.Bold))
        btn_clear.setFixedHeight(30)
        btn_clear.clicked.connect(self._on_clear_click)
        top_bar.addWidget(btn_clear)

        layout.addLayout(top_bar)

        # 滚动区域包裹波形画布
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.canvas = WaveformCanvas(get_data_func, is_dark_theme=self.is_dark)
        self.scroll.setWidget(self.canvas)
        layout.addWidget(self.scroll, 1)

        # 自动刷新 Timer (60 FPS, ~16ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_dialog)
        self.timer.start(16)

        # 样式应用
        bg_color = "#1E1E1E" if is_dark_theme else "#FFFFFF"
        text_color = "#CCCCCC" if is_dark_theme else "#24292F"
        btn_bg = "#3C3C3C" if is_dark_theme else "#F3F4F6"
        btn_hover = "#555555" if is_dark_theme else "#E5E7EB"
        border_color = "#555555" if is_dark_theme else "#D0D7DE"
        scroll_handle = "#555555" if is_dark_theme else "#D0D7DE"
        scroll_bg = "#2D2D30" if is_dark_theme else "#F6F8FA"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
            }}
            QLabel {{
                color: {text_color};
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollArea::viewport {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background: {scroll_bg};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {scroll_handle};
                border-radius: 5px;
            }}
            QPushButton {{
                background-color: {btn_bg};
                color: {text_color};
                border: 1px solid {border_color};
                border-radius: 4px;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
        """)

    def _refresh_dialog(self):
        self.canvas.adjust_height()
        now_str = time.strftime("%H:%M:%S", time.localtime())
        self.lbl_clock.setText(f"⏱ {now_str}")
        self.canvas.update()

    def _on_clear_click(self):
        if self.clear_func:
            self.clear_func()
        self.canvas.update()
