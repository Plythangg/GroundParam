# GroundParam v1.1.0

A professional desktop application for geotechnical parameter calculation and visualization.

![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6.0%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

| Module | Description |
|--------|-------------|
| **Module 1** - SPT Plot | Excel-like data input, real-time scatter plot, multi-borehole, PDF export |
| **Module 2** - Laboratory Data | Input lab results (Su, Phi, Gamma), override calculated values |
| **Module 3** - Parameters Summary | Automated geotechnical parameter calculations from SPT correlations |
| **Module 4** - Multi-Parameters Plot | Side-by-side multi-parameter visualization |
| **Module 5** - Soil Profile | Soil profile visualization |
| **Module 6** - PLAXIS 2D Scripts | Generate Python scripts for PLAXIS automation with phase tree hierarchy |

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

## Pull Latest Changes

```bash
git pull origin main
pip install -r requirements.txt
```

## Project Structure

```
GroundParam/
├── main.py                          # Application entry point
├── CORE_LOGIC_AND_CALCULATIONS.py   # Engineering calculations
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (NOT in git)
├── config/
│   ├── theme.py                     # Apple-style theme configuration
│   ├── auth_service.py              # Supabase authentication
│   └── session_manager.py           # Session management
├── ui/
│   ├── main_window.py               # Main application window
│   ├── login_window.py              # Login screen
│   ├── bh_settings_dialog.py        # Borehole settings dialog
│   ├── module1_spt_plot.py          # Module 1: SPT Plot
│   ├── module2_lab_data.py          # Module 2: Laboratory Data
│   ├── module3_parameters.py        # Module 3: Parameters Summary
│   ├── module4_multi_plot.py        # Module 4: Multi-Parameters Plot
│   ├── module5_soil_profile.py      # Module 5: Soil Profile
│   └── module6_plaxis_scripts.py    # Module 6: PLAXIS 2D Scripts
├── widgets/
│   └── plot_widget.py               # Matplotlib integration
├── assets/
│   ├── icons/
│   └── images/
├── scripts/
│   └── convert_icon.py              # Icon conversion utility
└── docs/
    ├── DESIGN_SYSTEM.md
    ├── BUILD_INSTRUCTIONS.md
    └── RELEASE_NOTES.md
```

## Engineering Calculations

Based on industry-standard correlations:

- Unit Weight, Effective Stress, CN Correction Factor
- Corrected N-value, Undrained Shear Strength (Su)
- Friction Angle, Young's Modulus, Poisson's Ratio
- K0 Coefficient, Interface Friction (Rint)

### References

- Terzaghi and Peck (1967)
- Meyerhof (1956)
- Peck, Hanson, and Thornburn (1974)
- Liao and Whitman (1986)
- Duncan and Buchignani (1976)
- NAVFAC DM-7 (1982)

## License

MIT License

## Author

**Viriya**
