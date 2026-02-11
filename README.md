# Ground Param v 1.1.0

A professional desktop application for geotechnical parameter calculation and visualization with Apple-style UI design.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6.0%2B-green.svg)

## 🎯 Features

### 📊 Module 1: SPT Plot
- Excel-like data input interface
- Real-time scatter plot visualization
- SPT N-value vs Depth plotting
- Multiple borehole support
- Customizable axis limits and labels
- Export to PDF
- Import/Export CSV

### 🔬 Module 2: Laboratory Data (Coming Soon)
- Input laboratory test results (Su, Phi, Grammar)
- Integration with Module 1 data
- Override calculated values with lab data

### 📈 Module 3: Parameters Summary (Coming Soon)
- Automated geotechnical parameter calculations
- Based on SPT correlations
- Summary tables with all parameters
- Export to CSV/PDF

### 📉 Module 4: Multi-Parameters Plot (Coming Soon)
- Multiple parameter visualization
- Side-by-side plot comparison
- Professional engineering charts

## 🎨 Design

Apple-style UI with:
- Clean, minimal layout
- Soft modern design
- Light/Dark theme support
- High information density
- Professional engineering focus

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Step 1: Clone or Download

```bash
cd V3-UI
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies include:
- **PyQt6** (6.6.0+) - Modern Qt bindings
- **matplotlib** (3.8.0+) - Plotting library
- **numpy** (1.26.0+) - Numerical calculations
- **pandas** (2.1.0+) - Data manipulation

### Step 3: Run the Application

```bash
python main.py
```

## 🚀 Quick Start

### 1. Launch the Application

```bash
python main.py
```

### 2. Using Module 1: SPT Plot

1. **Add/Remove Boreholes**: Use the "+ Add BH" and "- Remove BH" buttons
2. **Input Data**: Double-click cells to enter SPT values and soil classification
3. **Adjust Axis**: Modify X/Y min/max values for custom plot range
4. **Label Size**: Change label font size for better readability
5. **Export**: Save your plot as PDF or save data as JSON

### 3. Sample Data

The application comes with sample data for BH-1:
- Depth: 1.5m → SPT: 8, Class: CH
- Depth: 3.0m → SPT: 12, Class: CL
- Depth: 4.5m → SPT: 15, Class: SM
- Depth: 6.0m → SPT: 20, Class: SC
- Depth: 7.5m → SPT: 25, Class: SM

## 📁 Project Structure

```
V3-UI/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
├── CORE_LOGIC_AND_CALCULATIONS.py   # Engineering calculations
├── config/
│   └── theme.py                     # Apple-style theme configuration
├── ui/
│   ├── __init__.py
│   ├── main_window.py               # Main application window
│   ├── module1_spt_plot.py          # Module 1: SPT Plot
│   ├── module2_lab_data.py          # Module 2: Lab Data (Coming Soon)
│   ├── module3_parameters.py        # Module 3: Parameters (Coming Soon)
│   └── module4_multi_plot.py        # Module 4: Multi-Plot (Coming Soon)
└── widgets/
    ├── __init__.py
    ├── plot_widget.py               # Matplotlib integration
    └── table_widget.py              # Custom table widget (Coming Soon)
```

## 🔧 Engineering Calculations

The application uses industry-standard correlations and methods:

### Calculated Parameters

1. **γwet** - Unit Weight (kN/m³)
2. **Elevation** - Height above datum (m MSL)
3. **σv'** - Vertical Effective Stress (kN/m²)
4. **CN** - Correction Factor for Overburden
5. **Ncor** - Corrected N-value (blow/ft)
6. **Su** - Undrained Shear Strength (kN/m²) for Clay
7. **Ø'** - Effective Friction Angle (degrees) for Sand
8. **E/E'** - Young's Modulus (kN/m²)
9. **ν** - Poisson's Ratio
10. **K0** - Earth Pressure at Rest Coefficient
11. **Rint** - Interface Friction

### References

- Terzaghi and Peck (1967)
- Meyerhof (1956)
- Peck, Hanson, and Thornburn (1974)
- Liao and Whitman (1986)
- Duncan and Buchignani (1976)
- NAVFAC DM-7 (1982)

## 🎨 Theme Customization

Edit `config/theme.py` to customize colors:

```python
COLORS = {
    'primary': '#007AFF',      # Apple Blue
    'success': '#34C759',      # Green
    'warning': '#FF9F0A',      # Orange
    'error': '#FF3B30',        # Red
}
```

## 📊 Data Format

### JSON Export Format

```json
{
  "bh_names": ["BH-1", "BH-2"],
  "depths": [0, 1.5, 3.0, ...],
  "borehole_data": {
    "BH-1": {
      "1.5": {"spt": 8, "class": "CH"},
      "3.0": {"spt": 12, "class": "CL"}
    }
  }
}
```

### CSV Import Format (Coming Soon)

```csv
Depth,BH-1_SPT,BH-1_Class,BH-2_SPT,BH-2_Class
0,,,
1.5,8,CH,10,CL
3.0,12,CL,15,SM
```

## 🐛 Troubleshooting

### Issue: Module 'PyQt6' not found

**Solution:**
```bash
pip install --upgrade PyQt6
```

### Issue: Matplotlib plots not showing

**Solution:**
```bash
pip install --upgrade matplotlib
pip install --upgrade PyQt6
```

### Issue: High DPI scaling issues

**Solution:** The application automatically handles High DPI displays. If you experience issues, check your system display settings.

## 🛠️ Development

### Adding New Modules

1. Create a new file in `ui/` folder (e.g., `module2_lab_data.py`)
2. Inherit from `QWidget`
3. Implement the UI and functionality
4. Import and add to `main_window.py`:

```python
from ui.module2_lab_data import Module2LabData

self.module2 = Module2LabData()
self.tab_widget.addTab(self.module2, "🔬 Module 2: Lab Data")
```

### Coding Style

- Follow PEP 8 guidelines
- Use docstrings for all functions/classes
- Comment complex logic
- Use type hints where appropriate

## 📝 Roadmap

- [x] Module 1: SPT Plot with data input and visualization
- [x] Apple-style UI theme
- [ ] Module 2: Laboratory Data input
- [ ] Module 3: Automated parameter calculations
- [ ] Module 4: Multi-parameter visualization
- [ ] CSV import/export functionality
- [ ] Dark theme support
- [ ] Project save/load functionality
- [ ] Print layout designer
- [ ] Report generation

## 📄 License

This project is licensed under the MIT License.

## 👤 Author

**Viriya**

## 🙏 Acknowledgments

- Design inspired by Apple's macOS interface
- Engineering correlations from industry-standard references
- Built with PyQt6 and Matplotlib

---

**Note:** This is Version 1.1.0 of the Ground Param tool. Modules 2-4 are under development and will be released in future updates.
