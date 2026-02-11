"""
Module 5: Soil Profile
Manual soil profile creation with visualization
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QFileDialog, QMessageBox, QLineEdit, QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches
import numpy as np


# Soil types configuration
SOIL_TYPES = {
    'Fill': {
        'color': '#8B7355',
        'pattern': 'dots_on_dark',
        'description': 'Fill Material'
    },
    'Topsoil': {
        'color': '#654321',
        'pattern': 'wavy_dots',
        'description': 'Topsoil/Organic'
    },
    'Very Soft Clay': {
        'color': '#C8C8C8',
        'pattern': 'none',
        'description': 'Very Soft Clay'
    },
    'Soft Clay': {
        'color': '#B0B0B0',
        'pattern': 'horizontal_sparse',
        'description': 'Soft Clay'
    },
    'Medium Stiff Clay': {
        'color': '#989898',
        'pattern': 'horizontal_dense',
        'description': 'Medium Stiff Clay'
    },
    'Stiff Clay': {
        'color': '#808080',
        'pattern': 'horizontal_thick',
        'description': 'Stiff Clay'
    },
    'Very Stiff Clay': {
        'color': '#787878',
        'pattern': 'horizontal_thick',
        'description': 'Very Stiff Clay'
    },
    'Hard Clay': {
        'color': '#707070',
        'pattern': 'crosshatch',
        'description': 'Hard Clay'
    },
    'Loose Sand': {
        'color': '#F4E4C1',
        'pattern': 'stipple_light',
        'description': 'Loose Sand'
    },
    'Medium Dense Sand': {
        'color': '#E6D7A8',
        'pattern': 'stipple_medium',
        'description': 'Medium Dense Sand'
    },
    'Dense Sand': {
        'color': '#D4C48D',
        'pattern': 'stipple_dense',
        'description': 'Dense Sand'
    },
    'Very Dense Sand': {
        'color': '#C4B67D',
        'pattern': 'stipple_heavy',
        'description': 'Very Dense Sand'
    },
    'Gravel': {
        'color': '#B8956A',
        'pattern': 'circles',
        'description': 'Gravel'
    },
    'Rock': {
        'color': "#353535",
        'pattern': 'circles',
        'description': 'Rock/Bedrock'
    }
}


class SoilProfileCanvas(FigureCanvasQTAgg):
    """Canvas for drawing soil profile with matplotlib"""

    def __init__(self, parent=None, width=6, height=10):
        self.fig = Figure(figsize=(width, height), facecolor='white')
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)

    def plot_profile(self, layers, water_level=None, ground_elevation=100.0):
        """Plot soil profile"""
        self.ax.clear()

        if not layers:
            self.ax.text(0.5, 0.5, 'No layers defined\nAdd rows to create profile',
                        ha='center', va='center', fontsize=12, color='gray')
            self.draw()
            return

        # Setup axes
        min_elev = min([layer['to_elev'] for layer in layers])
        max_elev = 100.0  # Fixed to 100 as requested

        # Add some margin
        elev_range = max_elev - min_elev
        margin = elev_range * 0.05

        self.ax.set_xlim(-0.5, 3.5)  # Extended for description text
        self.ax.set_ylim(min_elev - margin, max_elev + margin)

        # Draw layers
        for layer in layers:
            from_elev = layer['from_elev']
            to_elev = layer['to_elev']
            soil_type = layer['soil_type']
            n_value = layer.get('n_value', '-')
            height = from_elev - to_elev

            if height <= 0:
                continue

            # Get soil config
            soil_config = SOIL_TYPES.get(soil_type, {
                'color': '#CCCCCC',
                'pattern': 'none'
            })

            # Draw layer rectangle
            rect = Rectangle((0, to_elev), 1, height,
                           facecolor=soil_config['color'],
                           edgecolor='black',
                           linewidth=1.5)
            self.ax.add_patch(rect)

            # Add pattern
            self._add_pattern(soil_config['pattern'], 0, to_elev, 1, height)

            # Add soil type label without background box
            mid_elev = (from_elev + to_elev) / 2
            self.ax.text(0.5, mid_elev, soil_type,
                        ha='center', va='center',
                        fontsize=7, fontweight='bold')

            # Add N-value on right side
            n_text = str(n_value) if n_value not in [None, '-', ''] else '-'
            self.ax.text(1.5, mid_elev, n_text,
                        ha='center', va='center',
                        fontsize=7, fontweight='bold')

            # Add description on far right
            description = layer.get('description', '')
            if description:
                self.ax.text(2.1, mid_elev, description,
                            ha='left', va='center',
                            fontsize=7, style='italic', color='#333333')

            # Add elevation labels
            self.ax.text(-0.1, from_elev, f"{from_elev:.2f}",
                        ha='right', va='center', fontsize=7)
            self.ax.text(-0.1, to_elev, f"{to_elev:.2f}",
                        ha='right', va='center', fontsize=7)

        # Draw water level
        if water_level is not None:
            water_elev = ground_elevation + water_level  # water_level is negative
            if min_elev <= water_elev <= max_elev:
                self.ax.axhline(y=water_elev, color='blue', linestyle='--',
                              linewidth=2, alpha=0.7)
                # Add WL label above the line
                self.ax.text(1.8, water_elev, f'WL. {water_level:.2f}',
                           ha='left', va='bottom',
                           fontsize=9, color='blue', fontweight='bold')

        # Labels - Place title above the plot area
        self.ax.set_ylabel('Elevation (m)', fontsize=10, fontweight='bold')
        self.ax.text(0.5, max_elev + margin*0.8, 'Soil Profile',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        self.ax.text(1.5, max_elev + margin*0.8, 'SPT-N',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Remove top and right spines
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_visible(False)

        # Remove x-axis ticks
        self.ax.set_xticks([])

        self.fig.tight_layout()
        self.draw()

    def _add_pattern(self, pattern_type, x, y, width, height):
        """Add pattern overlay to layer"""
        if pattern_type == 'none' or height <= 0 or width <= 0:
            return

        elif pattern_type == 'horizontal_sparse':
            num_lines = max(3, int(height * 2))
            for i in range(num_lines):
                y_pos = y + (i + 0.5) * height / num_lines
                self.ax.plot([x, x + width], [y_pos, y_pos],
                           'k-', linewidth=0.5, alpha=0.6)

        elif pattern_type == 'horizontal_dense':
            num_lines = max(5, int(height * 4))
            for i in range(num_lines):
                y_pos = y + (i + 0.5) * height / num_lines
                self.ax.plot([x, x + width], [y_pos, y_pos],
                           'k-', linewidth=0.5, alpha=0.7)

        elif pattern_type == 'horizontal_thick':
            num_lines = max(3, int(height * 2))
            for i in range(num_lines):
                y_pos = y + (i + 0.5) * height / num_lines
                self.ax.plot([x, x + width], [y_pos, y_pos],
                           'k-', linewidth=1.5, alpha=0.8)

        elif pattern_type == 'crosshatch':
            num_lines = max(3, int(height * 2))
            for i in range(num_lines):
                y_pos = y + (i + 0.5) * height / num_lines
                self.ax.plot([x, x + width], [y_pos, y_pos],
                           'k-', linewidth=1.5, alpha=0.8)
            num_v_lines = max(2, int(width * 10))
            for i in range(num_v_lines):
                x_pos = x + (i + 0.5) * width / num_v_lines
                self.ax.plot([x_pos, x_pos], [y, y + height],
                           'k-', linewidth=0.8, alpha=0.6)

        elif pattern_type in ['stipple_light', 'stipple_medium', 'stipple_dense', 'stipple_heavy']:
            density_map = {
                'stipple_light': 20,
                'stipple_medium': 40,
                'stipple_dense': 60,
                'stipple_heavy': 100
            }
            num_dots = int(width * height * density_map[pattern_type])
            np.random.seed(42)
            x_dots = np.random.uniform(x, x + width, num_dots)
            y_dots = np.random.uniform(y, y + height, num_dots)
            self.ax.scatter(x_dots, y_dots, s=1, c='black', alpha=0.4)

        elif pattern_type == 'circles':
            num_circles = max(3, int(height * 5))
            for i in range(num_circles):
                y_pos = y + np.random.uniform(0.1, 0.9) * height
                x_pos = x + np.random.uniform(0.2, 0.8) * width
                radius = np.random.uniform(0.03, 0.08)
                circle = mpatches.Circle((x_pos, y_pos), radius,
                                       facecolor='none', edgecolor='black',
                                       linewidth=1, alpha=0.7)
                self.ax.add_patch(circle)

        elif pattern_type == 'diagonal':
            spacing = 0.15
            num_lines = int((height + width) / spacing) + 2
            for i in range(num_lines):
                offset = i * spacing - width
                x1, y1 = x, y + offset
                x2, y2 = x + width, y + height + offset
                if y1 < y:
                    x1 = x + (y - y1)
                    y1 = y
                if y2 > y + height:
                    x2 = x2 - (y2 - (y + height))
                    y2 = y + height
                if x1 >= x and x2 <= x + width and y1 <= y2:
                    self.ax.plot([x1, x2], [y1, y2], 'k-', linewidth=1, alpha=0.6, clip_on=True)

        elif pattern_type == 'dots_on_dark':
            num_dots = int(width * height * 50)
            np.random.seed(42)
            x_dots = np.random.uniform(x, x + width, num_dots)
            y_dots = np.random.uniform(y, y + height, num_dots)
            self.ax.scatter(x_dots, y_dots, s=2, c='white', alpha=0.6)

        elif pattern_type == 'wavy_dots':
            num_waves = max(2, int(height * 2))
            for i in range(num_waves):
                y_pos = y + (i + 0.5) * height / num_waves
                x_wave = np.linspace(x, x + width, 20)
                y_wave = y_pos + 0.05 * np.sin(x_wave * 20)
                self.ax.plot(x_wave, y_wave, 'k-', linewidth=0.8, alpha=0.6)
            num_dots = int(width * height * 30)
            np.random.seed(43)
            x_dots = np.random.uniform(x, x + width, num_dots)
            y_dots = np.random.uniform(y, y + height, num_dots)
            self.ax.scatter(x_dots, y_dots, s=1, c='black', alpha=0.4)


class Module5SoilProfile(QWidget):
    """
    Module 5: Soil Profile Visualization
    Manual input for creating soil profiles
    """

    def __init__(self, parent=None, module1=None, module3=None):
        super().__init__(parent)

        # Link to Module 1 for BH names and count
        self.module1 = module1
        self.water_level = -2.0
        self.ground_elevation = 100.0
        self.num_boreholes = 1
        self.current_bh_index = 0
        self.borehole_data = {}  # {bh_name: {'water_level': float, 'ground_level': float, 'layers': []}}
        self.bh_display_settings = {}  # {bh_name: {'symbol', 'label', 'size', 'color'}}

        self._setup_ui()

        # Load initial data from Module 1 if available
        if self.module1:
            self._sync_from_module1()

    def _setup_ui(self):
        """Setup user interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Top bar
        top_bar = self._create_top_bar()
        main_layout.addLayout(top_bar)

        # Splitter for left (profile) and right (table)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - Soil profile preview
        left_widget = self._create_profile_panel()
        splitter.addWidget(left_widget)

        # Right side - Layer table
        right_widget = self._create_table_panel()
        splitter.addWidget(right_widget)

        # Set splitter sizes (320px left for profile, rest for table)
        splitter.setSizes([320, 1080])

        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

        # Initialize first borehole
        self._load_borehole(0)

    def _create_top_bar(self):
        """Create top bar with controls"""
        layout = QHBoxLayout()

        # Number of boreholes (read-only, synced from Module 1)
        layout.addWidget(QLabel("Number of Boreholes:"))

        self.num_bh_label = QLabel("0")
        self.num_bh_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.num_bh_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.num_bh_label.setFixedWidth(40)
        self.num_bh_label.setStyleSheet("QLabel { background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 3px; padding: 2px; }")
        layout.addWidget(self.num_bh_label)

        layout.addSpacing(20)

        # Borehole selector
        layout.addWidget(QLabel("Current Borehole:"))
        self.bh_combo = QComboBox()
        self.bh_combo.addItem("BH-01")
        self.bh_combo.setFont(QFont("SF Pro Display", 12))
        self.bh_combo.currentIndexChanged.connect(self.on_bh_changed)
        layout.addWidget(self.bh_combo)

        layout.addSpacing(20)

        # Ground level input for current borehole
        layout.addWidget(QLabel("Ground Level (m):"))
        self.gl_input = QLineEdit()
        self.gl_input.setText("100.00")
        self.gl_input.setMaximumWidth(100)
        self.gl_input.setFont(QFont("Arial", 12))
        self.gl_input.textChanged.connect(self.on_ground_level_changed)
        layout.addWidget(self.gl_input)

        layout.addStretch()

        # Export buttons
        btn_export_png = QPushButton("Export PNG")
        btn_export_png.setFont(QFont("SF Pro Display", 13))
        btn_export_png.clicked.connect(self.export_png)
        layout.addWidget(btn_export_png)

        btn_export_pdf = QPushButton("Export PDF")
        btn_export_pdf.setFont(QFont("SF Pro Display", 13))
        btn_export_pdf.clicked.connect(self.export_pdf)
        layout.addWidget(btn_export_pdf)

        btn_export_all_png = QPushButton("Export All PNG")
        btn_export_all_png.setFont(QFont("SF Pro Display", 13))
        btn_export_all_png.clicked.connect(self.export_all_png)
        layout.addWidget(btn_export_all_png)

        btn_export_all_pdf = QPushButton("Export All PDF")
        btn_export_all_pdf.setFont(QFont("SF Pro Display", 13))
        btn_export_all_pdf.clicked.connect(self.export_all_pdf)
        layout.addWidget(btn_export_all_pdf)

        return layout

    def _create_profile_panel(self):
        """Create left panel with soil profile visualization"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Soil profile canvas
        self.profile_canvas = SoilProfileCanvas(width=4.5, height=10)
        layout.addWidget(self.profile_canvas)

        # Water level input
        wl_layout = QHBoxLayout()
        wl_layout.addWidget(QLabel("Water Level (m):"))
        self.wl_input = QLineEdit()
        self.wl_input.setText("-2.00")
        self.wl_input.setMaximumWidth(100)
        self.wl_input.setFont(QFont("SF Pro Display", 12))
        self.wl_input.textChanged.connect(self.on_water_level_changed)
        wl_layout.addWidget(self.wl_input)
        wl_layout.addStretch()
        layout.addLayout(wl_layout)

        widget.setLayout(layout)
        return widget

    def _create_table_panel(self):
        """Create right panel with layer table"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Layer table
        self.layer_table = QTableWidget()
        self.layer_table.setColumnCount(5)
        self.layer_table.setHorizontalHeaderLabels([
            'Layer', 'Thickness (m)', 'Soil Type', 'N-value', 'Description'
        ])

        # Set column widths
        header = self.layer_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.layer_table.setColumnWidth(0, 60)
        self.layer_table.setColumnWidth(1, 100)
        self.layer_table.setColumnWidth(3, 80)

        self.layer_table.setFont(QFont("SF Pro Display", 9))
        self.layer_table.verticalHeader().setDefaultSectionSize(35)
        self.layer_table.cellChanged.connect(self.on_table_changed)

        layout.addWidget(self.layer_table)

        # Add/Remove row buttons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("+ Add Layer")
        btn_add.setFont(QFont("SF Pro Display", 10))
        btn_add.clicked.connect(self.add_layer_row)
        btn_layout.addWidget(btn_add)

        btn_remove = QPushButton("- Remove Layer")
        btn_remove.setFont(QFont("SF Pro Display", 10))
        btn_remove.clicked.connect(self.remove_layer_row)
        btn_layout.addWidget(btn_remove)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Legend Section
        legend_group = QGroupBox("SOIL TYPES LEGEND")
        legend_group.setFont(QFont("SF Pro Display", 11, QFont.Weight.Bold))
        legend_layout = QVBoxLayout()
        legend_layout.setSpacing(5)
        legend_layout.setContentsMargins(10, 10, 10, 10)

        # Create legend table
        self.legend_table = QTableWidget()
        self.legend_table.setRowCount(14)
        self.legend_table.setColumnCount(2)
        self.legend_table.setHorizontalHeaderLabels(['Pattern', 'Soil Type'])
        self.legend_table.verticalHeader().setVisible(False)
        self.legend_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.legend_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.legend_table.setMaximumHeight(400)
        self.legend_table.setFont(QFont("SF Pro Display", 9))

        self.legend_table.setColumnWidth(0, 100)
        header = self.legend_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Populate legend
        row = 0
        for soil_type, config in SOIL_TYPES.items():
            pattern_canvas = self._create_pattern_preview(config['color'], config['pattern'])
            self.legend_table.setCellWidget(row, 0, pattern_canvas)

            name_item = QTableWidgetItem(soil_type)
            name_item.setFont(QFont("SF Pro Display", 9))
            self.legend_table.setItem(row, 1, name_item)
            self.legend_table.setRowHeight(row, 28)
            row += 1

        legend_layout.addWidget(self.legend_table)
        legend_group.setLayout(legend_layout)
        layout.addWidget(legend_group)

        widget.setLayout(layout)
        return widget

    def _create_pattern_preview(self, color, pattern):
        """Create pattern preview canvas"""
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

        fig = Figure(figsize=(0.5, 0.3), facecolor='white')
        ax = fig.add_subplot(111)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        rect = Rectangle((0, 0), 1, 1, facecolor=color, edgecolor='black', linewidth=1)
        ax.add_patch(rect)

        # Add simplified pattern preview
        if pattern == 'horizontal_sparse':
            for i in range(3):
                y_pos = (i + 0.5) / 3
                ax.plot([0, 1], [y_pos, y_pos], 'k-', linewidth=0.5, alpha=0.6)
        elif pattern == 'horizontal_dense':
            for i in range(5):
                y_pos = (i + 0.5) / 5
                ax.plot([0, 1], [y_pos, y_pos], 'k-', linewidth=0.5, alpha=0.7)
        elif pattern == 'horizontal_thick':
            for i in range(3):
                y_pos = (i + 0.5) / 3
                ax.plot([0, 1], [y_pos, y_pos], 'k-', linewidth=1.5, alpha=0.8)
        elif pattern == 'crosshatch':
            for i in range(3):
                y_pos = (i + 0.5) / 3
                ax.plot([0, 1], [y_pos, y_pos], 'k-', linewidth=1.5, alpha=0.8)
            for i in range(5):
                x_pos = (i + 0.5) / 5
                ax.plot([x_pos, x_pos], [0, 1], 'k-', linewidth=0.8, alpha=0.6)
        elif 'stipple' in pattern:
            density_map = {'stipple_light': 10, 'stipple_medium': 20, 'stipple_dense': 30, 'stipple_heavy': 50}
            num_dots = density_map.get(pattern, 20)
            np.random.seed(42)
            x_dots = np.random.uniform(0, 1, num_dots)
            y_dots = np.random.uniform(0, 1, num_dots)
            ax.scatter(x_dots, y_dots, s=0.5, c='black', alpha=0.4)
        elif pattern == 'circles':
            for i in range(3):
                y_pos = np.random.uniform(0.2, 0.8)
                x_pos = np.random.uniform(0.2, 0.8)
                circle = mpatches.Circle((x_pos, y_pos), 0.08,
                                       facecolor='none', edgecolor='black',
                                       linewidth=0.5, alpha=0.7)
                ax.add_patch(circle)
        elif pattern == 'diagonal':
            for i in range(5):
                offset = i * 0.3 - 0.6
                ax.plot([0, 1], [offset, 1 + offset], 'k-', linewidth=0.5, alpha=0.6, clip_on=True)
        elif pattern == 'dots_on_dark':
            num_dots = 20
            np.random.seed(42)
            x_dots = np.random.uniform(0, 1, num_dots)
            y_dots = np.random.uniform(0, 1, num_dots)
            ax.scatter(x_dots, y_dots, s=1, c='white', alpha=0.9)
        elif pattern == 'wavy_dots':
            for i in range(2):
                y_pos = 0.3 + i * 0.4
                x_wave = np.linspace(0, 1, 20)
                y_wave = y_pos + 0.05 * np.sin(x_wave * 10)
                ax.plot(x_wave, y_wave, 'k-', linewidth=0.5, alpha=0.6)
            num_dots = 15
            np.random.seed(42)
            x_dots = np.random.uniform(0, 1, num_dots)
            y_dots = np.random.uniform(0, 1, num_dots)
            ax.scatter(x_dots, y_dots, s=0.5, c='black', alpha=0.4)

        fig.tight_layout(pad=0)
        canvas = FigureCanvasQTAgg(fig)
        canvas.setFixedSize(50, 25)
        return canvas

    def _sync_from_module1(self):
        """Sync borehole count and names from Module 1"""
        if not self.module1:
            return

        # Get BH names from Module 1
        bh_names = getattr(self.module1, 'bh_names', [])
        if not bh_names:
            return

        # Update number of boreholes
        self.num_boreholes = len(bh_names)
        self.num_bh_label.setText(str(self.num_boreholes))

        # Convert old integer-based borehole_data to name-based if needed
        old_data = self.borehole_data.copy()
        self.borehole_data = {}

        # Update combo box with BH names from Module 1
        self.bh_combo.blockSignals(True)
        self.bh_combo.clear()
        for bh_name in bh_names:
            self.bh_combo.addItem(bh_name)
            # Initialize empty data if doesn't exist
            if bh_name not in self.borehole_data:
                # Try to migrate old index-based data
                old_index = bh_names.index(bh_name)
                if old_index in old_data:
                    self.borehole_data[bh_name] = old_data[old_index]
        self.bh_combo.blockSignals(False)

        # Load first borehole
        if bh_names:
            self.current_bh_index = 0
            self.bh_combo.setCurrentIndex(0)
            self._load_borehole(0)

    def on_ground_level_changed(self):
        """Handle ground level change"""
        try:
            text = self.gl_input.text()
            self.ground_elevation = float(text)
            self.update_profile()
        except ValueError:
            pass

    def on_bh_changed(self, index):
        """Handle borehole selection change"""
        if index < 0:
            return

        # Save current borehole data
        self._save_current_bh()

        # Load new borehole
        self.current_bh_index = index
        self._load_borehole(index)

    def _get_bh_name_by_index(self, index):
        """Get BH name by combo box index"""
        if self.module1 and hasattr(self.module1, 'bh_names'):
            bh_names = self.module1.bh_names
            if 0 <= index < len(bh_names):
                return bh_names[index]
        return f"BH-{index+1:02d}"

    def _save_current_bh(self):
        """Save current borehole data"""
        layers = []
        for row in range(self.layer_table.rowCount()):
            try:
                depth_item = self.layer_table.item(row, 1)
                combo = self.layer_table.cellWidget(row, 2)
                n_item = self.layer_table.item(row, 3)
                desc_item = self.layer_table.item(row, 4)

                if depth_item and combo:
                    layers.append({
                        'depth': depth_item.text(),
                        'soil_type': combo.currentText(),
                        'n_value': n_item.text() if n_item else '',
                        'description': desc_item.text() if desc_item else ''
                    })
            except:
                continue

        # Use BH name as key instead of index
        bh_name = self._get_bh_name_by_index(self.current_bh_index)
        self.borehole_data[bh_name] = {
            'water_level': self.water_level,
            'ground_level': self.ground_elevation,
            'layers': layers
        }

    def _load_borehole(self, index):
        """Load borehole data"""
        # Clear table
        self.layer_table.setRowCount(0)

        # Get BH name
        bh_name = self._get_bh_name_by_index(index)

        # Load saved data if exists
        if bh_name in self.borehole_data:
            data = self.borehole_data[bh_name]
            self.water_level = data.get('water_level', -2.0)
            self.ground_elevation = data.get('ground_level', 100.0)
            self.wl_input.setText(f"{self.water_level:.2f}")
            self.gl_input.setText(f"{self.ground_elevation:.2f}")

            for layer_data in data.get('layers', []):
                self._add_layer_from_data(layer_data)
        else:
            # Default water level and ground level
            self.water_level = -2.0
            self.ground_elevation = 100.0
            self.wl_input.setText("-2.00")
            self.gl_input.setText("100.00")

        self.update_profile()

    def _add_layer_from_data(self, layer_data):
        """Add layer row from saved data"""
        row = self.layer_table.rowCount()
        self.layer_table.insertRow(row)

        # Layer number
        item = QTableWidgetItem(str(row + 1))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 0, item)

        # Depth
        item = QTableWidgetItem(layer_data.get('depth', '1.0'))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 1, item)

        # Soil type combo
        combo = QComboBox()
        combo.addItems(list(SOIL_TYPES.keys()))
        combo.setCurrentText(layer_data.get('soil_type', 'Fill'))
        combo.currentTextChanged.connect(self.on_table_changed)
        self.layer_table.setCellWidget(row, 2, combo)

        # N-value
        item = QTableWidgetItem(layer_data.get('n_value', ''))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 3, item)

        # Description
        item = QTableWidgetItem(layer_data.get('description', ''))
        self.layer_table.setItem(row, 4, item)

    def on_water_level_changed(self):
        """Handle water level change"""
        try:
            self.water_level = float(self.wl_input.text())
            self.update_profile()
        except ValueError:
            pass

    def on_table_changed(self):
        """Handle table change"""
        self.update_profile()

    def add_layer_row(self):
        """Add new layer row"""
        row = self.layer_table.rowCount()
        self.layer_table.insertRow(row)

        # Layer number
        item = QTableWidgetItem(str(row + 1))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 0, item)

        # Depth
        item = QTableWidgetItem("1.0")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 1, item)

        # Soil type combo
        combo = QComboBox()
        combo.addItems(list(SOIL_TYPES.keys()))
        combo.currentTextChanged.connect(self.on_table_changed)
        self.layer_table.setCellWidget(row, 2, combo)

        # N-value
        item = QTableWidgetItem("")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layer_table.setItem(row, 3, item)

        # Description
        item = QTableWidgetItem("")
        self.layer_table.setItem(row, 4, item)

        self.update_profile()

    def remove_layer_row(self):
        """Remove selected layer row"""
        current_row = self.layer_table.currentRow()
        if current_row >= 0:
            self.layer_table.removeRow(current_row)
            # Update layer numbers
            for row in range(self.layer_table.rowCount()):
                item = self.layer_table.item(row, 0)
                if item:
                    item.setText(str(row + 1))
            self.update_profile()

    def update_profile(self):
        """Update soil profile visualization"""
        layers = []
        current_elev = self.ground_elevation

        for row in range(self.layer_table.rowCount()):
            try:
                depth_item = self.layer_table.item(row, 1)
                combo = self.layer_table.cellWidget(row, 2)
                n_item = self.layer_table.item(row, 3)
                desc_item = self.layer_table.item(row, 4)

                if not depth_item or not combo:
                    continue

                depth = float(depth_item.text())
                from_elev = current_elev
                to_elev = current_elev - depth
                current_elev = to_elev

                layers.append({
                    'from_elev': from_elev,
                    'to_elev': to_elev,
                    'soil_type': combo.currentText(),
                    'n_value': n_item.text() if n_item else '-',
                    'description': desc_item.text() if desc_item else ''
                })
            except ValueError:
                continue

        self.profile_canvas.plot_profile(layers, self.water_level, self.ground_elevation)

    def export_png(self):
        """Export as PNG"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export PNG", "", "PNG Files (*.png)"
        )
        if file_path:
            self.profile_canvas.fig.savefig(file_path, format='png', dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Success", f"Exported to {file_path}")

    def export_pdf(self):
        """Export as PDF"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "", "PDF Files (*.pdf)"
        )
        if file_path:
            self.profile_canvas.fig.savefig(file_path, format='pdf', bbox_inches='tight')
            QMessageBox.information(self, "Success", f"Exported to {file_path}")

    def export_all_png(self):
        """Export all boreholes as PNG side by side"""
        if self.num_boreholes == 0:
            QMessageBox.warning(self, "Warning", "No boreholes to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export All PNG", "", "PNG Files (*.png)"
        )
        if not file_path:
            return

        # Save current borehole state
        self._save_current_bh()

        # Get BH names from Module 1
        bh_names = []
        if self.module1 and hasattr(self.module1, 'bh_names'):
            bh_names = self.module1.bh_names
        else:
            # Fallback to generated names
            bh_names = [f"BH-{i+1:02d}" for i in range(self.num_boreholes)]

        # Create figure with subplots for all boreholes
        fig = Figure(figsize=(4 * len(bh_names), 10))

        for i, bh_name in enumerate(bh_names):
            ax = fig.add_subplot(1, len(bh_names), i + 1)

            # Get borehole data
            if bh_name in self.borehole_data:
                bh_data = self.borehole_data[bh_name]
                ground_level = bh_data.get('ground_level', 100.0)
                water_level = bh_data.get('water_level', -2.0)
                layers = bh_data.get('layers', [])
            else:
                ground_level = 100.0
                water_level = -2.0
                layers = []

            # Draw the profile for this borehole
            self._draw_profile_on_axis(ax, bh_name, ground_level, water_level, layers)

        fig.tight_layout()
        fig.savefig(file_path, format='png', dpi=300, bbox_inches='tight')
        QMessageBox.information(self, "Success", f"Exported all boreholes to {file_path}")

    def export_all_pdf(self):
        """Export all boreholes as PDF side by side"""
        if self.num_boreholes == 0:
            QMessageBox.warning(self, "Warning", "No boreholes to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export All PDF", "", "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        # Save current borehole state
        self._save_current_bh()

        # Get BH names from Module 1
        bh_names = []
        if self.module1 and hasattr(self.module1, 'bh_names'):
            bh_names = self.module1.bh_names
        else:
            # Fallback to generated names
            bh_names = [f"BH-{i+1:02d}" for i in range(self.num_boreholes)]

        # Create figure with subplots for all boreholes
        fig = Figure(figsize=(4 * len(bh_names), 10))

        for i, bh_name in enumerate(bh_names):
            ax = fig.add_subplot(1, len(bh_names), i + 1)

            # Get borehole data
            if bh_name in self.borehole_data:
                bh_data = self.borehole_data[bh_name]
                ground_level = bh_data.get('ground_level', 100.0)
                water_level = bh_data.get('water_level', -2.0)
                layers = bh_data.get('layers', [])
            else:
                ground_level = 100.0
                water_level = -2.0
                layers = []

            # Draw the profile for this borehole
            self._draw_profile_on_axis(ax, bh_name, ground_level, water_level, layers)

        fig.tight_layout()
        fig.savefig(file_path, format='pdf', bbox_inches='tight')
        QMessageBox.information(self, "Success", f"Exported all boreholes to {file_path}")

    def _draw_profile_on_axis(self, ax, bh_name, ground_level, water_level, layers):
        """Draw soil profile on a given axis"""
        ax.clear()
        ax.set_xlim(0, 1)

        if not layers:
            ax.set_ylim(ground_level - 10, ground_level + 2)
            ax.text(0.5, ground_level - 5, 'No layers',
                   ha='center', va='center', fontsize=10, color='gray')
        else:
            # Calculate elevation ranges
            current_elev = ground_level
            layer_elevations = []

            for layer in layers:
                try:
                    depth = float(layer.get('depth', 0))
                    from_elev = current_elev
                    to_elev = current_elev - depth
                    layer_elevations.append({
                        'from_elev': from_elev,
                        'to_elev': to_elev,
                        'soil_type': layer.get('soil_type', 'Fill'),
                        'n_value': layer.get('n_value', '-')
                    })
                    current_elev = to_elev
                except:
                    continue

            if layer_elevations:
                min_elev = min(l['to_elev'] for l in layer_elevations)
                max_elev = ground_level
                ax.set_ylim(min_elev - 2, max_elev + 2)

                # Draw layers
                for layer in layer_elevations:
                    from_elev = layer['from_elev']
                    to_elev = layer['to_elev']
                    soil_type = layer['soil_type']
                    n_value = layer['n_value']

                    # Get soil properties
                    soil_props = SOIL_TYPES.get(soil_type, SOIL_TYPES['Fill'])
                    color = soil_props['color']
                    pattern = soil_props['pattern']

                    # Draw layer rectangle
                    height = from_elev - to_elev
                    rect = Rectangle((0, to_elev), 1, height,
                                   facecolor=color, edgecolor='black', linewidth=1)
                    ax.add_patch(rect)

                    # Add pattern
                    self._add_pattern_to_axis(ax, pattern, to_elev, height)

                    # Add depth labels
                    ax.text(-0.05, from_elev, f'{from_elev:.2f}',
                           ha='right', va='center', fontsize=8)

                    # Add soil type and N-value
                    mid_elev = (from_elev + to_elev) / 2
                    ax.text(0.5, mid_elev, soil_type,
                           ha='center', va='center', fontsize=7, weight='bold')
                    if n_value and n_value != '-':
                        ax.text(1.05, mid_elev, f'N={n_value}',
                               ha='left', va='center', fontsize=7)

                # Draw water level
                if water_level is not None:
                    wl_elev = ground_level + water_level
                    if min_elev <= wl_elev <= max_elev:
                        ax.axhline(y=wl_elev, color='blue', linestyle='--',
                                  linewidth=2, alpha=0.7, label='Water Level')
                        ax.text(1.05, wl_elev, 'WL', ha='left', va='center',
                               fontsize=8, color='blue', weight='bold')
            else:
                ax.set_ylim(ground_level - 10, ground_level + 2)

        # Set title and labels
        ax.set_title(bh_name, fontsize=12, weight='bold', pad=10)
        ax.set_ylabel('Elevation (m)', fontsize=10)
        ax.set_xticks([])
        ax.grid(True, axis='y', alpha=0.3)

    def _add_pattern_to_axis(self, ax, pattern, y_start, height):
        """Add pattern overlay to axis"""
        if pattern == 'horizontal_lines':
            num_lines = int(height * 2)
            for i in range(num_lines):
                y = y_start + (i + 0.5) * height / num_lines
                ax.plot([0, 1], [y, y], 'k-', linewidth=0.5, alpha=0.6)
        elif pattern == 'horizontal_dense':
            num_lines = int(height * 4)
            for i in range(num_lines):
                y = y_start + (i + 0.5) * height / num_lines
                ax.plot([0, 1], [y, y], 'k-', linewidth=0.5, alpha=0.6)
        elif pattern == 'horizontal_thick':
            num_lines = int(height * 2)
            for i in range(num_lines):
                y = y_start + (i + 0.5) * height / num_lines
                ax.plot([0, 1], [y, y], 'k-', linewidth=1.2, alpha=0.7)
        elif pattern == 'horizontal_vertical':
            num_h_lines = int(height * 2)
            for i in range(num_h_lines):
                y = y_start + (i + 0.5) * height / num_h_lines
                ax.plot([0, 1], [y, y], 'k-', linewidth=1.2, alpha=0.7)
            for i in range(3):
                x = 0.25 + i * 0.25
                ax.plot([x, x], [y_start, y_start + height], 'k-', linewidth=1.2, alpha=0.7)
        elif pattern == 'stipple_light' or pattern == 'stipple_medium' or pattern == 'stipple_dense' or pattern == 'stipple_heavy':
            density = {'stipple_light': 30, 'stipple_medium': 50,
                      'stipple_dense': 70, 'stipple_heavy': 100}.get(pattern, 50)
            num_dots = int(height * density)
            np.random.seed(42)
            x_dots = np.random.uniform(0, 1, num_dots)
            y_dots = np.random.uniform(y_start, y_start + height, num_dots)
            ax.scatter(x_dots, y_dots, s=1, c='black', alpha=0.5)
        elif pattern == 'circles':
            num_circles = int(height * 3)
            np.random.seed(42)
            for i in range(num_circles):
                x = np.random.uniform(0.1, 0.9)
                y = np.random.uniform(y_start + 0.1, y_start + height - 0.1)
                circle = mpatches.Circle((x, y), 0.03, fill=False, edgecolor='black', linewidth=0.5)
                ax.add_patch(circle)
        elif pattern == 'diagonal':
            num_lines = int(height * 4)
            for i in range(num_lines):
                y = y_start + i * height / num_lines
                ax.plot([0, 1], [y, y + height/num_lines], 'k-', linewidth=0.5, alpha=0.6)
        elif pattern == 'crosshatch':
            num_lines = int(height * 4)
            for i in range(num_lines):
                y = y_start + i * height / num_lines
                ax.plot([0, 1], [y, y + height/num_lines], 'k-', linewidth=0.5, alpha=0.6)
                ax.plot([0, 1], [y + height/num_lines, y], 'k-', linewidth=0.5, alpha=0.6)
        elif pattern == 'dots_on_dark':
            num_dots = int(height * 20)
            np.random.seed(42)
            x_dots = np.random.uniform(0, 1, num_dots)
            y_dots = np.random.uniform(y_start, y_start + height, num_dots)
            ax.scatter(x_dots, y_dots, s=1, c='white', alpha=0.9)
        elif pattern == 'wavy_dots':
            num_waves = int(height * 2)
            for i in range(num_waves):
                y_pos = y_start + (i + 0.5) * height / num_waves
                x_wave = np.linspace(0, 1, 20)
                y_wave = y_pos + 0.05 * np.sin(x_wave * 10)
                ax.plot(x_wave, y_wave, 'k-', linewidth=0.5, alpha=0.6)

    def get_project_data(self):
        """Get data for saving"""
        self._save_current_bh()
        # borehole_data now uses BH names as keys (strings), so no conversion needed
        return {
            'num_boreholes': self.num_boreholes,
            'current_bh_index': self.current_bh_index,
            'borehole_data': self.borehole_data,
        }

    def load_project_data(self, data):
        """Load data from project"""
        try:
            # Load borehole data (now uses BH names as keys)
            self.borehole_data = data.get('borehole_data', {})

            # Sync from Module 1 to get current BH names and count
            if self.module1:
                self._sync_from_module1()
            else:
                # Fallback if Module 1 not available
                self.num_boreholes = data.get('num_boreholes', 1)
                self.num_bh_label.setText(str(self.num_boreholes))

                # Try to get BH names from saved data
                bh_names = list(self.borehole_data.keys()) if self.borehole_data else [f"BH-{i+1:02d}" for i in range(self.num_boreholes)]

                # Update combo box
                self.bh_combo.blockSignals(True)
                self.bh_combo.clear()
                for bh_name in bh_names:
                    self.bh_combo.addItem(bh_name)
                self.bh_combo.blockSignals(False)

                saved_index = data.get('current_bh_index', 0)
                if saved_index < len(bh_names):
                    self.current_bh_index = saved_index
                    self.bh_combo.setCurrentIndex(saved_index)
                    self._load_borehole(saved_index)
                else:
                    self.current_bh_index = 0
                    self.bh_combo.setCurrentIndex(0)
                    self._load_borehole(0)

        except Exception as e:
            print(f"Error loading Module 5 data: {e}")
            import traceback
            traceback.print_exc()

