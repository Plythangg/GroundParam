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
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QSplitter, QScrollArea, QComboBox, QLineEdit,
    QGroupBox, QTextEdit, QTreeWidget, QTreeWidgetItem,
    QDialog, QListWidget, QDialogButtonBox, QAbstractItemView
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

        # Create vertical splitter: Tables on top, Preview on bottom
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top side - Tables (full width)
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        # Scroll area for tables
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)

        # 1. Borehole, Water Level & Soil Contour (horizontal layout)
        scroll_layout.addWidget(self._create_borehole_water_contour_section())

        # 2. Layer Properties Table
        scroll_layout.addWidget(self._create_layer_table_section())

        # 4. Staged Construction Table
        scroll_layout.addWidget(self._create_staged_construction_section())

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        top_layout.addWidget(scroll)

        # Bottom side - Preview and Actions
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        # Preview section
        bottom_layout.addWidget(self._create_preview_section())

        # Add to splitter (tables top, preview bottom)
        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        splitter.setSizes([500, 300])

        main_layout.addWidget(splitter)
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

        # Load from Module 4 button
        btn_load = QPushButton("Load from Module 4")
        btn_load.setToolTip("Load layer data from Module 4")
        btn_load.setFont(QFont("SF Pro Display", 10))
        btn_load.setMaximumWidth(200)
        btn_load.clicked.connect(self._load_from_module4)
        layout.addWidget(btn_load)

        # Action buttons
        btn_generate = QPushButton("Generate Script")
        btn_generate.setToolTip("Generate Python script from table data")
        btn_generate.setFont(QFont("SF Pro Display", 10))
        btn_generate.setMaximumWidth(200)
        btn_generate.clicked.connect(self._run_code)
        layout.addWidget(btn_generate)

        btn_save = QPushButton("Save .py")
        btn_save.setToolTip("Save Python script to file")
        btn_save.setFont(QFont("SF Pro Display", 10))
        btn_save.setMaximumWidth(100)
        btn_save.clicked.connect(self._save_script)
        layout.addWidget(btn_save)

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

        group.setLayout(layout)
        return group

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
                background-color: #E3F2FD;
                color: black;
            }
            QTableWidget::item:focus {
                background-color: #E3F2FD;
                border: 1px solid #007AFF;
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
                selection-background-color: #E3F2FD;
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

        self.layer_table.setMinimumHeight(200)
        layout.addWidget(self.layer_table)

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

        self.staged_tree.setMinimumHeight(280)
        layout.addWidget(self.staged_tree)

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

    def _create_preview_section(self):
        """Create preview section for Python script"""
        group = QGroupBox("Preview Python Scripts")
        group.setFont(QFont("SF Pro Display", 11, QFont.Weight.Bold))
        layout = QVBoxLayout()

        # Preview text area
        self.preview_text = QTextEdit()
        self.preview_text.setFont(QFont("Consolas", 10))
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        self.preview_text.setPlaceholderText("# Python script will be generated here...\n# Click 'Generate Script' in the top bar to preview")
        self.preview_text.setMinimumHeight(150)
        layout.addWidget(self.preview_text)

        group.setLayout(layout)
        return group

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
                k0_val = line_table.item(m4_row, 7).text() if line_table.item(m4_row, 7) else ''

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

        return {
            'borehole_position': self.position_input.text(),
            'lwl': self.lwl_input.text(),
            'hwl': self.hwl_input.text(),
            'xmin': self.xmin_input.text(),
            'xmax': self.xmax_input.text(),
            'ymin': self.ymin_input.text(),
            'ymax': self.ymax_input.text(),
            'layer_data': layer_data,
            'staged_data': staged_data
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

        except Exception as e:
            print(f"Error loading Module 6 data: {e}")
