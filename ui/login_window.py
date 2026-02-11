"""
Login Window for Ground Param
Apple-style login interface with Google Sheets authentication
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QPixmap
import os
import sys


class LoginWindow(QWidget):
    """Login window with email and password authentication"""

    # Signal emitted when login is successful
    login_successful = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Ground Param")
        self.setFixedSize(420, 760)
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinimizeButtonHint)

        # Set window icon
        icon_path = self._get_icon_path()
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._setup_ui()
        self._apply_styles()

    def _get_base_path(self):
        """Get the base path for assets"""
        try:
            return sys._MEIPASS
        except Exception:
            return os.path.dirname(os.path.dirname(__file__))

    def _get_icon_path(self):
        """Get the path to the application icon"""
        return os.path.join(self._get_base_path(), 'assets', 'icons', 'Program_Logo.png')

    def _get_brand_logo_path(self):
        """Get the path to the brand logo (FOUND-AXIS)"""
        return os.path.join(self._get_base_path(), 'assets', 'icons', 'Brand_Logo.png')

    def _get_program_logo_path(self):
        """Get the path to the program logo (Ground Param)"""
        return os.path.join(self._get_base_path(), 'assets', 'icons', 'Program_Logo.png')

    def _setup_ui(self):
        """Setup the login interface"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Logo section - Dual logo layout
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.setSpacing(8)

        # Brand logo (FOUND-AXIS - Asset 3)
        brand_logo_label = QLabel()
        brand_logo_path = self._get_brand_logo_path()
        if os.path.exists(brand_logo_path):
            pixmap = QPixmap(brand_logo_path)
            scaled_pixmap = pixmap.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            brand_logo_label.setPixmap(scaled_pixmap)
        brand_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(brand_logo_label)

        # Connector arrow
        arrow_label = QLabel("\u25BC")
        arrow_label.setObjectName("arrowLabel")
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(arrow_label)

        # Program logo (Ground Param - Asset 1)
        program_logo_label = QLabel()
        program_logo_path = self._get_program_logo_path()
        if os.path.exists(program_logo_path):
            pixmap = QPixmap(program_logo_path)
            scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            program_logo_label.setPixmap(scaled_pixmap)
        program_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(program_logo_label)

        # App title
        title_label = QLabel("Ground Param")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(title_label)

        # Subtitle
        subtitle_label = QLabel("Sign in to continue")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(subtitle_label)

        main_layout.addLayout(logo_layout)
        main_layout.addSpacing(24)

        # Login form card
        form_card = QFrame()
        form_card.setObjectName("loginCard")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(24, 24, 24, 24)
        form_layout.setSpacing(16)

        # Email field
        email_label = QLabel("Email")
        email_label.setObjectName("fieldLabel")
        form_layout.addWidget(email_label)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        self.email_input.setObjectName("loginInput")
        form_layout.addWidget(self.email_input)

        # Password field
        password_label = QLabel("Password")
        password_label.setObjectName("fieldLabel")
        form_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("loginInput")
        form_layout.addWidget(self.password_input)

        # Show/Hide password button
        password_toggle_layout = QHBoxLayout()
        password_toggle_layout.addStretch()
        self.show_password_btn = QPushButton("Show Password")
        self.show_password_btn.setObjectName("linkButton")
        self.show_password_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show_password_btn.clicked.connect(self._toggle_password_visibility)
        password_toggle_layout.addWidget(self.show_password_btn)
        form_layout.addLayout(password_toggle_layout)

        form_layout.addSpacing(8)

        # Login button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setObjectName("primaryButton")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self._on_login_clicked)
        form_layout.addWidget(self.login_btn)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        form_layout.addWidget(self.status_label)

        main_layout.addWidget(form_card)
        main_layout.addStretch()

        # Footer
        footer_label = QLabel("Version 3.0")
        footer_label.setObjectName("footer")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(footer_label)

        # Connect enter key to login
        self.email_input.returnPressed.connect(self._on_login_clicked)
        self.password_input.returnPressed.connect(self._on_login_clicked)

    def _apply_styles(self):
        """Apply Apple-style CSS"""
        self.setStyleSheet("""
            QWidget {
                background-color: #F5F5F7;
                font-family: 'SF Pro Display', 'Segoe UI', Arial, sans-serif;
            }

            QLabel#arrowLabel {
                font-size: 16px;
                color: #98989D;
                margin: 0px;
            }

            QLabel#title {
                font-size: 24px;
                font-weight: 600;
                color: #1D1D1F;
                margin-top: 8px;
            }

            QLabel#subtitle {
                font-size: 14px;
                color: #6E6E73;
                margin-top: 4px;
            }

            QFrame#loginCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #D1D1D6;
            }

            QLabel#fieldLabel {
                font-size: 13px;
                font-weight: 500;
                color: #1D1D1F;
            }

            QLineEdit#loginInput {
                padding: 12px 16px;
                font-size: 14px;
                border: 1px solid #D1D1D6;
                border-radius: 8px;
                background-color: #FFFFFF;
                color: #1D1D1F;
            }

            QLineEdit#loginInput:focus {
                border: 2px solid #007AFF;
                padding: 11px 15px;
            }

            QLineEdit#loginInput::placeholder {
                color: #98989D;
            }

            QPushButton#primaryButton {
                padding: 14px 24px;
                font-size: 15px;
                font-weight: 600;
                color: #FFFFFF;
                background-color: #007AFF;
                border: none;
                border-radius: 8px;
            }

            QPushButton#primaryButton:hover {
                background-color: #0066D6;
            }

            QPushButton#primaryButton:pressed {
                background-color: #004EA2;
            }

            QPushButton#primaryButton:disabled {
                background-color: #98989D;
            }

            QPushButton#linkButton {
                font-size: 12px;
                color: #007AFF;
                background: transparent;
                border: none;
                padding: 0;
            }

            QPushButton#linkButton:hover {
                color: #0066D6;
                text-decoration: underline;
            }

            QLabel#statusLabel {
                font-size: 13px;
                color: #FF3B30;
                min-height: 20px;
            }

            QLabel#footer {
                font-size: 11px;
                color: #98989D;
            }
        """)

    def _toggle_password_visibility(self):
        """Toggle password field visibility"""
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_btn.setText("Hide Password")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_btn.setText("Show Password")

    def _on_login_clicked(self):
        """Handle login button click"""
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        # Validate inputs
        if not email:
            self._show_status("Please enter your email address", error=True)
            self.email_input.setFocus()
            return

        if not password:
            self._show_status("Please enter your password", error=True)
            self.password_input.setFocus()
            return

        # Disable UI during login
        self._set_loading(True)
        self._show_status("Signing in...", error=False)

        # Import auth service here to avoid circular imports
        from config.auth_service import auth_service

        # Attempt login
        success, message = auth_service.login(email, password)

        self._set_loading(False)

        if success:
            self._show_status("Login successful!", error=False)
            self.login_successful.emit()
        else:
            self._show_status(message, error=True)

    def _show_status(self, message: str, error: bool = False):
        """Show status message"""
        self.status_label.setText(message)
        if error:
            self.status_label.setStyleSheet("color: #FF3B30; font-size: 13px;")
        else:
            self.status_label.setStyleSheet("color: #34C759; font-size: 13px;")

    def _set_loading(self, loading: bool):
        """Set loading state"""
        self.login_btn.setEnabled(not loading)
        self.email_input.setEnabled(not loading)
        self.password_input.setEnabled(not loading)

        if loading:
            self.login_btn.setText("Signing in...")
        else:
            self.login_btn.setText("Sign In")

    def show_error(self, message: str):
        """Show error from external caller (e.g. license check failed)"""
        self._set_loading(False)
        self._show_status(message, error=True)
