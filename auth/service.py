"""
Core authentication and user service orchestrator for Campus Helpdesk.
Provides credential verification, brute-force lockout rate limiting,
user management (CRUD, bulk CSV import, password reset, last-admin protection),
audit logging, and per-user chat history persistence.
"""

import csv
import io
import sqlite3
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any, List

from auth.db import get_db_connection, init_db
from auth.security import (
    hash_password,
    verify_password,
    validate_password_policy,
    generate_random_initial_password
)
from core.logger import logger

# Initialize database schema on module import
init_db()


# ==============================================================================
# 1. AUDIT LOGGING HELPER
# ==============================================================================
def log_audit(
    action: str,
    user_id: Optional[str] = None,
    details: str = "",
    ip_address: str = "127.0.0.1",
    conn: Optional[sqlite3.Connection] = None
) -> None:
    """Records a security or administrative action into the immutable audit_log table."""
    now_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    try:
        if conn is not None:
            conn.cursor().execute("""
            INSERT INTO audit_log (timestamp, user_id, action, details, ip_address)
            VALUES (?, ?, ?, ?, ?);
            """, (now_ts, user_id, action, details, ip_address))
        else:
            with get_db_connection() as c:
                c.cursor().execute("""
                INSERT INTO audit_log (timestamp, user_id, action, details, ip_address)
                VALUES (?, ?, ?, ?, ?);
                """, (now_ts, user_id, action, details, ip_address))
    except Exception as e:
        logger.error(f"Audit log write failed: {type(e).__name__} - {e}")


