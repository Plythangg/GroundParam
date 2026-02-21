"""
Calculation Reference Guide Dialog — Module 3 Parameters

Standalone dialog that explains every column in the Module 3 Parameters Summary
table, ordered left to right.  Each card shows:
  - Formula used
  - Published reference (standard / journal)
  - Scientist background (name, nationality, year, contribution)
  - Worked numerical example with units
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame, QWidget
)
from PyQt6.QtGui import QFont


class CalculationReferenceDialog(QDialog):
    """
    Scrollable reference guide covering all 16 columns of the
    Module 3 Parameters Summary table, ordered left to right.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calculation Reference Guide — Module 3 Parameters")
        self.setMinimumWidth(820)
        self.resize(940, 760)
        self._setup_ui()

    # ------------------------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── Header ────────────────────────────────────────────────────
        hdr = QLabel("Calculation Reference Guide")
        hdr.setFont(QFont("SF Pro Display", 16, QFont.Weight.Bold))
        hdr.setStyleSheet("padding: 14px 18px 4px 18px; color: #1C1C1E;")
        layout.addWidget(hdr)

        sub = QLabel(
            "Module 3 Parameters Summary  ·  Column order: left → right  "
            "·  Formula  ·  Reference  ·  Scientist  ·  Worked Example"
        )
        sub.setFont(QFont("SF Pro Display", 12))
        sub.setStyleSheet("padding: 0 18px 12px 18px; color: #6E6E73;")
        layout.addWidget(sub)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #E5E5EA;")
        layout.addWidget(sep)

        # ── Scroll area ───────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content.setStyleSheet("background: #F2F2F7;")
        cl = QVBoxLayout(content)
        cl.setSpacing(10)
        cl.setContentsMargins(14, 14, 14, 14)

        for sec in self._sections():
            cl.addWidget(self._make_card(sec))

        cl.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # ── Footer ────────────────────────────────────────────────────
        foot_sep = QFrame()
        foot_sep.setFrameShape(QFrame.Shape.HLine)
        foot_sep.setStyleSheet("color: #E5E5EA;")
        layout.addWidget(foot_sep)

        foot = QHBoxLayout()
        foot.setContentsMargins(14, 8, 14, 10)
        foot.addStretch()
        btn_close = QPushButton("Close")
        btn_close.setFixedWidth(80)
        btn_close.clicked.connect(self.accept)
        foot.addWidget(btn_close)
        layout.addLayout(foot)

    # ------------------------------------------------------------------
    def _make_card(self, sec):
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: white; border: 1px solid #E0E0E5;"
            " border-radius: 10px; }"
        )
        v = QVBoxLayout(card)
        v.setSpacing(0)
        v.setContentsMargins(0, 0, 0, 0)

        # ── Clean header (no colored bar) ─────────────────────────────
        hdr_w = QWidget()
        hdr_w.setStyleSheet(
            "background: #F7F7F9; border-radius: 9px 9px 0 0;"
            " border-bottom: 1px solid #E5E5EA;"
        )
        hl = QHBoxLayout(hdr_w)
        hl.setContentsMargins(14, 10, 14, 10)
        hl.setSpacing(10)

        # "Col X" badge
        col_badge = QLabel(f"Col {sec['col']}")
        col_badge.setFont(QFont("SF Pro Display", 9))
        col_badge.setStyleSheet(
            "color: #6E6E73; background: #E5E5EA; border-radius: 4px;"
            " padding: 2px 7px; border: none;"
        )
        hl.addWidget(col_badge)

        # Title
        name_lbl = QLabel(sec['name'])
        name_lbl.setFont(QFont("SF Pro Display", 13, QFont.Weight.Bold))
        name_lbl.setStyleSheet(
            "color: #1C1C1E; background: transparent; border: none;"
        )
        hl.addWidget(name_lbl)
        hl.addStretch()

        # Unit
        if sec.get('unit'):
            u_lbl = QLabel(f"[{sec['unit']}]")
            u_lbl.setFont(QFont("SF Pro Display", 11))
            u_lbl.setStyleSheet(
                "color: #8E8E93; background: transparent; border: none;"
            )
            hl.addWidget(u_lbl)

        v.addWidget(hdr_w)

        # ── Body ──────────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        bl = QVBoxLayout(body)
        bl.setSpacing(8)
        bl.setContentsMargins(14, 12, 14, 12)

        def row(label, text, border_color, bg, bold_first_line=False):
            w = QFrame()
            w.setStyleSheet(
                f"QFrame {{ background: {bg}; border-radius: 6px;"
                f" border-left: 3px solid {border_color}; }}"
            )
            wl = QVBoxLayout(w)
            wl.setContentsMargins(10, 8, 10, 8)
            wl.setSpacing(4)

            lbl = QLabel(label)
            lbl.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
            lbl.setStyleSheet(
                "color: #6E6E73; background: transparent; border: none;"
            )
            wl.addWidget(lbl)

            if bold_first_line and '\n' in text:
                first_line, rest = text.split('\n', 1)
                name_row = QLabel(first_line)
                name_row.setFont(QFont("SF Pro Display", 11, QFont.Weight.Bold))
                name_row.setWordWrap(True)
                name_row.setStyleSheet(
                    "color: #1C1C1E; background: transparent; border: none;"
                )
                wl.addWidget(name_row)

                rest_lbl = QLabel(rest)
                rest_lbl.setFont(QFont("SF Pro Display", 11))
                rest_lbl.setWordWrap(True)
                rest_lbl.setStyleSheet(
                    "color: #3C3C43; background: transparent; border: none;"
                )
                wl.addWidget(rest_lbl)
            else:
                txt = QLabel(text)
                txt.setFont(QFont("SF Pro Display", 11))
                txt.setWordWrap(True)
                txt.setStyleSheet(
                    "color: #1C1C1E; background: transparent; border: none;"
                )
                wl.addWidget(txt)
            return w

        if sec.get('formula'):
            bl.addWidget(row("Formula", sec['formula'], "#4A8FD4", "#EEF5FD"))
        if sec.get('reference'):
            bl.addWidget(row("Reference", sec['reference'], "#3A9E5F", "#EDF8F1"))
        if sec.get('scientist'):
            bl.addWidget(row("Scientist", sec['scientist'], "#C07800", "#FEF9EC",
                             bold_first_line=True))
        if sec.get('example'):
            bl.addWidget(row("Worked Example", sec['example'], "#6058C8", "#F3F2FD"))

        v.addWidget(body)
        return card

    # ------------------------------------------------------------------
    def _sections(self):
        return [
            # ── Col 1: Depth ──────────────────────────────────────────
            {
                'col': '1',                 'name': 'Depth', 'unit': 'm',
                'formula': (
                    'Direct field measurement — recorded at each SPT interval.\n'
                    'Standard interval: every 1.5 m per ASTM D1586.'
                ),
                'reference': (
                    'ASTM D1586 — Standard Test Method for Standard Penetration Test (SPT)\n'
                    'and Split-Barrel Sampling of Soils.'
                ),
                'scientist': (
                    'Karl Terzaghi (Austria–USA, 1883–1963) — Father of Soil Mechanics.\n'
                    'Standardised the SPT as the primary in-situ field test.\n'
                    'Test procedure: a 63.5 kg hammer is dropped 76 cm to drive a\n'
                    'Split Spoon Sampler into the soil in three 15 cm increments.\n'
                    'The blow count of the last two increments (30 cm) = N-value.'
                ),
                'example': (
                    'Typical SPT log:\n'
                    '  Depth 1.5 m → N = 5\n'
                    '  Depth 3.0 m → N = 8\n'
                    '  Depth 4.5 m → N = 12'
                ),
            },
            # ── Col 2: Elevation ──────────────────────────────────────
            {
                'col': '2',                 'name': 'Elevation', 'unit': 'm MSL',
                'formula': (
                    'Elevation = Ground Elevation − Depth\n'
                    '(referenced to Mean Sea Level)'
                ),
                'reference': (
                    'Basic surveying principle.\n'
                    'Datum: MSL — Mean Sea Level, defined by the\n'
                    'International Hydrographic Organization (IHO).'
                ),
                'scientist': (
                    'MSL is the internationally recognised vertical datum maintained by IHO.\n'
                    'Each country establishes a national benchmark tied to a tide-gauge\n'
                    'station. In Thailand the reference station is operated by the\n'
                    'Royal Thai Navy Hydrographic Department.'
                ),
                'example': (
                    'Ground Elevation = +100.00 m MSL\n'
                    'Depth           =    5.00 m\n'
                    '→ Elevation     = 100.00 − 5.00 = +95.00 m MSL'
                ),
            },
            # ── Col 3–5: Class / Type / Consistency ──────────────────
            {
                'col': '3–5',                 'name': 'Class / Type / Consistency', 'unit': '—',
                'formula': (
                    'Classification → Soil Type:\n'
                    '  CL, CH        → Clay\n'
                    '  SM, SC, SP-SM → Sand\n\n'
                    'Consistency — Clay (by Su, kN/m²):\n'
                    '  Su < 12  = Very Soft  |  12–25 = Soft    |  25–50 = Hard\n'
                    '  50–100   = Stiff      |  100–200 = Very Stiff  |  >200 = Hard\n\n'
                    'Consistency — Sand (by N):\n'
                    '  N < 4   = Very Loose  |  4–10  = Loose\n'
                    '  10–30   = Medium Dense  |  30–50 = Dense  |  >50 = Very Dense'
                ),
                'reference': (
                    'USCS — Unified Soil Classification System (ASTM D2487).\n'
                    'Consistency scale: Terzaghi & Peck (1967)\n'
                    '"Soil Mechanics in Engineering Practice", 2nd ed.'
                ),
                'scientist': (
                    'Arthur Casagrande (Austria–USA, 1902–1981) — Professor, Harvard University.\n'
                    'Developed the USCS in 1948 for the U.S. Army Corps of Engineers.\n'
                    'The system classifies soil using Atterberg Limits and Grain Size\n'
                    'Distribution, and is the most widely adopted soil classification\n'
                    'scheme in geotechnical engineering worldwide.'
                ),
                'example': (
                    'CH = High Plasticity Clay\n'
                    'CL = Low Plasticity Clay\n'
                    'SM = Silty Sand\n'
                    'SC = Clayey Sand'
                ),
            },
            # ── Col 6: N ─────────────────────────────────────────────
            {
                'col': '6',                 'name': 'N — SPT N-value', 'unit': 'blow/ft',
                'formula': (
                    'Direct measurement = number of blows to drive the Split Spoon\n'
                    'Sampler 30 cm (12 in.) using a 63.5 kg hammer dropped 76 cm.'
                ),
                'reference': (
                    'ASTM D1586 — Standard Penetration Test (SPT).'
                ),
                'scientist': (
                    'Developed by Charles R. Fletcher (USA) in 1927 and later\n'
                    'standardised by Terzaghi & Peck as the universal field test.\n'
                    'SPT is the most widely used in-situ test for foundation\n'
                    'engineering worldwide. N reflects the penetration resistance\n'
                    'of the soil and correlates to density, strength, and stiffness.'
                ),
                'example': (
                    'N = 0–4    → Very Soft Clay / Very Loose Sand\n'
                    'N = 5–10   → Soft Clay / Loose Sand\n'
                    'N = 11–30  → Stiff Clay / Medium Dense Sand\n'
                    'N = 31–50  → Very Stiff Clay / Dense Sand\n'
                    'N > 50     → Hard Clay / Very Dense Sand  (Refusal)'
                ),
            },
            # ── Col 7: γsat ──────────────────────────────────────────
            {
                'col': '7',                 'name': 'γsat — Saturated Unit Weight', 'unit': 'kN/m³',
                'formula': (
                    'Empirical lookup table from N-value:\n'
                    '  N = 0         →  0 kN/m³\n'
                    '  N < 5         → 15 kN/m³\n'
                    '  N = 5–7       → 16 kN/m³\n'
                    '  N = 8–10      → 17 kN/m³\n'
                    '  N = 11–26     → 18 kN/m³\n'
                    '  N = 27–34     → 19 kN/m³\n'
                    '  N ≥ 35        → 20 kN/m³'
                ),
                'reference': (
                    'General empirical correlation — Bowles (1996);\n'
                    'Das, B.M. — Principles of Geotechnical Engineering.'
                ),
                'scientist': (
                    'γsat (Saturated Unit Weight) is measured in the laboratory\n'
                    'per ASTM D7263 (unit weight of soil).\n'
                    'Unit: kN/m³ = kilonewtons per cubic metre.\n'
                    'Reference values: γw (water) = 9.81 kN/m³\n'
                    '                  γsat (clay) ≈ 15–19 kN/m³\n'
                    '                  γsat (sand) ≈ 16–20 kN/m³'
                ),
                'example': (
                    'N = 15  →  γsat = 18 kN/m³\n'
                    'Weight of a 1 m thick, 1 m² soil layer:\n'
                    '  W = 18 kN/m³ × 1 m × 1 m² = 18 kN  (≈ 1.84 tonnes)'
                ),
            },
            # ── Col 8: σv' ───────────────────────────────────────────
            {
                'col': '8',                 'name': "σv' — Vertical Effective Stress", 'unit': 'kN/m²',
                'formula': (
                    "Accumulated layer by layer from the surface downward:\n"
                    "  Above water table:  σv'(new) = σv'(prev) + γsat × Δh\n"
                    "  Below water table:  σv'(new) = σv'(prev) + (γsat − γw) × Δh\n"
                    "  γw = 9.81 kN/m³  (unit weight of water)"
                ),
                'reference': (
                    "Terzaghi's Effective Stress Principle (1925):\n"
                    "  σ' = σ − u\n"
                    "  (Effective Stress = Total Stress − Pore Water Pressure)"
                ),
                'scientist': (
                    "Karl Terzaghi (Austria–USA, 1883–1963).\n"
                    "Discovered the Effective Stress Principle in 1925 — the single\n"
                    "most important concept in modern soil mechanics.\n"
                    "Published in Erdbaumechanik (1925) and Theoretical Soil Mechanics (1943).\n\n"
                    "Key insight: pore water pressure u reduces the stress that soil\n"
                    "grains actually carry, so only σ' governs strength and settlement."
                ),
                'example': (
                    "Ground elevation = +100 m MSL, water table at El. = 98.00 m (−2 m)\n\n"
                    "Layer 1: depth 0–3 m, above water table, γ = 18 kN/m³\n"
                    "  σv' = 0 + 18 × 3 = 54.00 kN/m²\n\n"
                    "Layer 2: depth 3–5 m, below water table, γ = 18 kN/m³\n"
                    "  σv' = 54 + (18 − 9.81) × 2 = 54 + 16.38 = 70.38 kN/m²"
                ),
            },
            # ── Col 9: CN ────────────────────────────────────────────
            {
                'col': '9',                 'name': 'CN — Overburden Correction Factor', 'unit': '—',
                'formula': (
                    "CN = √(100 / σv')   [σv' in kN/m²]\n"
                    "Applied to Sand only — no correction needed for Clay.\n"
                    "Limits applied: 0.5 ≤ CN ≤ 2.0"
                ),
                'reference': (
                    "Liao, S.S.C. and Whitman, R.V. (1986)\n"
                    "Journal of Geotechnical Engineering, ASCE, Vol. 112.\n"
                    "Form: CN = √(Pa / σv'),  Pa = 100 kN/m² (≈ 1 atm)"
                ),
                'scientist': (
                    "S.S.C. Liao and R.V. Whitman (USA, 1986)\n"
                    "Researchers at MIT (Massachusetts Institute of Technology).\n"
                    "Proposed the CN formula to normalise N to a standard\n"
                    "overburden pressure of 100 kN/m² (≈ 1 atm).\n\n"
                    "Rationale: shallow sands (low σv') yield lower N than their\n"
                    "true density warrants → CN > 1 (upward correction);\n"
                    "deep sands (high σv') yield higher N → CN < 1 (downward)."
                ),
                'example': (
                    "σv' =  25 kN/m²  → CN = √(100/25)  = 2.00  (shallow)\n"
                    "σv' = 100 kN/m²  → CN = √(100/100) = 1.00  (reference depth)\n"
                    "σv' = 400 kN/m²  → CN = √(100/400) = 0.50  (deep)"
                ),
            },
            # ── Col 10: Ncor ─────────────────────────────────────────
            {
                'col': '10',                 'name': 'Ncor — Corrected N-value', 'unit': 'blow/ft',
                'formula': (
                    "Sand:\n"
                    "  Liao & Whitman (1986): Ncor = CN × N\n"
                    "  Terzaghi (1984):       N ≤ 15  →  Ncor = N\n"
                    "                         N > 15  →  Ncor = 15 + 0.5 × (N − 15)\n\n"
                    "Clay: Ncor = N  (no correction applied)"
                ),
                'reference': (
                    'Liao and Whitman (1986);\n'
                    'Terzaghi and Peck (1984) — Soil Mechanics in Engineering Practice.'
                ),
                'scientist': (
                    "Terzaghi method (1984) — traditional, conservative approach:\n"
                    "Caps N above 15 to avoid overestimating dense-sand strength.\n\n"
                    "Liao & Whitman method (1986) — modern, more precise:\n"
                    "Uses σv'-based CN for each layer, giving a correction that\n"
                    "directly reflects the actual overburden at that depth.\n\n"
                    "Clay: N is not significantly affected by overburden, so no\n"
                    "correction is applied."
                ),
                'example': (
                    "Sand, N = 20, σv' = 50 kN/m²  →  CN = 1.414\n"
                    "  Liao & Whitman: Ncor = 1.414 × 20 = 28.3 blow/ft\n"
                    "  Terzaghi:       Ncor = 15 + 0.5 × (20 − 15) = 17.5 blow/ft\n\n"
                    "Clay, N = 20:\n"
                    "  Ncor = 20 blow/ft  (unchanged)"
                ),
            },
            # ── Col 11: Su ───────────────────────────────────────────
            {
                'col': '11',                 'name': 'Su — Undrained Shear Strength', 'unit': 'kN/m²',
                'formula': (
                    "Su = α × Ncor × Pa   [Pa = 9.81 kN/m²  (atmospheric pressure)]\n"
                    "  CH (High Plasticity Clay):  α = 0.6739  →  Su = Ncor × 6.611\n"
                    "  CL (Low Plasticity Clay):   α = 0.5077  →  Su = Ncor × 4.981\n"
                    "  Applied to Clay only — Sand uses ϕ' instead."
                ),
                'reference': (
                    "Stroud, M.A. (1974) — BGS Conference on In-Situ Investigations\n"
                    "in Soils and Rocks.  Proposed Su / N60 ≈ 4–6 kN/m².\n"
                    "Terzaghi and Peck (1967) — Soil Mechanics in Engineering Practice, 2nd ed."
                ),
                'scientist': (
                    "M.A. Stroud (UK, 1974) — British Geotechnical Society researcher.\n"
                    "Established the empirical Su–N correlation widely used in UK practice.\n\n"
                    "Karl Terzaghi & Ralph B. Peck — co-authored the landmark textbook\n"
                    "Soil Mechanics in Engineering Practice (1967), the global standard\n"
                    "reference for geotechnical engineers for over 50 years.\n\n"
                    "Su = undrained shear strength; governs short-term (undrained)\n"
                    "behaviour of clay under rapid loading."
                ),
                'example': (
                    "Ncor = 10, soil CH:\n"
                    "  Su = 10 × 0.6739 × 9.81 = 66.1 kN/m²  → Stiff Clay\n\n"
                    "Ncor = 10, soil CL:\n"
                    "  Su = 10 × 0.5077 × 9.81 = 49.8 kN/m²"
                ),
            },
            # ── Col 12: ϕ' ───────────────────────────────────────────
            {
                'col': '12',                 'name': "ϕ' — Effective Friction Angle", 'unit': '°',
                'formula': (
                    "ϕ' = 27.1 + 0.3 × Ncor − 0.00054 × Ncor²\n"
                    "Applied to Sand only — Clay uses Su instead."
                ),
                'reference': (
                    "Peck, R.B., Hanson, W.E., and Thornburn, T.H. (1974)\n"
                    "Foundation Engineering, 2nd ed., Wiley.\n"
                    "Meyerhof, G.G. (1956) — Penetration Tests and Bearing Capacity\n"
                    "of Cohesionless Soils, J. Soil Mech. Found. Div., ASCE."
                ),
                'scientist': (
                    "Ralph B. Peck (USA, 1912–2008) — Terzaghi's foremost student;\n"
                    "Professor at the University of Illinois. Co-authored Foundation\n"
                    "Engineering (1974) which proposed the N-vs-ϕ' correlation.\n\n"
                    "George G. Meyerhof (UK–Canada, 1916–2003) — Professor at\n"
                    "Nova Scotia Technical College. Developed the general bearing\n"
                    "capacity equation used worldwide, and studied N-vs-ϕ' in 1956.\n\n"
                    "ϕ' = effective friction angle; governs long-term (drained)\n"
                    "shear strength and bearing capacity of sand."
                ),
                'example': (
                    "Ncor = 10:  ϕ' = 27.1 + 3.0   − 0.054  = 30.05°\n"
                    "Ncor = 20:  ϕ' = 27.1 + 6.0   − 0.216  = 32.88°\n"
                    "Ncor = 30:  ϕ' = 27.1 + 9.0   − 0.486  = 35.61°\n"
                    "Ncor = 40:  ϕ' = 27.1 + 12.0  − 0.864  = 38.24°"
                ),
            },
            # ── Col 13: E / E' ────────────────────────────────────────
            {
                'col': '13',                 'name': "E / E' — Young's Modulus", 'unit': 'kN/m²',
                'formula': (
                    "Clay:  E = α × Su\n"
                    "  Sheet Pile:              α = 150 / 300 / 500   (Su ≤ 2.5 / ≤ 5 / > 5 kN/m²)\n"
                    "  Earth Retaining Struct:  α = 250 / 350 / 500\n"
                    "  Diaphragm Wall:          α = 500 / 750 / 1,000\n\n"
                    "Sand:  E' = β × Ncor\n"
                    "  Sheet Pile:              β = 0  (not recommended)\n"
                    "  Earth Retaining Struct:  β = 1,000 kN/m²\n"
                    "  Diaphragm Wall:          β = 2,000 kN/m²"
                ),
                'reference': (
                    "Duncan, J.M. and Buchignani, A.L. (1976)\n"
                    "An Engineering Manual for Slope Stability Studies, Virginia Tech.\n"
                    "NAVFAC DM-7 (1982) — Design Manual: Soil Mechanics,\n"
                    "Foundations, and Earth Structures, U.S. Navy."
                ),
                'scientist': (
                    "James M. Duncan (USA, 1934–2018) — Professor, Virginia Tech.\n"
                    "Developed the Duncan–Chang Hyperbolic Model (1970) for\n"
                    "nonlinear elastic soil behaviour; widely used in FEM analysis.\n\n"
                    "NAVFAC DM-7 — Naval Facilities Engineering Command Design Manual\n"
                    "(1982). Published by the U.S. Navy for civil and military\n"
                    "foundation engineering; adopted broadly by practising engineers."
                ),
                'example': (
                    "Clay (Earth Retaining Structure), Su = 100 kN/m²  (> 5):\n"
                    "  E = 100 × 500 = 50,000 kN/m²\n\n"
                    "Sand (Diaphragm Wall), Ncor = 20:\n"
                    "  E' = 20 × 2,000 = 40,000 kN/m²"
                ),
            },
            # ── Col 14: ν ─────────────────────────────────────────────
            {
                'col': '14',                 'name': "ν — Poisson's Ratio", 'unit': '—',
                'formula': (
                    "Clay: ν = 0.495  (near 0.5 = incompressible, undrained)\n"
                    "Sand: ν = 0.333  (≈ 1/3, drained)"
                ),
                'reference': (
                    "Standard geotechnical engineering values.\n"
                    "Das, B.M. — Principles of Geotechnical Engineering.\n"
                    "Craig, R.F. — Craig's Soil Mechanics."
                ),
                'scientist': (
                    "Siméon Denis Poisson (France, 1781–1840) — French mathematician\n"
                    "and physicist. Discovered the Poisson Effect: a material\n"
                    "compressed axially expands laterally.\n\n"
                    "ν = ε_lateral / ε_axial  (ratio of lateral to axial strain)\n"
                    "ν = 0.0 → no lateral expansion\n"
                    "ν = 0.5 → incompressible (no volume change) — saturated clay\n"
                    "ν = 0.333 → moderate compressibility — sand, concrete"
                ),
                'example': (
                    "Clay (ν = 0.495):\n"
                    "  Compress 10 mm axially → lateral expansion ≈ 4.95 mm\n"
                    "  Volume essentially unchanged (saturated, undrained)\n\n"
                    "Sand (ν = 0.333):\n"
                    "  Compress 10 mm axially → lateral expansion ≈ 3.33 mm"
                ),
            },
            # ── Col 15: K0 ───────────────────────────────────────────
            {
                'col': '15',                 'name': 'K0 — Coefficient of Earth Pressure at Rest', 'unit': '—',
                'formula': (
                    "Sand:   K0 = 1 − sin(ϕ')   [Jaky's Formula, 1944]\n\n"
                    "Clay:\n"
                    "  Sheet Pile:   K0 = 0.65\n"
                    "  Other types:  K0 = 0.80"
                ),
                'reference': (
                    "Jaky, J. (1944) — 'The coefficient of earth pressure at rest',\n"
                    "Journal of the Society of Hungarian Architects and Engineers.\n"
                    "Mayne, P.W. and Kulhawy, F.H. (1982) — Journal of\n"
                    "Geotechnical Engineering, ASCE."
                ),
                'scientist': (
                    "Józef Jaky (Hungary, 1893–1950) — Hungarian geotechnical engineer.\n"
                    "Proposed K0 = 1 − sin(ϕ') in 1944 — now the most widely used\n"
                    "formula for at-rest lateral earth pressure worldwide.\n\n"
                    "K0 = σh' / σv'  (ratio of horizontal to vertical effective stress)\n"
                    "Applies in the at-rest condition: no lateral strain in the soil."
                ),
                'example': (
                    "ϕ' = 30°:  K0 = 1 − sin(30°) = 1 − 0.500 = 0.500\n"
                    "ϕ' = 35°:  K0 = 1 − sin(35°) = 1 − 0.574 = 0.426\n\n"
                    "If σv' = 100 kN/m² and K0 = 0.500:\n"
                    "  → σh' = 0.500 × 100 = 50 kN/m²  (lateral earth pressure)"
                ),
            },
            # ── Col 16: Rint ─────────────────────────────────────────
            {
                'col': '16',                 'name': 'Rint — Interface Friction Factor', 'unit': '—',
                'formula': (
                    "Clay — Installation method: Driven:\n"
                    "  Su < 2.5          → Rint = 1.00  (full adhesion)\n"
                    "  2.5 ≤ Su < 7.5   → Rint = 1.00 − 0.5 × ((Su − 2.5) / 5)\n"
                    "  Su ≥ 7.5          → Rint = 0.50\n"
                    "  Installation: Bored  → Rint = 0.45  (all cases)\n\n"
                    "Sand — by interface surface type:\n"
                    "  Rough Concrete = 1.00  |  Smooth Concrete = 0.80\n"
                    "  Rough Steel    = 0.70  |  Smooth Steel    = 0.50\n"
                    "  Timber         = 0.80"
                ),
                'reference': (
                    "Tomlinson, M.J. (1957) — Adhesion Factor (α method),\n"
                    "Proc. 4th Int. Conf. Soil Mech., London.\n"
                    "API RP 2A (2000) — Recommended Practice for Planning, Designing\n"
                    "and Constructing Fixed Offshore Platforms.\n"
                    "NAVFAC DM-7.2 (1982) — Foundations and Earth Structures."
                ),
                'scientist': (
                    "M.J. Tomlinson (UK, 1957) — Proposed the Adhesion Factor (α)\n"
                    "method for computing skin friction between driven piles and clay,\n"
                    "based on the undrained shear strength Su.\n\n"
                    "API RP 2A — American Petroleum Institute Recommended Practice 2A.\n"
                    "The global standard for offshore structural design; its pile\n"
                    "capacity methodology is adopted widely in onshore practice.\n\n"
                    "Rint = tan(δ) / tan(ϕ') = ratio of interface friction angle\n"
                    "to soil friction angle.\n"
                    "δ = friction angle between soil and structural surface."
                ),
                'example': (
                    "Clay (Driven), Su = 50 kN/m²  (≥ 7.5):\n"
                    "  Rint = 0.50\n\n"
                    "Clay (Bored):\n"
                    "  Rint = 0.45  (regardless of Su)\n\n"
                    "Sand, Smooth Concrete interface:\n"
                    "  Rint = 0.80\n\n"
                    "Sand, Smooth Steel interface:\n"
                    "  Rint = 0.50"
                ),
            },
        ]
