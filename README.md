# GroundParam v1.1.0

A professional desktop application for geotechnical parameter calculation and visualization.

![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6.0%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | **Python 3.8+** | Core application language |
| GUI Framework | **PyQt6** (Qt 6.x) | Desktop UI with tab-based navigation |
| Plotting | **Matplotlib** + FigureCanvasQTAgg | Scatter plots, parameter profiles, soil profiles |
| Calculations | **NumPy** | Numerical computation for engineering formulas |
| Data Export | **Pandas** + OpenPyXL | Excel (.xlsx) and CSV export |
| Backend/Auth | **Supabase** (PostgreSQL + Auth) | User authentication, license management, session tracking |
| Design System | Apple HIG inspired | SF Pro Display fonts, Apple color palette, soft modern UI |
| Build | **PyInstaller** | Single .exe distribution (no Python required on target) |
| Project Files | **JSON** | Save/load entire project state |

## Features

| Module | Description |
|--------|-------------|
| **Module 1** - SPT Plot | Excel-like data input, real-time scatter plot, multi-borehole, PDF/PNG export |
| **Module 2** - Laboratory Data | Input lab results (Su, Phi, Gamma), override calculated values |
| **Module 3** - Parameters Summary | Automated geotechnical parameter calculations from SPT correlations |
| **Module 4** - Multi-Parameters Plot | Side-by-side multi-parameter visualization with PDF/PNG export |
| **Module 5** - Soil Profile | Soil profile visualization per borehole |
| **Module 6** - PLAXIS 2D Scripts | Generate Python scripts for PLAXIS automation with phase tree hierarchy |

## Architecture

### Project Structure

```
GroundParam/
├── main.py                          # Application entry point & controller
├── CORE_LOGIC_AND_CALCULATIONS.py   # Engineering calculation engine
├── requirements.txt                 # Python dependencies
├── GroundParam.spec                 # PyInstaller build spec
├── .env                             # Environment variables (NOT in git)
├── config/
│   ├── auth_service.py              # Supabase authentication (singleton)
│   ├── session_manager.py           # License session with heartbeat
│   └── theme.py                     # Apple-style QSS theme
├── ui/
│   ├── login_window.py              # Login screen
│   ├── main_window.py               # Main window (tab hub + save/load)
│   ├── bh_settings_dialog.py        # Borehole settings dialog
│   ├── module1_spt_plot.py          # Module 1: SPT Plot
│   ├── module2_lab_data.py          # Module 2: Laboratory Data
│   ├── module3_parameters.py        # Module 3: Parameters Summary
│   ├── module4_multi_plot.py        # Module 4: Multi-Parameters Plot
│   ├── module5_soil_profile.py      # Module 5: Soil Profile
│   └── module6_plaxis_scripts.py    # Module 6: PLAXIS 2D Scripts
├── widgets/
│   └── plot_widget.py               # Matplotlib-PyQt6 integration
├── assets/icons/                    # Application icons and logos
└── scripts/
    ├── build_exe.bat                # Build script for .exe
    └── convert_icon.py              # PNG to ICO converter
```

### Application Flow

```
                    App Launch (main.py)
                          │
                ┌─────────▼─────────┐
                │ Restore Session?   │
                │ (temp file check)  │
                └─────────┬─────────┘
                    Yes ╱     ╲ No
                       ╱       ╲
              ┌───────▼──┐  ┌───▼────────┐
              │ Activate  │  │ Login      │
              │ License   │  │ Window     │
              └─────┬─────┘  └─────┬──────┘
                    │              │  Email + Password
                    │              │  → Supabase Auth
                    │              │  → License Check
                    ▼              ▼
              ┌──────────────────────┐
              │     Main Window      │
              │  (6 Module Tabs)     │
              │                      │
              │  Heartbeat every 5m  │
              │  → Supabase          │
              └──────────────────────┘
```

**Session Persistence:** Login tokens are saved to a temp file. If the app restarts (but PC has not restarted), the session is restored automatically without re-login. PC restart clears the session (detected via `GetTickCount64`).

### Data Flow Between Modules

```
  Module 1 (SPT Data)          Module 2 (Lab Data)
  ┌─────────────────┐          ┌─────────────────┐
  │ Borehole names   │          │ Su overrides     │
  │ SPT N-values     │          │ Phi overrides    │
  │ Depth intervals  │          │ Gamma overrides  │
  │ Soil class (USCS)│          │                  │
  │ Water level      │          │                  │
  │ Surface elevation│          │                  │
  └────────┬─────────┘          └────────┬─────────┘
           │                             │
           │  signal: data_changed       │  signal: lab_data_changed
           ▼                             ▼
  ┌──────────────────────────────────────────────┐
  │            Module 3 (Parameters)             │
  │                                              │
  │  CORE_LOGIC_AND_CALCULATIONS.py              │
  │  • γsat from N-value                         │
  │  • σv' (effective stress, cumulative)        │
  │  • CN correction (Liao & Whitman / Terzaghi) │
  │  • Su (Clay) or φ' (Sand)                   │
  │  • E modulus, ν, K0, Rint                    │
  │                                              │
  │  Lab overrides replace calculated values     │
  └──────────────┬───────────────────────────────┘
                 │
                 │  signal: results_updated
                 ▼
  ┌──────────────────────┐    ┌──────────────────────┐
  │ Module 4 (Multi-Plot)│    │ Module 5 (Soil Prof) │
  │                      │    │                      │
  │ Parameter profiles   │    │ Soil layers          │
  │ side-by-side graphs  │    │ Water level          │
  │ PDF/PNG export       │    │ Classification       │
  └──────────┬───────────┘    └──────────────────────┘
             │
             ▼
  ┌──────────────────────┐
  │ Module 6 (PLAXIS)    │
  │                      │
  │ Python script gen    │
  │ Soil model params    │
  │ Phase tree hierarchy │
  └──────────────────────┘
```

### Save/Load System

All 6 modules implement `get_project_data()` and `load_project_data()`. The main window orchestrates save/load:

```
Save:  MainWindow → call get_project_data() on each module → merge into JSON → write file
Load:  MainWindow → read JSON file → call load_project_data() on each module in order
```

**JSON Project File Structure:**
```json
{
  "version": "3.0",
  "module1": { "bh_names": [...], "depths": [...], "borehole_data": {...}, ... },
  "module2": { "lab_data": {...} },
  "module3": { "results": {...}, "settings": {...} },
  "module4": { "enabled_params": [...] },
  "module5": { "borehole_data": {...} },
  "module6": { "phases": [...], "scripts": {...} }
}
```

## Engineering Calculations

All calculations are in `CORE_LOGIC_AND_CALCULATIONS.py`. Processing is **sequential per layer** (each layer depends on the previous layer's effective stress).

### Calculation Pipeline

| Step | Parameter | Formula / Method | Applies To |
|------|-----------|-----------------|-----------|
| 1 | Elevation | Ground Elev - Depth | All |
| 2 | Soil Type | USCS classification → Clay or Sand | All |
| 3 | γsat | Lookup table from N-value (15-20 kN/m³) | All |
| 4 | σv' | Cumulative: prev + (γsat - γw) × Δh | All |
| 5 | CN | √(100/σv') — Liao & Whitman (1986) | Sand only |
| 6 | Ncor | CN × N (Sand) or N (Clay) | All |
| 7 | Su | Ncor × f × 9.81 — Stroud (1974) | Clay only |
| 8 | φ' | 27.1 + 0.3×Ncor - 0.00054×Ncor² — PHT (1974) | Sand only |
| 9 | E | α×Su (Clay) or β×Ncor (Sand) | All |
| 10 | ν | 0.495 (Clay) or 0.333 (Sand) | All |
| 11 | K0 | 0.65-0.80 (Clay) or 1-sin(φ') (Sand) — Jaky | All |
| 12 | Rint | Interpolation from Su (Clay) or lookup (Sand) | All |

### References

- Terzaghi and Peck (1967) — Effective stress principle
- Meyerhof (1956) — SPT correlations
- Peck, Hanson, and Thornburn (1974) — Friction angle from SPT
- Liao and Whitman (1986) — CN correction factor
- Duncan and Buchignani (1976) — Modulus ratios
- Stroud (1974) — Su from SPT for clay
- Jaky (1944) — K0 from friction angle
- NAVFAC DM-7 (1982) — Design manual references

## Getting Started

### Prerequisites

- Python 3.8+
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Plythangg/GroundParam.git
cd GroundParam
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

Activate it:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env` File

Create a file named `.env` in the project root with the following content:

```env
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
```

> **Note:** Ask the project owner for the actual Supabase credentials. Never commit `.env` to git.

### 5. Run the Application

```bash
python main.py
```

## Build Executable

Build a single `.exe` that runs without Python installed:

```bash
scripts\build_exe.bat
```

Output: `dist\GroundParam.exe`

- Supabase credentials are embedded in the executable (no `.env` needed)
- Uses `Program_Logo` as the application icon
- Requires Windows 10/11 and internet connection for login

## Pull Latest Changes

```bash
git pull origin main
pip install -r requirements.txt
```

## License

MIT License

## Author

**Viriya**
