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
    QApplication, QFrame, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QLocale
from PyQt6.QtGui import QFont, QKeyEvent, QKeySequence
import csv
import json
import math
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class CustomTableWidget(QTableWidget):
    """Custom table widget with Enter key navigation and paste support"""

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events - Enter moves down, Ctrl+A selects all, Ctrl+C copies, Ctrl+V pastes"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Move to next row (down) when Enter is pressed
            current = self.currentRow()
            current_col = self.currentColumn()
            if current < self.rowCount() - 1:
                self.setCurrentCell(current + 1, current_col)
            event.accept()
        elif event.matches(QKeySequence.StandardKey.SelectAll):
            self.selectAll()
            event.accept()
        elif event.matches(QKeySequence.StandardKey.Copy):
            self._copy_to_clipboard()
            event.accept()
        elif event.matches(QKeySequence.StandardKey.Paste):
            # Handle paste from clipboard
            self._paste_from_clipboard()
            event.accept()
        else:
            # Default behavior for other keys
            super().keyPressEvent(event)

    def _copy_to_clipboard(self):
        """Copy selected cells to clipboard in Excel-compatible tab-separated format"""
        selected = self.selectedRanges()
        if not selected:
            return

        # Find bounding box of all selected ranges
        min_row = min(r.topRow() for r in selected)
        max_row = max(r.bottomRow() for r in selected)
        min_col = min(r.leftColumn() for r in selected)
        max_col = max(r.rightColumn() for r in selected)

        # Build set of selected cells for quick lookup
        selected_cells = set()
        for r in selected:
            for row in range(r.topRow(), r.bottomRow() + 1):
                for col in range(r.leftColumn(), r.rightColumn() + 1):
                    selected_cells.add((row, col))

        # Build tab-separated text (Excel format)
        lines = []
        for row in range(min_row, max_row + 1):
            row_data = []
            for col in range(min_col, max_col + 1):
                if (row, col) in selected_cells:
                    item = self.item(row, col)
                    row_data.append(item.text() if item else '')
                else:
                    row_data.append('')
            lines.append('\t'.join(row_data))

        QApplication.clipboard().setText('\n'.join(lines))

    def _paste_from_clipboard(self):
        """Paste data from clipboard (Excel format)"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if not text:
            return

        # Always paste from top-left of current selection (mirrors Excel behaviour)
        selected = self.selectedRanges()
        if selected:
            current_row = min(r.topRow() for r in selected)
            current_col = min(r.leftColumn() for r in selected)
        else:
            current_row = self.currentRow()
            current_col = self.currentColumn()

        if current_row < 0 or current_col < 0:
            return

        # Block signals during paste so cellChanged fires once per cell
        self.blockSignals(True)
        changed_cells = []

        try:
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

                    # Set cell value
                    if not item:
                        item = QTableWidgetItem(cell_value.strip())
                        self.setItem(target_row, target_col, item)
                    else:
                        item.setText(cell_value.strip())
                    changed_cells.append((target_row, target_col))

        finally:
            self.blockSignals(False)

        # Fire cellChanged once per changed cell so the parent model updates
        for r, c in changed_cells:
            self.cellChanged.emit(r, c)


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

        # Content area: table + optional side panel
        content_area = QHBoxLayout()
        content_area.setSpacing(8)

        self.table_widget = self._create_table_widget()
        content_area.addWidget(self.table_widget, 1)

        self.phi_panel = self._create_phi_panel()
        self.phi_panel.setVisible(False)
        content_area.addWidget(self.phi_panel)

        self.fvt_panel = self._create_fvt_panel()
        self.fvt_panel.setVisible(False)
        content_area.addWidget(self.fvt_panel)

        main_layout.addLayout(content_area)
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

        # ϕ' from PI toggle button
        self.btn_phi_pi = QPushButton("ϕ' from PI")
        self.btn_phi_pi.setFont(QFont("SF Pro Display", 14))
        self.btn_phi_pi.setMaximumWidth(110)
        self.btn_phi_pi.setToolTip("Calculate ϕ' from Plasticity Index (Alpan 1967 + Brooker & Ireland 1965)")
        self.btn_phi_pi.setCheckable(True)
        self.btn_phi_pi.clicked.connect(self.toggle_phi_panel)
        layout.addWidget(self.btn_phi_pi)

        # Su,field (FVT) correction toggle button
        self.btn_fvt = QPushButton("Su,field (FVT)")
        self.btn_fvt.setFont(QFont("SF Pro Display", 14))
        self.btn_fvt.setMaximumWidth(130)
        self.btn_fvt.setToolTip("Su correction factor λ — Bjerrum (1972) & Morris and Williams (1994)")
        self.btn_fvt.setCheckable(True)
        self.btn_fvt.clicked.connect(self.toggle_fvt_panel)
        layout.addWidget(self.btn_fvt)

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

    def _create_phi_panel(self):
        """Create the ϕ' from PI side panel"""
        panel = QFrame()
        panel.setFixedWidth(330)
        panel.setStyleSheet(
            "QFrame { background: #F7F7F9; border: 1px solid #E0E0E5; border-radius: 10px; }"
        )

        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        # ── Title ─────────────────────────────────────────────────────
        title = QLabel("ϕ' from PI Calculator")
        title.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #1C1C1E; background: transparent; border: none;")
        layout.addWidget(title)

        desc = QLabel(
            "Combines Alpan (1967) and Brooker & Ireland (1965)\n"
            "to derive ϕ' from Plasticity Index."
        )
        desc.setFont(QFont("SF Pro Display", 11))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6E6E73; background: transparent; border: none;")
        layout.addWidget(desc)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setMaximumHeight(1)
        sep.setStyleSheet("background: #E0E0E5; border: none;")
        layout.addWidget(sep)

        # ── Equation cards ────────────────────────────────────────────
        layout.addWidget(self._make_eq_card(
            "Alpan (1967)",
            "K₀,ₙc  =  0.19 + 0.233 · log₁₀(PI)",
            "#4A8FD4", "#EEF5FD"
        ))

        layout.addWidget(self._make_eq_card(
            "Brooker & Ireland (1965)",
            "K₀,ₙc  =  0.95 − sin(ϕ')",
            "#3A9E5F", "#EDF8F1"
        ))

        layout.addWidget(self._make_eq_card(
            "Combined Formula  (set equal → solve for ϕ')",
            "sin(ϕ')  =  0.76 − 0.233 · log₁₀(PI)\n"
            "ϕ'  =  arcsin( 0.76 − 0.233 · log₁₀(PI) )",
            "#6058C8", "#F3F2FD"
        ))

        # ── PI input ──────────────────────────────────────────────────
        input_frame = QFrame()
        input_frame.setStyleSheet(
            "QFrame { background: white; border: 1px solid #D1D1D6; border-radius: 8px; }"
        )
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(12, 10, 12, 10)
        input_layout.setSpacing(6)

        pi_label = QLabel("Plasticity Index  (PI)")
        pi_label.setFont(QFont("SF Pro Display", 11, QFont.Weight.Bold))
        pi_label.setStyleSheet("color: #6E6E73; background: transparent; border: none;")
        input_layout.addWidget(pi_label)

        self.pi_input = QDoubleSpinBox()
        self.pi_input.setRange(1, 500)
        self.pi_input.setDecimals(1)
        self.pi_input.setValue(20.0)
        self.pi_input.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.pi_input.setSuffix("  %")
        self.pi_input.setFont(QFont("SF Pro Display", 14))
        self.pi_input.setFixedHeight(36)
        self.pi_input.setStyleSheet(
            "QDoubleSpinBox { border: 1px solid #D1D1D6; border-radius: 6px;"
            " padding: 4px 8px; background: white; }"
        )
        self.pi_input.valueChanged.connect(self._calc_phi_from_pi)
        input_layout.addWidget(self.pi_input)

        layout.addWidget(input_frame)

        # ── Result display ────────────────────────────────────────────
        result_frame = QFrame()
        result_frame.setStyleSheet(
            "QFrame { background: #4A8FD4; border-radius: 8px; border: none; }"
        )
        result_layout = QVBoxLayout(result_frame)
        result_layout.setContentsMargins(14, 12, 14, 12)
        result_layout.setSpacing(2)

        result_lbl = QLabel("Calculated ϕ'")
        result_lbl.setFont(QFont("SF Pro Display", 10))
        result_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_lbl.setStyleSheet(
            "color: white; background: transparent; border: none;"
        )
        result_layout.addWidget(result_lbl)

        self.phi_result_lbl = QLabel("—")
        self.phi_result_lbl.setFont(QFont("SF Pro Display", 30, QFont.Weight.Bold))
        self.phi_result_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.phi_result_lbl.setStyleSheet(
            "color: white; background: transparent; border: none;"
        )
        result_layout.addWidget(self.phi_result_lbl)

        layout.addWidget(result_frame)

        # ── Graph: PI vs ϕ' with crosshair ───────────────────────────
        self._fig = Figure(figsize=(2.9, 2.1), dpi=96)
        self._fig.patch.set_facecolor('#F7F7F9')
        self._ax = self._fig.add_subplot(111)
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setFixedHeight(210)
        self._canvas.setStyleSheet("background: transparent;")
        self._setup_graph()
        layout.addWidget(self._canvas)

        layout.addStretch()

        return panel

    def _setup_graph(self):
        """Build the PI vs ϕ' curve with crosshair lines"""
        ax = self._ax
        ax.clear()
        ax.set_facecolor('#FAFAFA')

        # ── Curve: PI from 1 to 200 ───────────────────────────────────
        pi_arr = np.linspace(1, 200, 400)
        phi_arr = np.degrees(np.arcsin(
            np.clip(0.76 - 0.233 * np.log10(pi_arr), -1.0, 1.0)
        ))

        ax.plot(pi_arr, phi_arr, color='#4A8FD4', linewidth=1.8, zorder=2)

        # ── Crosshair (initial position at PI=20) ─────────────────────
        init_pi = 20.0
        init_phi = math.degrees(math.asin(
            max(-1.0, min(1.0, 0.76 - 0.233 * math.log10(init_pi)))
        ))

        self._vline = ax.axvline(
            x=init_pi, ymin=0,
            color='#FF3B30', linewidth=1.0, linestyle='--', alpha=0.75, zorder=3
        )
        self._hline = ax.axhline(
            y=init_phi,
            color='#FF3B30', linewidth=1.0, linestyle='--', alpha=0.75, zorder=3
        )
        self._dot, = ax.plot(
            [init_pi], [init_phi],
            'o', color='#FF3B30', markersize=5, zorder=4
        )

        # ── Axes style ────────────────────────────────────────────────
        ax.set_xlabel('PI  (%)', fontsize=7.5, color='#6E6E73', labelpad=3)
        ax.set_ylabel("ϕ'  (°)", fontsize=7.5, color='#6E6E73', labelpad=3)
        ax.tick_params(labelsize=6.5, colors='#8E8E93', length=3)
        ax.set_xlim(0, 200)
        ax.set_ylim(phi_arr.min() - 1, phi_arr.max() + 1)
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['left', 'bottom']:
            ax.spines[spine].set_color('#D1D1D6')

        self._pi_curve = pi_arr
        self._phi_curve = phi_arr

        self._fig.tight_layout(pad=0.6)
        self._canvas.draw()

    def _make_eq_card(self, title, formula, border_color, bg):
        """Create a small equation card with colored left border"""
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {bg}; border-radius: 6px;"
            f" border-left: 3px solid {border_color}; }}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(10, 8, 10, 8)
        cl.setSpacing(4)

        t = QLabel(title)
        t.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        t.setStyleSheet("color: #6E6E73; background: transparent; border: none;")
        cl.addWidget(t)

        f = QLabel(formula)
        f.setFont(QFont("SF Pro Display", 11))
        f.setWordWrap(True)
        f.setStyleSheet("color: #1C1C1E; background: transparent; border: none;")
        cl.addWidget(f)

        return card

    def toggle_phi_panel(self, checked):
        """Show or hide the ϕ' from PI side panel"""
        self.phi_panel.setVisible(checked)
        if checked:
            self._calc_phi_from_pi()

    # ──────────────────────────────────────────────────────────────────
    # Su,field (FVT) Correction Panel
    # ──────────────────────────────────────────────────────────────────

    def _create_fvt_panel(self):
        """Create the Su,field (FVT) correction factor side panel"""
        panel = QFrame()
        panel.setFixedWidth(340)
        panel.setStyleSheet(
            "QFrame { background: #F7F7F9; border: 1px solid #E0E0E5; border-radius: 10px; }"
        )

        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(14, 14, 14, 14)

        # ── Title ────────────────────────────────────────────────────
        title = QLabel("Su Correction Factor  (FVT)")
        title.setFont(QFont("SF Pro Display", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #1C1C1E; background: transparent; border: none;")
        layout.addWidget(title)

        desc = QLabel(
            "Field Vane Test correction using Bjerrum (1972)\n"
            "and Morris & Williams (1994)."
        )
        desc.setFont(QFont("SF Pro Display", 11))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #6E6E73; background: transparent; border: none;")
        layout.addWidget(desc)

        # Main formula card
        layout.addWidget(self._make_eq_card(
            "Correction Formula",
            "Su,design  =  λ · Su,field",
            "#1C1C1E", "#EDEDF2"
        ))

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setMaximumHeight(1)
        sep.setStyleSheet("background: #E0E0E5; border: none;")
        layout.addWidget(sep)

        # ── Bjerrum (1972) ───────────────────────────────────────────
        bj_header = QLabel("Bjerrum (1972)")
        bj_header.setFont(QFont("SF Pro Display", 12, QFont.Weight.Bold))
        bj_header.setStyleSheet("color: #1C1C1E; background: transparent; border: none;")
        layout.addWidget(bj_header)

        layout.addWidget(self._make_eq_card(
            "Formula",
            "λ  =  1.7 − 0.54 · log₁₀(PI)",
            "#4A8FD4", "#EEF5FD"
        ))

        # Bjerrum input row (PI → λ inline)
        bj_row_frame = QFrame()
        bj_row_frame.setStyleSheet(
            "QFrame { background: white; border: 1px solid #D1D1D6; border-radius: 8px; }"
        )
        bj_row = QHBoxLayout(bj_row_frame)
        bj_row.setContentsMargins(12, 8, 12, 8)
        bj_row.setSpacing(8)

        bj_pi_lbl = QLabel("PI")
        bj_pi_lbl.setFont(QFont("SF Pro Display", 11, QFont.Weight.Bold))
        bj_pi_lbl.setStyleSheet("color: #6E6E73; background: transparent; border: none;")
        bj_row.addWidget(bj_pi_lbl)

        self.fvt_pi_input = QDoubleSpinBox()
        self.fvt_pi_input.setRange(1, 500)
        self.fvt_pi_input.setDecimals(1)
        self.fvt_pi_input.setValue(20.0)
        self.fvt_pi_input.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.fvt_pi_input.setSuffix("  %")
        self.fvt_pi_input.setFont(QFont("SF Pro Display", 13))
        self.fvt_pi_input.setFixedHeight(32)
        self.fvt_pi_input.setStyleSheet(
            "QDoubleSpinBox { border: 1px solid #D1D1D6; border-radius: 6px;"
            " padding: 2px 6px; background: white; }"
        )
        self.fvt_pi_input.valueChanged.connect(self._calc_bjerrum)
        bj_row.addWidget(self.fvt_pi_input, 1)

        bj_eq_lbl = QLabel("λ =")
        bj_eq_lbl.setFont(QFont("SF Pro Display", 13))
        bj_eq_lbl.setStyleSheet("color: #6E6E73; background: transparent; border: none;")
        bj_row.addWidget(bj_eq_lbl)

        self.bjerrum_result_lbl = QLabel("—")
        self.bjerrum_result_lbl.setFont(QFont("SF Pro Display", 15, QFont.Weight.Bold))
        self.bjerrum_result_lbl.setMinimumWidth(52)
        self.bjerrum_result_lbl.setStyleSheet("color: #4A8FD4; background: transparent; border: none;")
        bj_row.addWidget(self.bjerrum_result_lbl)

        layout.addWidget(bj_row_frame)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setMaximumHeight(1)
        sep2.setStyleSheet("background: #E0E0E5; border: none;")
        layout.addWidget(sep2)

        # ── Morris & Williams (1994) ──────────────────────────────────
        mw_header = QLabel("Morris & Williams (1994)")
        mw_header.setFont(QFont("SF Pro Display", 12, QFont.Weight.Bold))
        mw_header.setStyleSheet("color: #1C1C1E; background: transparent; border: none;")
        layout.addWidget(mw_header)

        layout.addWidget(self._make_eq_card(
            "From PI  (PI > 5)",
            "λ  =  1.18 · e^(−0.08·PI) + 0.57",
            "#3A9E5F", "#EDF8F1"
        ))
        layout.addWidget(self._make_eq_card(
            "From LL",
            "λ  =  7.01 · e^(−0.08·LL) + 0.57",
            "#C07800", "#FEF9EC"
        ))

        # MW inputs frame
        mw_frame = QFrame()
        mw_frame.setStyleSheet(
            "QFrame { background: white; border: 1px solid #D1D1D6; border-radius: 8px; }"
        )
        mw_layout = QVBoxLayout(mw_frame)
        mw_layout.setContentsMargins(12, 8, 12, 8)
        mw_layout.setSpacing(6)

        # PI row
        mw_pi_row = QHBoxLayout()
        mw_pi_row.setSpacing(8)
        mw_pi_lbl = QLabel("PI")
        mw_pi_lbl.setFont(QFont("SF Pro Display", 11, QFont.Weight.Bold))
        mw_pi_lbl.setStyleSheet("color: #6E6E73; background: transparent; border: none;")
        mw_pi_row.addWidget(mw_pi_lbl)

        self.mw_pi_input = QDoubleSpinBox()
        self.mw_pi_input.setRange(5, 500)
        self.mw_pi_input.setDecimals(1)
        self.mw_pi_input.setValue(20.0)
        self.mw_pi_input.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.mw_pi_input.setSuffix("  %")
        self.mw_pi_input.setFont(QFont("SF Pro Display", 13))
        self.mw_pi_input.setFixedHeight(32)
        self.mw_pi_input.setStyleSheet(
            "QDoubleSpinBox { border: 1px solid #D1D1D6; border-radius: 6px;"
            " padding: 2px 6px; background: white; }"
        )
        self.mw_pi_input.valueChanged.connect(self._calc_morris_williams)
        mw_pi_row.addWidget(self.mw_pi_input, 1)

        mw_pi_eq = QLabel("λ =")
        mw_pi_eq.setFont(QFont("SF Pro Display", 13))
        mw_pi_eq.setStyleSheet("color: #6E6E73; background: transparent; border: none;")
        mw_pi_row.addWidget(mw_pi_eq)

        self.mw_pi_result_lbl = QLabel("—")
        self.mw_pi_result_lbl.setFont(QFont("SF Pro Display", 15, QFont.Weight.Bold))
        self.mw_pi_result_lbl.setMinimumWidth(52)
        self.mw_pi_result_lbl.setStyleSheet("color: #3A9E5F; background: transparent; border: none;")
        mw_pi_row.addWidget(self.mw_pi_result_lbl)
        mw_layout.addLayout(mw_pi_row)

        # LL row
        mw_ll_row = QHBoxLayout()
        mw_ll_row.setSpacing(8)
        mw_ll_lbl = QLabel("LL")
        mw_ll_lbl.setFont(QFont("SF Pro Display", 11, QFont.Weight.Bold))
        mw_ll_lbl.setStyleSheet("color: #6E6E73; background: transparent; border: none;")
        mw_ll_row.addWidget(mw_ll_lbl)

        self.mw_ll_input = QDoubleSpinBox()
        self.mw_ll_input.setRange(1, 500)
        self.mw_ll_input.setDecimals(1)
        self.mw_ll_input.setValue(40.0)
        self.mw_ll_input.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.mw_ll_input.setSuffix("  %")
        self.mw_ll_input.setFont(QFont("SF Pro Display", 13))
        self.mw_ll_input.setFixedHeight(32)
        self.mw_ll_input.setStyleSheet(
            "QDoubleSpinBox { border: 1px solid #D1D1D6; border-radius: 6px;"
            " padding: 2px 6px; background: white; }"
        )
        self.mw_ll_input.valueChanged.connect(self._calc_morris_williams)
        mw_ll_row.addWidget(self.mw_ll_input, 1)

        mw_ll_eq = QLabel("λ =")
        mw_ll_eq.setFont(QFont("SF Pro Display", 13))
        mw_ll_eq.setStyleSheet("color: #6E6E73; background: transparent; border: none;")
        mw_ll_row.addWidget(mw_ll_eq)

        self.mw_ll_result_lbl = QLabel("—")
        self.mw_ll_result_lbl.setFont(QFont("SF Pro Display", 15, QFont.Weight.Bold))
        self.mw_ll_result_lbl.setMinimumWidth(52)
        self.mw_ll_result_lbl.setStyleSheet("color: #C07800; background: transparent; border: none;")
        mw_ll_row.addWidget(self.mw_ll_result_lbl)
        mw_layout.addLayout(mw_ll_row)

        layout.addWidget(mw_frame)

        # ── Graph: λ vs PI (Bjerrum + MW side-by-side) ───────────────
        self._fvt_fig = Figure(figsize=(2.9, 2.0), dpi=96)
        self._fvt_fig.patch.set_facecolor('#F7F7F9')
        self._fvt_ax = self._fvt_fig.add_subplot(111)
        self._fvt_canvas = FigureCanvas(self._fvt_fig)
        self._fvt_canvas.setFixedHeight(200)
        self._fvt_canvas.setStyleSheet("background: transparent;")
        self._setup_fvt_graph()
        layout.addWidget(self._fvt_canvas)

        layout.addStretch()
        return panel

    def toggle_fvt_panel(self, checked):
        """Show or hide the Su,field (FVT) correction side panel"""
        self.fvt_panel.setVisible(checked)
        if checked:
            self._calc_bjerrum()
            self._calc_morris_williams()

    def _calc_bjerrum(self):
        """Bjerrum (1972): λ = 1.7 − 0.54 · log₁₀(PI)"""
        pi_val = self.fvt_pi_input.value()
        if pi_val <= 0:
            self.bjerrum_result_lbl.setText("—")
            return
        lam = 1.7 - 0.54 * math.log10(pi_val)
        self.bjerrum_result_lbl.setText(f"{lam:.3f}")

        # Update Bjerrum crosshair on graph
        if hasattr(self, '_fvt_vline'):
            self._fvt_vline.set_xdata([pi_val, pi_val])
            self._fvt_hline_bj.set_ydata([lam, lam])
            self._fvt_dot_bj.set_data([pi_val], [lam])
            self._fvt_canvas.draw_idle()

    def _calc_morris_williams(self):
        """Morris & Williams (1994) correction factors from PI and LL"""
        pi_val = self.mw_pi_input.value()
        ll_val = self.mw_ll_input.value()

        # From PI (valid for PI > 5)
        if pi_val > 5:
            lam_pi = 1.18 * math.exp(-0.08 * pi_val) + 0.57
            self.mw_pi_result_lbl.setText(f"{lam_pi:.3f}")
        else:
            self.mw_pi_result_lbl.setText("PI ≤ 5")

        # From LL
        lam_ll = 7.01 * math.exp(-0.08 * ll_val) + 0.57
        self.mw_ll_result_lbl.setText(f"{lam_ll:.3f}")

    def _setup_fvt_graph(self):
        """Build the λ vs PI correction curves (Bjerrum + Morris & Williams)"""
        ax = self._fvt_ax
        ax.clear()
        ax.set_facecolor('#FAFAFA')

        pi_arr = np.linspace(5, 100, 300)

        # Bjerrum (1972)
        lam_bj = 1.7 - 0.54 * np.log10(pi_arr)
        ax.plot(pi_arr, lam_bj, color='#4A8FD4', linewidth=1.8, zorder=2, label='Bjerrum')

        # Morris & Williams (PI form)
        lam_mw = 1.18 * np.exp(-0.08 * pi_arr) + 0.57
        ax.plot(pi_arr, lam_mw, color='#3A9E5F', linewidth=1.8, zorder=2, label='MW (PI)')

        # λ = 1.0 reference line
        ax.axhline(y=1.0, color='#D1D1D6', linewidth=0.8, linestyle=':', zorder=1)

        # Initial crosshair at PI = 20 (Bjerrum)
        init_pi = 20.0
        init_lam = 1.7 - 0.54 * math.log10(init_pi)
        self._fvt_vline = ax.axvline(
            x=init_pi, color='#FF3B30', linewidth=1.0, linestyle='--', alpha=0.75, zorder=3
        )
        self._fvt_hline_bj = ax.axhline(
            y=init_lam, color='#FF3B30', linewidth=1.0, linestyle='--', alpha=0.75, zorder=3
        )
        self._fvt_dot_bj, = ax.plot(
            [init_pi], [init_lam], 'o', color='#FF3B30', markersize=5, zorder=4
        )

        # Legend
        ax.legend(fontsize=6.5, loc='upper right', framealpha=0.8,
                  borderpad=0.4, handlelength=1.5)

        # Axes style
        ax.set_xlabel('PI  (%)', fontsize=7.5, color='#6E6E73', labelpad=3)
        ax.set_ylabel('λ', fontsize=7.5, color='#6E6E73', labelpad=3)
        ax.tick_params(labelsize=6.5, colors='#8E8E93', length=3)
        ax.set_xlim(5, 100)
        all_lam = np.concatenate([lam_bj, lam_mw])
        ax.set_ylim(max(0, all_lam.min() - 0.05), all_lam.max() + 0.1)
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['left', 'bottom']:
            ax.spines[spine].set_color('#D1D1D6')

        self._fvt_fig.tight_layout(pad=0.6)
        self._fvt_canvas.draw()

    def _calc_phi_from_pi(self):
        """Calculate ϕ' from PI using the combined Alpan / Brooker-Ireland formula"""
        pi_val = self.pi_input.value()
        if pi_val <= 0:
            self.phi_result_lbl.setText("—")
            return

        sin_phi = 0.76 - 0.233 * math.log10(pi_val)
        sin_phi = max(-1.0, min(1.0, sin_phi))
        phi = math.degrees(math.asin(sin_phi))
        self.phi_result_lbl.setText(f"{phi:.2f}°")

        # Update crosshair on graph
        if hasattr(self, '_vline'):
            self._vline.set_xdata([pi_val, pi_val])
            self._hline.set_ydata([phi, phi])
            self._dot.set_data([pi_val], [phi])
            self._canvas.draw_idle()

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
                background-color: rgba(0, 122, 255, 0.10);
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
