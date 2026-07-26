#!/usr/bin/env python3
"""
PinScope v1.0 - QSS 主题与独立样式引擎 (styles.py)
"""

from config import B64_CHECKMARK, B64_ARROW_WHITE, B64_ARROW_DARK


def get_theme_qss(is_dark: bool) -> str:
    """获取无缝融合且屏蔽白边焦点的 QSS 样式表"""
    if is_dark:
        return f"""
            *:focus {{ outline: none; }}
            QMainWindow {{ background-color: #1E1E1E; }}
            QWidget {{ background-color: #1E1E1E; color: #CCCCCC; font-family: 'Noto Sans CJK SC'; font-size: 13px; }}
            QWidget:focus {{ outline: none; }}
            
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
            QScrollArea::viewport {{ border: none; background-color: #252526; }}
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
            QComboBox:focus {{
                outline: none;
                border: 1px solid #0E639C;
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
                outline: none;
            }}
            
            QCheckBox {{
                color: #E0E0E0;
                font-size: 12px;
                font-weight: bold;
                spacing: 6px;
                background: transparent;
                border: none;
                outline: none;
            }}
            QCheckBox:focus {{
                outline: none;
                border: none;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid #666666;
                border-radius: 4px;
                background-color: #2D2D30;
            }}
            QCheckBox::indicator:focus {{
                outline: none;
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid #0E639C;
                background-color: #0E639C;
                image: url("data:image/png;base64,{B64_CHECKMARK}");
            }}
        """
    else:
        return f"""
            *:focus {{ outline: none; }}
            QMainWindow {{ background-color: #F6F8FA; }}
            QWidget {{ background-color: #F6F8FA; color: #24292F; font-family: 'Noto Sans CJK SC'; font-size: 13px; }}
            QWidget:focus {{ outline: none; }}
            
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
            QScrollArea::viewport {{ border: none; background-color: #FFFFFF; }}
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
            QComboBox:focus {{
                outline: none;
                border: 1px solid #0969DA;
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
                outline: none;
            }}
            
            QCheckBox {{
                color: #24292F;
                font-size: 12px;
                font-weight: bold;
                spacing: 6px;
                background: transparent;
                border: none;
                outline: none;
            }}
            QCheckBox:focus {{
                outline: none;
                border: none;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid #8C959F;
                border-radius: 4px;
                background-color: #FFFFFF;
            }}
            QCheckBox::indicator:focus {{
                outline: none;
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid #0969DA;
                background-color: #0969DA;
                image: url("data:image/png;base64,{B64_CHECKMARK}");
            }}
        """
