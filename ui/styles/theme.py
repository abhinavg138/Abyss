from ui.styles.colors import *

STYLE = f"""
QMainWindow {{
    background: {BACKGROUND};
}}

QWidget {{
    background: {BACKGROUND};
    color: {TEXT};
    font-family: Segoe UI;
    font-size: 11pt;
}}

QFrame {{
    border: none;
}}

QPushButton {{
    background: {PRIMARY};
    border-radius: 10px;
    padding: 8px;
    color: white;
}}

QPushButton:hover {{
    background: {PRIMARY_HOVER};
}}

QLineEdit {{
    background: {CHAT_BACKGROUND};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 10px;
}}

QTextEdit {{
    background: {CHAT_BACKGROUND};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 10px;
}}
"""