"""
Module 1: SPT Plot
First module for geotechnical analysis - SPT data input and visualization

Features:
- Top bar: [Save As], [Import CSV], [Clear Data], [Export PDF], [Label Size]
- Axis settings: Select BH, Xmin, Xmax, Ymin, Ymax (individual per BH)
- Left frame: Grid table layout (Excel-like) with BH columns
  - Each BH has [SPT, Class] sub-columns
  - Depth as rows
  - One click to edit (no double-click needed)
- Right frame: Preview window with multiple graphs (one per BH)
  - Scatter plot: SPT (x-axis) vs Depth (y-axis)
  - Labels: "N=[SPT-value], [Class]"
  - Lines connecting scatters (except invalid data)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QDoubleSpinBox, QComboBox, QFileDialog, QMessageBox, QSplitter,
    QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, QLocale
from PyQt6.QtGui import QFont, QColor, QKeyEvent, QKeySequence
import json
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class CustomTableWidget(QTableWidget):
    """Custom table widget with Enter key navigation and paste support"""

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events - Enter moves down, Ctrl+V pastes"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Move to next row (down) when Enter is pressed
            current = self.currentRow()
            current_col = self.currentColumn()
            if current < self.rowCount() - 1:
                self.setCurrentCell(current + 1, current_col)
            event.accept()
        elif event.matches(QKeySequence.StandardKey.Paste):
            # Handle paste from clipboard
            self._paste_from_clipboard()
            event.accept()
        else:
            # Default behavior for other keys
            super().keyPressEvent(event)

    def _paste_from_clipboard(self):
        """Paste data from clipboard (Excel format)"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if not text:
            return

        # Get current selection
        current_row = self.currentRow()
        current_col = self.currentColumn()

        if current_row < 0 or current_col < 0:
            return

        # Parse clipboard data (tab-separated for columns, newline for rows)
        rows = text.strip().split('\n')

        for row_idx, row_data in enumerate(rows):
            target_row = current_row + row_idx
            if target_row >= self.rowCount():
                break

            # Split by tab for columns
            cells = row_data.split('\t')

            for col_idx, cell_value in enumerate(cells):
                target_col = current_col + col_idx
                if target_col >= self.columnCount():
                    break

                # Check if cell is editable
                item = self.item(target_row, target_col)
                if item and not (item.flags() & Qt.ItemFlag.ItemIsEditable):
                    continue

                # Set cell value (handle empty cells)
                if not item:
                    item = QTableWidgetItem(cell_value.strip())
                    self.setItem(target_row, target_col, item)
                else:
                    item.setText(cell_value.strip())


