"""
Borehole Settings Dialog
Dialog for editing borehole display settings (symbol, label, size, color)
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QSpinBox, QColorDialog
)
from PyQt6.QtCore import Qt, QLocale
from PyQt6.QtGui import QFont, QColor, QPixmap, QPainter, QPen
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np


class BHSettingsDialog(QDialog):
    """Dialog for editing borehole display settings"""

    # Available marker symbols with Unicode symbols for display
    MARKER_SYMBOLS = {
        '● Circle': 'o',
        '■ Square': 's',
        '▲ Triangle Up': '^',
        '▼ Triangle Down': 'v',
        '◄ Triangle Left': '<',
        '► Triangle Right': '>',
        '◆ Diamond': 'D',
        '⬟ Pentagon': 'p',
        '⬢ Hexagon': 'h',
        '★ Star': '*',
        '✚ Plus': 'P',
        '✖ Cross': 'X',
    }

    # Default colors
    DEFAULT_COLORS = [
        '#1f77b4',  # Blue
        '#ff7f0e',  # Orange
        '#2ca02c',  # Green
        '#d62728',  # Red
        '#9467bd',  # Purple
        '#8c564b',  # Brown
        '#e377c2',  # Pink
        '#7f7f7f',  # Gray
        '#bcbd22',  # Olive
        '#17becf',  # Cyan
    ]

    def __init__(self, bh_names, current_settings=None, parent=None):
        """
        Initialize BH Settings Dialog

        Args:
            bh_names: List of borehole names
            current_settings: Dict of current settings {bh_name: {symbol, label, size, color}}
            parent: Parent widget
        """
        super().__init__(parent)
        self.bh_names = bh_names
        self.current_settings = current_settings or {}
        self.settings = {}

        self.setWindowTitle("Borehole Display Settings")
        self.setMinimumSize(700, 500)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Description
        desc = QLabel("Customize the appearance of each borehole in plots")
        desc.setFont(QFont("SF Pro Display", 11))
        desc.setStyleSheet("color: #666;")
        layout.addWidget(desc)

        layout.addSpacing(8)

        # Settings table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            'Borehole', 'Symbol', 'Size', 'Color'
        ])
        self.table.setRowCount(len(self.bh_names))

        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 100)

        self.table.setFont(QFont("SF Pro Display", 12))
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        reset_btn = QPushButton("Reset to Default")
        reset_btn.setFont(QFont("SF Pro Display", 12))
        reset_btn.clicked.connect(self._reset_to_default)
        button_layout.addWidget(reset_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont("SF Pro Display", 12))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.setFont(QFont("SF Pro Display", 12))
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_settings(self):
        """Load current settings into table"""
        for row, bh_name in enumerate(self.bh_names):
            # Get current settings or use defaults
            if bh_name in self.current_settings:
                settings = self.current_settings[bh_name]
            else:
                settings = self._get_default_settings(row)

            # Column 0: Borehole name (read-only)
            name_item = QTableWidgetItem(bh_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setFont(QFont("SF Pro Display", 11, QFont.Weight.Bold))
            self.table.setItem(row, 0, name_item)

            # Column 1: Symbol (combo box with icons)
            symbol_combo = QComboBox()
            symbol_combo.addItems(list(self.MARKER_SYMBOLS.keys()))
            # Find current symbol
            current_symbol = settings.get('symbol', 'o')
            for i, (name, symbol) in enumerate(self.MARKER_SYMBOLS.items()):
                if symbol == current_symbol:
                    symbol_combo.setCurrentIndex(i)
                    break
            # Use larger font to make symbols more visible
            symbol_combo.setFont(QFont("Arial", 13))
            symbol_combo.setStyleSheet("QComboBox { padding: 2px 5px; }")
            self.table.setCellWidget(row, 1, symbol_combo)

            # Column 2: Size (spin box)
            size_spin = QSpinBox()
            size_spin.setMinimum(1)
            size_spin.setMaximum(30)
            size_spin.setValue(settings.get('size', 5))
            size_spin.setFont(QFont("Arial", 12))
            # Force English numerals
            size_spin.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
            # Set layout direction to right-to-left to reverse button order
            size_spin.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            # But keep text left-to-right
            size_spin.lineEdit().setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            self.table.setCellWidget(row, 2, size_spin)

            # Column 3: Color (button)
            color_btn = QPushButton()
            color = settings.get('color', self.DEFAULT_COLORS[row % len(self.DEFAULT_COLORS)])
            color_btn.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")
            color_btn.setFixedHeight(25)
            color_btn.clicked.connect(lambda checked, r=row, btn=color_btn: self._choose_color(r, btn))
            self.table.setCellWidget(row, 3, color_btn)

            # Set row height
            self.table.setRowHeight(row, 35)

    def _get_default_settings(self, index):
        """Get default settings for a borehole"""
        return {
            'symbol': 'o',
            'size': 5,  # Default marker size = 5
            'color': self.DEFAULT_COLORS[index % len(self.DEFAULT_COLORS)]
        }

    def _reset_to_default(self):
        """Reset all settings to default"""
        for row in range(len(self.bh_names)):
            default_settings = self._get_default_settings(row)

            # Reset symbol
            symbol_combo = self.table.cellWidget(row, 1)
            for i, (name, symbol) in enumerate(self.MARKER_SYMBOLS.items()):
                if symbol == default_settings['symbol']:
                    symbol_combo.setCurrentIndex(i)
                    break

            # Reset size
            size_spin = self.table.cellWidget(row, 2)
            size_spin.setValue(default_settings['size'])

            # Reset color
            color_btn = self.table.cellWidget(row, 3)
            color = default_settings['color']
            color_btn.setStyleSheet(f"background-color: {color}; border: 1px solid #ccc;")

    def _choose_color(self, row, button):
        """Open color picker dialog"""
        # Get current color from button
        current_style = button.styleSheet()
        current_color = QColor(current_style.split('background-color: ')[1].split(';')[0])

        # Create color dialog with English locale for non-Thai numerals
        color_dialog = QColorDialog(current_color, self)
        color_dialog.setWindowTitle("Choose Color")
        color_dialog.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))

        if color_dialog.exec():
            color = color_dialog.currentColor()
            if color.isValid():
                # Update button color
                button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #ccc;")

    def get_settings(self):
        """
        Get all settings from the table

        Returns:
            Dict: {bh_name: {symbol, size, color}}
        """
        settings = {}

        for row, bh_name in enumerate(self.bh_names):
            # Get symbol
            symbol_combo = self.table.cellWidget(row, 1)
            symbol_name = symbol_combo.currentText()
            symbol = self.MARKER_SYMBOLS[symbol_name]

            # Get size
            size_spin = self.table.cellWidget(row, 2)
            size = size_spin.value()

            # Get color
            color_btn = self.table.cellWidget(row, 3)
            color_style = color_btn.styleSheet()
            color = color_style.split('background-color: ')[1].split(';')[0]

            settings[bh_name] = {
                'symbol': symbol,
                'size': size,
                'color': color
            }

        return settings
