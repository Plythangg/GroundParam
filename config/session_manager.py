"""
Session Manager for Active Session Tracking
Handles license-based session: insert, heartbeat, and cleanup via Supabase
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from datetime import datetime, timezone
from typing import Optional, Tuple


class SessionManager(QObject):
    """Manages active_sessions in Supabase for license enforcement"""

    HEARTBEAT_INTERVAL_MS = 5 * 60 * 1000  # 5 minutes

    # Emitted when admin force-disconnects this session
    session_terminated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._client = None
        self._session_id: Optional[str] = None
        self._user_id: Optional[str] = None
        self._license_id: Optional[str] = None

        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.timeout.connect(self._send_heartbeat)

    def set_client(self, client):
        """Set the Supabase client"""
        self._client = client

    def activate(self, user_id: str, user_email: str) -> Tuple[bool, str]:
        """
        Full activation flow:
        1. Fetch user's active license
        2. Check if license is available
        3. Insert active_session
        4. Start heartbeat timer

        Returns:
            Tuple of (success, message)
        """
        if not self._client:
            return False, "No server connection"

        # 1. Fetch active license
        license_data = self._fetch_license(user_id)
        if not license_data:
            return False, "No active license found for this account"

        license_id = license_data["id"]
        license_token = license_data["token"]
        product_name = license_data["product_name"]

        # 2. Check availability
        available, used_by = self._check_availability(license_id, user_id)
        if not available:
            msg = "License is currently in use"
            if used_by:
                msg += f" by {used_by}"
            return False, msg

        # 3. Insert active session
        try:
            result = self._client.table("active_sessions").insert({
                "user_id": user_id,
                "user_email": user_email,
                "license_id": license_id,
                "license_token": license_token,
                "product_name": product_name,
            }).execute()

            if result.data:
                self._session_id = result.data[0]["id"]
                self._user_id = user_id
                self._license_id = license_id

                # 4. Start heartbeat
                self._heartbeat_timer.start(self.HEARTBEAT_INTERVAL_MS)
                return True, "Session started"

        except Exception as e:
            error_msg = str(e)
            # unique_license_session constraint violation = someone else took it
            if "unique_license_session" in error_msg:
                return False, "License is currently in use by another session"
            return False, f"Failed to start session: {error_msg}"

        return False, "Failed to create session"

    def deactivate(self):
        """End session: stop heartbeat and delete from active_sessions"""
        self._heartbeat_timer.stop()

        if self._client and self._session_id:
            try:
                self._client.table("active_sessions").delete().eq(
                    "id", self._session_id
                ).execute()
            except Exception:
                pass  # Best-effort cleanup

        self._session_id = None
        self._user_id = None
        self._license_id = None

    def _fetch_license(self, user_id: str) -> Optional[dict]:
        """Fetch user's active license from licenses table"""
        try:
            result = (
                self._client.table("licenses")
                .select("id, token, product_name")
                .eq("user_id", user_id)
                .eq("status", "active")
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0]
        except Exception:
            pass
        return None

    def _check_availability(
        self, license_id: str, user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """Check license availability via RPC function"""
        try:
            result = self._client.rpc(
                "check_license_availability",
                {"p_license_id": str(license_id), "p_user_id": str(user_id)},
            ).execute()
            if result.data:
                row = result.data[0]
                return row["is_available"], row.get("used_by_email")
        except Exception:
            pass
        # Default: allow if check fails (server unreachable, etc.)
        return True, None

    def _send_heartbeat(self):
        """Update last_heartbeat and detect force disconnect"""
        if not self._client or not self._session_id:
            return

        try:
            # Try to update heartbeat — returns updated row if session exists
            now = datetime.now(timezone.utc).isoformat()
            result = (
                self._client.table("active_sessions")
                .update({"last_heartbeat": now})
                .eq("id", self._session_id)
                .execute()
            )

            # UPDATE returns empty data when row doesn't exist (admin deleted it)
            if not result.data:
                self._on_session_gone()
                return

        except Exception as e:
            # If RLS blocks or row not found → check via RPC as fallback
            try:
                result = self._client.rpc(
                    "check_session_exists",
                    {"p_session_id": str(self._session_id)},
                ).execute()

                if result.data and not result.data[0].get("session_exists", True):
                    self._on_session_gone()
                    return
            except Exception:
                pass  # Network error — skip this cycle

    def _on_session_gone(self):
        """Handle session deleted by admin"""
        self._heartbeat_timer.stop()
        self._session_id = None
        self._user_id = None
        self._license_id = None
        self.session_terminated.emit()
