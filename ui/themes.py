"""
Theme management for QShare.

This module provides functions to apply and manage UI themes.
"""

def apply_theme(widget, theme_name):
    themes = {
        "dark": """
            QWidget { background-color: #1A1A1A; color: #FFFFFF; }
            QPushButton { background-color: #2D2D2D; border: 1px solid #3D3D3D; }
            QPushButton:hover { background-color: #3D3D3D; }
            QListWidget { background-color: #252525; border: 1px solid #3D3D3D; }
            QProgressBar { background: #252525; border: 1px solid #3D3D3D; }
            QProgressBar::chunk { background: #4CAF50; }
            QLabel { color: #CCCCCC; }
        """,
        # Other themes...
    }
    widget.setStyleSheet(themes.get(theme_name, themes["dark"]))
    widget.update() 