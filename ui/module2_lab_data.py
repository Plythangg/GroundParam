"""
Module 2: Laboratory Data
Secondary module for geotechnical analysis - Laboratory test data input

Features:
- Top bar: [Save As], [Import CSV], [Clear Data]
- Left frame: Grid table layout (Excel-like)
- BH number as column header - Same BH names and count as Module 1
- Depth as rows - Same depth values as Module 1
- For each BH has [Grammar, Su, Phi] as sub-columns for entry data
- This data will be used with Module 3 for calculations
- When lab data exists, it will override calculated values in Module 3

Purpose:
- Input laboratory test results to override empirical correlations
- Grammar: Soil description/type
- Su: Undrained Shear Strength (kN/m²) from lab tests
- Phi: Effective Friction Angle (degrees) from lab tests
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeyEvent, QKeySequence
import csv
import json


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


class Module2LabData(QWidget):
    """
    Module 2: Laboratory Data - Lab test results input
    Shares BH structure with Module 1
    """

    # Signal emitted when lab data (ysat, su, phi) changes
    lab_data_changed = pyqtSignal()

    def __init__(self, parent=None, module1=None):
        super().__init__(parent)

        # Reference to Module 1 to sync BH names and depths
        self.module1 = module1

        # Data storage
        self.lab_data = {}  # {BH_name: {depth: {'grammar': '', 'su': None, 'phi': None}}}
        self.bh_names = []
        self.depths = []

        # Setup UI
        self._setup_ui()

        # Initialize data if Module 1 is available
        if self.module1:
            self._sync_with_module1()

    def _setup_ui(self):
        """Setup the user interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Compact top bar
        top_bar = self._create_top_bar()
        main_layout.addLayout(top_bar)

        # Data table
        self.table_widget = self._create_table_widget()
        main_layout.addWidget(self.table_widget)

        self.setLayout(main_layout)

    def _create_top_bar(self):
        """Create compact top bar"""
        layout = QHBoxLayout()
        layout.setSpacing(8)

        # Title
        title = QLabel("Module 2")
        title.setFont(QFont("SF Pro Display", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("color: #D1D1D6;")
        layout.addWidget(separator)

        # Info
        info = QLabel("Lab data overrides Module 3 calculations")
        info.setFont(QFont("SF Pro Display", 14))
        info.setStyleSheet("color: #6E6E73;")
        layout.addWidget(info)

        layout.addStretch()

        # Buttons - compact
        btn_sync = QPushButton("Refresh")
        btn_sync.setFont(QFont("SF Pro Display", 14))
        btn_sync.setMaximumWidth(80)
        btn_sync.setToolTip("Sync datas with Module 1")
        btn_sync.clicked.connect(self._sync_with_module1)
        layout.addWidget(btn_sync)

        btn_save = QPushButton("Save")
        btn_save.setFont(QFont("SF Pro Display", 14))
        btn_save.setMaximumWidth(80)
        btn_save.setToolTip("Save data")
        btn_save.clicked.connect(self.save_data)
        layout.addWidget(btn_save)

        btn_clear = QPushButton("Clear")
        btn_clear.setFont(QFont("SF Pro Display", 14))
        btn_clear.setMaximumWidth(80)
        btn_clear.setObjectName("secondary")
        btn_clear.setToolTip("Clear all data")
        btn_clear.clicked.connect(self.clear_data)
        layout.addWidget(btn_clear)

        return layout

    def _create_table_widget(self):
        """Create table widget for lab data input with single-click editing"""
        table = CustomTableWidget()
        table.setColumnCount(0)
        table.setRowCount(0)

        # Enable single-click editing
        table.setEditTriggers(
            QTableWidget.EditTrigger.CurrentChanged |
            QTableWidget.EditTrigger.SelectedClicked |
            QTableWidget.EditTrigger.EditKeyPressed |
            QTableWidget.EditTrigger.AnyKeyPressed
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

    def _sync_with_module1(self):
        """Synchronize BH names and depths from Module 1"""
        if not self.module1:
            QMessageBox.warning(self, "Warning", "Module 1 is not available for synchronization!")
            return

        # Get data from Module 1
        module1_data = self.module1.get_data()
        self.bh_names = module1_data['bh_names'].copy()
        self.depths = module1_data['depths'].copy()

        # Initialize empty lab data structure
        for bh in self.bh_names:
            if bh not in self.lab_data:
                self.lab_data[bh] = {}

            for depth in self.depths:
                if depth not in self.lab_data[bh]:
                    self.lab_data[bh][depth] = {'gamma_sat': None, 'su': None, 'phi': None}

        # Update table
        self._update_table()



    def _update_table(self):
        """Update table widget with current data"""
        # Disconnect signal temporarily
        try:
            self.table_widget.cellChanged.disconnect(self.on_cell_changed)
        except:
            pass

        # Set table dimensions: +2 rows (1 for BH names, 1 for sub-headers)
        num_rows = len(self.depths) + 2  # +2 for header rows
        num_cols = 1 + len(self.bh_names) * 3  # Depth + (Grammar, Su, Phi) for each BH

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

        for i, bh in enumerate(self.bh_names):
            bh_item = QTableWidgetItem(bh)
            bh_item.setFlags(bh_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            bh_item.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
            bh_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            bh_item.setBackground(Qt.GlobalColor.white)
            self.table_widget.setItem(0, 1 + i * 3, bh_item)
            # Merge 3 columns for BH name
            self.table_widget.setSpan(0, 1 + i * 3, 1, 3)

        # Row 1: Sub-headers (Grammar, Su, Phi for each BH)
        depth_label = QTableWidgetItem("Depth\n(m)")
        depth_label.setFlags(depth_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
        depth_label.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        depth_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        depth_label.setBackground(Qt.GlobalColor.white)
        self.table_widget.setItem(1, 0, depth_label)

        for i, bh in enumerate(self.bh_names):
            # Grammar sub-header
            grammar_label = QTableWidgetItem("γsat\n(kN/m³)")
            grammar_label.setFlags(grammar_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
            grammar_label.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
            grammar_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            grammar_label.setBackground(Qt.GlobalColor.white)
            self.table_widget.setItem(1, 1 + i * 3, grammar_label)

            # Su sub-header
            su_label = QTableWidgetItem("Su\n(kN/m²)")
            su_label.setFlags(su_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
            su_label.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
            su_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            su_label.setBackground(Qt.GlobalColor.white)
            self.table_widget.setItem(1, 1 + i * 3 + 1, su_label)

            # Phi sub-header
            phi_label = QTableWidgetItem("ϕ'\n(°)")
            phi_label.setFlags(phi_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
            phi_label.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
            phi_label.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            phi_label.setBackground(Qt.GlobalColor.white)
            self.table_widget.setItem(1, 1 + i * 3 + 2, phi_label)

        # Fill data (starting from row 2)
        for row_idx, depth in enumerate(self.depths):
            actual_row = row_idx + 2  # Offset by 2 for header rows

            # Depth column
            depth_item = QTableWidgetItem(f"{depth:.2f}")
            depth_item.setFlags(depth_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
            depth_item.setFont(QFont("SF Pro Display", 9))
            depth_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(actual_row, 0, depth_item)
            self.table_widget.setRowHeight(1, 45)
            # BH data columns
            for col, bh in enumerate(self.bh_names):
                data = self.lab_data.get(bh, {}).get(depth, {'gamma_sat': None, 'su': None, 'phi': None})

                # Handle migration from old 'grammar' key to new 'gamma_sat' key
                if 'gamma_sat' not in data and 'grammar' in data:
                    # Migrate old data
                    try:
                        data['gamma_sat'] = float(data['grammar']) if data['grammar'] and str(data['grammar']).strip() else None
                    except (ValueError, AttributeError):
                        data['gamma_sat'] = None

                # Gamma_sat column
                gamma_sat_value = str(data.get('gamma_sat', '')) if data.get('gamma_sat') is not None else ''
                gamma_sat_item = QTableWidgetItem(gamma_sat_value)
                gamma_sat_item.setFont(QFont("SF Pro Display", 9))
                gamma_sat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(actual_row, 1 + col * 3, gamma_sat_item)

                # Su column
                su_value = str(data['su']) if data['su'] is not None else ''
                su_item = QTableWidgetItem(su_value)
                su_item.setFont(QFont("SF Pro Display", 9))
                su_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(actual_row, 1 + col * 3 + 1, su_item)

                # Phi column
                phi_value = str(data['phi']) if data['phi'] is not None else ''
                phi_item = QTableWidgetItem(phi_value)
                phi_item.setFont(QFont("SF Pro Display", 9))
                phi_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(actual_row, 1 + col * 3 + 2, phi_item)

        # Adjust column widths - all columns same width
        column_width = 100  # Equal width for all columns

        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table_widget.setColumnWidth(0, column_width)

        for i in range(len(self.bh_names)):
            self.table_widget.horizontalHeader().setSectionResizeMode(1 + i * 3, QHeaderView.ResizeMode.Fixed)
            self.table_widget.horizontalHeader().setSectionResizeMode(1 + i * 3 + 1, QHeaderView.ResizeMode.Fixed)
            self.table_widget.horizontalHeader().setSectionResizeMode(1 + i * 3 + 2, QHeaderView.ResizeMode.Fixed)
            self.table_widget.setColumnWidth(1 + i * 3, column_width)
            self.table_widget.setColumnWidth(1 + i * 3 + 1, column_width)
            self.table_widget.setColumnWidth(1 + i * 3 + 2, column_width)

        # Reconnect signal
        self.table_widget.cellChanged.connect(self.on_cell_changed)

    def on_cell_changed(self, row, col):
        """Handle cell value changes"""
        if col == 0:  # Depth column (read-only)
            return

        # Handle BH names row (row 0) - read only
        if row == 0:
            return

        # Handle sub-headers row (row 1) - read only
        if row == 1:
            return

        # Data rows (row >= 2)
        if row < 2:
            return

        depth_index = row - 2  # Account for 2 header rows
        if depth_index >= len(self.depths):
            return

        depth = self.depths[depth_index]
        bh_index = (col - 1) // 3
        field_index = (col - 1) % 3  # 0=gamma_sat, 1=su, 2=phi

        if bh_index >= len(self.bh_names):
            return

        bh_name = self.bh_names[bh_index]
        item = self.table_widget.item(row, col)

        if item is None:
            return

        value = item.text().strip()

        # Ensure bh and depth exist in lab_data
        if bh_name not in self.lab_data:
            self.lab_data[bh_name] = {}
        if depth not in self.lab_data[bh_name]:
            self.lab_data[bh_name][depth] = {'gamma_sat': None, 'su': None, 'phi': None}

        if field_index == 0:
            # Gamma_sat (numeric)
            try:
                self.lab_data[bh_name][depth]['gamma_sat'] = float(value) if value else None
            except ValueError:
                self.lab_data[bh_name][depth]['gamma_sat'] = None
                item.setText('')

        elif field_index == 1:
            # Su (numeric)
            try:
                self.lab_data[bh_name][depth]['su'] = float(value) if value else None
            except ValueError:
                self.lab_data[bh_name][depth]['su'] = None
                item.setText('')

        elif field_index == 2:
            # Phi (numeric)
            try:
                self.lab_data[bh_name][depth]['phi'] = float(value) if value else None
            except ValueError:
                self.lab_data[bh_name][depth]['phi'] = None
                item.setText('')

        # Notify Module 3 that lab data changed
        self.lab_data_changed.emit()

    def save_data(self):
        """Save lab data to JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Lab Data", "", "JSON Files (*.json)")
        if not file_path:
            return

        data = {
            'bh_names': self.bh_names,
            'depths': self.depths,
            'lab_data': self.lab_data
        }

        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            QMessageBox.information(self, "Success", "Lab data saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data: {str(e)}")

    def load_data(self, file_path):
        """Load lab data from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            self.bh_names = data.get('bh_names', [])
            self.depths = data.get('depths', [])
            self.lab_data = data.get('lab_data', {})

            self._update_table()
            QMessageBox.information(self, "Success", "Lab data loaded successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")

    def clear_data(self):
        """Clear all lab data"""
        reply = QMessageBox.question(
            self, "Confirm",
            "Are you sure you want to clear all laboratory data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for bh in self.bh_names:
                for depth in self.depths:
                    if bh in self.lab_data and depth in self.lab_data[bh]:
                        self.lab_data[bh][depth] = {'grammar': '', 'su': None, 'phi': None}
            self._update_table()

    def get_data(self):
        """Get current lab data (for use by Module 3)"""
        return {
            'bh_names': self.bh_names,
            'depths': self.depths,
            'lab_data': self.lab_data
        }

    def get_lab_value(self, bh_name, depth, parameter):
        """
        Get specific lab value for a borehole at a depth

        Args:
            bh_name (str): Borehole name
            depth (float): Depth value
            parameter (str): 'grammar', 'su', or 'phi'

        Returns:
            value or None if not available
        """
        if bh_name not in self.lab_data:
            return None
        if depth not in self.lab_data[bh_name]:
            return None

        return self.lab_data[bh_name][depth].get(parameter)

    def has_lab_data(self, bh_name, depth):
        """
        Check if lab data exists for a specific borehole and depth

        Returns:
            dict: {'has_su': bool, 'has_phi': bool, 'has_gamma_sat': bool}
        """
        if bh_name not in self.lab_data or depth not in self.lab_data[bh_name]:
            return {'has_su': False, 'has_phi': False, 'has_gamma_sat': False}

        data = self.lab_data[bh_name][depth]
        return {
            'has_su': data.get('su') is not None,
            'has_phi': data.get('phi') is not None,
            'has_gamma_sat': data.get('gamma_sat') is not None
        }

    def get_project_data(self):
        """Get all data for project save"""
        return {
            'bh_names': self.bh_names,
            'depths': self.depths,
            'lab_data': self.lab_data
        }

    def load_project_data(self, data):
        """Load project data and update UI"""
        try:
            # Load data
            self.bh_names = data.get('bh_names', [])
            self.depths = data.get('depths', [])

            # Load lab_data and convert depth keys from string to float
            lab_data_raw = data.get('lab_data', {})
            self.lab_data = {}
            for bh_name, depths_data in lab_data_raw.items():
                self.lab_data[bh_name] = {}
                for depth_str, depth_data in depths_data.items():
                    # Convert depth key to float
                    # Migrate old 'grammar' key to 'gamma_sat' if needed
                    if 'gamma_sat' not in depth_data and 'grammar' in depth_data:
                        try:
                            depth_data['gamma_sat'] = float(depth_data['grammar']) if depth_data['grammar'] and str(depth_data['grammar']).strip() else None
                        except (ValueError, AttributeError):
                            depth_data['gamma_sat'] = None
                        # Remove old key
                        depth_data.pop('grammar', None)

                    # Ensure gamma_sat exists
                    if 'gamma_sat' not in depth_data:
                        depth_data['gamma_sat'] = None

                    self.lab_data[bh_name][float(depth_str)] = depth_data

            # Update table
            self._update_table()

        except Exception as e:
            print(f"Error loading Module 2 data: {e}")
