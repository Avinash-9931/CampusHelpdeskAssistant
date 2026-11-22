"""
Unit tests for Campus Helpdesk Authentication, Security, RBAC, and Sessions.
Validates credentials authentication, brute-force lockouts, HMAC-SHA256 OTP hashing,
single-use invalidation, cooldowns, session timeouts, RBAC enforcement,
last-admin protection, SQL-injection prevention, and SMTP error resilience.
"""

import time
import unittest.mock as mock
from datetime import datetime, timedelta
import pytest

from core.auth import authenticate_user, USERS_DB
from auth.security import (
    hash_password,
    verify_password,
    validate_password_policy,
    generate_otp_code,
    hash_otp_code,
    verify_otp_hash
)
from auth.service import (
    authenticate_credentials,
    create_user,
    bulk_import_users_csv,
    toggle_user_status,
    update_user_role,
    reset_user_password_admin,
    check_account_lockout,
    get_audit_logs,
    count_active_admins
)
from auth.otp import (
    create_otp,
    verify_otp,
    get_otp_cooldown_remaining
)
from auth.session import (
    create_user_session,
    validate_session,
    revoke_session
)
from auth.guards import (
    require_role,
    enforce_backend_role
)
from auth.mailer import (
    mask_email,
    send_otp_email
)
from auth.db import get_db_connection


# ==============================================================================
# 1. CORE BACKWARD-COMPATIBILITY TESTS
# ==============================================================================
def test_student_authentication_success():
    """Verifies that student credentials authenticate correctly."""
    user = authenticate_user("student", "student123")
    assert user is not None
    assert user["role"] == "Student"
    assert user["name"] == "Avinash Kumar"
    assert "S24CSEU0709" in user["id"]


def test_student_roll_number_authentication_success():
    """Verifies that student roll number credentials authenticate correctly."""
    user = authenticate_user("s24cseu0709", "student123")
    assert user is not None
    assert user["role"] == "Student"


def test_admin_authentication_success():
    """Verifies that administrator credentials authenticate correctly."""
    user = authenticate_user("admin", "admin123")
    assert user is not None
    assert user["role"] == "Admin"
    assert user["name"] == "System Administrator"


def test_authentication_invalid_password():
    """Verifies that wrong password returns None."""
    assert authenticate_user("student", "wrongpass") is None
    assert authenticate_user("admin", "invalid") is None


def test_authentication_invalid_user():
    """Verifies that non-existent username returns None."""
    assert authenticate_user("unknown_user", "password") is None
    assert authenticate_user("", "") is None


# ==============================================================================
# 2. A6: CREDENTIALS AUTHENTICATION & LOCKOUT TESTS
# ==============================================================================
def test_credentials_generic_error_and_no_enumeration():
    """Non-existent user and wrong password both return the same generic error."""
    ok1, reason1, user1 = authenticate_credentials("non_existent_user_999", "password123")
    assert not ok1
    assert "Invalid ID or password" in reason1
    assert user1 is None

    ok2, reason2, user2 = authenticate_credentials("student", "WrongPassword999!")
    assert not ok2
    assert "Invalid ID or password" in reason2
    assert user2 is None


def test_account_lockout_triggers_after_five_failures():
    """Verifies 5 failed attempts locks the account for 15 minutes."""
    import secrets
    test_user_id = f"lockout_test_{secrets.token_hex(4)}"
    create_user(test_user_id, "Lockout Test", f"{test_user_id}@campus.edu", role="Student", password="CorrectPass123!")

    # Attempt 5 failed logins
    for _ in range(5):
        ok, reason, _ = authenticate_credentials(test_user_id, "WrongPass123!")
        assert not ok
        assert "Invalid ID or password" in reason

    # After 5 failed attempts, account is locked; even correct password is now denied
    ok, reason, user = authenticate_credentials(test_user_id, "CorrectPass123!")
    assert not ok
    assert "locked" in reason.lower()
    assert user is None

    is_locked, mins_left = check_account_lockout(test_user_id)
    assert is_locked
    assert mins_left > 0


