"""
Module 6: Python Scripts for PLAXIS
Generate Python scripts for PLAXIS software automation

Features:
- Create borehole with position
- Layer properties table (Soil Model, Drainage, Properties, Strength, etc.)
- Water Level settings (LWL, HWL, user-defined)
- Soil Contour settings
- Staged Construction table
- Preview and export Python scripts
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QFileDialog,
    QMessageBox, QSplitter, QComboBox, QLineEdit,
    QGroupBox, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QDialog, QDialogButtonBox, QAbstractItemView,
    QTabWidget
)
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QFont, QColor, QPen, QPainter
import re


class BranchTreeWidget(QTreeWidget):
    """QTreeWidget that paints blue connector lines (├ └ │) between phases."""

    _LINE_COLOR = QColor('#3B82F6')
    _LINE_WIDTH = 2

    def drawBranches(self, painter, rect, index):
        """Override to draw blue branch connector lines."""
        painter.fillRect(rect, QColor('white'))

        if not index.parent().isValid():
            return  # Top-level (root) — no lines needed

        indent = self.indentation()
        mid_y = (rect.top() + rect.bottom()) // 2

        # Build depth info: for each level → (row_in_parent, sibling_count)
        levels = []
        idx = index
        while idx.parent().isValid():
            parent = idx.parent()
            levels.insert(0, (idx.row(), self.model().rowCount(parent)))
            idx = parent

        painter.save()
        pen = QPen(self._LINE_COLOR)
        pen.setWidth(self._LINE_WIDTH)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        depth = len(levels)
        for i, (row, total) in enumerate(levels):
            x = rect.left() + indent * i + indent // 2
            has_more = row < total - 1

            if i == depth - 1:
                # This item's own level — draw connector to item
                painter.drawLine(x, mid_y, rect.right(), mid_y)
                if has_more:
                    # ├── vertical top → bottom
                    painter.drawLine(x, rect.top(), x, rect.bottom())
                else:
                    # └── vertical top → mid
                    painter.drawLine(x, rect.top(), x, mid_y)
            else:
                # Ancestor level — vertical continuation if siblings below
                if has_more:
                    # │ full vertical line
                    painter.drawLine(x, rect.top(), x, rect.bottom())

        painter.restore()


class Module6PlaxisScripts(QWidget):
    """
    Module 6: Python Scripts for PLAXIS
    """

    # PLAXIS dropdown options with code values
    SOIL_MODELS = {
        'None': 0,
        'Linear Elastic': 1,
        'Mohr-Coulomb': 2
    }

    DRAINAGE_TYPES = {
        'Drained': 0,
        'Undrained A': 1,
        'Undrained B': 2,
        'Undrained C': 3,
        'Non-porous': 4,
    }

    # Classification: GroundwaterClassificationType
    CLASSIFICATION_TYPES = {
        'Standard': 0,
        'Hypres': 1,
        'USDA' : 2,
        'Staring': 3
    }

    # GroundwaterSoilClassUSDA (for USDA classification)
    USDA_SOIL_CLASSES = {
        'Sand': 0,
        'Loamy Sand': 1,
        'Sandy Loam': 2,
        'Loam': 3,
        'Silt': 4,
        'Silt Loam': 5,
        'Sandy Clay Loam': 6,
        'Clay Loam': 7,
        'Silty Clay Loam': 8,
        'Sandy Clay': 9,
        'Silty Clay': 10,
        'Clay': 11,
    }

    # GroundwaterSoilClassStandard (for Standard classification)
    STANDARD_SOIL_CLASSES = {
        'Coarse': 0,
        'Medium': 1,
        'Medium fine': 2,
        'Fine': 3,
        'Very fine': 4,
        'Organic': 5,
    }
    
    # GwDefaultsMethod
    DEFAULTS_METHODS = {
        'From data set': 0,
        'From grain size distribution': 1,
    }

    # K0 Determination
    K0_DETERMINATION = {
        'Automatic': 0,
        'Manual': 1,
    }

    # InterfaceStrengthDetermination
    INTERFACE_STRENGTH = {
        'Rigid': 0,
        'Manual': 1,
    }

    # Staged Construction - InitialPhase Calculation Type
    INITIAL_PHASE_CALC_TYPE = {
        'K0 procedure': 0,
        'Field stress': 1,
        'Gravity loading': 2,
    }

    # Staged Construction - Phase Calculation Type
    PHASE_CALC_TYPE = {
        'Plastic': 0,
        'Consolidation': 1,
        'Safety': 2,
    }

    # Pore Pressure Calculation Type
    PORE_PRESSURE_CALC_TYPE = {
        'Phreatic': 0,
        'Use pressures from previous phase': 1,
        'Steady state groundwater flow': 2,
    }

    # Reset Displacements to Zero
    RESET_DISPLACEMENTS = {
        'TRUE': True,
        'FALSE': False,
        '-': None,
    }

    def __init__(self, parent=None, module4=None):
        super().__init__(parent)

        # Reference to Module 4 for data linking
        self.module4 = module4

        # Data storage
        self.borehole_position = 0
        self.layers_data = []
        self.staged_construction = []
        self.water_levels = {'LWL': None, 'HWL': None, 'user_defined': None}
        self.soil_contour = {'xmin': 0, 'xmax': 100, 'ymin': 75, 'ymax': 100}

        # Output script export folder (user-selectable)
        self._output_dir = r"C:\Users\Public\Documents\PLAXIS_Exports"

        self._setup_ui()

    def eventFilter(self, obj, event):
        """Handle double-click on tree viewport and Enter key in tables"""
        # Intercept double-click on staged tree column 0 → parent selection
        if hasattr(self, 'staged_tree') and obj == self.staged_tree.viewport():
            if event.type() == QEvent.Type.MouseButtonDblClick:
                pos = event.position().toPoint()
                index = self.staged_tree.indexAt(pos)
                if index.isValid() and index.column() == 0:
                    item = self.staged_tree.itemFromIndex(index)
                    if item:
                        if item.text(0).lower() == 'initial phase':
                            QMessageBox.information(
                                self, "Info",
                                "Initial phase is always the root "
                                "and cannot be reparented.")
                        else:
                            self._show_parent_selection_dialog(item)
                        return True  # Consume event — prevent Qt editing

        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if obj == self.layer_table:
                    current_row = self.layer_table.currentRow()
                    current_col = self.layer_table.currentColumn()
                    # Move to next column, or next row if at end
                    if current_col < self.layer_table.columnCount() - 1:
                        self.layer_table.setCurrentCell(current_row, current_col + 1)
                    elif current_row < self.layer_table.rowCount() - 1:
                        self.layer_table.setCurrentCell(current_row + 1, 0)
                    return True
        return super().eventFilter(obj, event)

    def _style_combobox(self, combo):
        """Apply style to combobox - no scroll, show all items"""
        combo.setMaxVisibleItems(20)  # Show all items without scroll
        combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def _setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Compact top bar (like other modules)
        top_bar = self._create_top_bar()
        main_layout.addLayout(top_bar)

        # Sub-tab widget with 3 tabs
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setFont(QFont("SF Pro Display", 10))
        self.sub_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                background: white;
                top: -1px;
            }
            QTabBar::tab {
                background: #F2F2F7;
                border: 1px solid #D1D1D6;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 24px;
                margin-right: 2px;
                font-size: 10pt;
                color: #6E6E73;
            }
            QTabBar::tab:selected {
                background: white;
                color: #007AFF;
                font-weight: bold;
                border-bottom: 2px solid white;
            }
            QTabBar::tab:hover:!selected {
                background: #E5E5EA;
                color: #3C3C43;
            }
        """)

        # ── Tab 1: Borehole, Water Level, Soil Contour & Layer Properties ──
        tab1_widget = QWidget()
        tab1_layout = QVBoxLayout(tab1_widget)
        tab1_layout.setContentsMargins(8, 12, 8, 8)
        tab1_layout.setSpacing(12)

        tab1_layout.addWidget(self._create_borehole_water_contour_section())
        tab1_layout.addWidget(self._create_layer_table_section(), 1)

        tab1_btn_layout = QHBoxLayout()
        tab1_btn_layout.addStretch()
        btn_load = QPushButton("Load from Module 4")
        btn_load.setToolTip("Load layer data from Module 4")
        btn_load.setFont(QFont("SF Pro Display", 10))
        btn_load.clicked.connect(self._load_from_module4)
        tab1_btn_layout.addWidget(btn_load)
        tab1_layout.addLayout(tab1_btn_layout)

        self.sub_tabs.addTab(tab1_widget, "Borehole && Layer Properties")

        # ── Tab 2: Staged Construction ──
        tab2_widget = QWidget()
        tab2_layout = QVBoxLayout(tab2_widget)
        tab2_layout.setContentsMargins(8, 12, 8, 8)
        tab2_layout.setSpacing(12)

        tab2_layout.addWidget(self._create_staged_construction_section(), 1)

        self.sub_tabs.addTab(tab2_widget, "Staged Construction")

        # ── Tab 3: Python Script ──
        tab3_widget = QWidget()
        tab3_layout = QVBoxLayout(tab3_widget)
        tab3_layout.setContentsMargins(8, 12, 8, 8)
        tab3_layout.setSpacing(8)

        tab3_btn_layout = QHBoxLayout()
        tab3_btn_layout.addStretch()
        btn_generate = QPushButton("Generate Script")
        btn_generate.setToolTip("Generate Python script from table data")
        btn_generate.setFont(QFont("SF Pro Display", 10))
        btn_generate.clicked.connect(self._run_code)
        tab3_btn_layout.addWidget(btn_generate)

        btn_save = QPushButton("Save .py")
        btn_save.setToolTip("Save Python script to file")
        btn_save.setFont(QFont("SF Pro Display", 10))
        btn_save.clicked.connect(self._save_script)
        tab3_btn_layout.addWidget(btn_save)
        tab3_layout.addLayout(tab3_btn_layout)

        tab3_layout.addWidget(self._create_preview_section(), 1)

        self.sub_tabs.addTab(tab3_widget, "Python Script")

        # ── Tab 4: Output Script ──
        tab4_widget = QWidget()
        tab4_layout = QVBoxLayout(tab4_widget)
        tab4_layout.setContentsMargins(8, 12, 8, 8)
        tab4_layout.setSpacing(8)

        # Buttons row for output script
        out_btn_layout = QHBoxLayout()

        # ── Left: folder picker ──
        btn_folder = QPushButton("Export Folder...")
        btn_folder.setToolTip("Select output folder for exported PNG files")
        btn_folder.setFont(QFont("SF Pro Display", 10))
        btn_folder.clicked.connect(self._pick_output_dir)
        out_btn_layout.addWidget(btn_folder)

        self._output_dir_label = QLabel(self._output_dir)
        self._output_dir_label.setFont(QFont("SF Pro Display", 9))
        self._output_dir_label.setStyleSheet("color: #6E6E73;")
        self._output_dir_label.setWordWrap(False)
        out_btn_layout.addWidget(self._output_dir_label, 1)

        out_btn_layout.addStretch()

        btn_gen_out = QPushButton("Generate Output Script")
        btn_gen_out.setToolTip("Generate Python script for PLAXIS Output")
        btn_gen_out.setFont(QFont("SF Pro Display", 10))
        btn_gen_out.setMaximumWidth(220)
        btn_gen_out.clicked.connect(self._run_output_code)
        out_btn_layout.addWidget(btn_gen_out)

        btn_save_out = QPushButton("Save Output .py")
        btn_save_out.setToolTip("Save output script to file")
        btn_save_out.setFont(QFont("SF Pro Display", 10))
        btn_save_out.setMaximumWidth(150)
        btn_save_out.clicked.connect(self._save_output_script)
        out_btn_layout.addWidget(btn_save_out)

        tab4_layout.addLayout(out_btn_layout)

        # Splitter: table top, preview bottom
        out_splitter = QSplitter(Qt.Orientation.Vertical)
        out_splitter.addWidget(self._create_output_script_section())
        out_splitter.addWidget(self._create_output_preview_section())
        out_splitter.setSizes([400, 300])

        tab4_layout.addWidget(out_splitter, 1)

        self.sub_tabs.addTab(tab4_widget, "Output Script")

        main_layout.addWidget(self.sub_tabs)
        self.setLayout(main_layout)

    def _create_top_bar(self):
        """Create compact top bar with title and action buttons"""
        layout = QHBoxLayout()
        layout.setSpacing(8)

        # Title
        title = QLabel("Module 6")
        title.setFont(QFont("SF Pro Display", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("color: #D1D1D6;")
        layout.addWidget(separator)

        # Subtitle
        subtitle = QLabel("Python Scripts for PLAXIS")
        subtitle.setFont(QFont("SF Pro Display", 12))
        subtitle.setStyleSheet("color: #6E6E73;")
        layout.addWidget(subtitle)

        layout.addStretch()

        return layout

    def _create_borehole_water_contour_section(self):
        """Create combined section with Borehole, Water Level, and Soil Contour in single horizontal line"""
        group = QGroupBox("Borehole, Water Level & Soil Contour")
        group.setFont(QFont("SF Pro Display", 11, QFont.Weight.Bold))
        layout = QHBoxLayout()
        layout.setSpacing(15)

        # Style for input fields
        input_style = "padding: 4px; border: 1px solid #ccc; border-radius: 3px;"
        input_width = 60

        # ---- Borehole Position ----
        layout.addWidget(QLabel("Borehole (x):"))
        self.position_input = QLineEdit("0")
        self.position_input.setFixedWidth(input_width)
        self.position_input.setStyleSheet(input_style)
        layout.addWidget(self.position_input)

        # Separator
        sep1 = QLabel("|")
        sep1.setStyleSheet("color: #ccc; margin: 0 5px;")
        layout.addWidget(sep1)

        # ---- Water Level ----
        layout.addWidget(QLabel("LWL:"))
        self.lwl_input = QLineEdit("")
        self.lwl_input.setFixedWidth(input_width)
        self.lwl_input.setStyleSheet(input_style)
        self.lwl_input.setPlaceholderText("Y")
        layout.addWidget(self.lwl_input)

        layout.addWidget(QLabel("HWL:"))
        self.hwl_input = QLineEdit("")
        self.hwl_input.setFixedWidth(input_width)
        self.hwl_input.setStyleSheet(input_style)
        self.hwl_input.setPlaceholderText("Y")
        layout.addWidget(self.hwl_input)

        # Separator
        sep2 = QLabel("|")
        sep2.setStyleSheet("color: #ccc; margin: 0 5px;")
        layout.addWidget(sep2)

        # ---- Soil Contour ----
        layout.addWidget(QLabel("Soil Contour  Xmin:"))
        self.xmin_input = QLineEdit("0")
        self.xmin_input.setFixedWidth(input_width)
        self.xmin_input.setStyleSheet(input_style)
        layout.addWidget(self.xmin_input)

        layout.addWidget(QLabel("Xmax:"))
        self.xmax_input = QLineEdit("100")
        self.xmax_input.setFixedWidth(input_width)
        self.xmax_input.setStyleSheet(input_style)
        layout.addWidget(self.xmax_input)

        layout.addWidget(QLabel("Ymin:"))
        self.ymin_input = QLineEdit("70")
        self.ymin_input.setFixedWidth(input_width)
        self.ymin_input.setStyleSheet(input_style)
        layout.addWidget(self.ymin_input)

        layout.addWidget(QLabel("Ymax:"))
        self.ymax_input = QLineEdit("100")
        self.ymax_input.setFixedWidth(input_width)
        self.ymax_input.setStyleSheet(input_style)
        layout.addWidget(self.ymax_input)

        layout.addStretch()

        # ---- Export CSV ----
        btn_csv = QPushButton("Export CSV")
        btn_csv.setToolTip("Export layer table to CSV file")
        btn_csv.setFont(QFont("SF Pro Display", 10))
        btn_csv.clicked.connect(self._export_layer_csv)
        layout.addWidget(btn_csv)

        group.setLayout(layout)
        return group

    def _export_layer_csv(self):
        """Export the layer properties table to a CSV file"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Layer Table as CSV", "layer_properties.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            import csv
            table = self.layer_table
            ncols = table.columnCount()
            nrows = table.rowCount()

            # Collect headers from horizontal header
            headers = []
            for col in range(ncols):
                item = table.horizontalHeaderItem(col)
                headers.append(item.text() if item else f"Col{col}")

            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in range(nrows):
                    row_data = []
                    for col in range(ncols):
                        row_data.append(self._get_layer_cell_value(row, col))
                    writer.writerow(row_data)

            QMessageBox.information(self, "Export CSV",
                                    f"Exported {nrows} rows to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export CSV Error", str(e))

    def _create_layer_table_section(self):
        """Create layer properties table matching PLAXIS requirements"""
        group = QGroupBox("Layer Properties")
        group.setFont(QFont("SF Pro Display", 11, QFont.Weight.Bold))
        layout = QVBoxLayout()

        # Layer Table - 19 columns matching the image
        # Layer | Identification | Soil Model | Drainage Type | Property | Strength | Groundwater | Interfaces | Initial
        self.layer_table = QTableWidget()
        self.layer_table.setColumnCount(19)
        headers = [
            'From', 'To', 'Name',                    # Layer info
            'Soil Model', 'Drainage Type',           # Model settings
            'γunsat', 'γsat', 'Void Ratio',          # Property
            'Eref', 'ν(nu)', 'Su', 'cref', 'phi',    # Strength
            'Classification', 'Soil class',          # Groundwater
            'Defaults method', 'Rinter', 'K0', 'K0-manual'  # Interfaces & Initial
        ]
        self.layer_table.setHorizontalHeaderLabels(headers)
        self.layer_table.setRowCount(5)
        self.layer_table.setFont(QFont("SF Pro Display", 9))

        # Set row height for better visibility
        self.layer_table.verticalHeader().setDefaultSectionSize(32)

        # Style for table - no white background covering text
        self.layer_table.setStyleSheet("""
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
            QComboBox {
                background-color: transparent;
                border: 1px solid #ccc;
                padding: 2px 5px;
            }
            QComboBox:focus {
                border: 1px solid #007AFF;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: rgba(0, 122, 255, 0.15);
            }
        """)

        # Enable Enter key navigation
        self.layer_table.installEventFilter(self)

        # Set column widths - compact for numbers, wider for text/dropdowns
        # From, To, Name, Soil Model, Drainage, γunsat, γsat, Void, Eref, ν, Su, cref, phi, Class, Soil, Default, Rint, K0, K0-manual
        col_widths = [50, 50, 180, 180, 120, 52, 52, 80, 50, 50, 50, 50, 50, 140, 110, 180, 50, 110, 80]
        for col, width in enumerate(col_widths):
            self.layer_table.setColumnWidth(col, width)

        # Connect cell change signal for γsat → γunsat auto-calculation
        self.layer_table.cellChanged.connect(self._on_layer_cell_changed)

        # Initialize table with dropdowns
        self._init_layer_table()

        layout.addWidget(self.layer_table, 1)

        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        add_row_btn = QPushButton("+ ROW")
        add_row_btn.setFont(QFont("SF Pro Display", 10))
        add_row_btn.clicked.connect(self._add_layer_row)
        btn_layout.addWidget(add_row_btn)

        del_row_btn = QPushButton("- ROW")
        del_row_btn.setFont(QFont("SF Pro Display", 10))
        del_row_btn.clicked.connect(self._delete_layer_row)
        btn_layout.addWidget(del_row_btn)

        layout.addLayout(btn_layout)

        group.setLayout(layout)
        return group

    def _init_layer_table(self):
        """Initialize layer table with dropdowns and default values"""
        # Default depth ranges
        depth_ranges = [(100, 95), (95, 85), (85, 75), (75, 65), (65, 55)]

        for row in range(self.layer_table.rowCount()):
            self._setup_layer_row(row, depth_ranges[row] if row < len(depth_ranges) else (0, 0))

    def _setup_layer_row(self, row, depth_range=(0, 0)):
        """Setup a single row with appropriate widgets"""
        from_val, to_val = depth_range

        # Column 0: From
        item = QTableWidgetItem(str(from_val) if from_val else '')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 0, item)

        # Column 1: To
        item = QTableWidgetItem(str(to_val) if to_val else '')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 1, item)

        # Column 2: Name (editable text)
        item = QTableWidgetItem('')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 2, item)

        # Column 3: Soil Model (dropdown)
        combo = QComboBox()
        combo.addItems(list(self.SOIL_MODELS.keys()))
        combo.setCurrentText('Mohr-Coulomb')
        self._style_combobox(combo)
        self.layer_table.setCellWidget(row, 3, combo)

        # Column 4: Drainage Type (dropdown)
        combo = QComboBox()
        combo.addItems(list(self.DRAINAGE_TYPES.keys()))
        combo.setCurrentText('Drained')
        self._style_combobox(combo)
        self.layer_table.setCellWidget(row, 4, combo)

        # Column 5: γunsat (editable)
        item = QTableWidgetItem('')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 5, item)

        # Column 6: γsat (editable)
        item = QTableWidgetItem('')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 6, item)

        # Column 7: Void Ratio (editable, default)
        item = QTableWidgetItem('Default')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 7, item)

        # Column 8: Eref (editable)
        item = QTableWidgetItem('')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 8, item)

        # Column 9: ν(nu) (editable)
        item = QTableWidgetItem('')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 9, item)

        # Column 10: Su (editable)
        item = QTableWidgetItem('')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 10, item)

        # Column 11: cref (editable)
        item = QTableWidgetItem('')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 11, item)

        # Column 12: phi (editable)
        item = QTableWidgetItem('')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 12, item)

        # Column 13: Classification (dropdown)
        class_combo = QComboBox()
        class_combo.addItems(list(self.CLASSIFICATION_TYPES.keys()))
        class_combo.setCurrentText('USDA')
        self._style_combobox(class_combo)
        self.layer_table.setCellWidget(row, 13, class_combo)

        # Column 14: Soil class (dropdown - changes based on Classification)
        soil_class_combo = QComboBox()
        soil_class_combo.addItems(list(self.USDA_SOIL_CLASSES.keys()))  # Default to USDA
        soil_class_combo.setCurrentText('Sand')
        self._style_combobox(soil_class_combo)
        self.layer_table.setCellWidget(row, 14, soil_class_combo)

        # Connect Classification change to update Soil class options
        class_combo.currentTextChanged.connect(
            lambda text, r=row: self._on_classification_changed(r, text)
        )

        # Column 15: Defaults method (dropdown)
        combo = QComboBox()
        combo.addItems(list(self.DEFAULTS_METHODS.keys()))
        combo.setCurrentText('From data set')
        self._style_combobox(combo)
        self.layer_table.setCellWidget(row, 15, combo)

        # Column 16: Rinter (editable)
        item = QTableWidgetItem('0.8')
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 16, item)

        # Column 17: K0 (dropdown: Automatic/Manual)
        k0_combo = QComboBox()
        k0_combo.addItems(list(self.K0_DETERMINATION.keys()))
        k0_combo.setCurrentText('Automatic')
        self._style_combobox(k0_combo)
        self.layer_table.setCellWidget(row, 17, k0_combo)

        # Column 18: K0-manual (editable, shows "-" when Auto, empty when Manual)
        k0_manual_item = QTableWidgetItem('-')
        k0_manual_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 18, k0_manual_item)

        # Connect K0 dropdown change to update K0-manual
        k0_combo.currentTextChanged.connect(
            lambda text, r=row: self._on_k0_changed(r, text)
        )

    def _on_k0_changed(self, row, k0_text):
        """Update K0-manual based on K0 selection"""
        k0_manual_item = self.layer_table.item(row, 18)
        if not k0_manual_item:
            return

        if k0_text == 'Automatic':
            # Show "-" and make read-only appearance
            k0_manual_item.setText('-')
        else:  # Manual
            # Show empty for user input
            current_text = k0_manual_item.text()
            if current_text == '-':
                k0_manual_item.setText('')

    def _on_layer_cell_changed(self, row, col):
        """Handle cell changes - auto-calculate γunsat from γsat"""
        # Column 6 is γsat, Column 5 is γunsat
        if col == 6:  # γsat changed
            gamma_sat_item = self.layer_table.item(row, 6)
            gamma_unsat_item = self.layer_table.item(row, 5)

            if gamma_sat_item and gamma_unsat_item:
                gamma_sat_text = gamma_sat_item.text().strip()
                gamma_unsat_text = gamma_unsat_item.text().strip()

                # Only auto-calculate if γunsat is empty or was auto-calculated before
                if gamma_sat_text:
                    try:
                        gamma_sat = float(gamma_sat_text)
                        gamma_unsat = gamma_sat - 1

                        # Only update if γunsat is empty or matches previous auto-calc
                        if not gamma_unsat_text or gamma_unsat_text == str(gamma_sat):
                            # Block signals to prevent recursion
                            self.layer_table.blockSignals(True)
                            gamma_unsat_item.setText(str(gamma_unsat))
                            self.layer_table.blockSignals(False)
                    except ValueError:
                        pass  # Invalid number, skip

    def _on_classification_changed(self, row, classification_text):
        """Update Soil class dropdown based on Classification selection"""
        soil_class_combo = self.layer_table.cellWidget(row, 14)
        if not soil_class_combo:
            return

        # Save current selection if possible
        current_text = soil_class_combo.currentText()

        # Clear and repopulate based on classification
        soil_class_combo.clear()

        if classification_text == 'USDA':
            soil_class_combo.addItems(list(self.USDA_SOIL_CLASSES.keys()))
            # Try to restore selection or default to Sand
            if current_text in self.USDA_SOIL_CLASSES:
                soil_class_combo.setCurrentText(current_text)
            else:
                soil_class_combo.setCurrentText('Sand')
        elif classification_text == 'Standard':
            soil_class_combo.addItems(list(self.STANDARD_SOIL_CLASSES.keys()))
            # Try to restore selection or default to Medium
            if current_text in self.STANDARD_SOIL_CLASSES:
                soil_class_combo.setCurrentText(current_text)
            else:
                soil_class_combo.setCurrentText('Medium')
        elif classification_text == 'Hypres':
            # Hypres uses same classes as Standard
            soil_class_combo.addItems(list(self.STANDARD_SOIL_CLASSES.keys()))
            soil_class_combo.setCurrentText('Medium')
        elif classification_text == 'Staring':
            # Staring uses same classes as Standard
            soil_class_combo.addItems(list(self.STANDARD_SOIL_CLASSES.keys()))
            soil_class_combo.setCurrentText('Medium')

    def _create_staged_construction_section(self):
        """Create staged construction with QTreeWidget for phase hierarchy"""
        group = QGroupBox("Staged Construction")
        group.setFont(QFont("SF Pro Display", 11, QFont.Weight.Bold))
        layout = QVBoxLayout()

        # Hint label
        hint = QLabel("Double-click phase to change parent  |  F2 to rename")
        hint.setFont(QFont("SF Pro Display", 9))
        hint.setStyleSheet("color: #8E8E93;")
        layout.addWidget(hint)

        # QTreeWidget with blue branch connector lines
        self.staged_tree = BranchTreeWidget()
        self.staged_tree.setColumnCount(4)
        self.staged_tree.setHeaderLabels([
            'Phase', 'Calculation Type',
            'Pore pressure calculation', 'Reset displacements to zero'
        ])
        self.staged_tree.setFont(QFont("SF Pro Display", 10))

        # Column widths
        self.staged_tree.setColumnWidth(0, 200)
        self.staged_tree.setColumnWidth(1, 150)
        self.staged_tree.setColumnWidth(2, 200)
        self.staged_tree.setColumnWidth(3, 180)

        # F2 to rename, double-click handled by signal for parent selection
        self.staged_tree.setEditTriggers(
            QAbstractItemView.EditTrigger.EditKeyPressed
        )

        # Styling
        self.staged_tree.setStyleSheet("""
            QTreeWidget {
                background-color: white;
                border: 1px solid #D1D1D6;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 4px;
                min-height: 28px;
            }
            QTreeWidget::item:selected {
                background-color: #E3F2FD;
                color: black;
            }
            QComboBox {
                background-color: transparent;
                border: 1px solid #ccc;
                padding: 2px 5px;
            }
            QComboBox:focus {
                border: 1px solid #007AFF;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #E3F2FD;
            }
        """)

        # Intercept double-click via viewport event filter (prevents Qt edit conflicts)
        self.staged_tree.viewport().installEventFilter(self)

        # Initialize with sample data
        self._init_staged_tree()

        layout.addWidget(self.staged_tree, 1)

        # Add/Remove Row buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        add_row_btn = QPushButton("+ ROW")
        add_row_btn.setFont(QFont("SF Pro Display", 10))
        add_row_btn.clicked.connect(self._add_staged_phase)
        btn_layout.addWidget(add_row_btn)

        del_row_btn = QPushButton("- ROW")
        del_row_btn.setFont(QFont("SF Pro Display", 10))
        del_row_btn.clicked.connect(self._delete_staged_phase)
        btn_layout.addWidget(del_row_btn)

        layout.addLayout(btn_layout)

        group.setLayout(layout)
        return group

    # ── Tree core methods ──────────────────────────────────────────

    def _init_staged_tree(self):
        """Initialize staged tree with sample phase hierarchy"""
        sample_data = [
            ['Initial phase', '', 'K0 procedure', 'Phreatic', '-'],
            ['Phase_1', 'Initial phase', 'Plastic', 'Phreatic', 'TRUE'],
            ['Phase_2', 'Phase_1', 'Plastic', 'Phreatic', '-'],
            ['Phase_3', 'Phase_2', 'Plastic', 'Phreatic', '-'],
            ['Phase_4', 'Phase_3', 'Plastic', 'Phreatic', '-'],
            ['Phase_5', 'Phase_4', 'Safety', 'Phreatic', 'TRUE'],
            ['Phase_6', 'Phase_4', 'Plastic', 'Phreatic', '-'],
            ['Phase_7', 'Phase_6', 'Safety', 'Phreatic', 'TRUE'],
        ]
        self._build_tree_from_flat_data(sample_data)

    def _setup_tree_item(self, parent, phase_name,
                         calc_type='Plastic', pore_pressure='Phreatic',
                         reset_disp='-'):
        """Create a QTreeWidgetItem with QComboBox widgets for columns 1-3.

        Args:
            parent: QTreeWidget (for top-level) or QTreeWidgetItem (for child)
        Returns:
            The newly created QTreeWidgetItem
        """
        item = QTreeWidgetItem(parent)
        item.setText(0, phase_name)
        item.setFont(0, QFont("SF Pro Display", 10))

        # Tooltip: show parent connection
        if isinstance(parent, QTreeWidgetItem):
            item.setToolTip(0, f"Parent: {parent.text(0)}  (double-click to change)")
        else:
            item.setToolTip(0, "Root phase")

        # Column 0: editable via F2
        item.setFlags(
            item.flags()
            | Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEnabled
        )

        # Column 1: Calculation Type
        calc_combo = QComboBox()
        if phase_name.lower() == 'initial phase':
            calc_combo.addItems(list(self.INITIAL_PHASE_CALC_TYPE.keys()))
            calc_combo.setCurrentText(
                calc_type if calc_type in self.INITIAL_PHASE_CALC_TYPE else 'K0 procedure')
        else:
            calc_combo.addItems(list(self.PHASE_CALC_TYPE.keys()))
            calc_combo.setCurrentText(
                calc_type if calc_type in self.PHASE_CALC_TYPE else 'Plastic')
        self._style_combobox(calc_combo)
        self.staged_tree.setItemWidget(item, 1, calc_combo)

        # Column 2: Pore pressure
        pore_combo = QComboBox()
        pore_combo.addItem('-')
        pore_combo.addItems(list(self.PORE_PRESSURE_CALC_TYPE.keys()))
        if calc_type == 'Safety':
            pore_combo.setCurrentText('-')
            pore_combo.setEnabled(False)
        else:
            pore_combo.setCurrentText(
                pore_pressure if pore_pressure in self.PORE_PRESSURE_CALC_TYPE else 'Phreatic')
        self._style_combobox(pore_combo)
        self.staged_tree.setItemWidget(item, 2, pore_combo)

        # Connect calc_type → pore_pressure update
        calc_combo.currentTextChanged.connect(
            lambda text, itm=item: self._on_calc_type_changed_tree(itm, text)
        )

        # Column 3: Reset displacements
        reset_combo = QComboBox()
        reset_combo.addItems(list(self.RESET_DISPLACEMENTS.keys()))
        reset_combo.setCurrentText(
            reset_disp if reset_disp in self.RESET_DISPLACEMENTS else '-')
        self._style_combobox(reset_combo)
        self.staged_tree.setItemWidget(item, 3, reset_combo)

        return item

    def _build_tree_from_flat_data(self, flat_data):
        """Build tree hierarchy from flat list [[phase, link, calc, pore, reset], ...]"""
        self.staged_tree.clear()
        if not flat_data:
            return

        # Build parent→children mapping
        children_map = {}  # parent_name → [child_row_data, ...]
        root_data = None

        for row in flat_data:
            phase_name = row[0] if len(row) > 0 else ''
            link = row[1] if len(row) > 1 else ''
            if not phase_name:
                continue
            if not link or link.strip() == '':
                root_data = row
            else:
                children_map.setdefault(link, []).append(row)

        if not root_data:
            root_data = flat_data[0]

        def add_children(parent_item, parent_name):
            for child_row in children_map.get(parent_name, []):
                child_name = child_row[0]
                calc = child_row[2] if len(child_row) > 2 else 'Plastic'
                pore = child_row[3] if len(child_row) > 3 else 'Phreatic'
                reset = child_row[4] if len(child_row) > 4 else '-'
                child_item = self._setup_tree_item(
                    parent_item, child_name, calc, pore, reset)
                add_children(child_item, child_name)

        # Create root
        root_name = root_data[0]
        root_calc = root_data[2] if len(root_data) > 2 else 'K0 procedure'
        root_pore = root_data[3] if len(root_data) > 3 else 'Phreatic'
        root_reset = root_data[4] if len(root_data) > 4 else '-'
        root_item = self._setup_tree_item(
            self.staged_tree, root_name, root_calc, root_pore, root_reset)
        add_children(root_item, root_name)

        self.staged_tree.expandAll()

    def _collect_phases_from_tree(self):
        """Depth-first traversal → list of dicts for script generation & save."""
        result = []

        def walk(item, parent_name):
            phase_name = item.text(0)
            calc_combo = self.staged_tree.itemWidget(item, 1)
            pore_combo = self.staged_tree.itemWidget(item, 2)
            reset_combo = self.staged_tree.itemWidget(item, 3)

            result.append({
                'name': phase_name,
                'link': parent_name,
                'calc_type': calc_combo.currentText() if calc_combo else '',
                'pore_pressure': pore_combo.currentText() if pore_combo else '',
                'reset_disp': reset_combo.currentText() if reset_combo else '',
            })
            for i in range(item.childCount()):
                walk(item.child(i), phase_name)

        for i in range(self.staged_tree.topLevelItemCount()):
            walk(self.staged_tree.topLevelItem(i), '')

        return result

    # ── Interaction methods ────────────────────────────────────────

    def _show_parent_selection_dialog(self, item):
        """Popup dialog with a tree view to select a new parent phase.

        Shows the full phase hierarchy.  Self + descendants are greyed out
        and cannot be selected.  OK is disabled when nothing valid is
        highlighted — so Cancel / OK are always safe (no data loss).
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Select Parent for '{item.text(0)}'")
        dialog.setMinimumSize(400, 420)
        dlg_layout = QVBoxLayout(dialog)

        # Current parent info
        current_parent = item.parent()
        current_parent_name = current_parent.text(0) if current_parent else "(root)"
        info_label = QLabel(
            f"<b>{item.text(0)}</b>  →  current parent: "
            f"<span style='color:#007AFF'>{current_parent_name}</span>")
        info_label.setFont(QFont("SF Pro Display", 10))
        dlg_layout.addWidget(info_label)

        hint = QLabel("Click to select a new parent phase:")
        hint.setFont(QFont("SF Pro Display", 9))
        hint.setStyleSheet("color: #8E8E93;")
        dlg_layout.addWidget(hint)

        # ── Dialog tree (mirrors main tree hierarchy) ──
        dialog_tree = QTreeWidget()
        dialog_tree.setHeaderHidden(True)
        dialog_tree.setFont(QFont("SF Pro Display", 10))
        dialog_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        dialog_tree.setStyleSheet("""
            QTreeWidget {
                background-color: white;
                border: 1px solid #D1D1D6;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 4px 8px;
                min-height: 26px;
            }
            QTreeWidget::item:selected {
                background-color: #007AFF;
                color: white;
            }
            QTreeWidget::item:hover:!selected {
                background-color: #E3F2FD;
            }
            QTreeWidget::branch { background: white; }
        """)
        dlg_layout.addWidget(dialog_tree)

        # Excluded: self + all descendants (cannot be parents)
        excluded = {item.text(0)}
        excluded.update(self._get_all_descendants(item))

        # Map dialog-tree items → main-tree items
        main_items = {}   # phase_name → main QTreeWidgetItem

        def collect_main(tree_item):
            main_items[tree_item.text(0)] = tree_item
            for i in range(tree_item.childCount()):
                collect_main(tree_item.child(i))

        for i in range(self.staged_tree.topLevelItemCount()):
            collect_main(self.staged_tree.topLevelItem(i))

        # Build mirror tree in dialog
        dialog_item_map = {}  # phase_name → dialog QTreeWidgetItem
        pre_select_item = None

        def build_mirror(source_item, dialog_parent):
            nonlocal pre_select_item
            name = source_item.text(0)
            d_item = QTreeWidgetItem(dialog_parent)
            dialog_item_map[name] = d_item

            if name in excluded:
                # Grey out — enabled (so children stay expandable) but NOT selectable
                d_item.setText(0, f"{name}  (not available)")
                d_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                d_item.setForeground(0, QColor('#BBBBBB'))
            else:
                d_item.setText(0, name)
                d_item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable)

            # Pre-select current parent
            if current_parent and name == current_parent.text(0):
                pre_select_item = d_item

            for i in range(source_item.childCount()):
                build_mirror(source_item.child(i), d_item)

        for i in range(self.staged_tree.topLevelItemCount()):
            build_mirror(self.staged_tree.topLevelItem(i), dialog_tree)

        dialog_tree.expandAll()

        if pre_select_item:
            dialog_tree.setCurrentItem(pre_select_item)
            dialog_tree.scrollToItem(pre_select_item)

        # ── Buttons with OK guarded by selection ──
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel)
        ok_btn = button_box.button(QDialogButtonBox.StandardButton.Ok)

        def _update_ok_state():
            sel = dialog_tree.selectedItems()
            if sel:
                name = sel[0].text(0)
                # Valid only if selectable (not in excluded set)
                ok_btn.setEnabled(name not in excluded
                                  and not name.endswith('(not available)'))
            else:
                ok_btn.setEnabled(False)

        dialog_tree.itemSelectionChanged.connect(_update_ok_state)
        _update_ok_state()  # initial state

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dlg_layout.addWidget(button_box)

        # ── Execute dialog ──
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return  # Cancel — nothing changes

        selected = dialog_tree.selectedItems()
        if not selected:
            return  # Nothing selected — safe no-op

        # Extract clean name (strip "(not available)" suffix if any)
        raw_name = selected[0].text(0).split('  (')[0]
        if raw_name in excluded:
            return  # Extra guard

        new_parent_item = main_items.get(raw_name)
        if not new_parent_item:
            return

        # Skip if same parent (no-op)
        if new_parent_item == current_parent:
            return

        self._reparent_item(item, new_parent_item)

    def _reparent_item(self, item, new_parent_item):
        """Move item (and its subtree) under a new parent.

        Strategy: collect ALL data → change the one link → rebuild entire tree.
        This avoids takeChild / setItemWidget issues that lose children.
        """
        phase_name = item.text(0)
        new_parent_name = new_parent_item.text(0)

        # 1. Snapshot every phase in the tree
        all_phases = self._collect_phases_from_tree()

        # 2. Change only the moved phase's parent link
        for entry in all_phases:
            if entry['name'] == phase_name:
                entry['link'] = new_parent_name
                break

        # 3. Convert to flat format and rebuild the whole tree
        flat_data = [
            [p['name'], p['link'], p['calc_type'],
             p['pore_pressure'], p['reset_disp']]
            for p in all_phases
        ]
        self._build_tree_from_flat_data(flat_data)

    # ── Helper methods ─────────────────────────────────────────────

    def _on_calc_type_changed_tree(self, item, calc_type):
        """Update Pore pressure combo based on Calculation Type for a tree item"""
        pore_combo = self.staged_tree.itemWidget(item, 2)
        if not pore_combo:
            return
        if calc_type == 'Safety':
            pore_combo.setCurrentText('-')
            pore_combo.setEnabled(False)
        else:
            pore_combo.setEnabled(True)
            if pore_combo.currentText() == '-':
                pore_combo.setCurrentText('Phreatic')

    def _get_all_descendants(self, item):
        """Return set of all descendant phase names"""
        descendants = set()
        for i in range(item.childCount()):
            child = item.child(i)
            descendants.add(child.text(0))
            descendants.update(self._get_all_descendants(child))
        return descendants

    def _count_descendants(self, item):
        """Count total descendants recursively"""
        count = item.childCount()
        for i in range(item.childCount()):
            count += self._count_descendants(item.child(i))
        return count

    def _get_next_phase_number(self):
        """Find highest Phase_N number in tree and return N+1"""
        max_num = 0

        def scan(item):
            nonlocal max_num
            match = re.match(r'^Phase_(\d+)$', item.text(0))
            if match:
                max_num = max(max_num, int(match.group(1)))
            for i in range(item.childCount()):
                scan(item.child(i))

        for i in range(self.staged_tree.topLevelItemCount()):
            scan(self.staged_tree.topLevelItem(i))
        return max_num + 1

    def _find_item_by_name(self, name):
        """Search tree for item with matching phase name"""
        def search(item):
            if item.text(0) == name:
                return item
            for i in range(item.childCount()):
                found = search(item.child(i))
                if found:
                    return found
            return None

        for i in range(self.staged_tree.topLevelItemCount()):
            found = search(self.staged_tree.topLevelItem(i))
            if found:
                return found
        return None

    # ── Add / Delete phase ─────────────────────────────────────────

    def _add_staged_phase(self):
        """Add a new phase as child of selected node (or root if none selected)"""
        selected = self.staged_tree.currentItem()

        if selected is None:
            if self.staged_tree.topLevelItemCount() == 0:
                # Empty tree — create Initial phase as root
                self._setup_tree_item(
                    self.staged_tree, 'Initial phase',
                    'K0 procedure', 'Phreatic', '-')
                self.staged_tree.expandAll()
                return
            selected = self.staged_tree.topLevelItem(0)

        phase_name = f"Phase_{self._get_next_phase_number()}"
        new_item = self._setup_tree_item(selected, phase_name, 'Plastic', 'Phreatic', '-')
        selected.setExpanded(True)
        self.staged_tree.setCurrentItem(new_item)

    def _delete_staged_phase(self):
        """Delete selected phase and all its children"""
        selected = self.staged_tree.currentItem()
        if not selected:
            QMessageBox.information(self, "Info", "Please select a phase to delete.")
            return

        if selected.text(0).lower() == 'initial phase':
            QMessageBox.warning(
                self, "Warning",
                "Cannot delete the Initial phase.")
            return

        child_count = self._count_descendants(selected)
        if child_count > 0:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"'{selected.text(0)}' has {child_count} child phase(s).\n"
                f"All children will also be deleted. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return

        parent = selected.parent()
        if parent:
            parent.removeChild(selected)
        else:
            idx = self.staged_tree.indexOfTopLevelItem(selected)
            self.staged_tree.takeTopLevelItem(idx)

    # ── Output Script table ──────────────────────────────────────

    # Material Type dropdown options for Output table
    OUTPUT_MATERIAL_TYPES = [
        'and interfaces',
        'Discontinuities',
        'Plates',
        'Geogrids',
        'Embedded beams',
        'Cables',
        'Anchors',
    ]

    # Column layout for the output table
    # Phase | Deformations(3) | γₛ | Stresses(6) | Pore Pressure(2) | Material(2) | Force(3) | Scaling(4) | Scale
    OUTPUT_COLUMNS = [
        'Phase',                                  # 0
        '|u|', 'ux', 'uy',                       # 1-3   Deformations
        'γₛ',                                     # 4     TotalDeviatoricStrain
        "σ'xx", "σ'yy",                          # 5-6   Effective Stress
        'σxx', 'σyy',                            # 7-8   Total Stress
        'τxy',                                    # 9     Shear Stress
        'Rel.τ',                                  # 10    RelativeShearStress
        'PExcess', 'PActive',                     # 11-12 Pore Pressure
        'Name', 'Type',                           # 13-14 Material
        'M', 'Q', 'N',                           # 15-17 Force (kN)
        'Automation',                             # 18    Scaling - auto checkbox
        'Min.', 'Max.', 'Interval',              # 19-21 Scaling - manual values
        'Scale',                                  # 22    Image size
    ]

    # Columns that use checkboxes (by index)
    OUTPUT_CHECK_COLS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18}
    # Text-editable: Phase(0), Name(13), Min(19), Max(20), Interval(21), Scale(22)
    # Dropdown: Type(14)

    # Column widths (shared between header table and data table)
    _OUTPUT_COL_WIDTHS = [
        200,           # 0   Phase
        50, 50, 50,     # 1-3   |u|, ux, uy
        50,          # 4   γₛ
        50, 50,        # 5-6   σ'xx, σ'yy
        50, 50,        # 7-8   σxx, σyy
        50,          # 9   τxy
        50,          # 10  Rel.τ
        80,80,         # 11-12 PExcess, PActive
        150, 150,    # 13-14 Name, Type
        50,50,50,     # 15-17 M, Q, N
        80,             # 18  Automation
        50, 50, 70,   # 19-21 Min., Max., Interval
        80,             # 22  Scale
    ]

    def _create_output_script_section(self):
        """Create output script table with multi-level header and checkboxes"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Hint
        hint = QLabel("Name = PLAXIS element name (e.g. Plate_1, EmbeddedBeam_7)  |  ใส่ '-' สำหรับ Soil plot")
        hint.setFont(QFont("SF Pro Display", 9))
        hint.setStyleSheet("color: #8E8E93; margin-bottom: 4px;")
        layout.addWidget(hint)

        # ── Multi-level group header (separate read-only table) ──
        self._output_header_tbl = self._build_output_header()
        layout.addWidget(self._output_header_tbl)

        # ── Data table (horizontal header hidden, replaced by header table) ──
        self.output_table = QTableWidget()
        self.output_table.setColumnCount(len(self.OUTPUT_COLUMNS))
        self.output_table.setFont(QFont("SF Pro Display", 9))
        self.output_table.horizontalHeader().setVisible(False)
        self.output_table.verticalHeader().setVisible(False)
        self.output_table.verticalHeader().setDefaultSectionSize(30)

        for col, w in enumerate(self._OUTPUT_COL_WIDTHS):
            self.output_table.setColumnWidth(col, w)

        # Table styling
        self.output_table.setStyleSheet("""
            QTableWidget {
                border-top: none;
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
            QComboBox {
                background-color: transparent;
                border: 1px solid #ccc;
                padding: 2px 5px;
            }
            QComboBox:focus {
                border: 1px solid #007AFF;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: rgba(0, 122, 255, 0.15);
            }
        """)

        # Initialize with sample rows
        sample_rows = [
            {'phase': 'Loading', 'name': 'Plate_1', 'type': 'Plates',
             'checks': {15: True, 16: True}, 'scale': '1600x900'},
            {'phase': 'Loading', 'name': 'EmbeddedBeam_6', 'type': 'Embedded beams',
             'checks': {15: True, 16: True}, 'scale': '1600x900'},
            {'phase': 'Loading', 'name': 'EmbeddedBeam_7', 'type': 'Embedded beams',
             'checks': {15: True}, 'scale': '1600x900'},
            {'phase': 'Loading', 'name': 'EmbeddedBeam_1', 'type': 'Embedded beams',
             'checks': {15: True}, 'scale': '1600x900'},
            {'phase': 'LWL_FS', 'name': '-', 'type': '',
             'checks': {1: True, 4: True, 7: True, 18: True}, 'scale': '1600x900'},
            {'phase': 'RDD_FS', 'name': '-', 'type': '',
             'checks': {1: True, 4: True, 7: True, 18: True}, 'scale': '1600x900'},
        ]

        self.output_table.setRowCount(len(sample_rows))
        for row, data in enumerate(sample_rows):
            self._setup_output_row(row, data)

        layout.addWidget(self.output_table, 1)

        # Sync horizontal scroll between header and data table
        self.output_table.horizontalScrollBar().valueChanged.connect(
            self._output_header_tbl.horizontalScrollBar().setValue
        )

        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 6, 0, 0)
        btn_layout.addStretch()

        add_btn = QPushButton("+ ROW")
        add_btn.setFont(QFont("SF Pro Display", 10))
        add_btn.clicked.connect(self._add_output_row)
        btn_layout.addWidget(add_btn)

        del_btn = QPushButton("- ROW")
        del_btn.setFont(QFont("SF Pro Display", 10))
        del_btn.clicked.connect(self._delete_output_row)
        btn_layout.addWidget(del_btn)

        layout.addLayout(btn_layout)

        return container

    def _build_output_header(self):
        """Build a 3-row merged header table for the output table.

        Col layout (23 cols):
        0:Phase | 1-3:Deformations | 4:γₛ | 5-10:Stresses | 11-12:PorePressure
        | 13-14:Material | 15-17:Force | 18-21:Scaling | 22:Scale

        Row 0: Phase(3r) | Deformations(3c) | γₛ(3r) | Stresses(6c) | Pore Pressure(2c) | Material(2c) | Force(3c) | Scaling(4c) | Scale(3r)
        Row 1:           | |u| ux uy (2r)   |        | Effective(2c) Total(2c) τxy(2r) Rel.τ(2r) | PEx(2r) PAc(2r) | Name(2r) Type(2r) | M Q N(2r) | Auto(2r) Manual(3c) |
        Row 2:           |                   |        | σ'xx σ'yy | σxx σyy |   |   |   |   |   |   |   |   |          | Min Max Interval |
        """
        ncols = len(self.OUTPUT_COLUMNS)
        tbl = QTableWidget(3, ncols)
        tbl.horizontalHeader().setVisible(False)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tbl.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        row_h = 22
        tbl.verticalHeader().setDefaultSectionSize(row_h)
        tbl.setFixedHeight(3 * row_h + 2)

        for col, w in enumerate(self._OUTPUT_COL_WIDTHS):
            tbl.setColumnWidth(col, w)

        # Styles
        grp = "background-color:#E8E8ED; font-weight:bold;"
        sub = "background-color:#F2F2F7;"
        leaf = "background-color:#F8F8FA;"

        def cell(text, style=""):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFont(QFont("SF Pro Display", 8, QFont.Weight.Bold))
            if style:
                item.setBackground(QColor(style.split(':')[1].split(';')[0]))
            return item

        def put(r, c, text, rs=1, cs=1, st=grp):
            """Place a header cell with optional span"""
            if rs > 1 or cs > 1:
                tbl.setSpan(r, c, rs, cs)
            tbl.setItem(r, c, cell(text, st))

        # ── Row 0: Top-level group headers ──
        put(0, 0, "Phase", 3, 1, grp)            # col 0
        put(0, 1, "Deformations", 1, 3, grp)     # cols 1-3
        put(0, 4, "γₛ", 3, 1, grp)               # col 4
        put(0, 5, "Stresses", 1, 6, grp)         # cols 5-10
        put(0, 11, "Pore\nPressure", 1, 2, grp)  # cols 11-12
        put(0, 13, "Material", 1, 2, grp)        # cols 13-14
        put(0, 15, "Force (kN)", 1, 3, grp)      # cols 15-17
        put(0, 18, "Scaling", 1, 4, grp)         # cols 18-21
        put(0, 22, "Scale", 3, 1, grp)           # col 22

        # ── Row 1: Sub-headers ──
        put(1, 1, "|u|", 2, 1, sub)              # col 1
        put(1, 2, "ux", 2, 1, sub)               # col 2
        put(1, 3, "uy", 2, 1, sub)               # col 3
        put(1, 5, "Effective", 1, 2, sub)         # cols 5-6
        put(1, 7, "Total", 1, 2, sub)            # cols 7-8
        put(1, 9, "τxy", 2, 1, sub)              # col 9
        put(1, 10, "Rel.τ", 2, 1, sub)           # col 10
        put(1, 11, "PExcess", 2, 1, sub)         # col 11
        put(1, 12, "PActive", 2, 1, sub)         # col 12
        put(1, 13, "Name", 2, 1, sub)            # col 13
        put(1, 14, "Type", 2, 1, sub)            # col 14
        put(1, 15, "M", 2, 1, sub)               # col 15
        put(1, 16, "Q", 2, 1, sub)               # col 16
        put(1, 17, "N", 2, 1, sub)               # col 17
        put(1, 18, "Auto", 2, 1, sub)            # col 18
        put(1, 19, "Manual", 1, 3, sub)          # cols 19-21

        # ── Row 2: Leaf headers ──
        put(2, 5, "σ'xx", 1, 1, leaf)            # col 5
        put(2, 6, "σ'yy", 1, 1, leaf)            # col 6
        put(2, 7, "σxx", 1, 1, leaf)             # col 7
        put(2, 8, "σyy", 1, 1, leaf)             # col 8
        put(2, 19, "Min.", 1, 1, leaf)            # col 19
        put(2, 20, "Max.", 1, 1, leaf)            # col 20
        put(2, 21, "Interval", 1, 1, leaf)        # col 21

        # Overall style
        tbl.setStyleSheet("""
            QTableWidget {
                border: 1px solid #D1D1D6;
                border-bottom: none;
                gridline-color: #D1D1D6;
            }
        """)

        return tbl

    def _setup_output_row(self, row, data=None):
        """Setup a single row in the output table with checkboxes and dropdown"""
        if data is None:
            data = {'phase': '', 'name': '', 'type': '', 'checks': {},
                    'scale_min': '', 'scale_max': '', 'scale_interval': '',
                    'scale': '1600x900'}

        for col in range(len(self.OUTPUT_COLUMNS)):
            if col in self.OUTPUT_CHECK_COLS:
                # Checkbox column (includes col 13 = Automation)
                item = QTableWidgetItem()
                item.setFlags(
                    Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                )
                checked = data.get('checks', {}).get(col, False)
                item.setCheckState(
                    Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
                )
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.output_table.setItem(row, col, item)

            elif col == 0:  # Phase
                item = QTableWidgetItem(data.get('phase', ''))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.output_table.setItem(row, col, item)

            elif col == 13:  # Name
                item = QTableWidgetItem(data.get('name', ''))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.output_table.setItem(row, col, item)

            elif col == 14:  # Type (dropdown)
                combo = QComboBox()
                combo.addItem('')  # Empty option
                combo.addItems(self.OUTPUT_MATERIAL_TYPES)
                combo.setCurrentText(data.get('type', ''))
                self._style_combobox(combo)
                self.output_table.setCellWidget(row, col, combo)

            elif col == 19:  # Min. (Manual Scaling)
                item = QTableWidgetItem(data.get('scale_min', ''))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.output_table.setItem(row, col, item)

            elif col == 20:  # Max. (Manual Scaling)
                item = QTableWidgetItem(data.get('scale_max', ''))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.output_table.setItem(row, col, item)

            elif col == 21:  # Interval (Manual Scaling)
                item = QTableWidgetItem(data.get('scale_interval', ''))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.output_table.setItem(row, col, item)

            elif col == 22:  # Scale (image size)
                item = QTableWidgetItem(data.get('scale', '1600x900'))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.output_table.setItem(row, col, item)

    def _add_output_row(self):
        """Add new row to output table"""
        row = self.output_table.rowCount()
        self.output_table.insertRow(row)
        self._setup_output_row(row)

    def _delete_output_row(self):
        """Delete selected row from output table"""
        current = self.output_table.currentRow()
        if current >= 0:
            self.output_table.removeRow(current)
        elif self.output_table.rowCount() > 0:
            self.output_table.removeRow(self.output_table.rowCount() - 1)

    def _create_output_preview_section(self):
        """Create preview area for the generated output script"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        hint = QLabel("Generated PLAXIS Output script preview")
        hint.setFont(QFont("SF Pro Display", 9))
        hint.setStyleSheet("color: #8E8E93; margin-bottom: 4px;")
        layout.addWidget(hint)

        self.output_preview_text = QTextEdit()
        self.output_preview_text.setFont(QFont("Consolas", 10))
        self.output_preview_text.setReadOnly(True)
        self.output_preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        self.output_preview_text.setPlaceholderText(
            "# Output script will be generated here...\n"
            "# Click 'Generate Output Script' to preview")
        layout.addWidget(self.output_preview_text, 1)

        return container

    def _pick_output_dir(self):
        """Let user select the PNG export folder for Output script"""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", self._output_dir)
        if folder:
            self._output_dir = folder
            self._output_dir_label.setText(folder)

    def _run_output_code(self):
        """Preview the generated output script"""
        script = self._generate_output_script()
        self.output_preview_text.setPlainText(script)

    def _save_output_script(self):
        """Save output script to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output Script",
            "plaxis_output.py",
            "Python Files (*.py);;All Files (*)")
        if file_path:
            script = self._generate_output_script()
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(script)
                QMessageBox.information(self, "Success", f"Output script saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save:\n{str(e)}")

    # ── Output table data helpers ──────────────────────────────────

    def _get_output_cell_value(self, row, col):
        """Get value from output table cell (handles items and widgets)"""
        widget = self.output_table.cellWidget(row, col)
        if widget and isinstance(widget, QComboBox):
            return widget.currentText()
        item = self.output_table.item(row, col)
        return item.text() if item else ""

    def _is_output_checked(self, row, col):
        """Check if a checkbox column is checked in output table"""
        item = self.output_table.item(row, col)
        if item:
            return item.checkState() == Qt.CheckState.Checked
        return False

    def _collect_output_rows(self):
        """Collect all output table rows as list of dicts"""
        rows = []
        for row in range(self.output_table.rowCount()):
            phase = self._get_output_cell_value(row, 0).strip()
            if not phase:
                continue
            rows.append({
                'phase': phase,
                'u_tot': self._is_output_checked(row, 1),
                'ux': self._is_output_checked(row, 2),
                'uy': self._is_output_checked(row, 3),
                'total_strain': self._is_output_checked(row, 4),
                'sig_xx_eff': self._is_output_checked(row, 5),
                'sig_yy_eff': self._is_output_checked(row, 6),
                'sig_xx_tot': self._is_output_checked(row, 7),
                'sig_yy_tot': self._is_output_checked(row, 8),
                'sig_xy': self._is_output_checked(row, 9),
                'rel_shear': self._is_output_checked(row, 10),
                'p_excess': self._is_output_checked(row, 11),
                'p_active': self._is_output_checked(row, 12),
                'name': self._get_output_cell_value(row, 13).strip(),
                'type': self._get_output_cell_value(row, 14).strip(),
                'M': self._is_output_checked(row, 15),
                'Q': self._is_output_checked(row, 16),
                'N': self._is_output_checked(row, 17),
                'scaling_auto': self._is_output_checked(row, 18),
                'scale_min': self._get_output_cell_value(row, 19).strip(),
                'scale_max': self._get_output_cell_value(row, 20).strip(),
                'scale_interval': self._get_output_cell_value(row, 21).strip(),
                'scale': self._get_output_cell_value(row, 22).strip() or '1600x900',
            })
        return rows

    # ── Generate Output Script ─────────────────────────────────────

    # PLAXIS Output ResultType mapping
    # Structure type → PLAXIS collection name and ResultTypes prefix
    _STRUCT_MAP = {
        'Plates':          ('Plates',         'Plate'),
        'Embedded beams':  ('EmbeddedBeams',  'EmbeddedBeam'),
        'Geogrids':        ('Geogrids',       'Geogrid'),
        'Anchors':         ('Anchors',        'Anchor'),
        'Cables':          ('Cables',         'Cable'),
        'and interfaces':  ('Interfaces',     'Interface'),
    }

    # Force component → PLAXIS suffix
    _FORCE_SUFFIX = {'M': 'M2D', 'Q': 'Q2D', 'N': 'Nx2D'}

    # Soil result key → PLAXIS ResultTypes.Soil.* attribute
    _SOIL_RESULTS = {
        'u_tot':        'Utot',
        'ux':           'Ux',
        'uy':           'Uy',
        'total_strain': 'TotalDeviatoricStrain',
        'sig_xx_eff':   'SigxxE',
        'sig_yy_eff':   'SigyyE',
        'sig_xx_tot':   'SigxxT',
        'sig_yy_tot':   'SigyyT',
        'sig_xy':       'Sigxy',
        'rel_shear':    'RelativeShearStress',
        'p_excess':     'PExcess',
        'p_active':     'PActive',
    }

    # Friendly label for filenames
    _SOIL_LABELS = {
        'u_tot':        'Utot',
        'ux':           'Ux',
        'uy':           'Uy',
        'total_strain': 'TotalStrain',
        'sig_xx_eff':   'SigxxE',
        'sig_yy_eff':   'SigyyE',
        'sig_xx_tot':   'SigxxT',
        'sig_yy_tot':   'SigyyT',
        'sig_xy':       'Sigxy',
        'rel_shear':    'RelShearStress',
        'p_excess':     'PExcess',
        'p_active':     'PActive',
    }

    def _generate_output_script(self):
        """Generate PLAXIS Output Python script from the output table"""
        rows = self._collect_output_rows()
        if not rows:
            return "# No output rows configured."

        # Indent helper for try block
        I = "    "  # 4-space indent inside try block

        L = []  # script lines
        a = L.append

        # ─── Header ───
        a("# ============================================================")
        a("# PLAXIS Output Script")
        a("# Generated by GeoTech v3.0")
        a("# ============================================================")
        a("")
        a("from plxscripting.easy import *")
        a("import os")
        a("")
        a("try:")

        # ─── Connection ───
        a(f"{I}# ------------------------------------------------------------")
        a(f"{I}# 1. Connect to PLAXIS Output")
        a(f"{I}# ------------------------------------------------------------")
        a(f'{I}password = os.getenv("PLAXIS_PASSWORD")')
        a(f'{I}s_o, g_o = new_server("localhost", 10001, password=password)')
        a(f'{I}print(">>> Connected to PLAXIS Output")')
        a("")

        # ─── Setup ───
        a(f"{I}# ------------------------------------------------------------")
        a(f"{I}# 2. Setup")
        a(f"{I}# ------------------------------------------------------------")
        a(f'{I}output_dir = r"{self._output_dir}"')
        a(f"{I}os.makedirs(output_dir, exist_ok=True)")
        a("")

        # ─── Helper: Legend Settings ───
        a(f"{I}# ------------------------------------------------------------")
        a(f"{I}# 3. Legend Settings Config")
        a(f"{I}# ------------------------------------------------------------")
        a(f"{I}# None = Auto (PLAXIS default per phase)")
        a(f"{I}# value = Manual (set Min/Max)")
        a(f"{I}LEGEND = {{")

        # Build LEGEND dict from all rows
        legend_entries = {}
        for r in rows:
            phase_name = r['phase']
            name_raw = r['name']
            struct_type = r['type']
            is_soil = (not name_raw or name_raw == '-' or not struct_type)
            scale_min = r.get('scale_min', '')
            scale_max = r.get('scale_max', '')

            if is_soil:
                # Soil results → legend key per result type
                for key in self._SOIL_RESULTS:
                    if r.get(key):
                        label = self._SOIL_LABELS[key]
                        legend_key = f"{phase_name}_{label}"
                        min_v = scale_min if scale_min else None
                        max_v = scale_max if scale_max else None
                        legend_entries[legend_key] = (min_v, max_v)
            else:
                # Structure results → legend key per force
                elem_name = name_raw.strip('"')
                for fk in ('M', 'Q', 'N'):
                    if r.get(fk):
                        legend_key = f"{phase_name}_{elem_name}_{fk}"
                        min_v = scale_min if scale_min else None
                        max_v = scale_max if scale_max else None
                        legend_entries[legend_key] = (min_v, max_v)

        for lk, (mn, mx) in legend_entries.items():
            mn_s = mn if mn else 'None'
            mx_s = mx if mx else 'None'
            a(f'{I}    "{lk}": {{"min": {mn_s}, "max": {mx_s}}},')
        a(f"{I}}}")
        a("")

        # ─── Helper functions ───
        a(f"{I}# ------------------------------------------------------------")
        a(f"{I}# 4. Helper functions")
        a(f"{I}# ------------------------------------------------------------")
        a(f"{I}def apply_legend(plot, key):")
        a(f'{I}    """Apply legend settings: None=Auto, value=Manual"""')
        a(f"{I}    cfg = LEGEND.get(key)")
        a(f"{I}    if cfg is None:")
        a(f"{I}        return")
        a(f'{I}    if cfg["min"] is None and cfg["max"] is None:')
        a(f"{I}        return")
        a(f"{I}    try:")
        a(f'{I}        if cfg["min"] is not None:')
        a(f'{I}            plot.LegendSettings.MinValue = cfg["min"]')
        a(f'{I}        if cfg["max"] is not None:')
        a(f'{I}            plot.LegendSettings.MaxValue = cfg["max"]')
        a(f"{I}    except Exception as e:")
        a(f'{I}        print(f"  NOTE: LegendSettings error ({{e}})")')
        a("")

        a(f"{I}def export_plot(plot, filename, legend_key=None, img_w=1600, img_h=900):")
        a(f"{I}    if legend_key:")
        a(f"{I}        apply_legend(plot, legend_key)")
        a(f'{I}    filepath = os.path.join(output_dir, f"{{filename}}.png")')
        a(f"{I}    try:")
        a(f"{I}        plot.export(filepath, img_w, img_h)")
        a(f"{I}        cfg = LEGEND.get(legend_key, {{}})")
        a(f'{I}        mode = "Auto" if (cfg.get("min") is None and cfg.get("max") is None) else f"Manual [{{cfg[\'min\']}} ~ {{cfg[\'max\']}}]"')
        a(f'{I}        print(f"  OK {{filename}}.png  [{{mode}}]")')
        a(f"{I}        return True")
        a(f"{I}    except Exception as e:")
        a(f'{I}        print(f"  FAIL {{filename}}: {{e}}")')
        a(f"{I}        return False")
        a("")

        # ─── Helper: find phase ───
        a(f"{I}def find_phase(name):")
        a(f'{I}    """Find phase by Identification (partial match)"""')
        a(f"{I}    for p in g_o.Phases:")
        a(f"{I}        if name in str(p.Identification):")
        a(f"{I}            return p")
        a(f"{I}    return None")
        a("")

        # ─── Helper: find structure elements by PLAXIS name ───
        a(f"{I}def find_elements(name, collection):")
        a(f'{I}    """Find elements whose Name contains the given name.')
        a(f"{I}    e.g. name='EmbeddedBeam_6' matches 'EmbeddedBeam_6_1'")
        a(f'{I}    """')
        a(f"{I}    results = []")
        a(f"{I}    for elem in collection:")
        a(f"{I}        if name in str(elem.Name):")
        a(f"{I}            results.append(elem)")
        a(f"{I}    return results")
        a("")

        # ─── Collect unique phases ───
        unique_phases = []
        seen_phases = set()
        for r in rows:
            if r['phase'] not in seen_phases:
                unique_phases.append(r['phase'])
                seen_phases.add(r['phase'])

        a(f"{I}# ------------------------------------------------------------")
        a(f"{I}# 5. Get phases")
        a(f"{I}# ------------------------------------------------------------")
        for phase_name in unique_phases:
            var = self._phase_var_name(phase_name)
            a(f'{I}{var} = find_phase("{phase_name}")')
            a(f'{I}print(f"Phase {phase_name}: {{{var}.Identification}}")')
        a("")

        # ─── Process each row ───
        a(f"{I}# ============================================================")
        a(f"{I}# 6. Generate output plots")
        a(f"{I}# ============================================================")
        a("")

        current_phase = None
        for r in rows:
            phase_name = r['phase']
            phase_var = self._phase_var_name(phase_name)
            name_raw = r['name']
            struct_type = r['type']
            scale = r['scale']

            # Parse image size
            if 'x' in scale.lower():
                parts = scale.lower().split('x')
                img_w, img_h = parts[0].strip(), parts[1].strip()
            else:
                img_w, img_h = '1600', '900'

            # Phase header
            if phase_name != current_phase:
                current_phase = phase_name
                a(f"{I}# ══════════════════════════════════════════════════")
                a(f"{I}# PHASE: {phase_name}")
                a(f"{I}# ══════════════════════════════════════════════════")
                a(f'{I}print("\\n" + "=" * 50)')
                a(f'{I}print("PHASE: {phase_name}")')
                a(f'{I}print("=" * 50)')
                a("")

            # ── Case A: Soil result (no material / Name is "-" or empty) ──
            is_soil = (not name_raw or name_raw == '-' or not struct_type)
            has_soil_checks = any(r[k] for k in self._SOIL_RESULTS)

            if is_soil and has_soil_checks:
                a(f'{I}print("\\n[Soil Results]")')
                a(f"{I}try:")
                a(f"{I}    soil_plot = g_o.Plots[0]")
                a(f"{I}    soil_plot.Phase = {phase_var}")
                a("")

                for key, result_attr in self._SOIL_RESULTS.items():
                    if r.get(key):
                        label = self._SOIL_LABELS[key]
                        fname = f"{phase_name}_{label}"
                        legend_key = f"{phase_name}_{label}"
                        a(f"{I}    soil_plot.ResultType = g_o.ResultTypes.Soil.{result_attr}")
                        a(f'{I}    export_plot(soil_plot, "{fname}", "{legend_key}", {img_w}, {img_h})')
                        a("")

                a(f"{I}except Exception as e:")
                a(f'{I}    print(f"  FAIL: {{e}}")')
                a("")

            # ── Case B: Structural result (material specified) ──
            has_force = r['M'] or r['Q'] or r['N']

            if not is_soil and has_force and struct_type:
                elem_name = name_raw.strip('"')
                collection_name, rt_prefix = self._STRUCT_MAP.get(
                    struct_type, ('Plates', 'Plate'))

                a(f'{I}# --- {elem_name} ({struct_type}) ---')
                a(f'{I}print("\\n[{elem_name} - {struct_type}]")')
                a(f"{I}try:")
                a(f'{I}    elems = find_elements("{elem_name}", g_o.{collection_name})')
                a(f"{I}    if not elems:")
                a(f'{I}        print("  WARNING: {elem_name} not found")')
                a(f"{I}    for _i, _elem in enumerate(elems):")
                a(f"{I}        _suffix = f'_{{_i+1}}' if len(elems) > 1 else ''")
                a(f"{I}        _plot = g_o.structureplot(_elem)")
                a(f"{I}        _plot.Phase = {phase_var}")
                a("")

                for force_key in ('M', 'Q', 'N'):
                    if r[force_key]:
                        suffix = self._FORCE_SUFFIX[force_key]
                        legend_key = f"{phase_name}_{elem_name}_{force_key}"
                        a(f"{I}        _plot.ResultType = g_o.ResultTypes.{rt_prefix}.{suffix}")
                        a(f'{I}        export_plot(_plot, f"{phase_name}_{elem_name}{{_suffix}}_{force_key}", "{legend_key}", {img_w}, {img_h})')
                        a("")

                a(f"{I}except Exception as e:")
                a(f'{I}    print(f"  FAIL: {{e}}")')
                a("")

        # ─── Summary ───
        a(f"{I}# ============================================================")
        a(f"{I}# Summary")
        a(f"{I}# ============================================================")
        a(f'{I}print("\\n" + "=" * 50)')
        a(f'{I}print("SUMMARY")')
        a(f'{I}print("=" * 50)')
        a(f'{I}print(f"Output folder: {{output_dir}}")')
        a("")
        a(f"{I}png_files = sorted(f for f in os.listdir(output_dir) if f.endswith('.png'))")
        a(f'{I}print(f"\\nTotal PNG: {{len(png_files)}}")')
        a("")
        a(f"{I}for f in png_files:")
        a(f"{I}    size = os.path.getsize(os.path.join(output_dir, f))")
        a(f'{I}    print(f"  {{f}} ({{size:,}} bytes)")')

        # ─── Outer except + finally ───
        a("")
        a("except Exception as e:")
        a('    print(f"\\n!!! ERROR: {e}")')
        a("    import traceback")
        a("    traceback.print_exc()")
        a("")
        a('print("\\n" + "=" * 50)')
        a('input("Press Enter to close...")')

        return '\n'.join(L)

    @staticmethod
    def _phase_var_name(phase_name):
        """Convert phase name to a valid Python variable name"""
        var = phase_name.replace(' ', '_').replace('-', '_')
        var = ''.join(c for c in var if c.isalnum() or c == '_')
        if var[0].isdigit():
            var = 'p_' + var
        return f"phase_{var}"

    def _create_preview_section(self):
        """Create preview section for Python script"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Hint label
        hint = QLabel("Click 'Generate Script' to preview the PLAXIS Python script")
        hint.setFont(QFont("SF Pro Display", 9))
        hint.setStyleSheet("color: #8E8E93; margin-bottom: 4px;")
        layout.addWidget(hint)

        # Preview text area
        self.preview_text = QTextEdit()
        self.preview_text.setFont(QFont("Consolas", 10))
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        self.preview_text.setPlaceholderText("# Python script will be generated here...\n# Click 'Generate Script' in the top bar to preview")
        layout.addWidget(self.preview_text, 1)

        return container

    def _load_from_module4(self):
        """Load layer data from Module 4"""
        if not self.module4:
            QMessageBox.warning(self, "Warning", "Module 4 reference not available.")
            return

        try:
            # Get line_table from Module 4
            line_table = self.module4.line_table
            row_count = line_table.rowCount()

            # Count valid rows (rows with data)
            valid_rows = []
            for row in range(row_count):
                from_item = line_table.item(row, 0)
                to_item = line_table.item(row, 1)
                if from_item and to_item and from_item.text().strip() and to_item.text().strip():
                    valid_rows.append(row)

            if not valid_rows:
                QMessageBox.warning(self, "Warning", "No data found in Module 4.\nPlease enter data in Module 4 first.")
                return

            # Set row count in layer table
            self.layer_table.setRowCount(len(valid_rows))

            # Column mapping from Module 4: From(0), To(1), SPT(2), γsat(3), Su(4), ϕ'(5), E/E'(6), K0(7), Soil Type(8), Consistency(9)

            for idx, m4_row in enumerate(valid_rows):
                # Get values from Module 4
                from_val = line_table.item(m4_row, 0).text() if line_table.item(m4_row, 0) else ''
                to_val = line_table.item(m4_row, 1).text() if line_table.item(m4_row, 1) else ''
                gamma_sat = line_table.item(m4_row, 3).text() if line_table.item(m4_row, 3) else ''
                su_val = line_table.item(m4_row, 4).text() if line_table.item(m4_row, 4) else ''
                phi_val = line_table.item(m4_row, 5).text() if line_table.item(m4_row, 5) else ''
                e_val = line_table.item(m4_row, 6).text() if line_table.item(m4_row, 6) else ''

                # Get soil type from combo box in column 8
                soil_type_combo = line_table.cellWidget(m4_row, 8)
                soil_type = soil_type_combo.currentText() if soil_type_combo else ''

                # Get consistency from column 9
                consistency_item = line_table.item(m4_row, 9)
                consistency = consistency_item.text() if consistency_item else ''

                # Generate layer name: "01 Sand, Medium Dense" format
                layer_num = str(idx + 1).zfill(2)
                if soil_type and consistency:
                    layer_name = f"{layer_num} {soil_type}, {consistency}"
                elif soil_type:
                    layer_name = f"{layer_num} {soil_type}"
                else:
                    layer_name = f"{layer_num} Layer"

                # Determine Rinter based on soil type (Clay=0.5, Sand=0.8)
                rinter = '0.5' if soil_type == 'Clay' else '0.8'

                # Determine drainage type (Clay=Undrained, Sand=Drained)
                drainage = 'Undrained A' if soil_type == 'Clay' else 'Drained'

                # Determine permeability class based on soil type
                perm_class = 'Clay' if soil_type == 'Clay' else 'Sand'

                # Setup the row with widgets first
                self._setup_layer_row(idx, (0, 0))

                # Now set values
                # Column 0: From
                self.layer_table.item(idx, 0).setText(from_val)

                # Column 1: To
                self.layer_table.item(idx, 1).setText(to_val)

                # Column 2: Name
                self.layer_table.item(idx, 2).setText(layer_name)

                # Column 3: Soil Model (dropdown) - keep default Mohr-Coulomb

                # Column 4: Drainage Type (dropdown)
                drainage_combo = self.layer_table.cellWidget(idx, 4)
                if drainage_combo:
                    drainage_combo.setCurrentText(drainage)

                # Column 6: γsat (set first, then γunsat will auto-calculate)
                self.layer_table.item(idx, 6).setText(gamma_sat)

                # Column 5: γunsat (auto-calculated from γsat - 1)
                if gamma_sat:
                    try:
                        gamma_unsat = float(gamma_sat) - 1
                        self.layer_table.item(idx, 5).setText(str(gamma_unsat))
                    except ValueError:
                        pass

                # Column 7: Void Ratio - keep Default

                # Column 8: Eref
                self.layer_table.item(idx, 8).setText(e_val)

                # Column 9: ν(nu) - leave empty for user

                # Column 10: Su
                self.layer_table.item(idx, 10).setText(su_val)

                # Column 11: cref - leave empty for user

                # Column 12: phi
                self.layer_table.item(idx, 12).setText(phi_val)

                # Column 13: Classification - keep USDA

                # Column 14: Permeabilities (dropdown)
                perm_combo = self.layer_table.cellWidget(idx, 14)
                if perm_combo:
                    perm_combo.setCurrentText(perm_class)

                # Column 15: Defaults method - keep From grain size

                # Column 16: Rinter
                self.layer_table.item(idx, 16).setText(rinter)

                # Column 17: K0 - keep Automatic

            QMessageBox.information(self, "Success", f"Loaded {len(valid_rows)} layers from Module 4.\nγunsat auto-calculated from γsat.\nPlease fill in remaining values (ν, cref, etc.)")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data from Module 4:\n{str(e)}")

    def _add_layer_row(self):
        """Add new row to layer table"""
        row_count = self.layer_table.rowCount()
        self.layer_table.insertRow(row_count)
        self._setup_layer_row(row_count, (0, 0))

    def _delete_layer_row(self):
        """Delete selected row from layer table"""
        current_row = self.layer_table.currentRow()
        if current_row >= 0:
            self.layer_table.removeRow(current_row)
        else:
            # Delete last row if no selection
            if self.layer_table.rowCount() > 1:
                self.layer_table.removeRow(self.layer_table.rowCount() - 1)

    def _add_staged_row(self):
        """Legacy method — delegates to new tree-based add"""
        self._add_staged_phase()

    def _generate_script(self):
        """Generate PLAXIS Python script from table data"""
        lines = []

        # ============================================================
        # Header - Connection (unchanged as requested)
        # ============================================================
        lines.append("# ============================================================")
        lines.append("# PLAXIS Python Script")
        lines.append("# Generated by GeoTech v3.0")
        lines.append("# ============================================================")
        lines.append("")
        lines.append("from plxscripting.easy import *")
        lines.append("import os")
        lines.append("")
        lines.append("# ------------------------------------------------------------")
        lines.append("# Connect to PLAXIS")
        lines.append("# ------------------------------------------------------------")
        lines.append('password = os.getenv("PLAXIS_PASSWORD")')
        lines.append("s_i, g_i = new_server('localhost', 10000, password=password)")
        lines.append('print("Connected to PLAXIS")')
        lines.append("")

        # ============================================================
        # Collect layer data
        # ============================================================
        layers = []
        for row in range(self.layer_table.rowCount()):
            from_val = self._get_layer_cell_value(row, 0)
            to_val = self._get_layer_cell_value(row, 1)

            # Skip empty rows
            if not from_val or not to_val:
                continue

            layer_data = {
                'from': from_val,
                'to': to_val,
                'name': self._get_layer_cell_value(row, 2) or f"Layer_{row+1}",
                'soil_model': self._get_layer_cell_value(row, 3),
                'drainage_type': self._get_layer_cell_value(row, 4),
                'gamma_unsat': self._get_layer_cell_value(row, 5),
                'gamma_sat': self._get_layer_cell_value(row, 6),
                'void_ratio': self._get_layer_cell_value(row, 7),
                'eref': self._get_layer_cell_value(row, 8),
                'nu': self._get_layer_cell_value(row, 9),
                'su': self._get_layer_cell_value(row, 10),
                'cref': self._get_layer_cell_value(row, 11),
                'phi': self._get_layer_cell_value(row, 12),
                'classification': self._get_layer_cell_value(row, 13),
                'soil_class': self._get_layer_cell_value(row, 14),
                'defaults_method': self._get_layer_cell_value(row, 15),
                'rinter': self._get_layer_cell_value(row, 16),
                'k0_determination': self._get_layer_cell_value(row, 17),
                'k0_manual': self._get_layer_cell_value(row, 18),
            }
            layers.append(layer_data)

        # ============================================================
        # Step 1: Soil Data Dictionary
        # ============================================================
        lines.append("# ------------------------------------------------------------")
        lines.append("# Soil database")
        lines.append("# ------------------------------------------------------------")
        lines.append("")
        lines.append("soil_data = [")

        for idx, layer in enumerate(layers):
            # Get numeric codes
            classification_code = self.CLASSIFICATION_TYPES.get(layer['classification'], 2)
            drainage_code = self.DRAINAGE_TYPES.get(layer['drainage_type'], 0)
            defaults_method_code = self.DEFAULTS_METHODS.get(layer['defaults_method'], 0)
            k0_code = self.K0_DETERMINATION.get(layer['k0_determination'], 0)

            # Get soil class code based on classification
            if layer['classification'] == 'USDA':
                soil_class_code = self.USDA_SOIL_CLASSES.get(layer['soil_class'], 0)
                soil_class_key = 'GroundwaterSoilClassUSDA'
            else:
                soil_class_code = self.STANDARD_SOIL_CLASSES.get(layer['soil_class'], 1)
                soil_class_key = 'GroundwaterSoilClassStandard'

            lines.append("    {")
            lines.append(f'        "name": "{layer["name"]}",')
            lines.append(f'        "from": {layer["from"]},')
            lines.append(f'        "to": {layer["to"]},')

            # Properties
            if layer['gamma_unsat']:
                lines.append(f'        "gammaUnsat": {layer["gamma_unsat"]},')
            if layer['gamma_sat']:
                lines.append(f'        "gammaSat": {layer["gamma_sat"]},')
            if layer['eref']:
                lines.append(f'        "Eref": {layer["eref"]},')
            if layer['nu']:
                lines.append(f'        "nu": {layer["nu"]},')
            if layer['cref']:
                lines.append(f'        "cRef": {layer["cref"]},')
            if layer['phi']:
                lines.append(f'        "phi": {layer["phi"]},')

            # Su (sURef) - required for Undrained B
            if layer['su'] and layer['drainage_type'] == 'Undrained B':
                lines.append(f'        "sURef": {layer["su"]},  # Su for Undrained B')

            # Drainage type (numeric)
            lines.append(f'        "DrainageType": {drainage_code},  # {layer["drainage_type"]}')

            # Groundwater (numeric codes)
            lines.append(f'        "GroundwaterClassificationType": {classification_code},  # {layer["classification"]}')
            lines.append(f'        "{soil_class_key}": {soil_class_code},  # {layer["soil_class"]}')
            lines.append(f'        "GwDefaultsMethod": {defaults_method_code},  # {layer["defaults_method"]}')

            # Interface
            if layer['rinter']:
                lines.append(f'        "Rinter": {layer["rinter"]},')

            # K0
            lines.append(f'        "K0Determination": {k0_code},  # {layer["k0_determination"]}')
            if layer['k0_determination'] == 'Manual' and layer['k0_manual'] and layer['k0_manual'] != '-':
                lines.append(f'        "K0Primary": {layer["k0_manual"]},')

            # Close dict
            if idx < len(layers) - 1:
                lines.append("    },")
            else:
                lines.append("    }")

        lines.append("]")
        lines.append("")

        # ============================================================
        # Step 2: Create Materials Loop
        # ============================================================
        lines.append("# ------------------------------------------------------------")
        lines.append("# Create materials in loop")
        lines.append("# ------------------------------------------------------------")
        lines.append("materials = []")
        lines.append("for data in soil_data:")
        lines.append("")
        lines.append("    soil = g_i.soilmat()")
        lines.append("    materials.append(soil)")
        lines.append("")
        lines.append("    # General")
        lines.append('    soil.Identification = data["name"]')
        lines.append('    soil.SoilModel = "Mohr-Coulomb"')
        lines.append('    soil.DrainageType = data["DrainageType"]')
        lines.append("")
        lines.append("    # Unit weights")
        lines.append('    if "gammaUnsat" in data:')
        lines.append('        soil.gammaUnsat = data["gammaUnsat"]')
        lines.append('    if "gammaSat" in data:')
        lines.append('        soil.gammaSat = data["gammaSat"]')
        lines.append("")
        lines.append("    # Mechanical - Stiffness")
        lines.append('    if "Eref" in data:')
        lines.append('        soil.ERef = data["Eref"]')
        lines.append('    if "nu" in data:')
        lines.append('        soil.nu = data["nu"]')
        lines.append("")
        lines.append("    # Mechanical - Strength")
        lines.append('    if "cRef" in data:')
        lines.append('        soil.cRef = data["cRef"]')
        lines.append('    if "phi" in data:')
        lines.append('        soil.phi = data["phi"]')
        lines.append('    if "sURef" in data:  # Su for Undrained B')
        lines.append('        soil.sURef = data["sURef"]')
        lines.append("")
        lines.append("    # Groundwater")
        lines.append('    soil.GroundwaterClassificationType = data["GroundwaterClassificationType"]')
        lines.append('    if "GroundwaterSoilClassUSDA" in data:')
        lines.append('        soil.GroundwaterSoilClassUSDA = data["GroundwaterSoilClassUSDA"]')
        lines.append('    if "GroundwaterSoilClassStandard" in data:')
        lines.append('        soil.GroundwaterSoilClassStandard = data["GroundwaterSoilClassStandard"]')
        lines.append("")
        lines.append("    soil.GwUseDefaults = True")
        lines.append('    soil.GwDefaultsMethod = data["GwDefaultsMethod"]')
        lines.append("")
        lines.append("    # Interfaces")
        lines.append("    soil.InterfaceStrengthDetermination = 1  # Manual")
        lines.append('    if "Rinter" in data:')
        lines.append('        soil.Rinter = data["Rinter"]')
        lines.append("")
        lines.append("    # Initial - K0")
        lines.append('    soil.K0Determination = data["K0Determination"]')
        lines.append('    if "K0Primary" in data:')
        lines.append('        soil.K0Primary = data["K0Primary"]')
        lines.append("")
        lines.append('    print(f"Created material: {data[\'name\']}")')
        lines.append("")

        # ============================================================
        # Step 3: Create Borehole and Layers
        # ============================================================
        lines.append("# ------------------------------------------------------------")
        lines.append("# Create Borehole and Soil Layers")
        lines.append("# ------------------------------------------------------------")
        position_x = self.position_input.text() or '0'
        lines.append(f"g_i.borehole({position_x})")
        lines.append("")

        # Create soil layers (all at once)
        lines.append("# Create soil layers")
        for idx in range(len(layers)):
            lines.append("g_i.soillayer(0)")

        lines.append("")

        # Assign materials to layers
        lines.append("# Assign materials to layers")
        for idx in range(len(layers)):
            lines.append(f"g_i.Soillayers[{idx}].Soil.Material = materials[{idx}]")

        lines.append("")

        # Set layer zones (From/To)
        if layers:
            lines.append("# Set layer zones (From/To)")
            lines.append(f"g_i.Soillayers[0].Zones[0].Top = {layers[0]['from']}")
            lines.append(f"g_i.Soillayers[0].Zones[0].Bottom = {layers[0]['to']}")
            for idx, layer in enumerate(layers[1:], start=1):
                lines.append(f"g_i.Soillayers[{idx}].Zones[0].Bottom = {layer['to']}")

        lines.append("")

        # ============================================================
        # Step 4: Soil Contour
        # ============================================================
        lines.append("# ------------------------------------------------------------")
        lines.append("# Initialize Soil Contour")
        lines.append("# ------------------------------------------------------------")
        xmin = self.xmin_input.text() or '0'
        xmax = self.xmax_input.text() or '100'
        ymin = self.ymin_input.text() or '0'
        ymax = self.ymax_input.text() or '100'

        lines.append(f"g_i.SoilContour.initializerectangular({xmin}, {ymin}, {xmax}, {ymax})")
        lines.append("")

        # ============================================================
        # Step 5: Staged Construction
        # ============================================================
        lines.append("# ------------------------------------------------------------")
        lines.append("# Staged Construction")
        lines.append("# ------------------------------------------------------------")
        lines.append("g_i.gotostages()")
        lines.append("")

        # Collect all phase data from tree (depth-first traversal)
        all_phases = self._collect_phases_from_tree()

        # Create mapping from phase name to variable name
        phase_name_to_var = {}
        phase_name_to_var['initial phase'] = 'InitialPhase'
        phase_name_to_var['Initial phase'] = 'InitialPhase'

        phase_count = 0
        for phase in all_phases:
            if phase['name'].lower() == 'initial phase':
                continue
            phase_count += 1
            phase_var = f"Phase_{phase_count}"
            phase_name_to_var[phase['name']] = phase_var

        # Generate code for each phase
        phase_count = 0
        for phase in all_phases:
            phase_name = phase['name']
            link = phase['link']
            calc_type = phase['calc_type']
            pore_pressure = phase['pore_pressure']
            reset_disp = phase['reset_disp']

            # Handle Initial phase differently
            if phase_name.lower() == 'initial phase':
                lines.append(f'# Initial Phase')
                if calc_type and calc_type not in ['', '-']:
                    lines.append(f'g_i.InitialPhase.DeformCalcType = "{calc_type}"')
                lines.append("")
                continue

            phase_count += 1
            phase_var = f"Phase_{phase_count}"
            lines.append(f"# {phase_name} ({phase_var})")

            # Create new phase
            lines.append(f"g_i.phase(g_i.InitialPhase)")
            lines.append(f"{phase_var} = g_i.Phases[-1]")

            # Set phase identification (custom name)
            lines.append(f'{phase_var}.Identification = "{phase_name}"')

            # Set PreviousPhase to link to correct phase
            if link:
                # Look up the variable name for the linked phase
                link_var = phase_name_to_var.get(link)
                if link_var:
                    if link_var == 'InitialPhase':
                        lines.append(f"{phase_var}.PreviousPhase = g_i.InitialPhase")
                    else:
                        lines.append(f"{phase_var}.PreviousPhase = {link_var}")
                else:
                    # Fallback: try to find by checking if link matches a Phase_X pattern
                    link_clean = link.replace(" ", "_").replace("-", "_")
                    lines.append(f"{phase_var}.PreviousPhase = {link_clean}")

            # Set Calculation Type
            if calc_type and calc_type not in ['', '-']:
                calc_type_lower = calc_type.lower()
                lines.append(f'{phase_var}.DeformCalcType = "{calc_type_lower}"')

            # Set Pore Pressure Calculation Type (NOT for Safety - it's read-only)
            if calc_type.lower() != 'safety':
                if pore_pressure and pore_pressure not in ['', '-']:
                    lines.append(f'{phase_var}.PorePresCalcType = "{pore_pressure}"')

            # Set Reset Displacements to Zero
            if reset_disp == 'TRUE':
                lines.append(f"{phase_var}.Deform.ResetDisplacementsToZero = True")
            elif reset_disp == 'FALSE':
                lines.append(f"{phase_var}.Deform.ResetDisplacementsToZero = False")

            lines.append("")

        # ============================================================
        # Step 6: Flow Condition (Water Levels)
        # ============================================================
        lines.append("# ------------------------------------------------------------")
        lines.append("# Flow Condition")
        lines.append("# ------------------------------------------------------------")
        lines.append("g_i.gotoflow()")
        lines.append("")

        # Get water levels from input fields
        lwl = self.lwl_input.text().strip()
        hwl = self.hwl_input.text().strip()

        if lwl:
            lines.append(f"# LWL Water Level at Y = {lwl}")
            lines.append(f"lwl = g_i.waterlevel(({xmin}, {lwl}), ({xmax}, {lwl}))")
            lines.append("")

        if hwl:
            lines.append(f"# HWL/RDD Water Level")
            mid_x = str(int((float(xmin) + float(xmax)) / 2)) if xmin and xmax else '0'
            lwl_val = lwl if lwl else hwl
            lines.append(f"hwl = g_i.waterlevel(({xmin}, {hwl}), ({mid_x}, {hwl}), ({xmax}, {lwl_val}))")
            lines.append("")

        # ============================================================
        # Footer
        # ============================================================
        lines.append("# ------------------------------------------------------------")
        lines.append("# Complete")
        lines.append("# ------------------------------------------------------------")
        lines.append('print("==============================================")')
        lines.append('print("PLAXIS script executed successfully")')
        lines.append('print("==============================================")')

        return '\n'.join(lines)

    def _run_code(self):
        """Preview/Run the generated code"""
        script = self._generate_script()
        self.preview_text.setPlainText(script)

    def _save_script(self):
        """Save Python script to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Python Script",
            "plaxis_script.py",
            "Python Files (*.py);;All Files (*)"
        )

        if file_path:
            script = self._generate_script()
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(script)
                QMessageBox.information(self, "Success", f"Script saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save script:\n{str(e)}")

    def _get_layer_cell_value(self, row, col):
        """Get value from layer table cell (handles both items and widgets)"""
        widget = self.layer_table.cellWidget(row, col)
        if widget and isinstance(widget, QComboBox):
            return widget.currentText()
        item = self.layer_table.item(row, col)
        return item.text() if item else ""

    def _set_layer_cell_value(self, row, col, value):
        """Set value in layer table cell (handles both items and widgets)"""
        widget = self.layer_table.cellWidget(row, col)
        if widget and isinstance(widget, QComboBox):
            widget.setCurrentText(value)
        else:
            item = self.layer_table.item(row, col)
            if item:
                item.setText(value)

    def get_project_data(self):
        """Get all data for project save"""
        # Get layer table data (including dropdown values)
        layer_data = []
        for row in range(self.layer_table.rowCount()):
            row_data = []
            for col in range(self.layer_table.columnCount()):
                value = self._get_layer_cell_value(row, col)
                row_data.append(value)
            layer_data.append(row_data)

        # Get staged construction data from tree (backward-compatible flat format)
        staged_data = []
        for phase in self._collect_phases_from_tree():
            staged_data.append([
                phase['name'], phase['link'], phase['calc_type'],
                phase['pore_pressure'], phase['reset_disp']
            ])

        # Get output table data
        output_data = []
        for row in range(self.output_table.rowCount()):
            row_dict = {
                'phase': self.output_table.item(row, 0).text() if self.output_table.item(row, 0) else '',
                'name': self.output_table.item(row, 13).text() if self.output_table.item(row, 13) else '',
                'scale_min': self.output_table.item(row, 19).text() if self.output_table.item(row, 19) else '',
                'scale_max': self.output_table.item(row, 20).text() if self.output_table.item(row, 20) else '',
                'scale_interval': self.output_table.item(row, 21).text() if self.output_table.item(row, 21) else '',
                'scale': self.output_table.item(row, 22).text() if self.output_table.item(row, 22) else '',
                'checks': {},
            }
            # Type dropdown
            type_combo = self.output_table.cellWidget(row, 14)
            row_dict['type'] = type_combo.currentText() if type_combo else ''
            # Checkboxes
            for col in self.OUTPUT_CHECK_COLS:
                item = self.output_table.item(row, col)
                if item and item.checkState() == Qt.CheckState.Checked:
                    row_dict['checks'][col] = True
            output_data.append(row_dict)

        return {
            'borehole_position': self.position_input.text(),
            'lwl': self.lwl_input.text(),
            'hwl': self.hwl_input.text(),
            'xmin': self.xmin_input.text(),
            'xmax': self.xmax_input.text(),
            'ymin': self.ymin_input.text(),
            'ymax': self.ymax_input.text(),
            'layer_data': layer_data,
            'staged_data': staged_data,
            'output_data': output_data,
        }

    def load_project_data(self, data):
        """Load project data and update UI"""
        try:
            # Load borehole position and water/contour settings
            self.position_input.setText(data.get('borehole_position', '0'))
            self.lwl_input.setText(data.get('lwl', ''))
            self.hwl_input.setText(data.get('hwl', ''))
            self.xmin_input.setText(data.get('xmin', '0'))
            self.xmax_input.setText(data.get('xmax', '100'))
            self.ymin_input.setText(data.get('ymin', '70'))
            self.ymax_input.setText(data.get('ymax', '100'))

            # Load layer table (with dropdowns)
            layer_data = data.get('layer_data', [])
            self.layer_table.setRowCount(len(layer_data))
            for row, row_data in enumerate(layer_data):
                # Setup row with widgets first
                self._setup_layer_row(row, (0, 0))
                # Then set values
                for col, value in enumerate(row_data):
                    if col < self.layer_table.columnCount():
                        self._set_layer_cell_value(row, col, value)

            # Load staged construction (build tree from flat data)
            staged_data = data.get('staged_data', [])
            if staged_data:
                self._build_tree_from_flat_data(staged_data)

            # Load output table data
            output_data = data.get('output_data', [])
            if output_data:
                self.output_table.setRowCount(len(output_data))
                for row, row_dict in enumerate(output_data):
                    # Convert string keys back to int for checks
                    checks = {}
                    for k, v in row_dict.get('checks', {}).items():
                        checks[int(k)] = v
                    row_dict_fixed = dict(row_dict)
                    row_dict_fixed['checks'] = checks
                    self._setup_output_row(row, row_dict_fixed)

        except Exception as e:
            print(f"Error loading Module 6 data: {e}")
