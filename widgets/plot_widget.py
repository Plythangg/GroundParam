"""
Matplotlib Plot Widget for PyQt6
Integrates Matplotlib charts into PyQt6 applications
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


class PlotWidget(QWidget):
    """
    Custom widget for embedding Matplotlib plots in PyQt6

    Features:
    - Resizable canvas
    - Apple-style plot styling
    - Easy to use API
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create Matplotlib figure and canvas
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Setup layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Initialize axes
        self.ax = None

        # Apply Apple-style theme
        self._apply_plot_style()

    def _apply_plot_style(self):
        """Apply Apple-style theme to matplotlib plots"""
        plt.style.use('seaborn-v0_8-whitegrid')

        # Set custom colors matching Apple theme
        plt.rcParams.update({
            'font.family': 'sans-serif',
            'font.sans-serif': ['SF Pro Display', 'Arial', 'Helvetica'],
            'font.size': 10,
            'axes.labelsize': 11,
            'axes.titlesize': 13,
            'axes.labelcolor': '#1C1C1E',
            'axes.edgecolor': '#D1D1D6',
            'axes.linewidth': 1,
            'axes.facecolor': '#FFFFFF',
            'figure.facecolor': '#F5F5F7',
            'grid.color': '#E5E5E7',
            'grid.linewidth': 0.5,
            'xtick.color': '#6E6E73',
            'ytick.color': '#6E6E73',
            'text.color': '#1C1C1E',
        })

    def clear_plot(self):
        """Clear the current plot"""
        self.figure.clear()
        self.ax = None
        self.canvas.draw()

    def get_axes(self):
        """Get or create axes for plotting"""
        if self.ax is None:
            self.ax = self.figure.add_subplot(111)
        return self.ax

    def refresh(self):
        """Refresh the canvas to display changes"""
        self.figure.tight_layout()
        self.canvas.draw()
