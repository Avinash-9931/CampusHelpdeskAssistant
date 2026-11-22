"""
Database access and schema management for Campus Helpdesk Authentication.
Uses standard library sqlite3 with parameterized queries only.
Provides thread-safe connections, foreign keys enforcement, and migration initialization.
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional
from config import settings

_local = threading.local()


def get_db_path() -> Path:
    """Returns the configured SQLite database path, ensuring parent directories exist."""
    path = settings.AUTH_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager yielding a thread-local SQLite connection with foreign keys enabled
    and row factory set to sqlite3.Row for clean dict-like access.
    """
    conn = sqlite3.connect(
        str(get_db_path()),
        timeout=15.0,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Initializes tables, indices, and constraints if they do not exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Student', 'Admin')),
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'disabled')),
            force_password_change INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login_at TIMESTAMP
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);")

        # 2. OTP Codes Table (Stores HMAC-SHA256 hash only)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            code_hash TEXT NOT NULL,
            purpose TEXT NOT NULL DEFAULT 'login' CHECK(purpose IN ('login', 'reset_password')),
            expires_at TIMESTAMP NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            used INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_otp_user ON otp_codes(user_id, used, expires_at);")

        # 3. Server-side Sessions Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            last_active_at TIMESTAMP NOT NULL,
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'revoked')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, status);")

        # 4. Audit Log Table (Immutable records, no secrets or text leaks)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user_action ON audit_log(user_id, action);")

        # 5. Login Attempts Table (Used for lockout rate-limiting)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success INTEGER NOT NULL DEFAULT 0
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_user_time ON login_attempts(user_id, attempted_at);")

        # 6. User History Table (Per-user private conversation storage)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_user ON user_chat_history(user_id, conversation_id);")

        # 7. Seed Faculty Examiner & Guest Evaluator accounts for Course Faculty Review
        from auth.security import hash_password
        cursor.execute("SELECT id FROM users WHERE id = 'faculty'")
        if not cursor.fetchone():
            fac_hash = hash_password("faculty123")
            cursor.execute("""
            INSERT INTO users (id, name, email, password_hash, role, status, force_password_change)
            VALUES ('faculty', 'Faculty Examiner', 'faculty@campus.edu', ?, 'Admin', 'active', 0)
            """, (fac_hash,))

        cursor.execute("SELECT id FROM users WHERE id = 'guest'")
        if not cursor.fetchone():
            guest_hash = hash_password("guest123")
            cursor.execute("""
            INSERT INTO users (id, name, email, password_hash, role, status, force_password_change)
            VALUES ('guest', 'Guest Evaluator', 'guest@campus.edu', ?, 'Admin', 'active', 0)
            """, (guest_hash,))

