"""
Security, cryptographic hashing, and validation utilities for Campus Helpdesk Auth.
Enforces Argon2 password hashing, HMAC-SHA256 OTP hashing, constant-time comparisons,
and cryptographically secure random token generation.
"""

import hmac
import hashlib
import secrets
import string
import re
from typing import Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from config import settings

_ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
    salt_len=16
)


def hash_password(plaintext_password: str) -> str:
    """Hashes a plaintext password using Argon2id with cryptographically random salt."""
    if not plaintext_password:
        raise ValueError("Password cannot be empty.")
    return _ph.hash(plaintext_password)


def verify_password(plaintext_password: str, hashed_password: str) -> bool:
    """Verifies a password against an Argon2 hash using constant-time verification."""
    if not plaintext_password or not hashed_password:
        return False
    try:
        return _ph.verify(hashed_password, plaintext_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    except Exception:
        return False


def validate_password_policy(password: str) -> Tuple[bool, str]:
    """
    Enforces university password policy:
    - Minimum 8 characters
    - Mixed character types (letters and digits/symbols)
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[\d\W_]", password):
        return False, "Password must contain at least one number or symbol (mixed characters)."
    return True, "Password meets security requirements."


def generate_secure_token(nbytes: int = 32) -> str:
    """Generates a cryptographically secure URL-safe random hex token."""
    return secrets.token_hex(nbytes)


def generate_otp_code(digits: int = 6) -> str:
    """Generates a cryptographically secure numeric OTP string."""
    return "".join(secrets.choice(string.digits) for _ in range(digits))


def hash_otp_code(code: str, secret: str = None) -> str:
    """
    Hashes an OTP code with HMAC-SHA256 using the server's AUTH_SECRET_KEY.
    Guarantees raw OTPs are never stored in the database.
    """
    sec = secret or settings.AUTH_SECRET_KEY
    return hmac.new(sec.encode("utf-8"), code.strip().encode("utf-8"), hashlib.sha256).hexdigest()


def verify_otp_hash(entered_code: str, stored_hash: str, secret: str = None) -> bool:
    """Performs constant-time comparison of the entered OTP against the stored HMAC-SHA256 hash."""
    if not entered_code or not stored_hash:
        return False
    computed = hash_otp_code(entered_code, secret=secret)
    return hmac.compare_digest(computed, stored_hash)


def generate_random_initial_password(length: int = 12) -> str:
    """Generates a secure temporary password complying with the password policy."""
    lower = secrets.choice(string.ascii_lowercase)
    upper = secrets.choice(string.ascii_uppercase)
    digit = secrets.choice(string.digits)
    symbol = secrets.choice("!@#$%^&*")
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    remaining = [secrets.choice(all_chars) for _ in range(length - 4)]
    password_list = [lower, upper, digit, symbol] + remaining
    secrets.SystemRandom().shuffle(password_list)
    return "".join(password_list)
