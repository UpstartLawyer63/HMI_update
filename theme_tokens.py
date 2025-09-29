from PyQt6.QtGui import QColor
from enum import Enum
from typing import Dict

class ColorToken(Enum):
    BACKGROUND = "background"
    BOX = "box"
    BORDER = "border"
    TEXT_PRIMARY = "text_primary"
    TEXT_SECONDARY = "text_secondary"
    ACCENT = "accent"    # add as needed

dark_theme: Dict[ColorToken, str] = {
    ColorToken.BACKGROUND: "#1E1E1E",
    ColorToken.BOX: "#2A2A2A",
    ColorToken.BORDER: "#383838",
    ColorToken.TEXT_PRIMARY: "#EAEAEA",
    ColorToken.TEXT_SECONDARY: "#B0B0B0",
    ColorToken.ACCENT: "#A67C52",
}

creme_theme: Dict[ColorToken, str] = {
    ColorToken.BACKGROUND: "#FAF7F2",
    ColorToken.BOX: "#FFFFFF",
    ColorToken.BORDER: "#E6DCCF",
    ColorToken.TEXT_PRIMARY: "#000000",
    ColorToken.TEXT_SECONDARY: "#6E6A66",
    ColorToken.ACCENT: "#A67C52",
}

"""
Explanation of theme manager: go to little developer manual for more on this to learn
There are two color themes the user can select from dark and creme
"""

class ThemeManager:
    def __init__(self, initial_theme: Dict[ColorToken, str] = dark_theme):
        self._theme = initial_theme
    
    def set_theme(self, theme_dict: Dict[ColorToken, str]):
        self._theme = theme_dict

    def get_hex(self, token: ColorToken) -> str:
        return self._theme[token]

    def get_qcolor(self, token: ColorToken, alpha: int = None) -> QColor:
        hexv = self.get_hex(token)
        if alpha is None:
            return QColor(hexv)
        c = QColor(hexv)
        c.setAlpha(alpha)
        return c

# Create the default theme instance that your main code expects
_theme = ThemeManager(initial_theme=dark_theme)

# Also keep the original name for backwards compatibility
theme = _theme