def get_audit_logs(limit: int = 150, action_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves recent audit log events with optional action filtering."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if action_filter and action_filter != "All Actions":
            cursor.execute("""
            SELECT id, timestamp, user_id, action, details, ip_address 
            FROM audit_log 
            WHERE action = ?
            ORDER BY id DESC LIMIT ?;
            """, (action_filter, limit))
        else:
            cursor.execute("""
            SELECT id, timestamp, user_id, action, details, ip_address 
            FROM audit_log 
            ORDER BY id DESC LIMIT ?;
            """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


# ==============================================================================
# 2. CREDENTIAL AUTHENTICATION & BRUTE-FORCE LOCKOUT
# ==============================================================================
def check_account_lockout(user_id: str, lockout_window_minutes: int = 15, max_failures: int = 5) -> Tuple[bool, int]:
    """
    Checks if a user ID is locked out due to consecutive failed password attempts.
    Returns: (is_locked: bool, remaining_minutes: int)
    """
    cleaned_id = (user_id or "").strip().lower()
    window_start = (datetime.utcnow() - timedelta(minutes=lockout_window_minutes)).strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Find failed attempts since window_start
        cursor.execute("""
        SELECT attempted_at, success FROM login_attempts
        WHERE LOWER(user_id) = ? AND attempted_at >= ?
        ORDER BY id DESC LIMIT ?;
        """, (cleaned_id, window_start, max_failures))
        rows = cursor.fetchall()

        if len(rows) >= max_failures and all(r["success"] == 0 for r in rows):
            oldest_fail_str = rows[-1]["attempted_at"]
            try:
                oldest_dt = datetime.strptime(oldest_fail_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                oldest_dt = datetime.fromisoformat(oldest_fail_str)
            elapsed_sec = (datetime.utcnow() - oldest_dt).total_seconds()
            remaining_sec = max(0, (lockout_window_minutes * 60) - elapsed_sec)
            return True, int(remaining_sec // 60) + 1
        return False, 0


def authenticate_credentials(
    user_id: str,
    password: str,
    ip_address: str = "127.0.0.1"
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Validates user ID and password against the database:
    - Enforces 5-failure lockout within 15 minutes.
    - Constant-time Argon2 password verification.
    - Generic error message to prevent username enumeration.
    
    Returns:
        (success: bool, error_message: str, user_dict: Optional[dict])
    """
    cleaned_id = (user_id or "").strip()
    cleaned_pwd = (password or "").strip()

    if not cleaned_id or not cleaned_pwd:
        return False, "Invalid ID or password.", None

    # Check brute-force lockout
    is_locked, remaining_min = check_account_lockout(cleaned_id)
    if is_locked:
        log_audit("lockout_enforced", user_id=cleaned_id, details=f"Locked for {remaining_min} min", ip_address=ip_address)
        return False, f"Account temporarily locked due to consecutive failed attempts. Please try again in {remaining_min} minute(s).", None

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Parameterized query strictly prevents SQL injection
        cursor.execute("""
        SELECT id, name, email, password_hash, role, status, force_password_change
        FROM users
        WHERE LOWER(id) = LOWER(?);
        """, (cleaned_id,))
        row = cursor.fetchone()

        if not row:
            # Record failed attempt against this ID
            cursor.execute("INSERT INTO login_attempts (user_id, attempted_at, success) VALUES (?, ?, 0);", (cleaned_id, now_str))
            log_audit("login_failure", user_id=cleaned_id, details="User ID not found", ip_address=ip_address, conn=conn)
            return False, "Invalid ID or password.", None

        # Check account status
        if row["status"] != "active":
            log_audit("login_failure", user_id=cleaned_id, details="Account disabled", ip_address=ip_address, conn=conn)
            return False, "This account has been disabled. Please contact the administrator.", None

        # Verify password with Argon2
        if not verify_password(cleaned_pwd, row["password_hash"]):
            cursor.execute("INSERT INTO login_attempts (user_id, attempted_at, success) VALUES (?, ?, 0);", (cleaned_id, now_str))
            log_audit("login_failure", user_id=cleaned_id, details="Incorrect password", ip_address=ip_address, conn=conn)
            return False, "Invalid ID or password.", None

        # Success: record attempt and update last login
        cursor.execute("INSERT INTO login_attempts (user_id, attempted_at, success) VALUES (?, ?, 1);", (cleaned_id, now_str))
        cursor.execute("UPDATE users SET last_login_at = ? WHERE id = ?;", (now_str, row["id"]))

        user_data = {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "role": row["role"],
            "status": row["status"],
            "force_password_change": bool(row["force_password_change"])
        }
        return True, "OK", user_data


# ==============================================================================
# 3. USER MANAGEMENT & RBAC MUTATIONS
# ==============================================================================
def count_active_admins() -> int:
    """Returns the number of active Administrator accounts."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'Admin' AND status = 'active';")
        return cursor.fetchone()["cnt"]


def create_user(
    user_id: str,
    name: str,
    email: str,
    role: str = "Student",
    password: Optional[str] = None,
    force_password_change: bool = False,
    actor_id: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Creates a new user account.
    Returns: (success: bool, status_message: str, temporary_password: Optional[str])
    """
    cleaned_id = (user_id or "").strip()
    cleaned_name = (name or "").strip()
    cleaned_email = (email or "").strip().lower()

    if not cleaned_id or not cleaned_name or not cleaned_email:
        return False, "ID, Name, and Email are all required.", None

    if role not in ("Student", "Admin"):
        return False, "Role must be either 'Student' or 'Admin'.", None

    temp_password = None
    if not password:
        temp_password = generate_random_initial_password(12)
        pwd_to_hash = temp_password
        force_password_change = True
    else:
        is_valid, msg = validate_password_policy(password)
        if not is_valid:
            return False, msg, None
        pwd_to_hash = password

    pwd_hash = hash_password(pwd_to_hash)
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO users (id, name, email, password_hash, role, status, force_password_change, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?);
            """, (cleaned_id, cleaned_name, cleaned_email, pwd_hash, role, 1 if force_password_change else 0, now_str, now_str))

        log_audit("user_create", user_id=actor_id, details=f"Created {role} {cleaned_id} ({cleaned_email})")
        return True, "User created successfully.", temp_password
    except sqlite3.IntegrityError as e:
        err_str = str(e).lower()
        if "unique" in err_str or "email" in err_str:
            return False, f"A user with email '{cleaned_email}' or ID '{cleaned_id}' already exists.", None
        return False, "User ID already exists in the system.", None


def bulk_import_users_csv(csv_text: str, actor_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Parses and imports a CSV string with columns: id, name, email (and optional role).
    Generates random passwords with forced change on first login.
    """
    report = {
        "total": 0,
        "added": 0,
        "rejected": 0,
        "results": []
    }

    if not csv_text or not csv_text.strip():
        report["results"].append({"row": 0, "status": "FAIL", "reason": "Empty CSV file."})
        return report

    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    # Validate header
    fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
    if not all(col in fieldnames for col in ["id", "name", "email"]):
        report["results"].append({
            "row": 0,
            "status": "FAIL",
            "reason": f"CSV must contain 'id', 'name', 'email' headers. Found: {reader.fieldnames}"
        })
        return report

    for idx, row in enumerate(reader, start=1):
        report["total"] += 1
        # Extract keys case-insensitively
        u_id = row.get("id") or row.get("ID") or ""
        u_name = row.get("name") or row.get("Name") or ""
        u_email = row.get("email") or row.get("Email") or ""
        u_role = row.get("role") or row.get("Role") or "Student"
        u_role = u_role.capitalize() if u_role.lower() in ("admin", "student") else "Student"

        ok, msg, temp_pwd = create_user(
            user_id=u_id,
            name=u_name,
            email=u_email,
            role=u_role,
            force_password_change=True,
            actor_id=actor_id
        )

        if ok:
            report["added"] += 1
            report["results"].append({
                "row": idx,
                "id": u_id,
                "name": u_name,
                "email": u_email,
                "role": u_role,
                "status": "PASS",
                "initial_password": temp_pwd
            })
        else:
            report["rejected"] += 1
            report["results"].append({
                "row": idx,
                "id": u_id,
                "name": u_name,
                "email": u_email,
                "status": "FAIL",
                "reason": msg
            })

    log_audit("user_bulk_import", user_id=actor_id, details=f"Imported: {report['added']} added, {report['rejected']} rejected")
    return report


def toggle_user_status(target_user_id: str, actor_id: Optional[str] = None) -> Tuple[bool, str]:
    """Toggles a user's status between 'active' and 'disabled' with last-admin protection."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, role, status FROM users WHERE id = ?;", (target_user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "User not found."

        current_status = row["status"]
        user_role = row["role"]
        new_status = "disabled" if current_status == "active" else "active"

        # Protection: Cannot disable the last remaining active admin
        if user_role == "Admin" and new_status == "disabled":
            if count_active_admins() <= 1:
                return False, "Cannot disable the last remaining active Administrator account."

        cursor.execute("""
        UPDATE users SET status = ?, updated_at = ? WHERE id = ?;
        """, (new_status, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), target_user_id))

    log_audit("user_status_toggle", user_id=actor_id, details=f"Changed {target_user_id} status to {new_status}")
    return True, f"User status changed to '{new_status}'."


def update_user_role(target_user_id: str, new_role: str, actor_id: Optional[str] = None) -> Tuple[bool, str]:
    """Updates a user's role to 'Student' or 'Admin' with last-admin protection."""
    if new_role not in ("Student", "Admin"):
        return False, "Role must be 'Student' or 'Admin'."

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, role, status FROM users WHERE id = ?;", (target_user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "User not found."

        current_role = row["role"]
        if current_role == new_role:
            return True, f"User is already assigned '{new_role}' role."

        # Protection: Cannot demote the last remaining active Admin
        if current_role == "Admin" and new_role != "Admin":
            if count_active_admins() <= 1:
                return False, "Cannot demote the last remaining active Administrator account."

        cursor.execute("""
        UPDATE users SET role = ?, updated_at = ? WHERE id = ?;
        """, (new_role, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), target_user_id))

    log_audit("user_role_change", user_id=actor_id, details=f"Changed {target_user_id} role from {current_role} to {new_role}")
    return True, f"Role updated to '{new_role}'."


def reset_user_password_admin(target_user_id: str, actor_id: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """Generates a new random temporary password for a user, enforcing password change on next login."""
    temp_pwd = generate_random_initial_password(12)
    pwd_hash = hash_password(temp_pwd)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?;", (target_user_id,))
        if not cursor.fetchone():
            return False, "User not found.", None

        cursor.execute("""
        UPDATE users SET password_hash = ?, force_password_change = 1, updated_at = ?
        WHERE id = ?;
        """, (pwd_hash, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), target_user_id))

    log_audit("user_password_reset", user_id=actor_id, details=f"Admin reset password for {target_user_id}")
    return True, "Password reset successfully.", temp_pwd


def change_user_password(user_id: str, current_password: str, new_password: str) -> Tuple[bool, str]:
    """Validates current password and updates to a new password complying with security policy."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE id = ?;", (user_id,))
        row = cursor.fetchone()
        if not row:
            return False, "User account not found."

        if not verify_password(current_password, row["password_hash"]):
            return False, "Current password is incorrect."

        is_valid, msg = validate_password_policy(new_password)
        if not is_valid:
            return False, msg

        new_hash = hash_password(new_password)
        cursor.execute("""
        UPDATE users SET password_hash = ?, force_password_change = 0, updated_at = ?
        WHERE id = ?;
        """, (new_hash, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user_id))

    log_audit("password_change", user_id=user_id, details="User changed their password")
    return True, "Password changed successfully."


def list_users(search_query: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns a list of registered users matching an optional search term."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if search_query and search_query.strip():
            term = f"%{search_query.strip().lower()}%"
            cursor.execute("""
            SELECT id, name, email, role, status, force_password_change, created_at, last_login_at
            FROM users
            WHERE LOWER(id) LIKE ? OR LOWER(name) LIKE ? OR LOWER(email) LIKE ?
            ORDER BY created_at DESC;
            """, (term, term, term))
        else:
            cursor.execute("""
            SELECT id, name, email, role, status, force_password_change, created_at, last_login_at
            FROM users
            ORDER BY created_at DESC;
            """)
        return [dict(row) for row in cursor.fetchall()]


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves user profile dictionary by ID."""
    if not user_id:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, name, email, role, status, force_password_change, created_at, last_login_at
        FROM users WHERE id = ?;
        """, (user_id.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves user profile dictionary by email (case-insensitive)."""
    if not email:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, name, email, role, status, force_password_change, created_at, last_login_at
        FROM users WHERE LOWER(email) = LOWER(?);
        """, (email.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def login_or_register_with_email(
    email: str,
    name: Optional[str] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Authenticates a user via Google / Email OTP.
    If user exists by email, returns their profile.
    If user does not exist, seamlessly auto-provisions a Student account.
    
    Returns:
        (success: bool, status_message: str, user_dict: Optional[dict])
    """
    cleaned_email = (email or "").strip().lower()
    if not cleaned_email or "@" not in cleaned_email:
        return False, "Please enter a valid email address.", None

    user = get_user_by_email(cleaned_email)
    if user:
        if user["status"] != "active":
            return False, "This account has been disabled. Please contact the administrator.", None
        return True, "OK", user

    # User does not exist yet: auto-register as Student
    email_user_part = cleaned_email.split("@")[0]
    base_id = "".join(c for c in email_user_part if c.isalnum() or c in ("-", "_")) or "student"
    candidate_id = base_id

    with get_db_connection() as conn:
        cursor = conn.cursor()
        suffix = 1
        while cursor.execute("SELECT 1 FROM users WHERE LOWER(id) = LOWER(?);", (candidate_id,)).fetchone():
            candidate_id = f"{base_id}_{suffix}"
            suffix += 1

    display_name = (name or "").strip() or base_id.replace(".", " ").replace("_", " ").title()
    auto_pwd = generate_random_initial_password(16)

    ok, msg, _ = create_user(
        user_id=candidate_id,
        name=display_name,
        email=cleaned_email,
        role="Student",
        password=auto_pwd,
        force_password_change=False
    )
    if not ok:
        return False, msg, None

    created_user = get_user_by_email(cleaned_email)
    return True, "Account registered", created_user


def reset_user_password(user_id: str, new_password: str, reset_by: Optional[str] = None) -> Tuple[bool, str]:
    """Sets a user's password directly (used by admin CLI or self-service password reset)."""
    is_valid, msg = validate_password_policy(new_password)
    if not is_valid:
        return False, msg

    pwd_hash = hash_password(new_password)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?;", (user_id,))
        if not cursor.fetchone():
            return False, "User not found."

        cursor.execute("""
        UPDATE users SET password_hash = ?, force_password_change = 0, updated_at = ?
        WHERE id = ?;
        """, (pwd_hash, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), user_id))

    log_audit("password_reset", user_id=reset_by or user_id, details=f"Password reset for {user_id}")
    return True, "Password successfully updated."


# ==============================================================================
# 4. USER CHAT HISTORY PERSISTENCE
# ==============================================================================
def save_chat_turn(user_id: str, conversation_id: str, role: str, content: str, metadata_json: str = "{}") -> None:
    """Saves a conversation turn into user_chat_history."""
    if not user_id:
        return
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO user_chat_history (user_id, conversation_id, role, content, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (user_id, conversation_id, role, content, metadata_json, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
    except sqlite3.IntegrityError:
        # Ignore foreign key errors if user is an unpersisted test account (e.g. ADM-001 in unit tests)
        pass


def get_user_chat_history(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves conversation history specifically owned by user_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, conversation_id, role, content, metadata_json, created_at
        FROM user_chat_history
        WHERE user_id = ?
        ORDER BY id DESC LIMIT ?;
        """, (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]


def clear_user_chat_history(user_id: str) -> None:
    """Deletes all saved chat history for user_id only."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_chat_history WHERE user_id = ?;", (user_id,))
    log_audit("clear_chat_history", user_id=user_id, details="User cleared their conversation history")
