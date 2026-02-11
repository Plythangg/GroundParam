"""
Apple-Style Theme Configuration
Based on Theme.txt design specifications

Design Philosophy:
- Soft Modern, Clean, Premium, Data-focused
- Less UI, More Content
- Calm, Trust, Professional, Confident
"""

# Color Palette
COLORS = {
    # Background Colors
    'background_light': '#F5F5F7',
    'background_dark': '#1C1C1E',

    # Surface/Card Colors
    'surface_light': '#FFFFFF',
    'surface_dark': '#2C2C2E',

    # Accent Colors (use sparingly)
    'primary': '#007AFF',      # Apple Blue
    'success': '#34C759',      # Green
    'warning': '#FF9F0A',      # Orange
    'error': '#FF3B30',        # Red

    # Text Colors
    'text_primary_light': '#000000',
    'text_secondary_light': '#6E6E73',
    'text_primary_dark': '#FFFFFF',
    'text_secondary_dark': '#98989D',

    # Border Colors
    'border_light': '#D1D1D6',
    'border_dark': '#38383A',

    # Shadow
    'shadow': 'rgba(0, 0, 0, 0.08)',
}

# Typography
FONTS = {
    'family': 'SF Pro Display, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif',
    'size_large': 20,
    'size_medium': 14,
    'size_small': 12,
}

# Spacing
SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 16,
    'lg': 24,
    'xl': 32,
}

# Border Radius
RADIUS = {
    'small': 6,
    'medium': 10,
    'large': 14,
}


def get_stylesheet(theme='light'):
    """
    Generate QSS (Qt Style Sheet) for Apple-style UI

    Args:
        theme (str): 'light' or 'dark'

    Returns:
        str: Complete QSS stylesheet
    """

    if theme == 'dark':
        bg = COLORS['background_dark']
        surface = COLORS['surface_dark']
        text_primary = COLORS['text_primary_dark']
        text_secondary = COLORS['text_secondary_dark']
        border = COLORS['border_dark']
    else:
        bg = COLORS['background_light']
        surface = COLORS['surface_light']
        text_primary = COLORS['text_primary_light']
        text_secondary = COLORS['text_secondary_light']
        border = COLORS['border_light']

    return f"""
    /* Main Window */
    QMainWindow {{
        background-color: {bg};
    }}

    /* Panels and Cards */
    QWidget#card {{
        background-color: {surface};
        border-radius: {RADIUS['medium']}px;
        border: 1px solid {border};
    }}

    QFrame {{
        background-color: {surface};
        border-radius: {RADIUS['medium']}px;
        border: 1px solid {border};
    }}

    /* Buttons */
    QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: {RADIUS['small']}px;
        padding: 8px 16px;
        font-size: {FONTS['size_medium']}px;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: #0051D5;
    }}

    QPushButton:pressed {{
        background-color: #004FC1;
    }}

    QPushButton:disabled {{
        background-color: {border};
        color: {text_secondary};
    }}

    /* Secondary Button */
    QPushButton#secondary {{
        background-color: {surface};
        color: {text_primary};
        border: 1px solid {border};
    }}

    QPushButton#secondary:hover {{
        background-color: {border};
    }}

    /* Labels */
    QLabel {{
        color: {text_primary};
        font-size: {FONTS['size_medium']}px;
        background: transparent;
        border: none;
    }}

    QLabel#title {{
        font-size: {FONTS['size_large']}px;
        font-weight: 600;
        color: {text_primary};
    }}

    QLabel#subtitle {{
        font-size: {FONTS['size_small']}px;
        color: {text_secondary};
    }}

    /* Input Fields */
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {surface};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: {RADIUS['small']}px;
        padding: 6px 10px;
        font-size: {FONTS['size_medium']}px;
    }}

    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {COLORS['primary']};
    }}

    /* Combo Box */
    QComboBox {{
        background-color: {surface};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: {RADIUS['small']}px;
        padding: 6px 10px;
        font-size: {FONTS['size_medium']}px;
    }}

    QComboBox:hover {{
        border: 1px solid {COLORS['primary']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {surface};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: {RADIUS['small']}px;
        selection-background-color: {COLORS['primary']};
    }}

    /* Table Widget */
    QTableWidget {{
        background-color: {surface};
        color: {text_primary};
        gridline-color: {border};
        border: 1px solid {border};
        border-radius: {RADIUS['small']}px;
        font-size: {FONTS['size_medium']}px;
    }}

    QTableWidget::item {{
        padding: 4px;
    }}

    QTableWidget::item:selected {{
        background-color: {COLORS['primary']};
        color: white;
    }}

    QHeaderView::section {{
        background-color: {bg};
        color: {text_primary};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {border};
        border-right: 1px solid {border};
        font-weight: 600;
    }}

    /* Scroll Bar */
    QScrollBar:vertical {{
        background: {bg};
        width: 10px;
        border-radius: 5px;
    }}

    QScrollBar::handle:vertical {{
        background: {border};
        border-radius: 5px;
        min-height: 20px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {text_secondary};
    }}

    QScrollBar:horizontal {{
        background: {bg};
        height: 10px;
        border-radius: 5px;
    }}

    QScrollBar::handle:horizontal {{
        background: {border};
        border-radius: 5px;
        min-width: 20px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {text_secondary};
    }}

    QScrollBar::add-line, QScrollBar::sub-line {{
        border: none;
        background: none;
    }}

    /* Tab Widget */
    QTabWidget::pane {{
        border: 1px solid {border};
        border-radius: {RADIUS['medium']}px;
        background-color: {surface};
    }}

    QTabBar::tab {{
        background-color: {bg};
        color: {text_secondary};
        padding: 10px 20px;
        border: none;
        border-top-left-radius: {RADIUS['small']}px;
        border-top-right-radius: {RADIUS['small']}px;
        margin-right: 2px;
    }}

    QTabBar::tab:selected {{
        background-color: {surface};
        color: {COLORS['primary']};
        font-weight: 600;
    }}

    QTabBar::tab:hover {{
        background-color: {border};
    }}

    /* Menu Bar */
    QMenuBar {{
        background-color: {surface};
        color: {text_primary};
        border-bottom: 1px solid {border};
        padding: 4px;
    }}

    QMenuBar::item:selected {{
        background-color: {COLORS['primary']};
        color: white;
        border-radius: {RADIUS['small']}px;
    }}

    QMenu {{
        background-color: {surface};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: {RADIUS['small']}px;
    }}

    QMenu::item:selected {{
        background-color: {COLORS['primary']};
        color: white;
        border-radius: {RADIUS['small']}px;
    }}

    /* Tooltips */
    QToolTip {{
        background-color: {surface};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: {RADIUS['small']}px;
        padding: 4px 8px;
        font-size: {FONTS['size_small']}px;
    }}
    """