# ==============================================================================
# 3. A6: OTP CRYPTOGRAPHY & SECURITY LIFECYCLE
# ==============================================================================
def test_otp_properties_and_hmac_hashing():
    """Verifies OTP generation, length, and HMAC-SHA256 hashing."""
    code = generate_otp_code(6)
    assert len(code) == 6
    assert code.isdigit()

    code_hash = hash_otp_code(code)
    assert len(code_hash) == 64  # SHA256 hex length
    assert verify_otp_hash(code, code_hash)
    assert not verify_otp_hash("000000", code_hash)


def test_otp_single_use_and_replay_rejection():
    """Verifies OTP can be verified once, and second attempt is rejected."""
    import secrets
    test_id = f"otp_replay_{secrets.token_hex(4)}"
    create_user(test_id, "OTP Replay User", f"{test_id}@campus.edu", role="Student", password="ValidPass123!")

    ok, raw_code, _ = create_otp(test_id)
    assert ok
    assert len(raw_code) == 6

    # First verification must succeed
    v_ok, msg = verify_otp(test_id, raw_code)
    assert v_ok

    # Second verification must fail (already used)
    v_ok2, msg2 = verify_otp(test_id, raw_code)
    assert not v_ok2
    assert "no active verification code" in msg2.lower() or "expired" in msg2.lower()


def test_otp_max_wrong_attempts_invalidation():
    """5 consecutive wrong OTP attempts permanently invalidates the OTP."""
    import secrets
    test_id = f"otp_brute_{secrets.token_hex(4)}"
    create_user(test_id, "OTP Brute User", f"{test_id}@campus.edu", role="Student", password="ValidPass123!")

    ok, raw_code, _ = create_otp(test_id)
    assert ok

    # 4 wrong attempts
    for _ in range(4):
        v_ok, msg = verify_otp(test_id, "000000")
        assert not v_ok

    # 5th wrong attempt invalidates the OTP code
    v_ok, msg = verify_otp(test_id, "000000")
    assert not v_ok
    assert "maximum attempts exceeded" in msg.lower() or "invalidated" in msg.lower()

    # Even the correct code is now rejected
    v_ok, msg = verify_otp(test_id, raw_code)
    assert not v_ok


def test_otp_resend_cooldown():
    """Requests within 30 seconds are rejected with cooldown notice."""
    import secrets
    test_id = f"otp_cooldown_{secrets.token_hex(4)}"
    create_user(test_id, "Cooldown User", f"{test_id}@campus.edu", role="Student", password="ValidPass123!")

    ok, code1, _ = create_otp(test_id)
    assert ok

    # Immediate second request must be blocked by 30s cooldown
    ok2, msg2, cooldown = create_otp(test_id)
    assert not ok2
    assert cooldown > 0
    assert "Please wait" in msg2


