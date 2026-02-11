"""
Ground Param - Main Entry Point

A professional desktop application for geotechnical parameter calculation
and visualization with Apple-style UI design.

Author: Viriya
Version: 3.0
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from config.theme import get_stylesheet
from config.session_manager import SessionManager
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class Application:
    """Application controller that manages login and main window"""

    def __init__(self, app: QApplication):
        self.app = app
        self.login_window = None
        self.main_window = None
        self.session_manager = SessionManager()

        # Force disconnect from admin → close app
        self.session_manager.session_terminated.connect(self._on_force_disconnect)

        # Cleanup session on app quit
        self.app.aboutToQuit.connect(self._on_app_quit)

    def start(self):
        """Start the application — try restore session, fallback to login"""
        from config.auth_service import auth_service

        # Try to restore saved session (persists across app restart, not PC restart)
        restored, _ = auth_service.restore_session()

        if restored:
            # Session restored — go straight to license check + main window
            if self._activate_and_open():
                return

            # Restore succeeded but license check failed — fall through to login
            auth_service.logout()

        # Show login window
        self._show_login()

    def _show_login(self):
        """Show the login window"""
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self._on_login_success)
        self.login_window.show()

    def _activate_and_open(self) -> bool:
        """Activate license session and open main window. Returns True on success."""
        from config.auth_service import auth_service

        user = auth_service.get_current_user()
        client = auth_service.get_client()

        if not user or not client:
            return False

        self.session_manager.set_client(client)
        try:
            success, _ = self.session_manager.activate(
                user["id"], user["email"]
            )
        except Exception:
            success = False

        if not success:
            return False

        # All checks passed — open main window
        self.main_window = MainWindow()
        self.main_window.logout_requested.connect(self._on_logout)
        self.main_window.show()
        return True

    def _on_login_success(self):
        """Handle successful login — activate session then open main window"""
        from config.auth_service import auth_service

        user = auth_service.get_current_user()
        client = auth_service.get_client()

        # Guard 1: must have valid auth
        if not user or not client:
            if self.login_window:
                self.login_window.show_error("Authentication failed. Please try again.")
            return

        # Guard 2: must activate license session
        self.session_manager.set_client(client)
        try:
            success, msg = self.session_manager.activate(
                user["id"], user["email"]
            )
        except Exception as e:
            success = False
            msg = f"Session error: {str(e)}"

        if not success:
            auth_service.logout()
            if self.login_window:
                self.login_window.show_error(msg)
            return

        # All checks passed — open main window
        if self.login_window:
            self.login_window.close()
            self.login_window = None

        self.main_window = MainWindow()
        self.main_window.logout_requested.connect(self._on_logout)
        self.main_window.show()

    def _on_logout(self):
        """Handle logout from main window — return to login"""
        from config.auth_service import auth_service

        # End session and logout
        self.session_manager.deactivate()
        auth_service.logout()

        # Close main window
        if self.main_window:
            self.main_window.close()
            self.main_window = None

        # Show login window again
        self._show_login()

    def _on_force_disconnect(self):
        """Admin force-disconnected this session — notify user and close"""
        from config.auth_service import auth_service
        auth_service.logout()

        parent = self.main_window or self.login_window
        QMessageBox.critical(
            parent,
            "Session Terminated",
            "Your session has been terminated by an administrator.\n"
            "The application will now close.",
        )
        self.app.quit()

    def _on_app_quit(self):
        """Cleanup: end session on quit (but don't clear saved session for persistence)"""
        self.session_manager.deactivate()


def main():
    """Main entry point for the application"""

    # Create Qt application
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("FOUND-AXIS | Ground Param")
    app.setApplicationVersion("1.1")
    app.setOrganizationName("FOUND-AXIS")

    # Set application icon (Program Logo - Asset 1)
    icon_path = get_resource_path('assets/icons/Program_Logo.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Apply Apple-style theme
    app.setStyleSheet(get_stylesheet('light'))

    # Enable High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application controller and start with login
    application = Application(app)
    application.start()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
