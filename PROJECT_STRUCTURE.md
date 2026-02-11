# Project Structure - Ground Param v 1.1.0.0

```
V3-UI/
│
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── Geotech.spec              # PyInstaller build configuration
├── README.md                  # Project overview
├── PROJECT_STRUCTURE.md       # This file
│
├── assets/                    # Static assets
│   └── icons/
│       ├── App_Logo.ico       # Application icon (Windows)
│       ├── App_Logo.png       # Application logo (original)
│       └── App_logo2.png      # Alternative logo
│
├── config/                    # Application configuration
│   └── theme.py               # UI theme and styling
│
├── ui/                        # User interface modules
│   ├── __init__.py
│   ├── main_window.py         # Main application window
│   ├── bh_settings_dialog.py  # Borehole settings dialog
│   ├── module1_spt_plot.py    # Module 1: SPT Data Input
│   ├── module2_lab_data.py    # Module 2: Lab Test Data
│   ├── module3_parameters.py  # Module 3: Parameter Calculation
│   ├── module4_multi_plot.py  # Module 4: Multi-Parameter Plot
│   ├── module5_soil_profile.py # Module 5: Soil Profile
│   ├── module6_plaxis_scripts.py # Module 6: PLAXIS Scripts
│   ├── about.html             # About dialog content
│   ├── terms_of_policy.html   # Terms and policies
│   ├── tool_tips.html         # Tool tips content
│   ├── geotechnical_manual.html # User manual
│   └── geotechnical_manual.txt  # Manual source
│
├── widgets/                   # Reusable UI widgets
│   ├── __init__.py
│   └── plot_widget.py         # Custom plot widget
│
├── scripts/                   # Utility scripts
│   ├── build_exe.bat          # Build script for Windows
│   ├── convert_icon.py        # PNG to ICO converter
│   └── CORE_LOGIC_AND_CALCULATIONS.py  # Core calculation logic
│
├── docs/                      # Documentation
│   ├── BUILD_INSTRUCTIONS.md  # How to build the executable
│   ├── DESIGN_SYSTEM.md       # UI design guidelines
│   ├── RELEASE_NOTES.md       # Version history
│   └── dev_notes/             # Development notes (internal)
│       ├── BH_SETTINGS_*.txt
│       ├── BUILD_*.txt
│       ├── MODULE*_*.txt
│       └── ...
│
├── build/                     # PyInstaller build artifacts (generated)
│   └── Geotech/
│
├── dist/                      # Distribution folder (generated)
│   └── Geotech.exe            # Final executable
│
├── .venv/                     # Python virtual environment
├── .vscode/                   # VS Code settings
└── .claude/                   # Claude Code settings
```

## Module Overview

| Module | Description |
|--------|-------------|
| Module 1 | SPT Data Input - Enter borehole SPT test data |
| Module 2 | Lab Test Data - Enter laboratory test results |
| Module 3 | Parameter Calculation - Calculate soil parameters |
| Module 4 | Multi-Parameter Plot - Visualize multiple parameters |
| Module 5 | Soil Profile - Generate soil profile diagrams |
| Module 6 | PLAXIS Scripts - Generate Python scripts for PLAXIS |

## Build Instructions

```bash
# Install dependencies
pip install -r requirements.txt

# Build executable
pyinstaller --clean Geotech.spec
```

Output: `dist/Geotech.exe`
