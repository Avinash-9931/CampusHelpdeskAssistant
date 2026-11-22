"""
One-Time Passcode (OTP) lifecycle management for Campus Helpdesk Auth.
Enforces HMAC-SHA256 hashing, 5-minute expiry, 30s resend cooldown,
hourly send limits (max 5/hr), max 5 wrong attempts lockout, and single-use invalidation.
"""

from datetime import datetime, timedelta
from typing import Tuple, Optional
from config import settings
from auth.db import get_db_connection
from auth.security import generate_otp_code, hash_otp_code, verify_otp_hash
from auth.mailer import send_otp_email


def get_otp_cooldown_remaining(user_id: str) -> int:
    """Returns the seconds remaining before a user can request a resend (30s cooldown)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT created_at FROM otp_codes 
        WHERE user_id = ? 
        ORDER BY id DESC LIMIT 1;
        """, (user_id,))
        row = cursor.fetchone()
        if not row:
            return 0
        created_str = row["created_at"]
        try:
            created_dt = datetime.strptime(created_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            created_dt = datetime.fromisoformat(created_str)
        elapsed = (datetime.utcnow() - created_dt).total_seconds()
        if elapsed < 30:
            return int(30 - elapsed)
        return 0


def create_otp(user_id: str, purpose: str = "login") -> Tuple[bool, str, int]:
    """
    Generates and stores a new OTP challenge in SQLite.
    Returns: (success: bool, raw_code_or_err: str, cooldown_seconds_remaining: int)
    """
    cooldown = get_otp_cooldown_remaining(user_id)
    if cooldown > 0:
        return False, f"Please wait {cooldown} seconds before requesting a new code.", cooldown

    with get_db_connection() as conn:
        cursor = conn.cursor()
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        SELECT COUNT(*) as cnt FROM otp_codes
        WHERE user_id = ? AND created_at >= ?;
        """, (user_id, one_hour_ago))
        count = cursor.fetchone()["cnt"]
        if count >= 5:
            return False, "Too many verification requests. Please wait an hour before requesting another code.", 0

        raw_code = generate_otp_code(6)
        code_hash = hash_otp_code(raw_code)
        now_dt = datetime.utcnow()
        expires_dt = now_dt + timedelta(seconds=settings.OTP_TTL_SECONDS)
        expires_str = expires_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Invalidate prior unused codes
        cursor.execute("""
        UPDATE otp_codes SET used = 1 
        WHERE user_id = ? AND purpose = ? AND used = 0;
        """, (user_id, purpose))

        cursor.execute("""
        INSERT INTO otp_codes (user_id, code_hash, purpose, expires_at, attempts, used, created_at)
        VALUES (?, ?, ?, ?, 0, 0, ?);
        """, (user_id, code_hash, purpose, expires_str, now_dt.strftime("%Y-%m-%d %H:%M:%S")))

    return True, raw_code, 0


def create_and_send_otp(
    user_id: str,
    email: str,
    user_name: str = "Student",
    purpose: str = "login"
) -> Tuple[bool, str, Optional[str]]:
    """
    Generates a cryptographically secure 6-digit OTP, stores its HMAC-SHA256 hash,
    and sends it via email.
    
    Returns:
        (success: bool, status_message: str, dev_otp_code: Optional[str])
    """
    # 1. Check Resend Cooldown (30s)
    cooldown = get_otp_cooldown_remaining(user_id)
    if cooldown > 0:
        return False, f"Please wait {cooldown} seconds before requesting a new code.", None

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 2. Enforce Hourly Limit (max 5 OTPs per hour per user)
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        SELECT COUNT(*) as cnt FROM otp_codes
        WHERE user_id = ? AND created_at >= ?;
        """, (user_id, one_hour_ago))
        count = cursor.fetchone()["cnt"]
        if count >= 5:
            return False, "Too many verification requests. Please wait an hour before requesting another code.", None

        # 3. Generate and Hash Code
        raw_code = generate_otp_code(6)
        code_hash = hash_otp_code(raw_code)
        now_dt = datetime.utcnow()
        expires_dt = now_dt + timedelta(seconds=settings.OTP_TTL_SECONDS)
        expires_str = expires_dt.strftime("%Y-%m-%d %H:%M:%S")

        # Invalidate any previous unused OTPs for this user and purpose
        cursor.execute("""
        UPDATE otp_codes SET used = 1 
        WHERE user_id = ? AND purpose = ? AND used = 0;
        """, (user_id, purpose))

        # Insert new hashed record
        cursor.execute("""
        INSERT INTO otp_codes (user_id, code_hash, purpose, expires_at, attempts, used, created_at)
        VALUES (?, ?, ?, ?, 0, 0, ?);
        """, (user_id, code_hash, purpose, expires_str, now_dt.strftime("%Y-%m-%d %H:%M:%S")))

    # 4. Dispatch Email
    ttl_min = max(1, settings.OTP_TTL_SECONDS // 60)
    sent_ok, msg = send_otp_email(
        to_email=email,
        otp_code=raw_code,
        user_name=user_name,
        purpose=purpose,
        ttl_minutes=ttl_min
    )

    if not sent_ok:
        return False, msg, None

    if msg == "DEV_MODE":
        return True, "DEV_MODE", raw_code
    return True, "SUCCESS", None


def verify_otp(user_id: str, entered_code: str, purpose: str = "login") -> Tuple[bool, str]:
    """
    Verifies a user-entered OTP against the stored HMAC-SHA256 hash using constant-time comparison.
    Enforces maximum 5 attempts and single-use consumption.
    """
    cleaned_code = (entered_code or "").strip()
    if not cleaned_code or len(cleaned_code) != 6 or not cleaned_code.isdigit():
        return False, "Please enter a valid 6-digit verification code."

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, code_hash, expires_at, attempts, used, created_at
        FROM otp_codes
        WHERE user_id = ? AND purpose = ? AND used = 0
        ORDER BY id DESC LIMIT 1;
        """, (user_id, purpose))
        row = cursor.fetchone()

        if not row:
            return False, "No active verification code found. Please request a new code."

        otp_id = row["id"]
        stored_hash = row["code_hash"]
        expires_str = row["expires_at"]
        attempts = row["attempts"]

        # Check Expiry
        try:
            expires_dt = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            expires_dt = datetime.fromisoformat(expires_str)

        if datetime.utcnow() > expires_dt:
            cursor.execute("UPDATE otp_codes SET used = 1 WHERE id = ?;", (otp_id,))
            return False, "Verification code has expired. Please request a new code."

        # Check Max Attempts Lockout
        if attempts >= 5:
            cursor.execute("UPDATE otp_codes SET used = 1 WHERE id = ?;", (otp_id,))
            return False, "Maximum attempts exceeded. This code has been invalidated. Please request a new code."

        # Increment attempts counter
        new_attempts = attempts + 1
        cursor.execute("UPDATE otp_codes SET attempts = ? WHERE id = ?;", (new_attempts, otp_id))

        # Constant-time comparison
        is_valid = verify_otp_hash(cleaned_code, stored_hash)

        if is_valid:
            cursor.execute("UPDATE otp_codes SET used = 1 WHERE id = ?;", (otp_id,))
            return True, "Verification successful."
        else:
            remaining = max(0, 5 - new_attempts)
            if remaining == 0:
                cursor.execute("UPDATE otp_codes SET used = 1 WHERE id = ?;", (otp_id,))
                return False, "Maximum attempts exceeded. This code has been invalidated. Please request a new code."
            return False, f"Invalid verification code. {remaining} attempt(s) remaining."
