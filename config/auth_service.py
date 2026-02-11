"""
Authentication Service for Supabase Integration
Handles user authentication via Supabase Auth
"""

import os
import sys
import json
import time
import ctypes
import tempfile
from typing import Tuple, Optional, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client


# Load .env from project root
def _get_env_path():
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, '.env')


load_dotenv(_get_env_path())

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Session persistence file in temp directory
_SESSION_FILE = os.path.join(tempfile.gettempdir(), ".groundparam_session")


def _get_boot_time() -> int:
    """Get system boot timestamp (seconds since epoch). Windows only."""
    try:
        uptime_ms = ctypes.windll.kernel32.GetTickCount64()
        return int(time.time() - uptime_ms / 1000)
    except Exception:
        return 0


class AuthService:
    """Service for authenticating users via Supabase"""

    def __init__(self):
        self.current_user: Optional[Dict[str, Any]] = None
        self.supabase: Optional[Client] = None
        self._init_client()

    def _init_client(self):
        """Initialize Supabase client"""
        if SUPABASE_URL and SUPABASE_ANON_KEY:
            try:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
            except Exception:
                self.supabase = None

    def login(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate user with email and password via Supabase Auth

        Args:
            email: User's email address
            password: User's password

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not email or not password:
            return False, "Please enter both email and password"

        if not self.supabase:
            return False, "Cannot connect to server. Please check configuration."

        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email.strip().lower(),
                "password": password
            })

            user = response.user
            session = response.session

            if user and session:
                # Fetch profile for display_name and role
                profile = self._fetch_profile(user.id)

                self.current_user = {
                    "id": user.id,
                    "email": user.email,
                    "name": profile.get("display_name", user.email) if profile else user.email,
                    "role": profile.get("role", "user") if profile else "user",
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                }

                # Save session for persistence
                self._save_session()

                return True, "Login successful"
            else:
                return False, "Invalid email or password"

        except Exception as e:
            error_msg = str(e)
            if "Invalid login credentials" in error_msg:
                return False, "Invalid email or password"
            elif "Email not confirmed" in error_msg:
                return False, "Please confirm your email address first"
            elif "connect" in error_msg.lower() or "network" in error_msg.lower():
                return False, "Cannot connect to server. Please check your internet connection."
            else:
                return False, f"Login error: {error_msg}"

    def restore_session(self) -> Tuple[bool, str]:
        """
        Try to restore a saved session from disk.
        Session is only valid if the PC has not been restarted since saving.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.supabase:
            return False, "No server connection"

        data = self._load_session()
        if not data:
            return False, "No saved session"

        # Check if PC was restarted since session was saved
        current_boot = _get_boot_time()
        saved_boot = data.get("boot_time", 0)
        if abs(current_boot - saved_boot) > 120:
            # Boot time differs → PC was restarted
            self._clear_session()
            return False, "Session expired (PC restarted)"

        access_token = data.get("access_token", "")
        refresh_token = data.get("refresh_token", "")
        if not access_token or not refresh_token:
            self._clear_session()
            return False, "Invalid saved session"

        try:
            # Restore the Supabase session using refresh token
            response = self.supabase.auth.set_session(access_token, refresh_token)

            user = response.user
            session = response.session

            if user and session:
                profile = self._fetch_profile(user.id)

                self.current_user = {
                    "id": user.id,
                    "email": user.email,
                    "name": profile.get("display_name", user.email) if profile else user.email,
                    "role": profile.get("role", "user") if profile else "user",
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                }

                # Update saved session with refreshed tokens
                self._save_session()

                return True, "Session restored"
            else:
                self._clear_session()
                return False, "Session expired"

        except Exception:
            self._clear_session()
            return False, "Session expired"

    def _save_session(self):
        """Save current session to temp file for persistence"""
        if not self.current_user:
            return
        try:
            data = {
                "access_token": self.current_user.get("access_token", ""),
                "refresh_token": self.current_user.get("refresh_token", ""),
                "boot_time": _get_boot_time(),
            }
            with open(_SESSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_session(self) -> Optional[Dict]:
        """Load saved session from temp file"""
        try:
            if os.path.exists(_SESSION_FILE):
                with open(_SESSION_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def _clear_session(self):
        """Delete the saved session file"""
        try:
            if os.path.exists(_SESSION_FILE):
                os.remove(_SESSION_FILE)
        except Exception:
            pass

    def _fetch_profile(self, user_id: str) -> Optional[Dict]:
        """Fetch user profile from profiles table"""
        try:
            result = self.supabase.table("profiles").select(
                "display_name, role"
            ).eq("id", user_id).single().execute()
            return result.data
        except Exception:
            return None

    def logout(self):
        """Sign out and clear current user session"""
        self._clear_session()
        if self.supabase:
            try:
                self.supabase.auth.sign_out()
            except Exception:
                pass
        self.current_user = None

    def is_logged_in(self) -> bool:
        """Check if user is currently logged in"""
        return self.current_user is not None

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current logged in user info"""
        return self.current_user

    def get_client(self) -> Optional[Client]:
        """Get the Supabase client for database operations"""
        return self.supabase


# Global auth service instance
auth_service = AuthService()
