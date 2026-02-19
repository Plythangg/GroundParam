"""
Module 4: Multi-Parameters Plot
Fourth module for geotechnical analysis - Multiple parameter visualization

Features:
- Top bar: [Save Image], [Export PDF]
- Left frame: Grid table for adjusting axis settings (optional manual input)
  - Rows: [Grammar] [Su] [Phi] [E,E'] [K0]
  - Can manually input values or use calculated from Module 3
- Right frame: Preview window with multiple graphs (horizontal layout)
  - One graph per parameter: Grammar, SPT, Su, Phi, E/E', K0
  - Each graph shows all BH data
  - Depth as Y-axis (vertical), Parameter as X-axis (horizontal)
  - Scatter plots without connecting lines

Parameters to plot:
1. Grammar - Soil type/description
2. SPT - SPT N-value
3. Su - Undrained Shear Strength (kN/m²)
4. Phi (ϕ') - Effective Friction Angle (degrees)
5. E/E' - Young's Modulus (kN/m²)
6. K0 - Earth Pressure at Rest Coefficient
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QSplitter, QScrollArea, QCheckBox, QComboBox,
    QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeyEvent, QKeySequence
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from ui.bh_settings_dialog import BHSettingsDialog


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


class Module4MultiPlot(QWidget):
    """
    Module 4: Multi-Parameters Plot - Advanced visualization
    Displays multiple parameters in separate graphs (horizontal layout)
    """

    def __init__(self, parent=None, module3=None):
        super().__init__(parent)

        # Reference to Module 3 for calculated data
        self.module3 = module3

        # Data storage
        self.plot_data = {}  # {BH_name: {depth: {param: value}}}
        self.bh_names = []
        self.bh_settings = {}  # {BH_name: {'surface_elev': 100.0}}
        self.bh_display_settings = {}  # {BH_name: {'symbol', 'label', 'size', 'color'}}

        # Parameters to plot
        self.parameters = {
            'spt': {'label': 'SPT N-value', 'unit': '(blow/ft)', 'enabled': True},
            'gamma_sat': {'label': 'γsat', 'unit': '(kN/m³)', 'enabled': True},
            'su': {'label': 'Su', 'unit': '(kN/m²)', 'enabled': True},
            'phi': {'label': "ϕ'", 'unit': '(degrees)', 'enabled': True},
            'e_modulus': {'label': "E/E'", 'unit': '(kN/m²)', 'enabled': True},
            'k0': {'label': 'K0', 'unit': '', 'enabled': True},
        }

        # Axis limits for each parameter
        self.axis_limits = {
            'soil': {'xmin': 0, 'xmax': 0, 'ymin': 100, 'ymax': 70},  # X values not editable for Soil Profile
            'gamma_sat': {'xmin': 0, 'xmax': 25, 'ymin': 100, 'ymax': 70},
            'spt': {'xmin': 0, 'xmax': 100, 'ymin': 100, 'ymax': 70},
            'su': {'xmin': 0, 'xmax': 200, 'ymin': 100, 'ymax': 70},
            'phi': {'xmin': 0, 'xmax': 50, 'ymin': 100, 'ymax': 70},
            'e_modulus': {'xmin': 0, 'xmax': 50000, 'ymin': 100, 'ymax': 70},
            'k0': {'xmin': 0, 'xmax': 1.5, 'ymin': 100, 'ymax': 70},
        }

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Compact top bar with everything in one row
        top_bar = self._create_top_bar()
        main_layout.addLayout(top_bar)

        # Main content: Splitter with Left (Tables) and Right (Plots)
        content_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Tables
        left_widget = self._create_left_tables()
        content_splitter.addWidget(left_widget)

        # Right side: Plots
        self.plot_container = self._create_plot_container()
        content_splitter.addWidget(self.plot_container)

        # Set initial sizes (30% left, 70% right)
        content_splitter.setSizes([300, 700])

        main_layout.addWidget(content_splitter)

        self.setLayout(main_layout)

    def _create_left_tables(self):
        """Create left side tables: Axis settings and Line settings"""
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(16)

        # Table 1: Adjust X,Y - axis
        axis_group = self._create_axis_table()
        left_layout.addWidget(axis_group)

        # Table 2: X,Y - Line
        line_group = self._create_line_table()
        left_layout.addWidget(line_group)

        left_layout.addStretch()

        left_widget.setLayout(left_layout)
        left_widget.setMinimumWidth(400)
        left_widget.setMaximumWidth(500)

        return left_widget

    def _create_axis_table(self):
        """Create Adjust X,Y - axis table"""
        from PyQt6.QtWidgets import QGroupBox

        group = QGroupBox("Setting axis")
        group.setFont(QFont("SF Pro Display", 12, QFont.Weight.Bold))
        layout = QVBoxLayout()

        # Create table
        self.axis_table = CustomTableWidget()
        self.axis_table.setRowCount(7)  # Soil Profile, SPT, ysat, Su, Phi, E/E', K0
        self.axis_table.setColumnCount(4)
        self.axis_table.setHorizontalHeaderLabels(['Xmin', 'Xmax', 'Ymin', 'Ymax'])

        # Set row headers
        row_labels = ['Soil', 'SPT', 'γsat', 'Su', "ϕ'", "E/E'", 'K0']
        self.axis_table.setVerticalHeaderLabels(row_labels)

        # Apply theme styling - match Module 1 & 2
        self.axis_table.setFont(QFont("SF Pro Display", 10))
        self.axis_table.horizontalHeader().setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        self.axis_table.verticalHeader().setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        self.axis_table.setAlternatingRowColors(True)
        self.axis_table.setEditTriggers(
            QTableWidget.EditTrigger.CurrentChanged |
            QTableWidget.EditTrigger.SelectedClicked |
            QTableWidget.EditTrigger.EditKeyPressed |
            QTableWidget.EditTrigger.AnyKeyPressed
        )

        # Remove selection highlight (no blue cover on selected cells)
        self.axis_table.setStyleSheet("""
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

        # Set column widths - all equal width like Module 1 & 2
        column_width = 50
        for col in range(4):
            self.axis_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.axis_table.setColumnWidth(col, column_width)

        # Set default values from axis_limits with center alignment
        param_keys_ordered = ['soil', 'spt', 'gamma_sat', 'su', 'phi', 'e_modulus', 'k0']
        for row, param_key in enumerate(param_keys_ordered):
            limits = self.axis_limits.get(param_key, {'xmin': 0, 'xmax': 100, 'ymin': 0, 'ymax': 30})

            # Xmin
            if param_key == 'soil':
                item = QTableWidgetItem("-")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
            else:
                item = QTableWidgetItem(str(limits['xmin']))
            item.setFont(QFont("SF Pro Display", 10))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.axis_table.setItem(row, 0, item)

            # Xmax
            if param_key == 'soil':
                item = QTableWidgetItem("-")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
            else:
                item = QTableWidgetItem(str(limits['xmax']))
            item.setFont(QFont("SF Pro Display", 10))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.axis_table.setItem(row, 1, item)

            # Ymin
            item = QTableWidgetItem(str(limits['ymin']))
            item.setFont(QFont("SF Pro Display", 10))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.axis_table.setItem(row, 2, item)

            # Ymax
            item = QTableWidgetItem(str(limits['ymax']))
            item.setFont(QFont("SF Pro Display", 10))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.axis_table.setItem(row, 3, item)

        # Connect cell changes to update axis limits
        self.axis_table.cellChanged.connect(self._on_axis_changed)

        layout.addWidget(self.axis_table)
        group.setLayout(layout)

        return group

    def _create_line_table(self):
        """Create X,Y - Line table"""
        from PyQt6.QtWidgets import QGroupBox

        group = QGroupBox("Parameters Selected")
        group.setFont(QFont("SF Pro Display", 12, QFont.Weight.Bold))
        layout = QVBoxLayout()

        # Create table
        self.line_table = CustomTableWidget()
        self.line_table.setRowCount(6)  # Default 6 rows
        self.line_table.setColumnCount(10)  # Changed from 8 to 10 (added Soil Type and Consistency)
        self.line_table.setHorizontalHeaderLabels(['From', 'To', 'SPT', 'γsat', 'Su', "ϕ'", "E/E'", 'K0', 'Soil Type', 'Consistency'])

        # Set default depth ranges
        depth_ranges = [
            (100, 95),
            (95, 90),
            (90, 85),
            (85, 80),
            (80, 75),
            (75, 70)
        ]

        for row, (from_depth, to_depth) in enumerate(depth_ranges):
            # From column - editable only in first row
            item = QTableWidgetItem(str(from_depth))
            item.setFont(QFont("SF Pro Display", 10))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if row > 0:
                # Make From column read-only for rows after first
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.line_table.setItem(row, 0, item)

            # To column
            item = QTableWidgetItem(str(to_depth))
            item.setFont(QFont("SF Pro Display", 10))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.line_table.setItem(row, 1, item)

            # Initialize empty cells for parameters (columns 2-7)
            for col in range(2, 8):
                item = QTableWidgetItem("")
                item.setFont(QFont("SF Pro Display", 10))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.line_table.setItem(row, col, item)

            # Column 8: Soil Type - QComboBox with Sand/Clay
            soil_type_combo = QComboBox()
            soil_type_combo.setFont(QFont("SF Pro Display", 10))
            soil_type_combo.addItems(["", "Sand", "Clay"])
            soil_type_combo.setCurrentText("")
            # Minimize combo box size with compact styling
            soil_type_combo.setStyleSheet("""
                QComboBox {
                    padding: 1px 2px;
                    border: 1px solid #ccc;
                    background: white;
                }
                QComboBox::drop-down {
                    width: 15px;
                    border: none;
                }
            """)
            soil_type_combo.currentTextChanged.connect(lambda text, r=row: self._on_soil_type_changed(r))
            self.line_table.setCellWidget(row, 8, soil_type_combo)

            # Column 9: Consistency - Read-only
            item = QTableWidgetItem("")
            item.setFont(QFont("SF Pro Display", 10))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
            self.line_table.setItem(row, 9, item)

        # Apply theme styling - match Module 1 & 2
        self.line_table.setFont(QFont("SF Pro Display", 10))
        self.line_table.horizontalHeader().setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        self.line_table.setAlternatingRowColors(True)
        self.line_table.setEditTriggers(
            QTableWidget.EditTrigger.CurrentChanged |
            QTableWidget.EditTrigger.SelectedClicked |
            QTableWidget.EditTrigger.EditKeyPressed |
            QTableWidget.EditTrigger.AnyKeyPressed
        )

        # Remove selection highlight (no blue cover on selected cells)
        self.line_table.setStyleSheet("""
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

        # Set column widths
        column_widths = [45, 45, 45, 45, 45, 45, 45, 45, 75, 110]  # Wider for Consistency to fit "Medium Dense"
        for col, width in enumerate(column_widths):
            self.line_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            self.line_table.setColumnWidth(col, width)

        # Connect cell changes to update plots
        self.line_table.cellChanged.connect(self._on_line_changed)

        layout.addWidget(self.line_table)

        # Add "Add Row" button
        btn_add_row = QPushButton("Add Row")
        btn_add_row.setFont(QFont("SF Pro Display", 10))
        btn_add_row.setMaximumWidth(100)
        btn_add_row.clicked.connect(self._add_line_row)
        layout.addWidget(btn_add_row)

        group.setLayout(layout)

        return group

    def _add_line_row(self):
        """Add a new row to the line table"""
        current_rows = self.line_table.rowCount()
        self.line_table.setRowCount(current_rows + 1)

        # Initialize empty cells for the new row (columns 0-7, 9)
        for col in range(8):
            item = QTableWidgetItem("")
            item.setFont(QFont("SF Pro Display", 10))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Make From column read-only for all rows except first
            if col == 0 and current_rows > 0:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.line_table.setItem(current_rows, col, item)

        # Column 8: Soil Type - QComboBox
        soil_type_combo = QComboBox()
        soil_type_combo.setFont(QFont("SF Pro Display", 10))
        soil_type_combo.addItems(["", "Sand", "Clay"])
        # Minimize combo box size with compact styling
        soil_type_combo.setStyleSheet("""
            QComboBox {
                padding: 1px 2px;
                border: 1px solid #ccc;
                background: white;
            }
            QComboBox::drop-down {
                width: 15px;
                border: none;
            }
        """)
        soil_type_combo.currentTextChanged.connect(lambda text, r=current_rows: self._on_soil_type_changed(r))
        self.line_table.setCellWidget(current_rows, 8, soil_type_combo)

        # Column 9: Consistency - Read-only
        item = QTableWidgetItem("")
        item.setFont(QFont("SF Pro Display", 10))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.line_table.setItem(current_rows, 9, item)

    def _on_line_changed(self, row, col):
        """Handle line table cell changes"""
        # Auto-link From/To values: if To column (col 1) changes, update next row's From
        if col == 1:  # To column changed
            if row < self.line_table.rowCount() - 1:
                to_item = self.line_table.item(row, 1)
                if to_item and to_item.text().strip():
                    next_from_item = self.line_table.item(row + 1, 0)
                    if next_from_item:
                        # Temporarily disconnect to avoid recursive updates
                        self.line_table.cellChanged.disconnect(self._on_line_changed)
                        next_from_item.setText(to_item.text())
                        self.line_table.cellChanged.connect(self._on_line_changed)

        # If phi or Su column changes, recalculate consistency
        if col in [5, 4]:  # phi (col 5) or Su (col 4)
            self._update_consistency(row)

        # Update plots when line data changes
        self.update_plots()

    def _on_soil_type_changed(self, row):
        """Handle Soil Type combo box changes"""
        # Recalculate consistency when soil type changes
        self._update_consistency(row)

    def _update_consistency(self, row):
        """Update consistency column based on Soil Type and parameter values"""
        # Get Soil Type from combo box
        soil_type_combo = self.line_table.cellWidget(row, 8)
        if not soil_type_combo:
            return

        soil_type = soil_type_combo.currentText()
        consistency_item = self.line_table.item(row, 9)

        if not consistency_item:
            consistency_item = QTableWidgetItem("")
            consistency_item.setFont(QFont("SF Pro Display", 10))
            consistency_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            consistency_item.setFlags(consistency_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.line_table.setItem(row, 9, consistency_item)

        # Calculate consistency based on soil type
        if soil_type == "Sand":
            # Use phi value (column 5)
            phi_item = self.line_table.item(row, 5)
            if phi_item and phi_item.text().strip():
                try:
                    phi = float(phi_item.text().strip())
                    consistency = self._get_sand_consistency(phi)
                    consistency_item.setText(consistency)
                except ValueError:
                    consistency_item.setText("")
            else:
                consistency_item.setText("")

        elif soil_type == "Clay":
            # Use Su value (column 4)
            su_item = self.line_table.item(row, 4)
            if su_item and su_item.text().strip():
                try:
                    su = float(su_item.text().strip())
                    consistency = self._get_clay_consistency(su)
                    consistency_item.setText(consistency)
                except ValueError:
                    consistency_item.setText("")
            else:
                consistency_item.setText("")
        else:
            # No soil type selected
            consistency_item.setText("")

    def _get_sand_consistency(self, phi):
        """Determine sand consistency based on phi (friction angle) value"""
        # Standard ranges for sand based on friction angle
        if phi < 28:
            return "Loose"
        elif phi < 30:
            return "Loose to Medium"
        elif phi < 36:
            return "Medium Dense"
        elif phi < 41:
            return "Dense"
        else:
            return "Very Dense"

    def _get_clay_consistency(self, su):
        """Determine clay consistency based on Su (undrained shear strength) value"""
        # Standard ranges for clay based on undrained shear strength (kN/m²)
        if su < 12.5:
            return "Very Soft"
        elif su < 25:
            return "Soft"
        elif su < 50:
            return "Medium"
        elif su < 100:
            return "Stiff"
        elif su < 200:
            return "Very Stiff"
        else:
            return "Hard"

    def _plot_lines_on_axis(self, ax, param_key):
        """Plot horizontal lines from X,Y - Line table on the given axis
        From/To define the depth range, and the parameter value defines the horizontal line position
        """
        # Map parameter keys to column indices in line_table
        param_col_map = {
            'spt': 2,
            'gamma_sat': 3,
            'su': 4,
            'phi': 5,
            'e_modulus': 6,
            'k0': 7
        }

        if param_key not in param_col_map:
            return

        col_idx = param_col_map[param_key]

        # Read line data from table
        for row in range(self.line_table.rowCount()):
            try:
                # Get From depth (starting Y position)
                from_item = self.line_table.item(row, 0)
                if from_item is None or not from_item.text().strip():
                    continue
                from_depth = float(from_item.text().strip())

                # Get To depth (ending Y position)
                to_item = self.line_table.item(row, 1)
                if to_item is None or not to_item.text().strip():
                    continue
                to_depth = float(to_item.text().strip())

                # Always draw horizontal lines at from_depth and to_depth
                ax.axhline(y=from_depth, color="#000000", linewidth=1.5, linestyle='--',
                          alpha=0.5, zorder=2)
                ax.axhline(y=to_depth, color="#000000", linewidth=1.5, linestyle='--',
                          alpha=0.5, zorder=2)

                # If parameter value is provided, also draw a vertical line at that X value
                value_item = self.line_table.item(row, col_idx)
                if value_item and value_item.text().strip():
                    value = float(value_item.text().strip())
                    ax.plot([value, value], [from_depth, to_depth],
                           color="#FF0000", linewidth=2, linestyle='-',
                           alpha=0.7, zorder=3)

                    # Add red label showing the value at the midpoint of the vertical line
                    mid_depth = (from_depth + to_depth) / 2
                    ax.text(value, mid_depth, f'{value}',
                           color='#FF0000', fontsize=9, fontweight='bold',
                           ha='left', va='center',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                   edgecolor='#FF0000', alpha=0.8),
                           zorder=4)

            except (ValueError, AttributeError):
                continue  # Skip invalid rows

    def _on_axis_changed(self, row, col):
        """Handle axis table cell changes"""
        try:
            item = self.axis_table.item(row, col)
            if item is None:
                return

            # Skip if it's a read-only cell (Soil Profile X values)
            if not (item.flags() & Qt.ItemFlag.ItemIsEditable):
                return

            value = float(item.text().strip())

            # Update axis_limits dictionary
            param_keys_ordered = ['soil', 'spt', 'gamma_sat', 'su', 'phi', 'e_modulus', 'k0']
            if row >= len(param_keys_ordered):
                return

            param_key = param_keys_ordered[row]

            if col == 0:  # Xmin
                self.axis_limits[param_key]['xmin'] = value
            elif col == 1:  # Xmax
                self.axis_limits[param_key]['xmax'] = value
            elif col == 2:  # Ymin
                self.axis_limits[param_key]['ymin'] = value
            elif col == 3:  # Ymax
                self.axis_limits[param_key]['ymax'] = value

            # Update plots
            self.update_plots()

        except ValueError:
            pass  # Invalid number, ignore

    def _create_top_bar(self):
        """Create compact top bar with everything in one row"""
        layout = QHBoxLayout()
        layout.setSpacing(8)

        # Title - smaller and more compact
        title = QLabel("Module 4")
        title.setFont(QFont("SF Pro Display", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("color: #D1D1D6;")
        layout.addWidget(separator)

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
        separator2 = QLabel("|")
        separator2.setStyleSheet("color: #D1D1D6;")
        layout.addWidget(separator2)

        # Show Parameters label - compact
        layout.addWidget(QLabel("Show:"))

        # Soil Profile checkbox - appears first (leftmost graph)
        self.soil_profile_checkbox = QCheckBox("Soil Profile")
        self.soil_profile_checkbox.setChecked(False)
        self.soil_profile_checkbox.setFont(QFont("SF Pro Display", 10))
        self.soil_profile_checkbox.stateChanged.connect(self.update_plots)
        layout.addWidget(self.soil_profile_checkbox)

        # Checkboxes for each parameter - compact
        self.param_checkboxes = {}
        for param_key, param_info in self.parameters.items():
            checkbox = QCheckBox(param_info['label'])
            checkbox.setChecked(param_info['enabled'])
            checkbox.setFont(QFont("SF Pro Display", 10))
            checkbox.stateChanged.connect(lambda state, key=param_key: self.toggle_parameter(key, state))
            layout.addWidget(checkbox)
            self.param_checkboxes[param_key] = checkbox

        layout.addStretch()

        # Info label - compact
        self.info_label = QLabel("Load from Module 3")
        self.info_label.setFont(QFont("SF Pro Display", 10))
        self.info_label.setStyleSheet("color: #6E6E73;")
        layout.addWidget(self.info_label)

        # Buttons - compact
        btn_load = QPushButton("Load")
        btn_load.setToolTip("Load calculated parameters from Module 3")
        btn_load.setFont(QFont("SF Pro Display", 10))
        btn_load.setMaximumWidth(80)
        btn_load.clicked.connect(self.load_from_module3)
        layout.addWidget(btn_load)

        btn_edit = QPushButton("Edit BH")
        btn_edit.setToolTip("Edit borehole display settings")
        btn_edit.setFont(QFont("SF Pro Display", 10))
        btn_edit.setMaximumWidth(80)
        btn_edit.clicked.connect(self.edit_bh_settings)
        layout.addWidget(btn_edit)

        btn_save = QPushButton("PNG")
        btn_save.setToolTip("Export preview to PNG")
        btn_save.setFont(QFont("SF Pro Display", 10))
        btn_save.setMaximumWidth(70)
        btn_save.clicked.connect(self.export_preview_png)
        layout.addWidget(btn_save)

        btn_export = QPushButton("PDF")
        btn_export.setToolTip("Export preview to PDF")
        btn_export.setFont(QFont("SF Pro Display", 10))
        btn_export.setMaximumWidth(70)
        btn_export.clicked.connect(self.export_preview_pdf)
        layout.addWidget(btn_export)

        return layout

    def _create_plot_container(self):
        """Create fixed container for multiple plots (horizontal layout) - locked at right edge"""
        # Container widget for plots (no scroll area - graphs will compress to fit)
        self.plot_widget = QWidget()
        self.plot_layout = QHBoxLayout()
        self.plot_layout.setSpacing(16)
        self.plot_widget.setLayout(self.plot_layout)

        return self.plot_widget

    def toggle_parameter(self, param_key, state):
        """Toggle parameter visibility"""
        self.parameters[param_key]['enabled'] = (state == Qt.CheckState.Checked.value)
        self.update_plots()

    def load_from_module3(self):
        """Load calculated parameters from Module 3"""
        if not self.module3:
            QMessageBox.warning(self, "Warning", "Module 3 is not available!")
            return

        module3_data = self.module3.get_results()
        if not module3_data:
            QMessageBox.warning(
                self, "Warning",
                "No results available in Module 3.\n"
                "Please calculate parameters in Module 3 first."
            )
            return

        results = module3_data.get('results', {})
        bh_settings = module3_data.get('bh_settings', {})

        if not results:
            QMessageBox.warning(
                self, "Warning",
                "No results available in Module 3.\n"
                "Please calculate parameters in Module 3 first."
            )
            return

        # Convert Module 3 results to plot data
        self.plot_data = {}
        self.bh_names = list(results.keys())
        self.bh_settings = bh_settings  # Store surface elevation data

        for bh_name, bh_results in results.items():
            self.plot_data[bh_name] = {}
            for result in bh_results:
                depth = result['depth']
                self.plot_data[bh_name][depth] = {
                    'gamma_sat': result.get('gamma_sat'),
                    'spt': result.get('n_value'),
                    'su': result.get('su'),
                    'phi': result.get('phi'),
                    'e_modulus': result.get('e_modulus'),
                    'k0': result.get('k0'),
                    'classification': result.get('classification', '')
                }

        # Update plots
        self.update_plots()
        self.info_label.setText(f"Loaded data for {len(self.bh_names)} borehole(s)")

    def refresh_from_module3(self):
        """Refresh plot data from Module 3 without user interaction.
        Called automatically when Module 3 results are updated (e.g., lab data changes).
        Only refreshes if data was previously loaded."""
        if not self.plot_data or not self.module3:
            return

        module3_data = self.module3.get_results()
        if not module3_data:
            return

        results = module3_data.get('results', {})
        if not results:
            return

        # Update plot data with latest results from Module 3
        for bh_name, bh_results in results.items():
            if bh_name not in self.plot_data:
                continue
            for result in bh_results:
                depth = result['depth']
                if depth in self.plot_data[bh_name]:
                    self.plot_data[bh_name][depth]['gamma_sat'] = result.get('gamma_sat')
                    self.plot_data[bh_name][depth]['su'] = result.get('su')
                    self.plot_data[bh_name][depth]['phi'] = result.get('phi')

        # Refresh plots
        self.update_plots()

    def update_plots(self):
        """Update all parameter plots (horizontal layout)"""
        # Clear existing plots
        while self.plot_layout.count():
            child = self.plot_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add Soil Profile plot first if checkbox is checked
        if self.soil_profile_checkbox.isChecked():
            soil_profile_widget = self._create_soil_profile_plot()
            if soil_profile_widget:
                self.plot_layout.addWidget(soil_profile_widget, stretch=1)

        if not self.plot_data:
            return

        # Create a plot for each enabled parameter
        for param_key, param_info in self.parameters.items():
            if param_info['enabled']:
                plot_widget = self._create_parameter_plot(param_key, param_info)
                self.plot_layout.addWidget(plot_widget, stretch=1)  # Equal distribution

    def _create_soil_profile_plot(self):
        """Create Soil Profile plot based on Parameters Selected table"""
        # Read data from line_table
        layers = []
        for row in range(self.line_table.rowCount()):
            try:
                from_item = self.line_table.item(row, 0)
                to_item = self.line_table.item(row, 1)
                soil_type_combo = self.line_table.cellWidget(row, 8)
                consistency_item = self.line_table.item(row, 9)

                if not from_item or not to_item or not from_item.text().strip() or not to_item.text().strip():
                    continue

                from_depth = float(from_item.text().strip())
                to_depth = float(to_item.text().strip())
                soil_type = soil_type_combo.currentText() if soil_type_combo else ""
                consistency = consistency_item.text() if consistency_item else ""

                if soil_type and consistency:
                    layers.append({
                        'from': from_depth,
                        'to': to_depth,
                        'thickness': abs(from_depth - to_depth),
                        'soil_type': soil_type,
                        'consistency': consistency
                    })
            except (ValueError, AttributeError):
                continue

        if not layers:
            return None

        # Create figure and canvas
        figure = Figure(figsize=(4, 7), dpi=80)
        canvas = FigureCanvas(figure)

        # Apply plot style
        self._apply_plot_style()

        # Create axes
        ax = figure.add_subplot(111)

        # Get Y-axis mode
        y_axis_mode = self.y_axis_combo.currentText()
        use_elevation = (y_axis_mode == "Elevation")

        # Get axis limits for Soil Profile
        soil_limits = self.axis_limits.get('soil', {'ymin': 100, 'ymax': 70})
        y_top = soil_limits['ymin']     # Top of the profile (e.g., 100)
        y_bottom = soil_limits['ymax']  # Bottom of the profile (e.g., 70)

        for layer in layers:
            y_start = layer['from']
            y_end = layer['to']

            # Draw layer rectangle
            ax.add_patch(plt.Rectangle((0, min(y_start, y_end)), 1, abs(y_start - y_end),
                                      facecolor='white', edgecolor='black', linewidth=1))

            # Draw pattern based on consistency
            self._draw_soil_pattern(ax, 0, 1, min(y_start, y_end), max(y_start, y_end),
                                   layer['soil_type'], layer['consistency'])

            # Add text label
            mid_y = (y_start + y_end) / 2
            ax.text(0.5, mid_y, f"{layer['consistency']}\n{layer['soil_type']}",
                   ha='center', va='center', fontsize=8, fontweight='bold')

        # Set axis properties
        ax.set_xlim(0, 1)
        ax.set_ylim(y_bottom, y_top)  # y_bottom at bottom, y_top at top (e.g., 70 to 100)
        ax.set_xlabel('', fontsize=9)
        y_label = 'Elevation (m)' if use_elevation else 'Depth (m)'
        ax.set_ylabel(y_label, fontsize=9, fontweight='bold')
        ax.set_title('Soil Profile', fontsize=11, fontweight='bold', pad=15)
        ax.set_xticks([])
        ax.grid(True, alpha=0.7, axis='y')

        # Adjust subplot
        figure.subplots_adjust(left=0.2, right=0.95, top=0.92, bottom=0.08)

        return canvas

    def _draw_soil_pattern(self, ax, x_start, x_end, y_start, y_end, soil_type, consistency):
        """Draw soil pattern based on soil type and consistency"""
        import numpy as np

        if soil_type == "Sand":
            # Draw dots pattern (density varies by consistency)
            if consistency == "Loose":
                num_dots = 30
            elif consistency == "Loose to Medium":
                num_dots = 50
            elif consistency == "Medium Dense":
                num_dots = 80
            elif consistency == "Dense":
                num_dots = 120
            elif consistency == "Very Dense":
                num_dots = 180
            else:
                num_dots = 50

            # Random dots
            np.random.seed(hash(consistency) % 1000)
            x_dots = np.random.uniform(x_start, x_end, num_dots)
            y_dots = np.random.uniform(y_start, y_end, num_dots)
            ax.scatter(x_dots, y_dots, s=1, c='black', alpha=0.6)

        elif soil_type == "Clay":
            # Draw horizontal lines pattern (density varies by consistency)
            if consistency == "Very Soft":
                num_lines = 3
            elif consistency == "Soft":
                num_lines = 5
            elif consistency == "Medium":
                num_lines = 7
            elif consistency == "Stiff":
                num_lines = 10
            elif consistency == "Very Stiff":
                num_lines = 15
            elif consistency == "Hard":
                num_lines = 20
            else:
                num_lines = 7

            # Horizontal lines
            for i in range(num_lines):
                y_pos = y_start + (i + 0.5) * (y_end - y_start) / num_lines
                ax.plot([x_start, x_end], [y_pos, y_pos], 'k-', linewidth=0.5, alpha=0.6)

    def _create_parameter_plot(self, param_key, param_info):
        """Create a single parameter plot"""
        # Create figure and canvas - reduced width to show y-axis labels
        figure = Figure(figsize=(4, 7), dpi=80)
        canvas = FigureCanvas(figure)
        # No min/max width - allow graphs to compress and fit within container

        # Apply Apple-style theme
        self._apply_plot_style()

        # Create axes with adjusted left margin for y-axis labels
        ax = figure.add_subplot(111)

        # Get Y-axis mode (Depth or Elevation)
        y_axis_mode = self.y_axis_combo.currentText()
        use_elevation = (y_axis_mode == "Elevation")

        # Colors for each borehole
        colors = ["#007BFF7B", "#5EC7348B", '#FF9F0A', "#FF3A308F", "#5856D68D", "#AF52DE90"]

        # Plot each borehole
        for i, bh_name in enumerate(self.bh_names):
            y_values = []
            values = []

            # Get surface elevation for this borehole
            settings = self.bh_settings.get(bh_name, {'surface_elev': 100.0, 'water_level': 0.0})
            surface_elev = settings['surface_elev']

            # Sort by depth
            for depth, data in sorted(self.plot_data[bh_name].items()):
                value = data.get(param_key)
                if value is not None:
                    # Ensure depth is float (should already be after loading)
                    depth_float = float(depth) if isinstance(depth, str) else depth

                    # Calculate Y value based on mode
                    if use_elevation:
                        y_values.append(surface_elev - depth_float)  # Elevation = Surface - Depth
                    else:
                        y_values.append(depth_float)
                    values.append(value)

            if y_values:
                # Get display settings for this borehole
                if bh_name in self.bh_display_settings:
                    settings = self.bh_display_settings[bh_name]
                    color = settings.get('color', colors[i % len(colors)])
                    marker = settings.get('symbol', 'o')
                    size = settings.get('size', 5) ** 2  # scatter uses size^2, default=5
                else:
                    color = colors[i % len(colors)]
                    marker = 'o'
                    size = 25  # 5^2 (default size=5)

                # Use bh_name directly as label (no custom label column)
                label = bh_name

                ax.scatter(values, y_values, c=color, s=size, alpha=1.0,
                          label=label, marker=marker, zorder=3)

        # Plot lines from X,Y - Line table
        self._plot_lines_on_axis(ax, param_key)

        # Invert y-axis only if using Depth mode (depth increases downward)
        # For Elevation mode, higher values should be at top (natural orientation)
        if not use_elevation:
            ax.invert_yaxis()

        # Set axis labels
        label_text = f"{param_info['label']} {param_info['unit']}".strip()
        ax.set_xlabel(label_text, fontsize=9, fontweight='bold')
        y_label = 'Elevation (m)' if use_elevation else 'Depth (m)'
        ax.set_ylabel(y_label, fontsize=9, fontweight='bold')
        title_suffix = 'Elevation' if use_elevation else 'Depth'
        ax.set_title(f"{param_info['label']} vs {title_suffix}", fontsize=11, fontweight='bold', pad=15)

        # Set axis limits
        limits = self.axis_limits.get(param_key, {'xmin': 0, 'xmax': 100, 'ymin': 0, 'ymax': 30})
        ax.set_xlim(limits['xmin'], limits['xmax'])
        ax.set_ylim(limits['ymax'], limits['ymin'])

        # Grid
        ax.grid(True, alpha=0.7)

        # Legend
        if len(self.bh_names) > 1:
            ax.legend(loc='best', framealpha=0.9, fontsize=9)

        # Adjust subplot to ensure y-axis labels are visible
        figure.subplots_adjust(left=0.2, right=0.95, top=0.92, bottom=0.08)

        return canvas

    def _plot_soil_profile_on_axis(self, ax):
        """Plot soil profile on a given axis (for PDF export)"""
        layers = []
        for row in range(self.line_table.rowCount()):
            try:
                from_item = self.line_table.item(row, 0)
                to_item = self.line_table.item(row, 1)
                soil_type_combo = self.line_table.cellWidget(row, 8)
                consistency_item = self.line_table.item(row, 9)

                if not from_item or not to_item or not from_item.text().strip() or not to_item.text().strip():
                    continue

                from_depth = float(from_item.text().strip())
                to_depth = float(to_item.text().strip())
                soil_type = soil_type_combo.currentText() if soil_type_combo else ""
                consistency = consistency_item.text() if consistency_item else ""

                if soil_type and consistency:
                    layers.append({
                        'from': from_depth, 'to': to_depth,
                        'soil_type': soil_type, 'consistency': consistency
                    })
            except (ValueError, AttributeError):
                continue

        if not layers:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            return

        y_axis_mode = self.y_axis_combo.currentText()
        use_elevation = (y_axis_mode == "Elevation")
        soil_limits = self.axis_limits.get('soil', {'ymin': 100, 'ymax': 70})

        for layer in layers:
            y_start = layer['from']
            y_end = layer['to']
            ax.add_patch(plt.Rectangle((0, min(y_start, y_end)), 1, abs(y_start - y_end),
                                       facecolor='white', edgecolor='black', linewidth=1))
            self._draw_soil_pattern(ax, 0, 1, min(y_start, y_end), max(y_start, y_end),
                                    layer['soil_type'], layer['consistency'])
            mid_y = (y_start + y_end) / 2
            ax.text(0.5, mid_y, f"{layer['consistency']}\n{layer['soil_type']}",
                    ha='center', va='center', fontsize=8, fontweight='bold')

        ax.set_xlim(0, 1)
        ax.set_ylim(soil_limits['ymax'], soil_limits['ymin'])
        ax.set_ylabel('Elevation (m)' if use_elevation else 'Depth (m)', fontsize=9, fontweight='bold')
        ax.set_title('Soil Profile', fontsize=11, fontweight='bold', pad=15)
        ax.set_xticks([])
        ax.grid(True, alpha=0.7, axis='y')

    def _plot_parameter_on_axis(self, ax, param_key, param_info):
        """Plot a single parameter on a given axis (for PDF export)"""
        y_axis_mode = self.y_axis_combo.currentText()
        use_elevation = (y_axis_mode == "Elevation")
        colors = ["#007BFF7B", "#5EC7348B", '#FF9F0A', "#FF3A308F", "#5856D68D", "#AF52DE90"]

        for i, bh_name in enumerate(self.bh_names):
            y_values = []
            values = []
            settings = self.bh_settings.get(bh_name, {'surface_elev': 100.0, 'water_level': 0.0})
            surface_elev = settings['surface_elev']

            for depth, data in sorted(self.plot_data[bh_name].items()):
                value = data.get(param_key)
                if value is not None:
                    depth_float = float(depth) if isinstance(depth, str) else depth
                    if use_elevation:
                        y_values.append(surface_elev - depth_float)
                    else:
                        y_values.append(depth_float)
                    values.append(value)

            if y_values:
                if bh_name in self.bh_display_settings:
                    s = self.bh_display_settings[bh_name]
                    color = s.get('color', colors[i % len(colors)])
                    marker = s.get('symbol', 'o')
                    size = s.get('size', 5) ** 2
                else:
                    color = colors[i % len(colors)]
                    marker = 'o'
                    size = 25

                ax.scatter(values, y_values, c=color, s=size, alpha=1.0,
                          label=bh_name, marker=marker, zorder=3)

        self._plot_lines_on_axis(ax, param_key)

        if not use_elevation:
            ax.invert_yaxis()

        label_text = f"{param_info['label']} {param_info['unit']}".strip()
        ax.set_xlabel(label_text, fontsize=9, fontweight='bold')
        ax.set_ylabel('Elevation (m)' if use_elevation else 'Depth (m)', fontsize=9, fontweight='bold')
        title_suffix = 'Elevation' if use_elevation else 'Depth'
        ax.set_title(f"{param_info['label']} vs {title_suffix}", fontsize=11, fontweight='bold', pad=15)

        limits = self.axis_limits.get(param_key, {'xmin': 0, 'xmax': 100, 'ymin': 0, 'ymax': 30})
        ax.set_xlim(limits['xmin'], limits['xmax'])
        ax.set_ylim(limits['ymax'], limits['ymin'])
        ax.grid(True, alpha=0.7)

        if len(self.bh_names) > 1:
            ax.legend(loc='best', framealpha=0.9, fontsize=9)

    def _apply_plot_style(self):
        """Apply Apple-style theme to matplotlib plots"""
        plt.rcParams.update({
            'font.family': 'sans-serif',
            'font.sans-serif': ['SF Pro Display', 'Arial', 'Helvetica'],
            'font.size': 8,
            'axes.labelsize': 12,
            'axes.titlesize': 13,
            'axes.labelcolor': "#000000",
            'axes.edgecolor': "#000000",
            'axes.linewidth': 1,
            'axes.facecolor': '#FFFFFF',
            'figure.facecolor': "#FFFFFF",
            'grid.color': "#CBCBCC",
            'grid.linewidth': 0.7,
            'xtick.color': "#000000",
            'ytick.color': "#000000",
            'text.color': "#000000",
        })

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
        """Export preview window (all graphs) to PDF - all plots on one page"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Preview to PDF", "", "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            from matplotlib.backends.backend_pdf import PdfPages

            # Count total plots
            plots_to_draw = []
            if self.soil_profile_checkbox.isChecked():
                plots_to_draw.append(('soil_profile', None))
            if self.plot_data:
                for param_key, param_info in self.parameters.items():
                    if param_info['enabled']:
                        plots_to_draw.append(('parameter', (param_key, param_info)))

            num_plots = len(plots_to_draw)
            if num_plots == 0:
                QMessageBox.warning(self, "Warning", "No plots to export. Update plots first.")
                return

            # Create combined figure with all plots side by side
            self._apply_plot_style()
            fig = Figure(figsize=(4 * num_plots, 7), dpi=150)

            for idx, (plot_type, plot_args) in enumerate(plots_to_draw):
                ax = fig.add_subplot(1, num_plots, idx + 1)
                if plot_type == 'soil_profile':
                    self._plot_soil_profile_on_axis(ax)
                else:
                    param_key, param_info = plot_args
                    self._plot_parameter_on_axis(ax, param_key, param_info)

            fig.tight_layout()

            with PdfPages(file_path) as pdf:
                pdf.savefig(fig, bbox_inches='tight')

            QMessageBox.information(
                self, "Success",
                f"Preview exported successfully!\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}")

    def get_project_data(self):
        """Get all data for project save"""
        # Get line table data
        line_table_data = []
        for row in range(self.line_table.rowCount()):
            row_data = []
            for col in range(self.line_table.columnCount()):
                if col == 8:  # Soil Type column (QComboBox)
                    combo = self.line_table.cellWidget(row, col)
                    row_data.append(combo.currentText() if combo else "")
                else:  # Regular QTableWidgetItem columns
                    item = self.line_table.item(row, col)
                    row_data.append(item.text() if item else "")
            line_table_data.append(row_data)

        return {
            'plot_data': self.plot_data,
            'bh_names': self.bh_names,
            'bh_settings': self.bh_settings,
            'bh_display_settings': self.bh_display_settings,  # Save BH display settings (symbol, size, color)
            'parameters': self.parameters,
            'axis_limits': self.axis_limits,
            'y_axis_mode': self.y_axis_combo.currentText(),
            'line_table_data': line_table_data,
            'soil_profile_enabled': self.soil_profile_checkbox.isChecked()
        }

    def load_project_data(self, data):
        """Load project data and update UI"""
        try:
            # Load data and convert depth keys from string to float
            plot_data_raw = data.get('plot_data', {})
            self.plot_data = {}
            for bh_name, depths_data in plot_data_raw.items():
                self.plot_data[bh_name] = {}
                for depth_str, depth_data in depths_data.items():
                    # Convert depth key to float
                    self.plot_data[bh_name][float(depth_str)] = depth_data

            self.bh_names = data.get('bh_names', [])
            self.bh_settings = data.get('bh_settings', {})

            # Load BH display settings with backward compatibility
            self.bh_display_settings = data.get('bh_display_settings', {})

            self.parameters = data.get('parameters', self.parameters)

            # Load axis_limits with backward compatibility
            loaded_axis_limits = data.get('axis_limits', {})
            # Ensure 'soil' key exists for old save files
            if 'soil' not in loaded_axis_limits:
                loaded_axis_limits['soil'] = {'xmin': 0, 'xmax': 0, 'ymin': 100, 'ymax': 70}
            self.axis_limits = loaded_axis_limits

            line_table_data = data.get('line_table_data', [])

            # Backward compatibility: Add missing columns for old save files
            if line_table_data and len(line_table_data) > 0:
                # Check if old format (8 columns instead of 10)
                if len(line_table_data[0]) == 8:
                    for row_data in line_table_data:
                        # Add empty Soil Type and Consistency columns
                        row_data.extend(["", ""])  # Columns 8 and 9

            # Update Y-axis mode
            y_axis_mode = data.get('y_axis_mode', 'Elevation')
            idx = self.y_axis_combo.findText(y_axis_mode)
            if idx >= 0:
                self.y_axis_combo.setCurrentIndex(idx)

            # Update Soil Profile checkbox
            soil_profile_enabled = data.get('soil_profile_enabled', False)
            self.soil_profile_checkbox.setChecked(soil_profile_enabled)

            # Update UI
            self._update_parameter_checkboxes()
            self._update_axis_table()
            self._update_line_table(line_table_data)

            # Update plots
            self.update_plots()

        except Exception as e:
            print(f"Error loading Module 4 data: {e}")

    def _update_parameter_checkboxes(self):
        """Update parameter checkboxes from loaded data"""
        # Update checkboxes based on loaded parameters using self.param_checkboxes
        for param_key, checkbox in self.param_checkboxes.items():
            if param_key in self.parameters:
                checkbox.setChecked(self.parameters[param_key]['enabled'])

    def _update_axis_table(self):
        """Update axis limits table from loaded data"""
        param_keys_ordered = ['soil', 'spt', 'gamma_sat', 'su', 'phi', 'e_modulus', 'k0']
        for row, param_key in enumerate(param_keys_ordered):
            limits = self.axis_limits.get(param_key, {'xmin': 0, 'xmax': 100, 'ymin': 0, 'ymax': 30})

            # For soil row, Xmin and Xmax should remain "-"
            if param_key == 'soil':
                self.axis_table.item(row, 0).setText("-")
                self.axis_table.item(row, 1).setText("-")
            else:
                self.axis_table.item(row, 0).setText(str(limits['xmin']))
                self.axis_table.item(row, 1).setText(str(limits['xmax']))

            self.axis_table.item(row, 2).setText(str(limits['ymin']))
            self.axis_table.item(row, 3).setText(str(limits['ymax']))

    def _update_line_table(self, line_table_data):
        """Update line table from loaded data"""
        if not line_table_data:
            return

        # Temporarily disconnect to avoid triggering updates during load
        self.line_table.cellChanged.disconnect(self._on_line_changed)

        for row_idx, row_data in enumerate(line_table_data):
            if row_idx >= self.line_table.rowCount():
                # Add new row if needed
                self._add_line_row()

            for col_idx, cell_value in enumerate(row_data):
                if col_idx >= self.line_table.columnCount():
                    break

                if col_idx == 8:  # Soil Type column (QComboBox)
                    combo = self.line_table.cellWidget(row_idx, col_idx)
                    if combo:
                        combo.setCurrentText(str(cell_value))
                else:  # Regular QTableWidgetItem columns
                    item = self.line_table.item(row_idx, col_idx)
                    if item:
                        item.setText(str(cell_value))
                    else:
                        item = QTableWidgetItem(str(cell_value))
                        item.setFont(QFont("SF Pro Display", 10))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        # Make From column read-only for rows after first
                        if col_idx == 0 and row_idx > 0:
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        # Make Consistency column read-only
                        if col_idx == 9:
                            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        self.line_table.setItem(row_idx, col_idx, item)

        # Reconnect
        self.line_table.cellChanged.connect(self._on_line_changed)

    def edit_bh_settings(self):
        """Open dialog to edit borehole display settings"""
        if not self.bh_names:
            QMessageBox.warning(self, "No Data", "Please load data from Module 3 first")
            return

        # Open settings dialog
        dialog = BHSettingsDialog(self.bh_names, self.bh_display_settings, self)
        if dialog.exec():
            # User clicked OK - apply settings
            self.bh_display_settings = dialog.get_settings()
            # Refresh plots with new settings
            self.update_plots()
