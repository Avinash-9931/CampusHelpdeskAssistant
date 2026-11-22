"""
Server-side session management for Campus Helpdesk Authentication.
Generates cryptographically random session tokens, verifies idle timeouts (default 30 min),
enforces total session lifetimes (default 8 hours), and provides atomic revocation on sign-out.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from config import settings
from auth.db import get_db_connection
from auth.security import generate_secure_token


def create_user_session(user_id: str, role: str = "Student", ip_address: str = "127.0.0.1") -> str:
    """
    Creates a new authenticated server-side session and returns a random 32-byte hex token.
    """
    token = generate_secure_token(32)
    now_dt = datetime.utcnow()
    expires_dt = now_dt + timedelta(minutes=settings.SESSION_TTL_MINUTES)

    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    expires_str = expires_dt.strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO sessions (session_id, user_id, role, expires_at, last_active_at, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'active', ?);
        """, (token, user_id, role, expires_str, now_str, now_str))

    return token


# Convenient alias
create_session = create_user_session


def validate_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Validates a session token against SQLite:
    - Verifies active status
    - Verifies overall expiration (8 hours)
    - Verifies idle timeout (30 minutes)
    - Updates last_active_at timestamp
    - Checks that user is active and returns user profile dict
    """
    if not session_id or not isinstance(session_id, str):
        return None

    cleaned_token = session_id.strip()
    now_dt = datetime.utcnow()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT s.session_id, s.user_id, s.role, s.expires_at, s.last_active_at, s.status as session_status,
               u.name, u.email, u.role as user_role, u.status as user_status, u.force_password_change
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_id = ? AND s.status = 'active';
        """, (cleaned_token,))
        row = cursor.fetchone()

        if not row:
            return None

        # 1. Check User Account Status
        if row["user_status"] != "active":
            cursor.execute("UPDATE sessions SET status = 'revoked' WHERE session_id = ?;", (cleaned_token,))
            return None

        # 2. Check Overall Expiration
        expires_str = row["expires_at"]
        try:
            expires_dt = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            expires_dt = datetime.fromisoformat(expires_str)

        if now_dt > expires_dt:
            cursor.execute("UPDATE sessions SET status = 'revoked' WHERE session_id = ?;", (cleaned_token,))
            return None

        # 3. Check Idle Timeout
        last_active_str = row["last_active_at"]
        try:
            last_active_dt = datetime.strptime(last_active_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            last_active_dt = datetime.fromisoformat(last_active_str)

        idle_seconds = (now_dt - last_active_dt).total_seconds()
        max_idle_seconds = settings.SESSION_IDLE_TIMEOUT_MINUTES * 60

        if idle_seconds > max_idle_seconds:
            cursor.execute("UPDATE sessions SET status = 'revoked' WHERE session_id = ?;", (cleaned_token,))
            return None

        # 4. Refresh Activity Timestamp
        cursor.execute("""
        UPDATE sessions SET last_active_at = ? WHERE session_id = ?;
        """, (now_str, cleaned_token))

        return {
            "session_id": cleaned_token,
            "id": row["user_id"],
            "name": row["name"],
            "email": row["email"],
            "role": row["user_role"],
            "status": row["user_status"],
            "force_password_change": bool(row["force_password_change"])
        }


def revoke_session(session_id: str) -> None:
    """Invalidates an active session token."""
    if not session_id:
        return
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET status = 'revoked' WHERE session_id = ?;", (session_id.strip(),))
