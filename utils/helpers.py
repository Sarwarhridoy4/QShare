"""
Utility functions for QShare.

This module provides helper functions used across the application.
"""

import os
from PyQt6.QtGui import QFontDatabase, QFont

def load_font(app):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(base_dir, "..", "res", "Roboto-Black.ttf")
    
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            app.setFont(QFont(font_family, 10)) 