class Module1SPTPlot(QWidget):
    """
    Module 1: SPT Plot - Data input and visualization
    Multiple graphs (one per borehole)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Data storage
        self.borehole_data = {}  # {BH_name: {depth: {'spt': value, 'class': value}}}
        self.bh_names = []
        self.depths = []

        # BH settings (Surface Elevation, Water Level, Pile Top, Pile Tip for each BH)
        self.bh_settings = {}  # {BH_name: {'surface_elev': 100.0, 'water_level': 0.0, 'pile_top': 100.0, 'pile_tip': 85.0}}

        # Axis limits for each borehole
        self.axis_limits = {}  # {BH_name: {'xmin': 0, 'xmax': 100, 'ymin': 0, 'ymax': 30}}

        self.label_size = 8
        self.selected_bh = None  # Currently selected BH for axis adjustment

        # Vertical reference line settings
        self.vline_enabled = False  # Enable/disable vertical line
        self.vline_x_value = 30.0  # X position of vertical line (default 30)

        # Setup UI
        self._setup_ui()

        # Initialize with default data
        self._initialize_default_data()

    def _setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Compact top bar (everything in one row)
        top_bar = self._create_top_bar()
        main_layout.addLayout(top_bar)

        # Main content: Left (table) + Right (plots)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Data table in scroll area
        table_scroll = QScrollArea()
        table_scroll.setWidgetResizable(True)
        table_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.table_widget = self._create_table_widget()
        table_scroll.setWidget(self.table_widget)
        splitter.addWidget(table_scroll)

        # Right: Multiple plots (fixed, no horizontal scroll to prevent overflow)
        plot_scroll = QScrollArea()
        plot_scroll.setWidgetResizable(True)
        plot_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        plot_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.plot_container = self._create_plot_container()
        plot_scroll.setWidget(self.plot_container)
        splitter.addWidget(plot_scroll)

        # Set initial sizes (40% table, 60% plot)
        splitter.setSizes([400, 600])

        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

    def _create_top_bar(self):
        """Create compact top bar with everything in one row"""
        layout = QHBoxLayout()
        layout.setSpacing(8)

        # Title - compact
        title = QLabel("Module 1")
        title.setFont(QFont("SF Pro Display", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("color: #D1D1D6;")
        layout.addWidget(separator)

        # Axis Settings
        layout.addWidget(QLabel("Axis:"))
        self.bh_selector = QComboBox()
        self.bh_selector.setFont(QFont("SF Pro Display", 14))
        self.bh_selector.setMaximumWidth(80)
        self.bh_selector.currentTextChanged.connect(self.on_bh_selected)
        layout.addWidget(self.bh_selector)

        # X limits
        layout.addWidget(QLabel("X:"))
        self.xmin_spin = QDoubleSpinBox()
        self.xmin_spin.setFont(QFont("SF Pro Display", 14))
        self.xmin_spin.setMaximumWidth(80)
        self.xmin_spin.setRange(-1000, 1000)
        self.xmin_spin.setValue(0)
        self.xmin_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)  # Remove increment/decrement buttons
        self.xmin_spin.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))  # Use standard number format
        self.xmin_spin.valueChanged.connect(self.update_axis_limits)
        layout.addWidget(self.xmin_spin)

        layout.addWidget(QLabel("-"))

        self.xmax_spin = QDoubleSpinBox()
        self.xmax_spin.setFont(QFont("SF Pro Display", 14))
        self.xmax_spin.setMaximumWidth(80)
        self.xmax_spin.setRange(-1000, 1000)
        self.xmax_spin.setValue(60)
        self.xmax_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)  # Remove increment/decrement buttons
        self.xmax_spin.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))  # Use standard number format
        self.xmax_spin.valueChanged.connect(self.update_axis_limits)
        layout.addWidget(self.xmax_spin)

        # Y limits
        layout.addWidget(QLabel("Y:"))
        self.ymin_spin = QDoubleSpinBox()
        self.ymin_spin.setFont(QFont("SF Pro Display", 14))
        self.ymin_spin.setMaximumWidth(80)
        self.ymin_spin.setRange(-1000, 1000)
        self.ymin_spin.setValue(100)
        self.ymin_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)  # Remove increment/decrement buttons
        self.ymin_spin.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))  # Use standard number format
        self.ymin_spin.valueChanged.connect(self.update_axis_limits)
        layout.addWidget(self.ymin_spin)

        layout.addWidget(QLabel("-"))

        self.ymax_spin = QDoubleSpinBox()
        self.ymax_spin.setFont(QFont("SF Pro Display", 14))
        self.ymax_spin.setMaximumWidth(80)
        self.ymax_spin.setRange(-1000, 1000)
        self.ymax_spin.setValue(70)  # Changed default from 30 to 100
        self.ymax_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)  # Remove increment/decrement buttons
        self.ymax_spin.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))  # Use standard number format
        self.ymax_spin.valueChanged.connect(self.update_axis_limits)
        layout.addWidget(self.ymax_spin)

        # Separator
        separator2 = QLabel("|")
        separator2.setStyleSheet("color: #D1D1D6;")
        layout.addWidget(separator2)

        # Y-axis type dropdown (Depth or Elevation)
        layout.addWidget(QLabel("Y-axis:"))
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.setFont(QFont("SF Pro Display", 14))
        self.y_axis_combo.setMaximumWidth(100)
        self.y_axis_combo.addItems(["Elevation", "Depth"])
        self.y_axis_combo.setCurrentText("Elevation")  # Default to Elevation
        self.y_axis_combo.currentTextChanged.connect(self.update_plots)
        layout.addWidget(self.y_axis_combo)

        # Separator
        separator_pile = QLabel("|")
        separator_pile.setStyleSheet("color: #D1D1D6;")
        layout.addWidget(separator_pile)

        # Pile Top input
        layout.addWidget(QLabel("Pile Top:"))
        self.pile_top_spin = QDoubleSpinBox()
        self.pile_top_spin.setFont(QFont("SF Pro Display", 14))
        self.pile_top_spin.setMaximumWidth(90)
        self.pile_top_spin.setRange(-1000, 1000)
        self.pile_top_spin.setValue(100.0)
        self.pile_top_spin.setDecimals(2)
        self.pile_top_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.pile_top_spin.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.pile_top_spin.valueChanged.connect(self.on_pile_settings_changed)
        layout.addWidget(self.pile_top_spin)

        # Pile Tip input
        layout.addWidget(QLabel("Pile Tip:"))
        self.pile_tip_spin = QDoubleSpinBox()
        self.pile_tip_spin.setFont(QFont("SF Pro Display", 14))
        self.pile_tip_spin.setMaximumWidth(90)
        self.pile_tip_spin.setRange(-1000, 1000)
        self.pile_tip_spin.setValue(85.0)
        self.pile_tip_spin.setDecimals(2)
        self.pile_tip_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.pile_tip_spin.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.pile_tip_spin.valueChanged.connect(self.on_pile_settings_changed)
        layout.addWidget(self.pile_tip_spin)

        # Separator
        separator_vline = QLabel("|")
        separator_vline.setStyleSheet("color: #D1D1D6;")
        layout.addWidget(separator_vline)

        # Vertical line checkbox
        from PyQt6.QtWidgets import QCheckBox
        self.vline_checkbox = QCheckBox("V-Line")
        self.vline_checkbox.setFont(QFont("SF Pro Display", 12))
        self.vline_checkbox.setChecked(False)
        self.vline_checkbox.stateChanged.connect(self.update_plots)
        layout.addWidget(self.vline_checkbox)

        # Vertical line X value
        self.vline_x_spin = QDoubleSpinBox()
        self.vline_x_spin.setFont(QFont("SF Pro Display", 14))
        self.vline_x_spin.setMaximumWidth(70)
        self.vline_x_spin.setRange(0, 1000)
        self.vline_x_spin.setValue(30.0)
        self.vline_x_spin.setDecimals(1)
        self.vline_x_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.vline_x_spin.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.vline_x_spin.valueChanged.connect(self.update_plots)
        layout.addWidget(self.vline_x_spin)

        # Label size
        layout.addWidget(QLabel("Label:"))
        self.label_size_spin = QSpinBox()
        self.label_size_spin.setFont(QFont("SF Pro Display", 14))
        self.label_size_spin.setMaximumWidth(100)
        self.label_size_spin.setRange(6, 16)
        self.label_size_spin.setValue(self.label_size)
        self.label_size_spin.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.label_size_spin.valueChanged.connect(self.update_label_size)
        layout.addWidget(self.label_size_spin)

        layout.addStretch()

        # Add/Remove BH buttons - compact
        btn_add_bh = QPushButton("+ BH")
        btn_add_bh.setFont(QFont("SF Pro Display", 14))
        btn_add_bh.setMaximumWidth(60)
        btn_add_bh.setToolTip("Add borehole")
        btn_add_bh.clicked.connect(self.add_borehole)
        layout.addWidget(btn_add_bh)

        btn_remove_bh = QPushButton("- BH")
        btn_remove_bh.setFont(QFont("SF Pro Display", 14))
        btn_remove_bh.setMaximumWidth(60)
        btn_remove_bh.setObjectName("secondary")
        btn_remove_bh.setToolTip("Remove borehole")
        btn_remove_bh.clicked.connect(self.remove_borehole)
        layout.addWidget(btn_remove_bh)

        # Separator
        separator3 = QLabel("|")
        separator3.setStyleSheet("color: #D1D1D6;")
        layout.addWidget(separator3)

        # Add/Remove Row buttons
        btn_add_row = QPushButton("+ Row")
        btn_add_row.setFont(QFont("SF Pro Display", 14))
        btn_add_row.setMaximumWidth(70)
        btn_add_row.setToolTip("Add depth row")
        btn_add_row.clicked.connect(self.add_depth_row)
        layout.addWidget(btn_add_row)

        btn_remove_row = QPushButton("- Row")
        btn_remove_row.setFont(QFont("SF Pro Display", 14))
        btn_remove_row.setMaximumWidth(70)
        btn_remove_row.setObjectName("secondary")
        btn_remove_row.setToolTip("Remove last depth row")
        btn_remove_row.clicked.connect(self.remove_depth_row)
        layout.addWidget(btn_remove_row)

        # Separator
        separator4 = QLabel("|")
        separator4.setStyleSheet("color: #D1D1D6;")
        layout.addWidget(separator4)

        # Action buttons - compact
        btn_save = QPushButton("Save")
        btn_save.setFont(QFont("SF Pro Display", 13))
        btn_save.setMaximumWidth(70)
        btn_save.setToolTip("Save data")
        btn_save.clicked.connect(self.save_data)
        layout.addWidget(btn_save)

        btn_clear = QPushButton("Clear")
        btn_clear.setFont(QFont("SF Pro Display", 13))
        btn_clear.setMaximumWidth(70)
        btn_clear.setObjectName("secondary")
        btn_clear.setToolTip("Clear all data")
        btn_clear.clicked.connect(self.clear_data)
        layout.addWidget(btn_clear)

        btn_export_png = QPushButton("PNG")
        btn_export_png.setFont(QFont("SF Pro Display", 13))
        btn_export_png.setMaximumWidth(70)
        btn_export_png.setToolTip("Export preview to PNG")
        btn_export_png.clicked.connect(self.export_preview_png)
        layout.addWidget(btn_export_png)

        btn_export_pdf = QPushButton("PDF")
        btn_export_pdf.setFont(QFont("SF Pro Display", 13))
        btn_export_pdf.setMaximumWidth(70)
        btn_export_pdf.setToolTip("Export preview to PDF")
        btn_export_pdf.clicked.connect(self.export_preview_pdf)
        layout.addWidget(btn_export_pdf)

        return layout

    def _create_table_widget(self):
        """Create table widget for data input with single-click editing"""
        table = CustomTableWidget()
        table.setColumnCount(0)
        table.setRowCount(0)

        # Enable single-click editing (CurrentChanged trigger)
        table.setEditTriggers(
            QTableWidget.EditTrigger.CurrentChanged |  # Single click
            QTableWidget.EditTrigger.SelectedClicked |  # Click on selected
            QTableWidget.EditTrigger.EditKeyPressed |   # Press key to edit
            QTableWidget.EditTrigger.AnyKeyPressed      # Any key starts edit
        )

        # Remove selection highlight (no blue cover on selected cells)
        table.setStyleSheet("""
            QTableWidget::item:hover {
                background-color: rgba(0, 122, 255, 0.06);
                color: black;
            }
            QTableWidget::item:selected {
                background-color: transparent;
                color: black;
            }
            QTableWidget::item:focus {
                background-color: transparent;
                border: 1px solid #007AFF;
            }
            QTableWidget QLineEdit {
                border: none;
                padding: 0px 2px;
                background-color: white;
                selection-background-color: rgba(0, 122, 255, 0.15);
                selection-color: black;
            }
        """)

        # Connect cell changed signal
        table.cellChanged.connect(self.on_cell_changed)

        return table

    def _create_plot_container(self):
        """Create container for multiple plots (horizontal layout, no horizontal scroll)"""
        # Container widget for plots - no scroll area to prevent overflow
        self.plot_widget = QWidget()
        self.plot_layout = QHBoxLayout()
        self.plot_layout.setSpacing(8)
        self.plot_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_widget.setLayout(self.plot_layout)

        return self.plot_widget

    def _initialize_default_data(self):
        """Initialize with default boreholes and depths"""
        # Default: 3 boreholes, specific depth values
        self.bh_names = ["BH-1", "BH-2", "BH-3"]
        self.depths = [
            1.45, 1.95, 2.45,2.95, 3.45, 4.95, 6.45, 7.95, 9.45, 10.95, 12.45,
            13.95, 15.45, 16.95, 18.45, 19.95, 21.45, 22.95, 24.45, 25.95,
            27.45, 28.95, 30.45, 31.95
        ]

        # Initialize empty data structure and default axis limits
        for bh in self.bh_names:
            self.borehole_data[bh] = {}
            self.axis_limits[bh] = {'xmin': 0, 'xmax': 60, 'ymin': 100, 'ymax': 70}
            self.bh_settings[bh] = {
                'surface_elev': 100.0,
                'water_level': 0.0,
                'pile_top': 100.0,
                'pile_tip': 85.0
            }

            for depth in self.depths:
                self.borehole_data[bh][depth] = {'spt': None, 'class': ''}

        # Initialize "All BH" axis limits (for applying to all boreholes at once)
        self.axis_limits["All BH"] = {'xmin': 0, 'xmax': 60, 'ymin': 100, 'ymax': 70}

        # Sample data for BH-1
        sample_data = {
            1.95: {'spt': 8, 'class': 'CH'},
            3.45: {'spt': 12, 'class': 'CL'},
            4.95: {'spt': 15, 'class': 'SM'},
            6.45: {'spt': 20, 'class': 'SC'},
            7.95: {'spt': 25, 'class': 'SM'},
        }
        for depth, data in sample_data.items():
            self.borehole_data["BH-1"][depth] = data

        # Update BH selector with "All BH" as first option
        self.bh_selector.clear()
        self.bh_selector.addItem("All BH")
        self.bh_selector.addItems(self.bh_names)
        self.selected_bh = "All BH"  # Default to All BH

        # Update table and plots
        self._update_table()
        self.update_plots()

    def _update_table(self):
        """Update table widget with current data"""
        # Disconnect signal temporarily
        self.table_widget.cellChanged.disconnect(self.on_cell_changed)

        # Set table dimensions: +4 rows (1 for BH names, 1 for sub-headers, 2 for Surface/Water)
        num_rows = len(self.depths) + 4  # +4 for header rows
        num_cols = 2 + len(self.bh_names) * 2  # Depth + Elevation + (SPT, Class) for each BH

        self.table_widget.setRowCount(num_rows)
        self.table_widget.setColumnCount(num_cols)

        # Hide default header - we'll use row 0 for BH names
        self.table_widget.horizontalHeader().setVisible(False)

        # Row 0: BH Names (merged cells) - this becomes the top header
        bh_row_label = QTableWidgetItem("BH-number")
        bh_row_label.setFlags(bh_row_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
        bh_row_label.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        bh_row_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        bh_row_label.setBackground(Qt.GlobalColor.white)
        self.table_widget.setItem(0, 0, bh_row_label)
        self.table_widget.setSpan(0, 0, 1, 2)  # Merge Depth and Elevation columns

        for i, bh in enumerate(self.bh_names):
            bh_item = QTableWidgetItem(bh)
            # Make BH name editable
            bh_item.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
            bh_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            bh_item.setBackground(QColor("#FFFFFF"))  # Light blue background to indicate editable
            self.table_widget.setItem(0, 2 + i * 2, bh_item)
            # Merge 2 columns for BH name
            self.table_widget.setSpan(0, 2 + i * 2, 1, 2)

        # Row 1: Sub-headers (Depth, Elevation, SPT, Class for each BH)
        depth_label = QTableWidgetItem("Depth")
        depth_label.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        depth_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        depth_label.setBackground(Qt.GlobalColor.white)
        self.table_widget.setItem(1, 0, depth_label)

        elev_label = QTableWidgetItem("Elev")
        elev_label.setFlags(elev_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
        elev_label.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        elev_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        elev_label.setBackground(Qt.GlobalColor.white)
        self.table_widget.setItem(1, 1, elev_label)

        for i, bh in enumerate(self.bh_names):
            # SPT sub-header
            spt_label = QTableWidgetItem("SPT")
            spt_label.setFlags(spt_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
            spt_label.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
            spt_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            spt_label.setBackground(Qt.GlobalColor.white)
            self.table_widget.setItem(1, 2 + i * 2, spt_label)

            # Class sub-header
            class_label = QTableWidgetItem("Class")
            class_label.setFlags(class_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
            class_label.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
            class_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            class_label.setBackground(Qt.GlobalColor.white)
            self.table_widget.setItem(1, 2 + i * 2 + 1, class_label)

        # Row 2: Surface Elevation
        surf_label = QTableWidgetItem("GL.")
        surf_label.setFlags(surf_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
        surf_label.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        surf_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_widget.setItem(2, 0, surf_label)
        self.table_widget.setSpan(2, 0, 1, 2)  # Merge Depth and Elevation columns

        for col, bh in enumerate(self.bh_names):
            settings = self.bh_settings.get(bh, {'surface_elev': 100.0, 'water_level': 0.0})
            surf_item = QTableWidgetItem(f"{settings['surface_elev']:.2f}")
            surf_item.setFont(QFont("SF Pro Display", 10))
            surf_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(2, 2 + col * 2, surf_item)
            # Merge cells for surface elev (span 2 columns)
            self.table_widget.setSpan(2, 2 + col * 2, 1, 2)

        # Row 3: Water Level
        water_label = QTableWidgetItem("WL.")
        water_label.setFlags(water_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
        water_label.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        water_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table_widget.setItem(3, 0, water_label)
        self.table_widget.setSpan(3, 0, 1, 2)  # Merge Depth and Elevation columns

        for col, bh in enumerate(self.bh_names):
            settings = self.bh_settings.get(bh, {'surface_elev': 100.0, 'water_level': 0.0})
            water_item = QTableWidgetItem(f"{settings['water_level']:.2f}")
            water_item.setFont(QFont("SF Pro Display", 9))
            water_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(3, 2 + col * 2, water_item)
            # Merge cells for water level (span 2 columns)
            self.table_widget.setSpan(3, 2 + col * 2, 1, 2)

        # Fill depth and data rows (starting from row 4)
        for row_idx, depth in enumerate(self.depths):
            actual_row = row_idx + 4  # Offset by 4 for header rows

            # Depth column (now editable)
            depth_item = QTableWidgetItem(f"{depth:.2f}")
            depth_item.setFont(QFont("SF Pro Display", 9))
            depth_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(actual_row, 0, depth_item)

            # Elevation column (calculated from first BH's surface elevation - depth)
            # Use first BH's surface elevation as reference
            if self.bh_names:
                first_bh = self.bh_names[0]
                settings = self.bh_settings.get(first_bh, {'surface_elev': 100.0, 'water_level': 0.0})
                elevation = settings['surface_elev'] - depth
                elev_item = QTableWidgetItem(f"{elevation:.2f}")
                elev_item.setFlags(elev_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
                elev_item.setFont(QFont("SF Pro Display", 9))
                elev_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elev_item.setForeground(Qt.GlobalColor.darkGray)  # Gray color for calculated value
                self.table_widget.setItem(actual_row, 1, elev_item)

            # BH data columns
            for col, bh in enumerate(self.bh_names):
                data = self.borehole_data[bh].get(depth, {'spt': None, 'class': ''})

                # SPT column
                spt_value = str(data['spt']) if data['spt'] is not None else ''
                spt_item = QTableWidgetItem(spt_value)
                spt_item.setFont(QFont("SF Pro Display", 9))
                spt_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(actual_row, 2 + col * 2, spt_item)

                # Class column
                class_item = QTableWidgetItem(data['class'])
                class_item.setFont(QFont("SF Pro Display", 9))
                class_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(actual_row, 2 + col * 2 + 1, class_item)

        # Adjust column widths - all columns same width
        column_width = 50  # Equal width for all columns

        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table_widget.setColumnWidth(0, column_width)
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.table_widget.setColumnWidth(1, column_width)

        for i in range(len(self.bh_names)):
            self.table_widget.setColumnWidth(2 + i * 2, column_width)
            self.table_widget.setColumnWidth(2 + i * 2 + 1, column_width)

        # Reconnect signal
        self.table_widget.cellChanged.connect(self.on_cell_changed)

    def on_cell_changed(self, row, col):
        """Handle cell value changes"""
        # Handle BH names row (row 0) - editable
        if row == 0:
            if col < 2:  # Label columns
                return
            bh_index = (col - 2) // 2
            if bh_index >= len(self.bh_names):
                return
            old_name = self.bh_names[bh_index]
            item = self.table_widget.item(row, col)
            if item is None:
                return
            new_name = item.text().strip()

            # Validate new name is not empty and not duplicate
            if not new_name:
                item.setText(old_name)
                return
            if new_name != old_name and new_name in self.bh_names:
                QMessageBox.warning(self, "Duplicate Name", f"Borehole name '{new_name}' already exists!")
                item.setText(old_name)
                return

            # Update bh_names list
            self.bh_names[bh_index] = new_name

            # Rename keys in all dictionaries
            if old_name in self.borehole_data:
                self.borehole_data[new_name] = self.borehole_data.pop(old_name)
            if old_name in self.axis_limits:
                self.axis_limits[new_name] = self.axis_limits.pop(old_name)
            if old_name in self.bh_settings:
                self.bh_settings[new_name] = self.bh_settings.pop(old_name)

            # Update selector dropdown
            current_selection = self.bh_selector.currentText()
            self.bh_selector.blockSignals(True)
            self.bh_selector.clear()
            self.bh_selector.addItem("All BH")
            self.bh_selector.addItems(self.bh_names)
            if current_selection == old_name:
                self.bh_selector.setCurrentText(new_name)
                self.selected_bh = new_name
            else:
                self.bh_selector.setCurrentText(current_selection)
            self.bh_selector.blockSignals(False)

            # Update axis controls if the renamed BH is selected
            if self.selected_bh == new_name:
                self._update_axis_controls()

            # Refresh plots
            self.update_plots()
            return

        # Handle sub-headers row (row 1) - read only
        if row == 1:
            return

        # Handle Surface Elevation row (row 2)
        if row == 2:
            if col < 2:  # Depth/Elev label columns
                return
            bh_index = (col - 2) // 2
            if bh_index >= len(self.bh_names):
                return
            bh_name = self.bh_names[bh_index]
            item = self.table_widget.item(row, col)
            if item is None:
                return
            try:
                value = float(item.text().strip())
                self.bh_settings[bh_name]['surface_elev'] = value
                # Update all elevation values in the table
                self._update_table()
            except ValueError:
                # Reset to previous value
                self.bh_settings[bh_name]['surface_elev'] = 100.0
                item.setText("100.00")
            return

        # Handle Water Level row (row 3)
        if row == 3:
            if col < 2:  # Depth/Elev label columns
                return
            bh_index = (col - 2) // 2
            if bh_index >= len(self.bh_names):
                return
            bh_name = self.bh_names[bh_index]
            item = self.table_widget.item(row, col)
            if item is None:
                return
            try:
                value = float(item.text().strip())
                self.bh_settings[bh_name]['water_level'] = value
            except ValueError:
                # Reset to previous value
                self.bh_settings[bh_name]['water_level'] = 0.0
                item.setText("0.00")
            return

        # Handle data rows (row >= 4)
        if row < 4:
            return

        depth_index = row - 4  # Account for 4 header rows
        if depth_index >= len(self.depths):
            return

        # Handle Depth column editing (col == 0)
        if col == 0:
            item = self.table_widget.item(row, col)
            if item is None:
                return
            try:
                new_depth = float(item.text().strip())
                old_depth = self.depths[depth_index]

                # Update depth in list
                self.depths[depth_index] = new_depth

                # Update data for all boreholes (move data from old depth to new depth)
                for bh_name in self.bh_names:
                    if old_depth in self.borehole_data[bh_name]:
                        self.borehole_data[bh_name][new_depth] = self.borehole_data[bh_name].pop(old_depth)
                    else:
                        self.borehole_data[bh_name][new_depth] = {'spt': None, 'class': ''}

                # Update elevation column
                self._update_table()
            except ValueError:
                # Reset to previous value
                item.setText(f"{self.depths[depth_index]:.1f}")
            return

        # Handle Elevation column (col == 1) - read only
        if col == 1:
            return

        depth = self.depths[depth_index]
        bh_index = (col - 2) // 2
        is_spt = (col - 2) % 2 == 0

        if bh_index >= len(self.bh_names):
            return

        bh_name = self.bh_names[bh_index]
        item = self.table_widget.item(row, col)

        if item is None:
            return

        value = item.text().strip()

        if is_spt:
            # Update SPT value
            try:
                self.borehole_data[bh_name][depth]['spt'] = float(value) if value else None
            except ValueError:
                self.borehole_data[bh_name][depth]['spt'] = None
                item.setText('')
        else:
            # Update Class value
            self.borehole_data[bh_name][depth]['class'] = value

        # Update plots
        self.update_plots()

    def on_bh_selected(self, bh_name):
        """Handle BH selection change in combo box"""
        if not bh_name or bh_name not in self.axis_limits:
            return

        self.selected_bh = bh_name

        # Update spin boxes with selected BH's axis limits
        limits = self.axis_limits[bh_name]

        # Temporarily disconnect to avoid triggering updates
        self.xmin_spin.valueChanged.disconnect(self.update_axis_limits)
        self.xmax_spin.valueChanged.disconnect(self.update_axis_limits)
        self.ymin_spin.valueChanged.disconnect(self.update_axis_limits)
        self.ymax_spin.valueChanged.disconnect(self.update_axis_limits)

        self.xmin_spin.setValue(limits['xmin'])
        self.xmax_spin.setValue(limits['xmax'])
        self.ymin_spin.setValue(limits['ymin'])
        self.ymax_spin.setValue(limits['ymax'])

        # Reconnect
        self.xmin_spin.valueChanged.connect(self.update_axis_limits)
        self.xmax_spin.valueChanged.connect(self.update_axis_limits)
        self.ymin_spin.valueChanged.connect(self.update_axis_limits)
        self.ymax_spin.valueChanged.connect(self.update_axis_limits)

        # Load pile settings for selected BH (or first BH if "All BH")
        if bh_name == "All BH" and self.bh_names:
            # Use first BH settings for display when "All BH" is selected
            bh_settings = self.bh_settings.get(self.bh_names[0], {})
        else:
            bh_settings = self.bh_settings.get(bh_name, {})

        pile_top = bh_settings.get('pile_top', 100.0)
        pile_tip = bh_settings.get('pile_tip', 85.0)

        # Temporarily disconnect to avoid triggering updates
        self.pile_top_spin.valueChanged.disconnect(self.on_pile_settings_changed)
        self.pile_tip_spin.valueChanged.disconnect(self.on_pile_settings_changed)

        self.pile_top_spin.setValue(pile_top)
        self.pile_tip_spin.setValue(pile_tip)

        # Reconnect
        self.pile_top_spin.valueChanged.connect(self.on_pile_settings_changed)
        self.pile_tip_spin.valueChanged.connect(self.on_pile_settings_changed)

    def on_pile_settings_changed(self):
        """Handle pile top/tip changes and save to current BH settings"""
        pile_top = self.pile_top_spin.value()
        pile_tip = self.pile_tip_spin.value()

        # If "All BH" is selected, apply to all boreholes
        if self.selected_bh == "All BH":
            for bh_name in self.bh_names:
                if bh_name not in self.bh_settings:
                    self.bh_settings[bh_name] = {}
                self.bh_settings[bh_name]['pile_top'] = pile_top
                self.bh_settings[bh_name]['pile_tip'] = pile_tip
        elif self.selected_bh:
            # Save to bh_settings for current BH
            if self.selected_bh not in self.bh_settings:
                self.bh_settings[self.selected_bh] = {}
            self.bh_settings[self.selected_bh]['pile_top'] = pile_top
            self.bh_settings[self.selected_bh]['pile_tip'] = pile_tip
        else:
            # No BH selected, skip
            return

        # Update plots
        self.update_plots()

    def update_axis_limits(self):
        """Update axis limits for selected BH or all BHs"""
        if not self.selected_bh:
            return

        new_limits = {
            'xmin': self.xmin_spin.value(),
            'xmax': self.xmax_spin.value(),
            'ymin': self.ymin_spin.value(),
            'ymax': self.ymax_spin.value()
        }

        if self.selected_bh == "All BH":
            # Update limits for all boreholes
            self.axis_limits["All BH"] = new_limits
            for bh in self.bh_names:
                self.axis_limits[bh] = new_limits.copy()
        else:
            # Update limits for specific borehole
            self.axis_limits[self.selected_bh] = new_limits

        self.update_plots()

    def update_label_size(self, value):
        """Update label size"""
        self.label_size = value
        self.update_plots()

    def update_plots(self):
        """Update all plots (one per borehole) - horizontal layout"""
        # Clear existing plots
        while self.plot_layout.count():
            child = self.plot_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Create a plot for each borehole (side by side)
        for bh in self.bh_names:
            plot_widget = self._create_single_plot(bh)
            self.plot_layout.addWidget(plot_widget, stretch=1)  # Equal stretch for all plots

    def _create_single_plot(self, bh_name):
        """Create a single plot for one borehole"""
        # Create figure and canvas (adjusted size for horizontal layout)
        figure = Figure(figsize=(5, 6), dpi=80)  # Smaller for better fit
        canvas = FigureCanvas(figure)
        canvas.setMinimumWidth(200)  # Smaller minimum width
        # No maximum width - allow stretching to fill available space

        # Apply Apple-style theme
        self._apply_plot_style()

        # Create axes
        ax = figure.add_subplot(111)

        # Get Y-axis mode (Depth or Elevation)
        y_axis_mode = self.y_axis_combo.currentText()
        use_elevation = (y_axis_mode == "Elevation")

        # Get surface elevation for this borehole
        settings = self.bh_settings.get(bh_name, {'surface_elev': 100.0, 'water_level': 0.0})
        surface_elev = settings['surface_elev']

        # Get data for this borehole
        spt_values = []
        y_values = []
        class_values = []
        depth_indices = []  # Track which depths have data

        for idx, depth in enumerate(sorted(self.depths)):
            data = self.borehole_data[bh_name].get(depth, {'spt': None, 'class': ''})
            if data['spt'] is not None:
                spt_values.append(data['spt'])
                # Calculate Y value based on mode
                if use_elevation:
                    y_values.append(surface_elev - depth)  # Elevation = Surface - Depth
                else:
                    y_values.append(depth)
                class_values.append(data['class'])
                depth_indices.append(idx)  # Track the depth index

        if spt_values:
            # Color
            color = "#0004FF"  # Apple Blue

            # Plot scatter (solid color, no transparency)
            ax.scatter(spt_values, y_values, c=color, s=80, alpha=1.0, zorder=3)

            # Plot connecting lines ONLY between consecutive depths (no gaps)
            # Group consecutive depth indices together
            for i in range(len(spt_values) - 1):
                # Only draw line if the next data point is at the consecutive depth index
                if depth_indices[i+1] - depth_indices[i] == 1:
                    ax.plot([spt_values[i], spt_values[i+1]],
                           [y_values[i], y_values[i+1]],
                           c=color, alpha=1.0, linewidth=1.5, zorder=2)

            # Add labels
            for spt, y_val, cls in zip(spt_values, y_values, class_values):
                label = f"N={int(spt)}"
                if cls:
                    label += f", {cls}"
                ax.annotate(label, (spt, y_val), textcoords="offset points",
                           xytext=(5, 0), ha='left', fontsize=self.label_size,
                           color='#1C1C1E', alpha=0.8)

        # Get pile settings from bh_settings (per-borehole)
        bh_settings = self.bh_settings.get(bh_name, {})
        pile_top = bh_settings.get('pile_top', 100.0)
        pile_tip = bh_settings.get('pile_tip', 85.0)

        # Get axis limits for this borehole to calculate pile position
        limits = self.axis_limits.get(bh_name, {'xmin': 0, 'xmax': 60, 'ymin': 100, 'ymax': 70})

        # Draw vertical reference line if enabled
        if self.vline_checkbox.isChecked():
            vline_x = self.vline_x_spin.value()
            if limits['xmin'] <= vline_x <= limits['xmax']:
                ax.axvline(x=vline_x, color='red', linewidth=1.0, linestyle='-',
                          alpha=0.5, zorder=1)

        # Draw pile visualization (before axis inversion to ensure correct orientation)
        if pile_top > pile_tip:  # Valid pile configuration
            # Draw horizontal line at Pile Top (Ground level) - Green with label
            ax.axhline(y=pile_top, color="#0E7224", linewidth=1.5, linestyle='-',
                      alpha=0.7, zorder=1, label=f'Pile Top ({pile_top:.1f}m)')

            # Draw horizontal line at Pile Tip - Red
            ax.axhline(y=pile_tip, color='#FF0000', linewidth=1.5, linestyle='-',
                      alpha=0.7, zorder=1, label=f'Pile Tip ({pile_tip:.1f}m)')

            # Draw vertical pile line (gray, thick)
            # Position at center of X-axis based on axis limits (not auto xlim)
            pile_x_position = limits['xmin'] + (limits['xmax'] - limits['xmin']) * 0.5
            ax.plot([pile_x_position, pile_x_position], [pile_top, pile_tip],
                   color="#818181", linewidth=8, linestyle='-',
                   alpha=0.6, zorder=1)

            # Calculate pile length
            pile_length = pile_top - pile_tip

            # Add pile length label with box
            pile_mid_y = (pile_top + pile_tip) / 2
            ax.text(pile_x_position, pile_mid_y, f'{pile_length:.1f}m',
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                            edgecolor='black', linewidth=1.5),
                   zorder=4)

        # Invert y-axis only if using Depth mode (depth increases downward)
        # For Elevation mode, higher values should be at top (natural orientation)
        if not use_elevation:
            ax.invert_yaxis()

        # Set axis labels
        ax.set_xlabel('SPT N-value (blow/ft)', fontsize=11, fontweight='bold', color='black')
        y_label = 'Elevation (m)' if use_elevation else 'Depth (m)'
        ax.set_ylabel(y_label, fontsize=11, fontweight='bold', color='black')

        # Add surface elevation to title (Pile Top moved to legend)
        title_suffix = 'Elevation' if use_elevation else 'Depth'
        title_text = f'{bh_name}\nSurface: {surface_elev:.2f} m'
        ax.set_title(title_text, fontsize=13, fontweight='bold', pad=15, color='black')

        # Set axis limits for this specific BH (limits already fetched above)
        ax.set_xlim(limits['xmin'], limits['xmax'])
        ax.set_ylim(limits['ymax'], limits['ymin'])

        # Grid
        ax.grid(True, alpha=0.3, color='#CCCCCC')

        # Add legend if pile is drawn
        if pile_top > pile_tip:
            ax.legend(loc='lower right', framealpha=0.9, fontsize=8)

        # Tight layout
        figure.tight_layout()

        return canvas

    def _plot_bh_on_axis(self, ax, bh_name, use_elevation):
        """Plot a single borehole on the given axes (shared by screen and PDF export)"""
        settings = self.bh_settings.get(bh_name, {'surface_elev': 100.0, 'water_level': 0.0})
        surface_elev = settings['surface_elev']

        spt_values = []
        y_values = []
        class_values = []
        depth_indices = []

        for idx, depth in enumerate(sorted(self.depths)):
            data = self.borehole_data[bh_name].get(depth, {'spt': None, 'class': ''})
            if data['spt'] is not None:
                spt_values.append(data['spt'])
                if use_elevation:
                    y_values.append(surface_elev - depth)
                else:
                    y_values.append(depth)
                class_values.append(data['class'])
                depth_indices.append(idx)

        if spt_values:
            color = "#0004FF"
            ax.scatter(spt_values, y_values, c=color, s=80, alpha=1.0, zorder=3)

            for i in range(len(spt_values) - 1):
                if depth_indices[i+1] - depth_indices[i] == 1:
                    ax.plot([spt_values[i], spt_values[i+1]],
                           [y_values[i], y_values[i+1]],
                           c=color, alpha=1.0, linewidth=1.5, zorder=2)

            for spt, y_val, cls in zip(spt_values, y_values, class_values):
                label = f"N={int(spt)}"
                if cls:
                    label += f", {cls}"
                ax.annotate(label, (spt, y_val), textcoords="offset points",
                           xytext=(5, 0), ha='left', fontsize=self.label_size,
                           color='#1C1C1E', alpha=0.8)

        bh_settings = self.bh_settings.get(bh_name, {})
        pile_top = bh_settings.get('pile_top', 100.0)
        pile_tip = bh_settings.get('pile_tip', 85.0)
        limits = self.axis_limits.get(bh_name, {'xmin': 0, 'xmax': 60, 'ymin': 100, 'ymax': 70})

        if self.vline_checkbox.isChecked():
            vline_x = self.vline_x_spin.value()
            if limits['xmin'] <= vline_x <= limits['xmax']:
                ax.axvline(x=vline_x, color='red', linewidth=1.0, linestyle='-',
                          alpha=0.5, zorder=1)

        if pile_top > pile_tip:
            ax.axhline(y=pile_top, color="#0E7224", linewidth=1.5, linestyle='-',
                      alpha=0.7, zorder=1, label=f'Pile Top ({pile_top:.1f}m)')
            ax.axhline(y=pile_tip, color='#FF0000', linewidth=1.5, linestyle='-',
                      alpha=0.7, zorder=1, label=f'Pile Tip ({pile_tip:.1f}m)')
            pile_x_position = limits['xmin'] + (limits['xmax'] - limits['xmin']) * 0.5
            ax.plot([pile_x_position, pile_x_position], [pile_top, pile_tip],
                   color="#818181", linewidth=8, linestyle='-',
                   alpha=0.6, zorder=1)
            pile_length = pile_top - pile_tip
            pile_mid_y = (pile_top + pile_tip) / 2
            ax.text(pile_x_position, pile_mid_y, f'{pile_length:.1f}m',
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white',
                            edgecolor='black', linewidth=1.5),
                   zorder=4)

        if not use_elevation:
            ax.invert_yaxis()

        ax.set_xlabel('SPT N-value (blow/ft)', fontsize=11, fontweight='bold', color='black')
        y_label = 'Elevation (m)' if use_elevation else 'Depth (m)'
        ax.set_ylabel(y_label, fontsize=11, fontweight='bold', color='black')
        title_text = f'{bh_name}\nSurface: {surface_elev:.2f} m'
        ax.set_title(title_text, fontsize=13, fontweight='bold', pad=15, color='black')
        ax.set_xlim(limits['xmin'], limits['xmax'])
        ax.set_ylim(limits['ymax'], limits['ymin'])
        ax.grid(True, alpha=0.3, color='#CCCCCC')

        if pile_top > pile_tip:
            ax.legend(loc='lower right', framealpha=0.9, fontsize=8)

    def _apply_plot_style(self):
        """Apply clean white background theme with dark text/borders"""
        plt.rcParams.update({
            'font.family': 'sans-serif',
            'font.sans-serif': ['SF Pro Display', 'Arial', 'Helvetica'],
            'font.size': 10,
            'axes.labelsize': 11,
            'axes.titlesize': 13,
            'axes.labelcolor': '#000000',  # Black text
            'axes.edgecolor': '#000000',   # Black borders
            'axes.linewidth': 1.5,
            'axes.facecolor': '#FFFFFF',   # White background
            'figure.facecolor': '#FFFFFF', # White figure background
            'grid.color': '#CCCCCC',       # Light gray grid
            'grid.linewidth': 0.5,
            'xtick.color': '#000000',      # Black tick marks
            'ytick.color': '#000000',      # Black tick marks
            'text.color': '#000000',       # Black text
        })

    def add_borehole(self):
        """Add a new borehole"""
        num = len(self.bh_names) + 1
        new_bh = f"BH-{num}"
        self.bh_names.append(new_bh)

        # Initialize empty data
        self.borehole_data[new_bh] = {}
        self.axis_limits[new_bh] = {'xmin': 0, 'xmax': 100, 'ymin': 0, 'ymax': 30}
        self.bh_settings[new_bh] = {
            'surface_elev': 100.0,
            'water_level': 0.0,
            'pile_top': 100.0,
            'pile_tip': 85.0
        }

        for depth in self.depths:
            self.borehole_data[new_bh][depth] = {'spt': None, 'class': ''}

        # Update BH selector
        self.bh_selector.addItem(new_bh)

        self._update_table()
        self.update_plots()

    def remove_borehole(self):
        """Remove the last borehole"""
        if len(self.bh_names) <= 1:
            QMessageBox.warning(self, "Warning", "Cannot remove the last borehole!")
            return

        bh_to_remove = self.bh_names.pop()
        del self.borehole_data[bh_to_remove]
        del self.axis_limits[bh_to_remove]
        del self.bh_settings[bh_to_remove]

        # Update BH selector
        self.bh_selector.clear()
        self.bh_selector.addItems(self.bh_names)
        self.selected_bh = self.bh_names[0] if self.bh_names else None

        self._update_table()
        self.update_plots()

    def add_depth_row(self):
        """Add a new depth row (increments by 1.50 from last depth)"""
        if len(self.depths) > 0:
            # Get the last depth and add 1.50
            new_depth = round(self.depths[-1] + 1.50, 2)
        else:
            # If no depths exist, start with 1.45
            new_depth = 1.45

        # Add new depth to the list
        self.depths.append(new_depth)

        # Add empty data for this depth in all boreholes
        for bh in self.bh_names:
            self.borehole_data[bh][new_depth] = {'spt': None, 'class': ''}

        self._update_table()
        self.update_plots()

    def remove_depth_row(self):
        """Remove the last depth row"""
        if len(self.depths) <= 1:
            QMessageBox.warning(self, "Warning", "Cannot remove the last depth row!")
            return

        # Remove the last depth
        depth_to_remove = self.depths.pop()

        # Remove this depth from all boreholes
        for bh in self.bh_names:
            if depth_to_remove in self.borehole_data[bh]:
                del self.borehole_data[bh][depth_to_remove]

        self._update_table()
        self.update_plots()

    def save_data(self):
        """Save data to JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "JSON Files (*.json)")
        if not file_path:
            return

        data = {
            'bh_names': self.bh_names,
            'depths': self.depths,
            'borehole_data': self.borehole_data,
            'bh_settings': self.bh_settings,
            'axis_limits': self.axis_limits,
            'label_size': self.label_size
        }

        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            QMessageBox.information(self, "Success", "Data saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data: {str(e)}")

    def clear_data(self):
        """Clear all data"""
        reply = QMessageBox.question(self, "Confirm", "Are you sure you want to clear all data?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for bh in self.bh_names:
                for depth in self.depths:
                    self.borehole_data[bh][depth] = {'spt': None, 'class': ''}
            self._update_table()
            self.update_plots()

    def export_preview_png(self):
        """Export preview window (all graphs) to PNG"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Preview to PNG", "", "PNG Files (*.png)"
        )
        if not file_path:
            return

        try:
            # Capture the plot container widget as an image
            pixmap = self.plot_widget.grab()
            pixmap.save(file_path, "PNG", quality=100)

            QMessageBox.information(
                self, "Success",
                f"Preview exported successfully!\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PNG: {str(e)}")

    def export_preview_pdf(self):
        """Export preview window (all graphs) to PDF"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Preview to PDF", "", "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            from matplotlib.backends.backend_pdf import PdfPages

            # Create a combined figure with all boreholes side by side
            num_bh = len(self.bh_names)
            if num_bh == 0:
                QMessageBox.warning(self, "Warning", "No boreholes to export.")
                return

            fig = Figure(figsize=(5 * num_bh, 6), dpi=150)
            self._apply_plot_style()

            y_axis_mode = self.y_axis_combo.currentText()
            use_elevation = (y_axis_mode == "Elevation")

            for idx, bh in enumerate(self.bh_names):
                ax = fig.add_subplot(1, num_bh, idx + 1)
                self._plot_bh_on_axis(ax, bh, use_elevation)

            fig.tight_layout()

            with PdfPages(file_path) as pdf:
                pdf.savefig(fig, bbox_inches='tight')

            QMessageBox.information(
                self, "Success",
                f"Preview exported successfully!\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}")

    def get_data(self):
        """Get current borehole data (for use by other modules)"""
        return {
            'bh_names': self.bh_names,
            'depths': self.depths,
            'borehole_data': self.borehole_data,
            'bh_settings': self.bh_settings
        }

    def get_project_data(self):
        """Get all data for project save"""
        return {
            'bh_names': self.bh_names,
            'depths': self.depths,
            'borehole_data': self.borehole_data,
            'bh_settings': self.bh_settings,
            'axis_limits': self.axis_limits,
            'label_size': self.label_size,
            'vline_enabled': self.vline_checkbox.isChecked(),
            'vline_x_value': self.vline_x_spin.value()
        }

    def load_project_data(self, data):
        """Load project data and update UI"""
        try:
            # Load basic data
            self.bh_names = data.get('bh_names', [])
            self.depths = data.get('depths', [])

            # Load borehole_data and convert depth keys from string to float
            borehole_data_raw = data.get('borehole_data', {})
            self.borehole_data = {}
            for bh_name, depths_data in borehole_data_raw.items():
                self.borehole_data[bh_name] = {}
                for depth_str, depth_data in depths_data.items():
                    # Convert depth key to float
                    self.borehole_data[bh_name][float(depth_str)] = depth_data

            self.bh_settings = data.get('bh_settings', {})
            self.axis_limits = data.get('axis_limits', {})
            self.label_size = data.get('label_size', 8)

            # Load vline settings
            vline_enabled = data.get('vline_enabled', False)
            vline_x_value = data.get('vline_x_value', 30.0)
            self.vline_checkbox.setChecked(vline_enabled)
            self.vline_x_spin.setValue(vline_x_value)

            # Update UI
            self._update_table_from_data()
            self.update_plots()

        except Exception as e:
            print(f"Error loading Module 1 data: {e}")

    def _update_table_from_data(self):
        """Update table widget from loaded data"""
        if not self.bh_names or not self.depths:
            return

        # Update BH selector
        self.bh_selector.clear()
        self.bh_selector.addItem("All BH")
        self.bh_selector.addItems(self.bh_names)
        self.selected_bh = "All BH"

        # Update label size spinbox if it exists
        if hasattr(self, 'label_size_spinbox'):
            self.label_size_spinbox.setValue(self.label_size)

        # Update table (uses existing _update_table method)
        self._update_table()

        # Update axis settings UI by selecting the current BH
        if hasattr(self, 'bh_selector'):
            self.on_bh_selected("All BH")
