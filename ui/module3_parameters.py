"""
Module 3: Parameters Summary
Third module for geotechnical analysis - Automated parameter calculations

Features:
- Top bar: [Export CSV], [Export PDF]
- Under top bar: Dropdown to select BH (or "All")
- Calculation using CORE_LOGIC_AND_CALCULATIONS.py
- If lab data exists from Module 2, use it instead of calculated values
- Display summary table with all parameters

Calculated Parameters:
1. γsat - Total Unit Weight (kN/m³)
2. Elevation (m MSL)
3. σv' - Vertical Effective Stress (kN/m²)
4. CN - Correction Factor
5. Ncor - Corrected N-value
6. Su - Undrained Shear Strength (kN/m²) for Clay
7. ϕ' - Effective Friction Angle (degrees) for Sand
8. E/E' - Young's Modulus (kN/m²)
9. ν - Poisson's Ratio
10. K0 - Earth Pressure at Rest Coefficient
11. Rint - Interface Friction
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFileDialog, QMessageBox, QDoubleSpinBox, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import csv
import sys
import os

# Add scripts directory to path to import CORE_LOGIC
scripts_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts')
sys.path.insert(0, scripts_path)
import CORE_LOGIC_AND_CALCULATIONS as calc


def get_consistency(soil_type, n_value=None, su=None):
    """
    Determine soil consistency based on soil type and strength parameters

    For Clay: Based on Su (Undrained Shear Strength)
    For Sand: Based on SPT N-value

    Returns: str like "Very Soft Clay" or "Dense Sand" or None
    """
    if not soil_type:
        return None

    if soil_type == 'Clay':
        # Clay consistency based on Su (kN/m²)
        if su is None:
            return None
        if su < 12:
            return "Very Soft Clay"
        elif su < 25:
            return "Soft Clay"
        elif su < 50:
            return "Hard Clay"
        elif su < 100:
            return "Stiff Clay"
        elif su < 200:
            return "Very Stiff Clay"
        else:
            return "Hard Clay"

    elif soil_type == 'Sand':
        # Sand consistency based on SPT N-value
        if n_value is None:
            return None
        if n_value < 4:
            return "Very Loose Sand"
        elif n_value < 10:
            return "Loose Sand"
        elif n_value < 30:
            return "Medium Dense Sand"
        elif n_value < 50:
            return "Dense Sand"
        else:
            return "Very Dense Sand"

    return None


class Module3Parameters(QWidget):
    """
    Module 3: Parameters Summary - Automated calculations
    Uses CORE_LOGIC_AND_CALCULATIONS.py with data from Modules 1 & 2
    """

    # Signal emitted when results are updated (for Module 4 to refresh plots)
    results_updated = pyqtSignal()

    def __init__(self, parent=None, module1=None, module2=None):
        super().__init__(parent)

        # References to other modules
        self.module1 = module1  # SPT data
        self.module2 = module2  # Lab data

        # Settings for calculations (Ground elevation and water depth now from Module 1)
        self.settings = {
            'structure_type': 'Earth Retaining Structure',
            'method': 'ตอก/กด',
            'surface_type': 'คอนกรีตผิวเรียบ',
            'correction_method': 'Liao and Whitman (1986)'
        }

        # Calculated results storage
        self.results = {}  # {BH_name: [list of result dicts]}
        self.bh_settings = {}  # {BH_name: {'surface_elev': 100.0, 'water_level': 0.0}}

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

        # Results table
        self.table_widget = self._create_table_widget()
        main_layout.addWidget(self.table_widget)

        self.setLayout(main_layout)

    def _create_top_bar(self):
        """Create compact top bar with everything in one row"""
        layout = QHBoxLayout()
        layout.setSpacing(8)

        # Title - compact
        title = QLabel("Module 3")
        title.setFont(QFont("SF Pro Display", 18, QFont.Weight.Bold))
        layout.addWidget(title)

        # Separator
        separator = QLabel("|")
        separator.setStyleSheet("color: #D1D1D6;")
        layout.addWidget(separator)

        # BH Selector - compact
        layout.addWidget(QLabel("BH:"))
        self.bh_selector = QComboBox()
        self.bh_selector.setFont(QFont("SF Pro Display", 14))
        self.bh_selector.setMaximumWidth(110)
        self.bh_selector.currentTextChanged.connect(self.on_bh_selected)
        layout.addWidget(self.bh_selector)

        # Separator
        separator2 = QLabel("|")
        separator2.setStyleSheet("color: #D1D1D6;")
        layout.addWidget(separator2)

        # Settings dropdowns - compact
        layout.addWidget(QLabel("Structure:"))
        self.structure_combo = QComboBox()
        self.structure_combo.setFont(QFont("SF Pro Display", 14))
        self.structure_combo.setMaximumWidth(200)
        self.structure_combo.addItems([
            'Sheet Pile',
            'Earth Retaining Structure',
            'Diaphragm Wall'
        ])
        self.structure_combo.setCurrentText(self.settings['structure_type'])
        self.structure_combo.currentTextChanged.connect(self.on_settings_changed)
        layout.addWidget(self.structure_combo)

        layout.addWidget(QLabel("Method:"))
        self.method_combo = QComboBox()
        self.method_combo.setFont(QFont("SF Pro Display", 14))
        self.method_combo.setMaximumWidth(150)
        self.method_combo.addItems(['ตอก/กด', 'เจาะ'])
        self.method_combo.setCurrentText(self.settings['method'])
        self.method_combo.currentTextChanged.connect(self.on_settings_changed)
        layout.addWidget(self.method_combo)

        layout.addWidget(QLabel("Surface:"))
        self.surface_combo = QComboBox()
        self.surface_combo.setFont(QFont("SF Pro Display", 14))
        self.surface_combo.setMaximumWidth(150)
        self.surface_combo.addItems([
            'คอนกรีตผิวหยาบ',
            'คอนกรีตผิวเรียบ',
            'เหล็กผิวหยาบ',
            'เหล็กผิวเรียบ',
            'ไม้'
        ])
        self.surface_combo.setCurrentText(self.settings['surface_type'])
        self.surface_combo.currentTextChanged.connect(self.on_settings_changed)
        layout.addWidget(self.surface_combo)

        layout.addWidget(QLabel("Correction:"))
        self.correction_combo = QComboBox()
        self.correction_combo.setFont(QFont("SF Pro Display", 14))
        self.correction_combo.setMaximumWidth(200)
        self.correction_combo.addItems([
            'Terzaghi (1984)',
            'Liao and Whitman (1986)'
        ])
        self.correction_combo.setCurrentText(self.settings['correction_method'])
        self.correction_combo.currentTextChanged.connect(self.on_settings_changed)
        layout.addWidget(self.correction_combo)

        layout.addStretch()

        # Info label - compact
        self.info_label = QLabel("Click Calculate")
        self.info_label.setFont(QFont("SF Pro Display", 13))
        self.info_label.setStyleSheet("color: #6E6E73;")
        layout.addWidget(self.info_label)

        # Buttons - compact
        btn_calculate = QPushButton("Calculation")
        btn_calculate.setFont(QFont("SF Pro Display", 13))
        btn_calculate.setMaximumWidth(110)
        btn_calculate.setToolTip("Calculate all parameters")
        btn_calculate.clicked.connect(self.calculate_all)
        layout.addWidget(btn_calculate)

        btn_export_csv = QPushButton("CSV")
        btn_export_csv.setFont(QFont("SF Pro Display", 13))
        btn_export_csv.setMaximumWidth(70)
        btn_export_csv.setToolTip("Export to CSV")
        btn_export_csv.clicked.connect(self.export_csv)
        layout.addWidget(btn_export_csv)

        btn_export_pdf = QPushButton("PDF")
        btn_export_pdf.setFont(QFont("SF Pro Display", 14))
        btn_export_pdf.setMaximumWidth(70)
        btn_export_pdf.setToolTip("Export to PDF")
        btn_export_pdf.clicked.connect(self.export_pdf)
        layout.addWidget(btn_export_pdf)

        return layout

    def _create_settings_panel(self):
        """Create settings panel for calculation parameters"""
        group = QGroupBox("Calculation Settings (Ground Elevation & Water Level from Module 1)")
        form = QFormLayout()

        # Structure type
        self.structure_combo = QComboBox()
        self.structure_combo.addItems([
            'Sheet Pile',
            'Earth Retaining Structure',
            'Diaphragm Wall'
        ])
        self.structure_combo.setCurrentText(self.settings['structure_type'])
        self.structure_combo.currentTextChanged.connect(self.on_settings_changed)
        form.addRow("Structure Type:", self.structure_combo)

        # Construction method
        self.method_combo = QComboBox()
        self.method_combo.addItems(['ตอก/กด', 'เจาะ'])
        self.method_combo.setCurrentText(self.settings['method'])
        self.method_combo.currentTextChanged.connect(self.on_settings_changed)
        form.addRow("Construction Method:", self.method_combo)

        # Surface type
        self.surface_combo = QComboBox()
        self.surface_combo.addItems([
            'คอนกรีตผิวหยาบ',
            'คอนกรีตผิวเรียบ',
            'เหล็กผิวหยาบ',
            'เหล็กผิวเรียบ',
            'ไม้'
        ])
        self.surface_combo.setCurrentText(self.settings['surface_type'])
        self.surface_combo.currentTextChanged.connect(self.on_settings_changed)
        form.addRow("Surface Type:", self.surface_combo)

        # Correction method
        self.correction_combo = QComboBox()
        self.correction_combo.addItems([
            'Terzaghi (1984)',
            'Liao and Whitman (1986)'
        ])
        self.correction_combo.setCurrentText(self.settings['correction_method'])
        self.correction_combo.currentTextChanged.connect(self.on_settings_changed)
        form.addRow("SPT Correction Method:", self.correction_combo)

        group.setLayout(form)
        return group

    def _create_selector_bar(self):
        """Create BH selector bar"""
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Select Borehole:"))

        self.bh_selector = QComboBox()
        self.bh_selector.currentTextChanged.connect(self.on_bh_selected)
        layout.addWidget(self.bh_selector)

        layout.addStretch()

        # Info label
        self.info_label = QLabel("Click 'Calculate Parameters' to start")
        self.info_label.setObjectName("subtitle")
        layout.addWidget(self.info_label)

        return layout

    def _create_table_widget(self):
        """Create table widget for displaying results"""
        table = QTableWidget()
        table.setColumnCount(0)
        table.setRowCount(0)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Read-only
        table.setAlternatingRowColors(True)

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
        """)

        # Apply theme styling - match Module 1 & 2
        table.setFont(QFont("SF Pro Display", 10))
        table.horizontalHeader().setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))

        return table

    def on_settings_changed(self):
        """Handle settings changes"""
        self.settings['structure_type'] = self.structure_combo.currentText()
        self.settings['method'] = self.method_combo.currentText()
        self.settings['surface_type'] = self.surface_combo.currentText()
        self.settings['correction_method'] = self.correction_combo.currentText()

    def on_bh_selected(self, bh_name):
        """Handle BH selection change"""
        if bh_name and bh_name != "All Boreholes":
            self._display_results(bh_name)
        elif bh_name == "All Boreholes":
            self._display_all_results()

    def calculate_all(self):
        """Calculate parameters for all boreholes"""
        if not self.module1:
            QMessageBox.warning(self, "Warning", "Module 1 data is not available!")
            return

        # Get data from Module 1
        module1_data = self.module1.get_data()
        bh_names = module1_data['bh_names']
        depths = module1_data['depths']
        borehole_data = module1_data['borehole_data']
        bh_settings = module1_data.get('bh_settings', {})

        if not bh_names or not depths:
            QMessageBox.warning(self, "Warning", "No data available in Module 1!")
            return

        self.results = {}
        self.bh_settings = bh_settings  # Store bh_settings for Module 4

        # Calculate for each borehole
        for bh_name in bh_names:
            # Get BH-specific settings from Module 1
            bh_setting = bh_settings.get(bh_name, {'surface_elev': 100.0, 'water_level': 0.0})
            ground_elevation = bh_setting['surface_elev']
            water_level_input = bh_setting['water_level']

            # Water level input is ALREADY relative to ground (negative = below)
            # So water_depth = water_level_input directly
            # Example: Surface = 99m, Water Level = -3m means water at 96m MSL
            # For CORE_LOGIC, water_depth = -3 (3m below surface)
            water_depth = water_level_input

            # Find first and last depth with data
            depths_with_data = []
            for depth in depths:
                bh_data = borehole_data[bh_name].get(depth, {})
                spt = bh_data.get('spt')
                classification = bh_data.get('class', '')
                if spt is not None and classification:
                    depths_with_data.append(depth)

            if not depths_with_data:
                continue

            # Get range from first to last depth with data
            first_depth = depths_with_data[0]
            last_depth = depths_with_data[-1]

            # Prepare data for calculation (only depths with SPT data for CORE_LOGIC)
            data_points = []
            for depth in depths_with_data:
                bh_data = borehole_data[bh_name].get(depth, {})
                spt = bh_data.get('spt')
                classification = bh_data.get('class', '')
                data_points.append({
                    'depth': depth,
                    'spt': spt,
                    'classification': classification
                })

            # Prepare borehole data structure for CORE_LOGIC
            bh_calc_data = {
                'name': bh_name,
                'ground_elevation': ground_elevation,
                'water_depth': water_depth,
                'data': data_points
            }

            # Calculate parameters for depths with SPT data
            try:
                calculated_results = calc.calculate_all_parameters(bh_calc_data, self.settings)

                # Create a mapping of depth -> calculated result
                calc_results_map = {r['depth']: r for r in calculated_results}

                # Now create results for ALL depths from first to last
                results = []
                prev_sigma = 0
                prev_depth = 0

                for depth in depths:
                    # Skip depths outside the range
                    if depth < first_depth or depth > last_depth:
                        continue

                    bh_data = borehole_data[bh_name].get(depth, {})

                    # Check if this depth has calculated results
                    if depth in calc_results_map:
                        # Use calculated result
                        result = calc_results_map[depth].copy()
                        # Add source tracking for calculated values
                        result['gamma_sat_source'] = 'Calculated'
                        result['su_source'] = 'Calculated'
                        result['phi_source'] = 'Calculated'
                        prev_sigma = result['sigma_v']
                        prev_depth = depth
                    else:
                        # No SPT data for this depth, create partial result
                        # Calculate only what we can without N-value
                        elevation = ground_elevation - depth

                        # Get lab data if available
                        gamma_sat = None
                        gamma_sat_source = 'Estimated'
                        su = None
                        su_source = None
                        phi = None
                        phi_source = None

                        if self.module2:
                            lab_check = self.module2.has_lab_data(bh_name, depth)

                            # Get gamma_sat from lab
                            if lab_check['has_gamma_sat']:
                                gamma_sat = self.module2.get_lab_value(bh_name, depth, 'gamma_sat')
                                if gamma_sat is not None:
                                    gamma_sat_source = 'Lab'

                            # Get Su from lab
                            if lab_check['has_su']:
                                su = self.module2.get_lab_value(bh_name, depth, 'su')
                                if su is not None:
                                    su_source = 'Lab'

                            # Get Phi from lab
                            if lab_check['has_phi']:
                                phi = self.module2.get_lab_value(bh_name, depth, 'phi')
                                if phi is not None:
                                    phi_source = 'Lab'

                        # If no lab gamma_sat, estimate from previous layer or use default
                        if gamma_sat is None:
                            if results and 'gamma_sat' in results[-1]:
                                gamma_sat = results[-1]['gamma_sat']
                            else:
                                gamma_sat = 18  # Default value
                            gamma_sat_source = 'Estimated'

                        # Calculate effective stress (continuous)
                        water_level_msl = ground_elevation + water_depth
                        if elevation > water_level_msl:
                            # Above water table
                            sigma_v = prev_sigma + gamma_sat * (depth - prev_depth)
                        else:
                            if prev_depth >= 0 and ground_elevation - prev_depth > water_level_msl:
                                # Transition through water table
                                depth_to_water = ground_elevation - water_level_msl
                                thickness_above = depth_to_water - prev_depth
                                thickness_below = depth - depth_to_water
                                sigma_v = prev_sigma + gamma_sat * thickness_above + (gamma_sat - 9.81) * thickness_below
                            else:
                                # Fully below water table
                                sigma_v = prev_sigma + (gamma_sat - 9.81) * (depth - prev_depth)

                        result = {
                            'depth': depth,
                            'elevation': elevation,
                            'gamma_sat': gamma_sat,
                            'gamma_sat_source': gamma_sat_source,
                            'classification': bh_data.get('class', ''),
                            'soil_type': '',
                            'n_value': None,
                            'sigma_v': sigma_v,
                            'cn': None,
                            'ncor': None,
                            'su': su,
                            'su_source': su_source,
                            'phi': phi,
                            'phi_source': phi_source,
                            'e_modulus': None,
                            'poisson': None,
                            'k0': None,
                            'rint': None
                        }

                        prev_sigma = sigma_v
                        prev_depth = depth

                    results.append(result)

                # Override with lab data if available
                if self.module2:
                    for result in results:
                        depth = result['depth']
                        lab_check = self.module2.has_lab_data(bh_name, depth)

                        # Override gamma_sat if lab data exists
                        if lab_check['has_gamma_sat']:
                            lab_gamma_sat = self.module2.get_lab_value(bh_name, depth, 'gamma_sat')
                            if lab_gamma_sat is not None:
                                result['gamma_sat'] = lab_gamma_sat
                                result['gamma_sat_source'] = 'Lab'
                            else:
                                result['gamma_sat_source'] = 'Calculated'
                        else:
                            result['gamma_sat_source'] = 'Calculated'

                        # Override Su if lab data exists
                        if lab_check['has_su']:
                            lab_su = self.module2.get_lab_value(bh_name, depth, 'su')
                            if lab_su is not None:
                                result['su'] = lab_su
                                result['su_source'] = 'Lab'
                            else:
                                result['su_source'] = 'Calculated'
                        else:
                            result['su_source'] = 'Calculated'

                        # Override Phi if lab data exists
                        if lab_check['has_phi']:
                            lab_phi = self.module2.get_lab_value(bh_name, depth, 'phi')
                            if lab_phi is not None:
                                result['phi'] = lab_phi
                                result['phi_source'] = 'Lab'
                            else:
                                result['phi_source'] = 'Calculated'
                        else:
                            result['phi_source'] = 'Calculated'

                # Calculate consistency for all results
                for result in results:
                    soil_type = result.get('soil_type', '')
                    n_value = result.get('n_value')
                    su = result.get('su')
                    result['consistency'] = get_consistency(soil_type, n_value, su)

                self.results[bh_name] = results

            except Exception as e:
                QMessageBox.critical(
                    self, "Calculation Error",
                    f"Failed to calculate parameters for {bh_name}:\n{str(e)}"
                )
                continue

        # Update BH selector
        self.bh_selector.clear()
        self.bh_selector.addItem("All Boreholes")
        self.bh_selector.addItems(list(self.results.keys()))

        # Display first BH results
        if self.results:
            first_bh = list(self.results.keys())[0]
            self.bh_selector.setCurrentText(first_bh)
            self.info_label.setText(f"Calculated parameters for {len(self.results)} borehole(s)")
            # Notify Module 4 that results are available
            self.results_updated.emit()
        else:
            QMessageBox.warning(self, "Warning", "No results calculated. Check your input data.")

    def update_lab_overrides(self):
        """Update lab data overrides in existing results without full recalculation.
        Called automatically when Module 2 lab data changes."""
        if not self.results or not self.module2:
            return

        for bh_name, results in self.results.items():
            for result in results:
                depth = result['depth']
                lab_check = self.module2.has_lab_data(bh_name, depth)

                # Override gamma_sat if lab data exists
                if lab_check['has_gamma_sat']:
                    lab_gamma_sat = self.module2.get_lab_value(bh_name, depth, 'gamma_sat')
                    if lab_gamma_sat is not None:
                        result['gamma_sat'] = lab_gamma_sat
                        result['gamma_sat_source'] = 'Lab'
                elif result.get('gamma_sat_source') == 'Lab':
                    # Lab data was removed, revert to Calculated (keep current value)
                    result['gamma_sat_source'] = 'Calculated'

                # Override Su if lab data exists
                if lab_check['has_su']:
                    lab_su = self.module2.get_lab_value(bh_name, depth, 'su')
                    if lab_su is not None:
                        result['su'] = lab_su
                        result['su_source'] = 'Lab'
                elif result.get('su_source') == 'Lab':
                    result['su_source'] = 'Calculated'

                # Override Phi if lab data exists
                if lab_check['has_phi']:
                    lab_phi = self.module2.get_lab_value(bh_name, depth, 'phi')
                    if lab_phi is not None:
                        result['phi'] = lab_phi
                        result['phi_source'] = 'Lab'
                elif result.get('phi_source') == 'Lab':
                    result['phi_source'] = 'Calculated'

        # Refresh the display
        current_bh = self.bh_selector.currentText()
        if current_bh == "All Boreholes":
            self._display_all_results()
        elif current_bh:
            self._display_results(current_bh)

        # Notify Module 4 that results changed
        self.results_updated.emit()

    def _display_results(self, bh_name):
        """Display results for a specific borehole"""
        if bh_name not in self.results:
            return

        results = self.results[bh_name]

        # Get BH settings for elevation display
        bh_setting = self.bh_settings.get(bh_name, {'surface_elev': 100.0})
        surface_elev = bh_setting['surface_elev']

        # Define columns
        columns = [
            ('Depth\n(m)', 'depth'),
            ('Elev\n(m)', 'elevation'),
            ('Class', 'classification'),
            ('Type', 'soil_type'),
            ('Consistency', 'consistency'),
            ('N', 'n_value'),
            ('γsat\n(kN/m³)', 'gamma_sat'),
            ('σv\'\n(kN/m²)', 'sigma_v'),
            ('CN', 'cn'),
            ('Ncor', 'ncor'),
            ('Su\n(kN/m²)', 'su'),
            ('ϕ\'\n(°)', 'phi'),
            ('E/E\'\n(kN/m²)', 'e_modulus'),
            ('ν', 'poisson'),
            ('K0', 'k0'),
            ('Rint', 'rint')
        ]

        # Setup table with BH header row
        self.table_widget.setRowCount(len(results) + 1)  # +1 for header row
        self.table_widget.setColumnCount(len(columns))
        self.table_widget.setHorizontalHeaderLabels([col[0] for col in columns])

        # Add BH header row (merged across all columns)
        bh_header = QTableWidgetItem(f" {bh_name} (El. {surface_elev:.2f}m) ")
        bh_header.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        bh_header.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        bh_header.setBackground(QColor("#FFFFFF"))
        self.table_widget.setItem(0, 0, bh_header)
        self.table_widget.setSpan(0, 0, 1, len(columns))  # Merge all columns

        # Fill data (starting from row 1)
        for row, result in enumerate(results, start=1):
            for col, (header, key) in enumerate(columns):
                value = result.get(key)

                if value is None:
                    item = QTableWidgetItem('-')
                elif isinstance(value, float):
                    # Add * if value is from Lab
                    text = f"{value:.2f}"
                    if key == 'gamma_sat' and result.get('gamma_sat_source') == 'Lab':
                        text += " *"
                    elif key == 'su' and result.get('su_source') == 'Lab':
                        text += " *"
                    elif key == 'phi' and result.get('phi_source') == 'Lab':
                        text += " *"
                    item = QTableWidgetItem(text)
                elif isinstance(value, int):
                    item = QTableWidgetItem(str(value))
                else:
                    item = QTableWidgetItem(str(value) if value else '-')

                item.setFont(QFont("SF Pro Display", 9))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Highlight lab data with green background
                if key == 'gamma_sat' and result.get('gamma_sat_source') == 'Lab':
                    item.setBackground(QColor('#D4EDDA'))  # Light green
                    item.setToolTip("Value from Laboratory Data (Module 2)")
                elif key == 'su' and result.get('su_source') == 'Lab':
                    item.setBackground(QColor('#D4EDDA'))  # Light green
                    item.setToolTip("Value from Laboratory Data (Module 2)")
                elif key == 'phi' and result.get('phi_source') == 'Lab':
                    item.setBackground(QColor('#D4EDDA'))  # Light green
                    item.setToolTip("Value from Laboratory Data (Module 2)")

                self.table_widget.setItem(row, col, item)

        # Set column widths - wider for Consistency column
        for col, (_, key) in enumerate(columns):
            self.table_widget.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            if key == 'consistency':
                self.table_widget.setColumnWidth(col, 150)  # Wider for "Medium Dense Sand"
            else:
                self.table_widget.setColumnWidth(col, 100)

    def _display_all_results(self):
        """Display results for all boreholes - separate tables stacked vertically"""
        if not self.results:
            return

        # Calculate total rows needed: sum of rows for each borehole + header rows between them
        total_rows = 0
        for bh_name, results in self.results.items():
            total_rows += 1  # Header row for BH name
            total_rows += len(results)  # Data rows
            total_rows += 1  # Spacing row between boreholes

        # Define columns (without BH column since each section has its own header)
        columns = [
            ('Depth\n(m)', 'depth'),
            ('Elev\n(m)', 'elevation'),
            ('Class', 'classification'),
            ('Type', 'soil_type'),
            ('Consistency', 'consistency'),
            ('N', 'n_value'),
            ('γsat\n(kN/m³)', 'gamma_sat'),
            ('σv\'\n(kN/m²)', 'sigma_v'),
            ('CN', 'cn'),
            ('Ncor', 'ncor'),
            ('Su\n(kN/m²)', 'su'),
            ('ϕ\'\n(°)', 'phi'),
            ('E/E\'\n(kN/m²)', 'e_modulus'),
            ('ν', 'poisson'),
            ('K0', 'k0'),
            ('Rint', 'rint')
        ]


        # Setup table
        self.table_widget.setRowCount(total_rows)
        self.table_widget.setColumnCount(len(columns))
        self.table_widget.setHorizontalHeaderLabels([col[0] for col in columns])

        # Fill data for each borehole
        current_row = 0
        for bh_name, results in self.results.items():
            # Get BH settings for elevation display
            bh_setting = self.bh_settings.get(bh_name, {'surface_elev': 100.0})
            surface_elev = bh_setting['surface_elev']

            # Add BH header row (merged across all columns)
            bh_header = QTableWidgetItem(f" {bh_name} (El. {surface_elev:.2f}m) ")
            bh_header.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
            bh_header.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            bh_header.setBackground(QColor("#FFFFFF"))
            self.table_widget.setItem(current_row, 0, bh_header)
            self.table_widget.setSpan(current_row, 0, 1, len(columns))  # Merge all columns
            current_row += 1

            # Add data rows for this borehole
            for result in results:
                for col, (header, key) in enumerate(columns):
                    value = result.get(key)

                    if value is None:
                        item = QTableWidgetItem('-')
                    elif isinstance(value, float):
                        # Add * if value is from Lab
                        text = f"{value:.2f}"
                        if key == 'gamma_sat' and result.get('gamma_sat_source') == 'Lab':
                            text += " *"
                        elif key == 'su' and result.get('su_source') == 'Lab':
                            text += " *"
                        elif key == 'phi' and result.get('phi_source') == 'Lab':
                            text += " *"
                        item = QTableWidgetItem(text)
                    elif isinstance(value, int):
                        item = QTableWidgetItem(str(value))
                    else:
                        item = QTableWidgetItem(str(value))

                    item.setFont(QFont("SF Pro Display", 9))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Highlight lab data
                    if key == 'gamma_sat' and result.get('gamma_sat_source') == 'Lab':
                        item.setBackground(QColor('#D4EDDA'))
                        item.setToolTip("Value from Laboratory Data (Module 2)")
                    elif key == 'su' and result.get('su_source') == 'Lab':
                        item.setBackground(QColor('#D4EDDA'))
                        item.setToolTip("Value from Laboratory Data (Module 2)")
                    elif key == 'phi' and result.get('phi_source') == 'Lab':
                        item.setBackground(QColor('#D4EDDA'))
                        item.setToolTip("Value from Laboratory Data (Module 2)")

                    self.table_widget.setItem(current_row, col, item)
                current_row += 1

            # Add spacing row (empty row with light gray background)
            for col in range(len(columns)):
                spacer = QTableWidgetItem("")
                spacer.setBackground(QColor('#F5F5F7'))
                self.table_widget.setItem(current_row, col, spacer)
            current_row += 1

        # Set column widths - wider for Consistency column
        for col, (_, key) in enumerate(columns):
            self.table_widget.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            if key == 'consistency':
                self.table_widget.setColumnWidth(col, 150)  # Wider for "Medium Dense Sand"
            else:
                self.table_widget.setColumnWidth(col, 100)

    def export_csv(self):
        """Export results to CSV"""
        if not self.results:
            QMessageBox.warning(self, "Warning", "No results to export. Calculate parameters first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)

                # Write data matching All Borehole table exactly
                for bh_name, results in self.results.items():
                    # Get BH settings for elevation display in header
                    bh_setting = self.bh_settings.get(bh_name, {'surface_elev': 100.0})
                    surface_elev = bh_setting['surface_elev']

                    # Write BH header row (matching table display)
                    writer.writerow([f"{bh_name} (El. {surface_elev:.2f}m)"])

                    # Write column headers (matching table columns exactly)
                    headers = [
                        'Depth (m)', 'Elev (m)', 'Class', 'Type', 'Consistency',
                        'N', 'γsat (kN/m³)', 'σv\' (kN/m²)', 'CN', 'Ncor',
                        'Su (kN/m²)', 'ϕ\' (°)', 'E/E\' (kN/m²)', 'ν', 'K0', 'Rint'
                    ]
                    writer.writerow(headers)

                    # Write data rows
                    for result in results:
                        # Format values with * for lab data (matching table display)
                        gamma_sat_val = f"{result.get('gamma_sat', ''):.2f}" if result.get('gamma_sat') else '-'
                        if result.get('gamma_sat_source') == 'Lab' and result.get('gamma_sat'):
                            gamma_sat_val += " *"

                        su_val = f"{result.get('su', ''):.2f}" if result.get('su') else '-'
                        if result.get('su_source') == 'Lab' and result.get('su'):
                            su_val += " *"

                        phi_val = f"{result.get('phi', ''):.2f}" if result.get('phi') else '-'
                        if result.get('phi_source') == 'Lab' and result.get('phi'):
                            phi_val += " *"

                        row = [
                            f"{result.get('depth', ''):.2f}" if result.get('depth') is not None else '-',
                            f"{result.get('elevation', ''):.2f}" if result.get('elevation') is not None else '-',
                            result.get('classification', '') if result.get('classification') else '-',
                            result.get('soil_type', '') if result.get('soil_type') else '-',
                            result.get('consistency', '') if result.get('consistency') else '-',
                            str(result.get('n_value', '')) if result.get('n_value') is not None else '-',
                            gamma_sat_val,
                            f"{result.get('sigma_v', ''):.2f}" if result.get('sigma_v') is not None else '-',
                            f"{result.get('cn', ''):.3f}" if result.get('cn') is not None else '-',
                            f"{result.get('ncor', ''):.2f}" if result.get('ncor') is not None else '-',
                            su_val,
                            phi_val,
                            f"{result.get('e_modulus', ''):.0f}" if result.get('e_modulus') is not None else '-',
                            f"{result.get('poisson', ''):.3f}" if result.get('poisson') is not None else '-',
                            f"{result.get('k0', ''):.3f}" if result.get('k0') is not None else '-',
                            f"{result.get('rint', ''):.2f}" if result.get('rint') is not None else '-'
                        ]
                        writer.writerow(row)

                    # Add blank row between boreholes (matching table display)
                    writer.writerow([])

            QMessageBox.information(self, "Success", "Results exported to CSV successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export CSV: {str(e)}")

    def export_pdf(self):
        """Export results to PDF with user selection"""
        if not self.results:
            QMessageBox.warning(self, "Warning", "No results to export. Calculate parameters first.")
            return

        # Ask user what to export
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox, QLabel, QButtonGroup

        dialog = QDialog(self)
        dialog.setWindowTitle("Export to PDF")
        dialog.setMinimumWidth(350)
        layout = QVBoxLayout()

        # Title
        title = QLabel("Select export option:")
        title.setFont(QFont("SF Pro Display", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Radio buttons
        button_group = QButtonGroup(dialog)
        radio_all = QRadioButton("All Boreholes (Combined)")
        radio_all.setFont(QFont("SF Pro Display", 11))
        radio_all.setChecked(True)
        button_group.addButton(radio_all)
        layout.addWidget(radio_all)

        radio_separate = QRadioButton("Separate files for each borehole")
        radio_separate.setFont(QFont("SF Pro Display", 11))
        button_group.addButton(radio_separate)
        layout.addWidget(radio_separate)

        # OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            if radio_all.isChecked():
                self._export_pdf_all()
            else:
                self._export_pdf_separate()

    def _export_pdf_all(self):
        """Export all boreholes to a single PDF"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export PDF - All Boreholes", "", "PDF Files (*.pdf)")
        if not file_path:
            return

        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm

            # Create PDF
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4),
                                   leftMargin=1*cm, rightMargin=1*cm,
                                   topMargin=1*cm, bottomMargin=1*cm)
            elements = []
            styles = getSampleStyleSheet()

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=20,
                alignment=1  # Center
            )
            elements.append(Paragraph("Geotechnical Parameters - All Boreholes", title_style))
            elements.append(Spacer(1, 0.5*cm))

            # Define column headers
            headers = ['Depth\n(m)', 'Elev\n(m)', 'Class', 'Type', 'Consistency', 'N',
                      'γsat\n(kN/m³)', 'σv\'\n(kN/m²)', 'CN', 'Ncor',
                      'Su\n(kN/m²)', 'ϕ\'\n(°)', 'E/E\'\n(kN/m²)', 'ν', 'K0', 'Rint']

            # Process each borehole
            for bh_idx, (bh_name, results) in enumerate(self.results.items()):
                # Get BH settings for elevation
                bh_setting = self.bh_settings.get(bh_name, {'surface_elev': 100.0})
                surface_elev = bh_setting['surface_elev']

                # BH Header
                bh_header_style = ParagraphStyle(
                    'BHHeader',
                    parent=styles['Heading2'],
                    fontSize=12,
                    textColor=colors.HexColor('#000000'),
                    spaceAfter=10,
                    alignment=0  # Left
                )
                elements.append(Paragraph(f"<b>{bh_name} (El. {surface_elev:.2f}m)</b>", bh_header_style))

                # Prepare table data
                table_data = [headers]

                for result in results:
                    # Format values with * for lab data
                    gamma_sat_val = f"{result.get('gamma_sat', ''):.2f}" if result.get('gamma_sat') else '-'
                    if result.get('gamma_sat_source') == 'Lab' and result.get('gamma_sat'):
                        gamma_sat_val += " *"

                    su_val = f"{result.get('su', ''):.2f}" if result.get('su') else '-'
                    if result.get('su_source') == 'Lab' and result.get('su'):
                        su_val += " *"

                    phi_val = f"{result.get('phi', ''):.2f}" if result.get('phi') else '-'
                    if result.get('phi_source') == 'Lab' and result.get('phi'):
                        phi_val += " *"

                    row = [
                        f"{result.get('depth', ''):.2f}" if result.get('depth') is not None else '-',
                        f"{result.get('elevation', ''):.2f}" if result.get('elevation') is not None else '-',
                        result.get('classification', '') if result.get('classification') else '-',
                        result.get('soil_type', '') if result.get('soil_type') else '-',
                        result.get('consistency', '') if result.get('consistency') else '-',
                        str(result.get('n_value', '')) if result.get('n_value') is not None else '-',
                        gamma_sat_val,
                        f"{result.get('sigma_v', ''):.2f}" if result.get('sigma_v') is not None else '-',
                        f"{result.get('cn', ''):.3f}" if result.get('cn') is not None else '-',
                        f"{result.get('ncor', ''):.2f}" if result.get('ncor') is not None else '-',
                        su_val,
                        phi_val,
                        f"{result.get('e_modulus', ''):.0f}" if result.get('e_modulus') is not None else '-',
                        f"{result.get('poisson', ''):.3f}" if result.get('poisson') is not None else '-',
                        f"{result.get('k0', ''):.3f}" if result.get('k0') is not None else '-',
                        f"{result.get('rint', ''):.2f}" if result.get('rint') is not None else '-'
                    ]
                    table_data.append(row)

                # Create table with custom column widths
                col_widths = [
                    1.3*cm,  # Depth
                    1.3*cm,  # Elev
                    1.2*cm,  # Class
                    1.2*cm,  # Type
                    2.2*cm,  # Consistency (wider)
                    1.0*cm,  # N
                    1.3*cm,  # γsat
                    1.4*cm,  # σv'
                    1.0*cm,  # CN
                    1.2*cm,  # Ncor
                    1.3*cm,  # Su
                    1.2*cm,  # ϕ'
                    1.5*cm,  # E/E'
                    0.9*cm,  # ν
                    1.0*cm,  # K0
                    1.1*cm   # Rint
                ]
                table = Table(table_data, colWidths=col_widths)

                # Table style
                table.setStyle(TableStyle([
                    # Header row
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E5EA')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 7),
                    ('FONTSIZE', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))

                elements.append(table)

                # Add page break between boreholes (except for last one)
                if bh_idx < len(self.results) - 1:
                    elements.append(PageBreak())

            # Build PDF
            doc.build(elements)
            QMessageBox.information(self, "Success", f"PDF exported successfully to:\n{file_path}")

        except ImportError:
            QMessageBox.critical(
                self, "Error",
                "ReportLab library not found.\nPlease install it using: pip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}")

    def _export_pdf_separate(self):
        """Export each borehole to separate PDF files"""
        from PyQt6.QtWidgets import QFileDialog

        # Ask for directory
        directory = QFileDialog.getExistingDirectory(self, "Select Directory for PDF Files")
        if not directory:
            return

        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            import os

            styles = getSampleStyleSheet()
            exported_files = []

            # Define column headers
            headers = ['Depth\n(m)', 'Elev\n(m)', 'Class', 'Type', 'Consistency', 'N',
                      'γsat\n(kN/m³)', 'σv\'\n(kN/m²)', 'CN', 'Ncor',
                      'Su\n(kN/m²)', 'ϕ\'\n(°)', 'E/E\'\n(kN/m²)', 'ν', 'K0', 'Rint']

            # Export each borehole
            for bh_name, results in self.results.items():
                # Create file path
                safe_filename = bh_name.replace('/', '_').replace('\\', '_')
                file_path = os.path.join(directory, f"{safe_filename}_parameters.pdf")

                # Get BH settings
                bh_setting = self.bh_settings.get(bh_name, {'surface_elev': 100.0})
                surface_elev = bh_setting['surface_elev']

                # Create PDF
                doc = SimpleDocTemplate(file_path, pagesize=landscape(A4),
                                       leftMargin=1*cm, rightMargin=1*cm,
                                       topMargin=1*cm, bottomMargin=1*cm)
                elements = []

                # Title
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    textColor=colors.HexColor('#1a1a1a'),
                    spaceAfter=10,
                    alignment=1
                )
                elements.append(Paragraph(f"Geotechnical Parameters", title_style))

                subtitle_style = ParagraphStyle(
                    'Subtitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    textColor=colors.HexColor('#333333'),
                    spaceAfter=20,
                    alignment=1
                )
                elements.append(Paragraph(f"{bh_name} (El. {surface_elev:.2f}m)", subtitle_style))

                # Prepare table data
                table_data = [headers]

                for result in results:
                    # Format values with * for lab data
                    gamma_sat_val = f"{result.get('gamma_sat', ''):.2f}" if result.get('gamma_sat') else '-'
                    if result.get('gamma_sat_source') == 'Lab' and result.get('gamma_sat'):
                        gamma_sat_val += " *"

                    su_val = f"{result.get('su', ''):.2f}" if result.get('su') else '-'
                    if result.get('su_source') == 'Lab' and result.get('su'):
                        su_val += " *"

                    phi_val = f"{result.get('phi', ''):.2f}" if result.get('phi') else '-'
                    if result.get('phi_source') == 'Lab' and result.get('phi'):
                        phi_val += " *"

                    row = [
                        f"{result.get('depth', ''):.2f}" if result.get('depth') is not None else '-',
                        f"{result.get('elevation', ''):.2f}" if result.get('elevation') is not None else '-',
                        result.get('classification', '') if result.get('classification') else '-',
                        result.get('soil_type', '') if result.get('soil_type') else '-',
                        result.get('consistency', '') if result.get('consistency') else '-',
                        str(result.get('n_value', '')) if result.get('n_value') is not None else '-',
                        gamma_sat_val,
                        f"{result.get('sigma_v', ''):.2f}" if result.get('sigma_v') is not None else '-',
                        f"{result.get('cn', ''):.3f}" if result.get('cn') is not None else '-',
                        f"{result.get('ncor', ''):.2f}" if result.get('ncor') is not None else '-',
                        su_val,
                        phi_val,
                        f"{result.get('e_modulus', ''):.0f}" if result.get('e_modulus') is not None else '-',
                        f"{result.get('poisson', ''):.3f}" if result.get('poisson') is not None else '-',
                        f"{result.get('k0', ''):.3f}" if result.get('k0') is not None else '-',
                        f"{result.get('rint', ''):.2f}" if result.get('rint') is not None else '-'
                    ]
                    table_data.append(row)

                # Create table with custom column widths
                col_widths = [
                    1.3*cm,  # Depth
                    1.3*cm,  # Elev
                    1.2*cm,  # Class
                    1.2*cm,  # Type
                    2.2*cm,  # Consistency (wider)
                    1.0*cm,  # N
                    1.3*cm,  # γsat
                    1.4*cm,  # σv'
                    1.0*cm,  # CN
                    1.2*cm,  # Ncor
                    1.3*cm,  # Su
                    1.2*cm,  # ϕ'
                    1.5*cm,  # E/E'
                    0.9*cm,  # ν
                    1.0*cm,  # K0
                    1.1*cm   # Rint
                ]
                table = Table(table_data, colWidths=col_widths)

                # Table style
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E5EA')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 7),
                    ('FONTSIZE', (0, 1), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))

                elements.append(table)

                # Build PDF
                doc.build(elements)
                exported_files.append(safe_filename)

            QMessageBox.information(
                self, "Success",
                f"Exported {len(exported_files)} PDF files to:\n{directory}\n\nFiles:\n" +
                "\n".join([f"- {f}_parameters.pdf" for f in exported_files[:5]]) +
                (f"\n... and {len(exported_files) - 5} more" if len(exported_files) > 5 else "")
            )

        except ImportError:
            QMessageBox.critical(
                self, "Error",
                "ReportLab library not found.\nPlease install it using: pip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export PDF: {str(e)}")

    def get_results(self):
        """Get calculated results (for use by Module 4)"""
        return {
            'results': self.results,
            'bh_settings': self.bh_settings
        }

    def get_project_data(self):
        """Get all data for project save"""
        return {
            'settings': self.settings,
            'results': self.results,
            'bh_settings': self.bh_settings
        }

    def load_project_data(self, data):
        """Load project data and update UI"""
        try:
            # Load settings
            self.settings = data.get('settings', self.settings)
            self.results = data.get('results', {})
            self.bh_settings = data.get('bh_settings', {})

            # Update UI with loaded settings
            self._update_settings_ui()

            # Update BH selector if we have results
            if self.results:
                self.bh_selector.clear()
                self.bh_selector.addItem("All Boreholes")
                self.bh_selector.addItems(list(self.results.keys()))

                # Display first BH or All Boreholes
                if list(self.results.keys()):
                    self.bh_selector.setCurrentText(list(self.results.keys())[0])
                    self.info_label.setText(f"Loaded {len(self.results)} borehole(s)")

        except Exception as e:
            print(f"Error loading Module 3 data: {e}")

    def _update_settings_ui(self):
        """Update UI controls with current settings"""
        # Update dropdowns to match loaded settings
        structure_idx = self.structure_combo.findText(self.settings.get('structure_type', 'Earth Retaining Structure'))
        if structure_idx >= 0:
            self.structure_combo.setCurrentIndex(structure_idx)

        method_idx = self.method_combo.findText(self.settings.get('method', 'ตอก/กด'))
        if method_idx >= 0:
            self.method_combo.setCurrentIndex(method_idx)

        surface_idx = self.surface_combo.findText(self.settings.get('surface_type', 'คอนกรีตผิวเรียบ'))
        if surface_idx >= 0:
            self.surface_combo.setCurrentIndex(surface_idx)

        correction_idx = self.correction_combo.findText(self.settings.get('correction_method', 'Liao and Whitman (1986)'))
        if correction_idx >= 0:
            self.correction_combo.setCurrentIndex(correction_idx)
