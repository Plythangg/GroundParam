"""
Main Window for Ground Param
Integrates all 4 modules with tab-based navigation
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QMenuBar, QMenu, QMessageBox,
    QFileDialog, QTextBrowser, QPushButton, QDialog, QLabel
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
import json
import csv
import os
import sys
from ui.module1_spt_plot import Module1SPTPlot
from ui.module2_lab_data import Module2LabData
from ui.module3_parameters import Module3Parameters
from ui.module4_multi_plot import Module4MultiPlot
from ui.module5_soil_profile import Module5SoilProfile
from ui.module6_plaxis_scripts import Module6PlaxisScripts


class MainWindow(QMainWindow):
    """
    Main application window with tab-based module navigation
    """

    # Signal emitted when user clicks logout
    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ground Param")
        self.setMinimumSize(1200, 800)

        # Set window icon (Program Logo - Asset 1)
        icon_path = self._get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Track unsaved changes and current file path
        self.has_unsaved_changes = False
        self.current_file_path = None

        # Setup UI
        self._setup_ui()
        self._create_menu_bar()
        self._create_user_widget()

        # Connect change signals from all modules
        self._connect_change_signals()

    def _setup_ui(self):
        """Setup the main user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        central_widget.setLayout(layout)

        # Tab widget for modules
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(False)

        # Add modules as tabs
        self.module1 = Module1SPTPlot()
        self.tab_widget.addTab(self.module1, "Standard Penetration Test") #Module1

        # Module 2: Laboratory Data (synced with Module 1)
        self.module2 = Module2LabData(module1=self.module1)
        self.tab_widget.addTab(self.module2, "Laboratory Result Input")

        # Module 3: Parameters Summary (uses Module 1 & 2 data)
        self.module3 = Module3Parameters(module1=self.module1, module2=self.module2)
        self.tab_widget.addTab(self.module3, "Parameters Summary")

        # Module 4: Multi-Parameters Plot (uses Module 3 results)
        self.module4 = Module4MultiPlot(module3=self.module3)
        self.tab_widget.addTab(self.module4, "Multi-Parameters Plot")

        # Module 5: Soil Profile (uses Module 1 for water level, Module 3 for data)
        self.module5 = Module5SoilProfile(module1=self.module1, module3=self.module3)
        self.tab_widget.addTab(self.module5, "Soil Profile")

        # Module 6: PLAXIS Python Scripts (uses Module 4 for data)
        self.module6 = Module6PlaxisScripts(module4=self.module4)
        self.tab_widget.addTab(self.module6, "PLAXIS Scripts")

        layout.addWidget(self.tab_widget)

    def _connect_change_signals(self):
        """Connect signals from all modules to track changes"""
        # Note: We'll mark as changed whenever user interacts with any module
        # This is a simple approach - tracking changes on any tab change
        self.tab_widget.currentChanged.connect(self._mark_as_changed)

        # Module 2 → Module 3: Lab data changes auto-update Parameters Summary
        self.module2.lab_data_changed.connect(self.module3.update_lab_overrides)

        # Module 3 → Module 4: Results updates auto-refresh plots
        self.module3.results_updated.connect(self.module4.refresh_from_module3)

    def _mark_as_changed(self):
        """Mark that there are unsaved changes"""
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self._update_window_title()

    def _mark_as_saved(self):
        """Mark that all changes have been saved"""
        self.has_unsaved_changes = False
        self._update_window_title()

    def _update_window_title(self):
        """Update window title to show unsaved changes indicator"""
        base_title = "Ground Param"
        if self.current_file_path:
            file_name = os.path.basename(self.current_file_path)
            title = f"{base_title} - {file_name}"
        else:
            title = f"{base_title} - Untitled"

        if self.has_unsaved_changes:
            title += " *"

        self.setWindowTitle(title)

    def _get_icon_path(self):
        """Get the path to the program icon (Asset 1 - Ground Param)"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_path, 'assets', 'icons', 'Program_Logo.png')

    def _show_message(self, title, text, icon_type='information'):
        """Show message box with application icon"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)

        # Set message icon type
        if icon_type == 'information':
            msg.setIcon(QMessageBox.Icon.Information)
        elif icon_type == 'warning':
            msg.setIcon(QMessageBox.Icon.Warning)
        elif icon_type == 'critical':
            msg.setIcon(QMessageBox.Icon.Critical)
        elif icon_type == 'question':
            msg.setIcon(QMessageBox.Icon.Question)

        # Set window icon
        icon_path = self._get_icon_path()
        if os.path.exists(icon_path):
            msg.setWindowIcon(QIcon(icon_path))

        msg.exec()

    def _show_question(self, title, text):
        """Show question dialog with application icon and return user response"""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        # Set window icon
        icon_path = self._get_icon_path()
        if os.path.exists(icon_path):
            msg.setWindowIcon(QIcon(icon_path))

        return msg.exec()

    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)

        open_action = QAction("Open Project", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)

        save_action = QAction("Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")

        theme_action = QAction("Toggle Theme", self)
        theme_action.setShortcut("Ctrl+T")
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        user_guide_action = QAction("User Guide", self)
        user_guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(user_guide_action)

        references_action = QAction("References", self)
        references_action.triggered.connect(self.show_references)
        help_menu.addAction(references_action)

        terms_action = QAction("Terms of Policy", self)
        terms_action.triggered.connect(self.show_terms)
        help_menu.addAction(terms_action)

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_user_widget(self):
        """Create user display name + logout button in the top-right corner of the menu bar"""
        from config.auth_service import auth_service

        user = auth_service.get_current_user()
        display_name = user.get("name", "User") if user else "User"

        # Container widget
        user_widget = QWidget()
        user_layout = QHBoxLayout(user_widget)
        user_layout.setContentsMargins(0, 0, 8, 0)
        user_layout.setSpacing(8)

        # User name label
        name_label = QLabel(display_name)
        name_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 500;
                color: #6E6E73;
                padding: 4px 0;
            }
        """)
        user_layout.addWidget(name_label)

        # Logout button
        logout_btn = QPushButton("Log Out")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet("""
            QPushButton {
                font-size: 12px;
                font-weight: 500;
                color: #FF3B30;
                background: transparent;
                border: 1px solid #FF3B30;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background-color: #FF3B30;
                color: #FFFFFF;
            }
        """)
        logout_btn.clicked.connect(self._on_logout_clicked)
        user_layout.addWidget(logout_btn)

        # Place in the top-right corner of the menu bar
        self.menuBar().setCornerWidget(user_widget, Qt.Corner.TopRightCorner)

    def _on_logout_clicked(self):
        """Handle logout button click"""
        reply = self._show_question("Log Out", "Are you sure you want to log out?")
        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested.emit()

    def new_project(self):
        """Create new project"""
        reply = self._show_question(
            "New Project",
            "Create a new project? All unsaved changes will be lost."
        )
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Reset all modules
            self._show_message("Info", "New project functionality coming soon!")

    def open_project(self):
        """Open existing project from JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                project_data = json.load(f)

            # Load Module 1 data
            if 'module1' in project_data:
                self.module1.load_project_data(project_data['module1'])

            # Load Module 2 data
            if 'module2' in project_data:
                self.module2.load_project_data(project_data['module2'])

            # Load Module 3 data
            if 'module3' in project_data:
                self.module3.load_project_data(project_data['module3'])

            # Load Module 4 data
            if 'module4' in project_data:
                self.module4.load_project_data(project_data['module4'])

            # Load Module 5 data
            if 'module5' in project_data:
                self.module5.load_project_data(project_data['module5'])

            # Load Module 6 data
            if 'module6' in project_data:
                self.module6.load_project_data(project_data['module6'])

            # Update current file path and mark as saved
            self.current_file_path = file_path
            self._mark_as_saved()

            self._show_message("Success", f"Project loaded successfully!\n{file_path}")

        except Exception as e:
            self._show_message("Error", f"Failed to load project: {str(e)}", 'critical')

    def save_project(self):
        """Save current project to JSON file"""
        # If we have an existing file, save to it directly
        if self.current_file_path:
            self._save_to_file(self.current_file_path)
        else:
            # Show save dialog for new file
            self.save_project_as()

    def save_project_as(self):
        """Save current project to a new JSON file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self._save_to_file(file_path)

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        self._show_message("Info", "Theme toggle functionality coming soon!")

    def show_references(self):
        """Show References dialog with technical manual"""

        dialog = QDialog(self)
        dialog.setWindowTitle("References - Technical Manual")
        dialog.resize(900, 650)

        # Set dialog icon
        icon_path = self._get_icon_path()
        if os.path.exists(icon_path):
            dialog.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout(dialog)

        # HTML Viewer
        browser = QTextBrowser(dialog)

        html_path = os.path.join(
            os.path.dirname(__file__),
            "geotechnical_manual.html"
        )

        browser.setSource(QUrl.fromLocalFile(html_path))
        browser.setOpenExternalLinks(True)

        layout.addWidget(browser)

        # Button layout
        button_layout = QHBoxLayout()

        # Language toggle button
        lang_btn = QPushButton("Thai / English")
        lang_btn.setFixedWidth(150)

        # Track current language state
        is_english = [True]  # Using list to allow modification in nested function

        def toggle_language():
            if is_english[0]:
                # Switch to Thai - scroll to bottom half
                browser.verticalScrollBar().setValue(int(browser.verticalScrollBar().maximum() * 0.55))
                lang_btn.setText("English")
                is_english[0] = False
            else:
                # Switch to English - scroll to top
                browser.verticalScrollBar().setValue(0)
                lang_btn.setText("Thai")
                is_english[0] = True

        lang_btn.clicked.connect(toggle_language)
        button_layout.addWidget(lang_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def show_user_guide(self):
        """Show User Guide dialog"""

        dialog = QDialog(self)
        dialog.setWindowTitle("User Guide")
        dialog.resize(900, 650)

        layout = QVBoxLayout(dialog)

        # HTML Viewer
        browser = QTextBrowser(dialog)

        html_path = os.path.join(
            os.path.dirname(__file__),
            "tool_tips.html"
        )

        browser.setSource(QUrl.fromLocalFile(html_path))
        browser.setOpenExternalLinks(True)

        layout.addWidget(browser)

        # Button layout
        button_layout = QHBoxLayout()

        # Language toggle button
        lang_btn = QPushButton("Thai / English")
        lang_btn.setFixedWidth(150)

        # Track current language state
        is_english = [True]  # Using list to allow modification in nested function

        def toggle_language():
            if is_english[0]:
                # Switch to Thai - scroll to bottom half
                browser.verticalScrollBar().setValue(int(browser.verticalScrollBar().maximum() * 0.55))
                lang_btn.setText("English")
                is_english[0] = False
            else:
                # Switch to English - scroll to top
                browser.verticalScrollBar().setValue(0)
                lang_btn.setText("Thai")
                is_english[0] = True

        lang_btn.clicked.connect(toggle_language)
        button_layout.addWidget(lang_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def show_terms(self):
        """Show Terms of Policy dialog"""

        dialog = QDialog(self)
        dialog.setWindowTitle("Terms of Policy")
        dialog.resize(900, 650)

        layout = QVBoxLayout(dialog)

        # HTML Viewer
        browser = QTextBrowser(dialog)

        html_path = os.path.join(
            os.path.dirname(__file__),
            "terms_of_policy.html"
        )

        browser.setSource(QUrl.fromLocalFile(html_path))
        browser.setOpenExternalLinks(True)

        layout.addWidget(browser)

        # Button layout
        button_layout = QHBoxLayout()

        # Language toggle button
        lang_btn = QPushButton("Thai / English")
        lang_btn.setFixedWidth(150)

        # Track current language state
        is_english = [True]  # Using list to allow modification in nested function

        def toggle_language():
            if is_english[0]:
                # Switch to Thai - scroll to bottom half
                browser.verticalScrollBar().setValue(int(browser.verticalScrollBar().maximum() * 0.55))
                lang_btn.setText("English")
                is_english[0] = False
            else:
                # Switch to English - scroll to top
                browser.verticalScrollBar().setValue(0)
                lang_btn.setText("Thai")
                is_english[0] = True

        lang_btn.clicked.connect(toggle_language)
        button_layout.addWidget(lang_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.exec()


    def show_about(self):
        """Show About dialog with developer information"""

        dialog = QDialog(self)
        dialog.setWindowTitle("About")
        dialog.resize(600, 500)

        # Set dialog icon
        icon_path = self._get_icon_path()
        if os.path.exists(icon_path):
            dialog.setWindowIcon(QIcon(icon_path))

        layout = QVBoxLayout(dialog)

        # HTML Viewer
        browser = QTextBrowser(dialog)

        html_path = os.path.join(
            os.path.dirname(__file__),
            "about.html"
        )

        browser.setSource(QUrl.fromLocalFile(html_path))
        browser.setOpenExternalLinks(True)

        layout.addWidget(browser)

        # Button layout
        button_layout = QHBoxLayout()

        # Language toggle button
        lang_btn = QPushButton("Thai / English")
        lang_btn.setFixedWidth(150)

        # Track current language state
        is_english = [True]

        def toggle_language():
            if is_english[0]:
                # Switch to Thai
                browser.verticalScrollBar().setValue(int(browser.verticalScrollBar().maximum() * 0.55))
                lang_btn.setText("English")
                is_english[0] = False
            else:
                # Switch to English
                browser.verticalScrollBar().setValue(0)
                lang_btn.setText("Thai")
                is_english[0] = True

        lang_btn.clicked.connect(toggle_language)
        button_layout.addWidget(lang_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def closeEvent(self, event):
        """Handle window close event - prompt to save if there are unsaved changes"""
        if self.has_unsaved_changes:
            # Create custom message box with save options
            msg = QMessageBox(self)
            msg.setWindowTitle("Unsaved Changes")
            msg.setText("Do you want to save your changes?")
            msg.setInformativeText("Your changes will be lost if you don't save them.")
            msg.setIcon(QMessageBox.Icon.Question)

            # Set window icon
            icon_path = self._get_icon_path()
            if os.path.exists(icon_path):
                msg.setWindowIcon(QIcon(icon_path))

            # Add custom buttons
            save_btn = msg.addButton("Save", QMessageBox.ButtonRole.AcceptRole)
            dont_save_btn = msg.addButton("Don't Save", QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

            msg.exec()

            clicked_button = msg.clickedButton()

            if clicked_button == save_btn:
                # Save the project
                if self.current_file_path:
                    # Save to existing file
                    self._save_to_file(self.current_file_path)
                    event.accept()
                else:
                    # Show save dialog
                    file_path, _ = QFileDialog.getSaveFileName(
                        self, "Save Project", "", "JSON Files (*.json);;All Files (*)"
                    )
                    if file_path:
                        self._save_to_file(file_path)
                        event.accept()
                    else:
                        # User cancelled save dialog
                        event.ignore()
            elif clicked_button == dont_save_btn:
                # Close without saving
                event.accept()
            else:  # Cancel button
                # Don't close
                event.ignore()
        else:
            # No unsaved changes, close normally
            event.accept()

    def _save_to_file(self, file_path):
        """Save project data to specified file path"""
        try:
            # Collect data from all modules
            project_data = {
                'version': '3.0',
                'module1': self.module1.get_project_data(),
                'module2': self.module2.get_project_data(),
                'module3': self.module3.get_project_data(),
                'module4': self.module4.get_project_data(),
                'module5': self.module5.get_project_data(),
                'module6': self.module6.get_project_data(),
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)

            self.current_file_path = file_path
            self._mark_as_saved()
            self._show_message("Success", f"Project saved successfully!\n{file_path}")

        except Exception as e:
            self._show_message("Error", f"Failed to save project: {str(e)}", 'critical')