# ==============================================================================
# 4. A6: SESSIONS & IDLE TIMEOUT
# ==============================================================================
def test_session_lifecycle_and_idle_timeout():
    """Verifies session issuance, validation, and idle timeout expiration."""
    import secrets
    test_id = f"session_test_{secrets.token_hex(4)}"
    create_user(test_id, "Session Test", f"{test_id}@campus.edu", role="Student", password="ValidPass123!")

    token = create_user_session(test_id, role="Student")
    assert token and len(token) == 64

    # Validate active session
    sess = validate_session(token)
    assert sess is not None
    assert sess["id"] == test_id
    assert sess["role"] == "Student"

    # Simulate idle timeout > 30 minutes in the database
    old_time = (datetime.utcnow() - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection() as conn:
        conn.cursor().execute("UPDATE sessions SET last_active_at = ? WHERE session_id = ?;", (old_time, token))

    # Should now be rejected due to idle timeout
    sess_expired = validate_session(token)
    assert sess_expired is None


def test_session_instant_revocation_on_logout():
    """Verifies that revoke_session immediately invalidates the session token."""
    import secrets
    test_id = f"logout_test_{secrets.token_hex(4)}"
    create_user(test_id, "Logout User", f"{test_id}@campus.edu", role="Student", password="ValidPass123!")

    token = create_user_session(test_id, role="Student")
    assert validate_session(token) is not None

    revoke_session(token)
    assert validate_session(token) is None


# ==============================================================================
# 5. A6: RBAC GUARDS & LAST-ADMIN PROTECTION
# ==============================================================================
def test_rbac_student_vs_admin_permissions():
    """Verifies that require_role correctly enforces Student vs Admin boundaries."""
    student_user = {"id": "S100", "role": "Student"}
    admin_user = {"id": "ADM100", "role": "Admin"}

    # Student checks
    assert require_role("Student", student_user)
    assert not require_role("Admin", student_user)

    # Admin checks (Admin satisfies both)
    assert require_role("Student", admin_user)
    assert require_role("Admin", admin_user)

    # enforce_backend_role raises PermissionError on unauthorized call
    with pytest.raises(PermissionError):
        enforce_backend_role("Admin", student_user)


def test_last_admin_protection():
    """Verifies that the last active Admin account cannot be deactivated or demoted."""
    # Ensure at least 1 active admin exists
    active_admins = count_active_admins()
    assert active_admins >= 1

    # Find an active admin
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE role = 'Admin' AND status = 'active';")
        admin_rows = cursor.fetchall()

    try:
        # If there are multiple, demote until only 1 remains
        if len(admin_rows) > 1:
            for r in admin_rows[1:]:
                update_user_role(r["id"], "Student", actor_id="TEST_RUNNER")

        sole_admin_id = admin_rows[0]["id"]
        assert count_active_admins() == 1

        # Attempting to deactivate the last admin must fail
        ok, msg = toggle_user_status(sole_admin_id, actor_id="TEST_RUNNER")
        assert not ok
        assert "last remaining active Administrator" in msg

        # Attempting to demote the last admin must fail
        ok2, msg2 = update_user_role(sole_admin_id, "Student", actor_id="TEST_RUNNER")
        assert not ok2
        assert "last remaining active Administrator" in msg2
    finally:
        # Restore demoted admins
        if len(admin_rows) > 1:
            for r in admin_rows[1:]:
                update_user_role(r["id"], "Admin", actor_id="TEST_RUNNER")


# ==============================================================================
# 6. A6: SQL INJECTION DEFENSE & SMTP RESILIENCE
# ==============================================================================
def test_sql_injection_defense():
    """Verifies SQL injection strings in username/ID fields are harmlessly handled."""
    sql_payloads = [
        "' OR '1'='1",
        "admin' --",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --"
    ]
    for payload in sql_payloads:
        ok, reason, user = authenticate_credentials(payload, "password123")
        assert not ok
        assert user is None

    # Verify users table is completely intact
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM users;")
        assert cursor.fetchone()["cnt"] > 0


def test_smtp_failure_handling_and_no_crash():
    """Mocks an SMTP exception and verifies graceful handling without leaking secrets."""
    with mock.patch("smtplib.SMTP") as mock_smtp, \
         mock.patch("config.settings.SMTP_USER", "test_admin@campus.edu"), \
         mock.patch("config.settings.SMTP_APP_PASSWORD", "test_secret_app_password"):
        mock_smtp.side_effect = Exception("SMTP connection refused")
        sent_ok, msg = send_otp_email("test@campus.edu", "123456", user_name="Student")
        assert not sent_ok
        assert "123456" not in msg  # No secret leakage in error output
        assert "Unable to send verification email" in msg or "SMTP" in msg


def test_email_masking():
    """Verifies privacy masking on email addresses."""
    assert mask_email("avinash.kumar@campus.edu") == "a************@campus.edu"
    assert mask_email("admin@university.edu") == "a****@university.edu"
    assert mask_email("x@y.com") == "x***@y.com"
