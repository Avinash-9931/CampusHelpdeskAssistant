#!/usr/bin/env python3
"""
CLI Provisioning Script: Create Administrator Account
Allows manual and scripted creation of Admin accounts in data/auth.db.
Usage:
    python scripts/create_admin.py
    python scripts/create_admin.py --id admin --name "System Admin" --email admin@campus.edu --password admin123
"""

import sys
import argparse
import getpass
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from auth.service import (
    create_user,
    get_user_by_id,
    reset_user_password,
    init_db
)
from auth.security import validate_password_policy


def main():
    parser = argparse.ArgumentParser(description="Provision an Administrator account for Campus Helpdesk Assistant.")
    parser.add_argument("--id", dest="user_id", help="Admin User ID (e.g. admin, ADM001)")
    parser.add_argument("--name", dest="name", help="Full Name")
    parser.add_argument("--email", dest="email", help="Administrator Email address")
    parser.add_argument("--password", dest="password", help="Account Password")
    parser.add_argument("--force", action="store_true", help="Reset password if user already exists")

    args = parser.parse_args()

    # Ensure DB is initialized
    init_db()

    user_id = args.user_id
    name = args.name
    email = args.email
    password = args.password

    # Interactive prompts if arguments not supplied
    if not user_id:
        print("=== Provision Administrator Account ===")
        user_id = input("Admin User ID (default: admin): ").strip() or "admin"

    existing = get_user_by_id(user_id)
    if existing:
        print(f"\nUser '{user_id}' already exists with role '{existing['role']}'.")
        if not args.force:
            confirm = input("Would you like to reset this user's password to an Admin account? [y/N]: ").strip().lower()
            if confirm not in ("y", "yes"):
                print("Aborted.")
                sys.exit(0)
        
        if not password:
            password = getpass.getpass("New Password: ")
            confirm_pass = getpass.getpass("Confirm New Password: ")
            if password != confirm_pass:
                print("Error: Passwords do not match.")
                sys.exit(1)

        ok, msg = validate_password_policy(password)
        if not ok:
            print(f"Password policy violation: {msg}")
            sys.exit(1)

        success, err = reset_user_password(user_id, password, reset_by="CLI_PROVISIONER")
        if success:
            print(f"Successfully reset password for Admin account '{user_id}'.")
            sys.exit(0)
        else:
            print(f"Error resetting password: {err}")
            sys.exit(1)

    if not name:
        name = input("Admin Full Name (default: System Administrator): ").strip() or "System Administrator"

    if not email:
        email = input("Admin Email: ").strip()
        if not email or "@" not in email:
            print("Error: A valid email address is required.")
            sys.exit(1)

    if not password:
        password = getpass.getpass("Password: ")
        confirm_pass = getpass.getpass("Confirm Password: ")
        if password != confirm_pass:
            print("Error: Passwords do not match.")
            sys.exit(1)

    ok, msg = validate_password_policy(password)
    if not ok:
        print(f"Password policy violation: {msg}")
        sys.exit(1)

    success, err = create_user(
        user_id=user_id,
        name=name,
        email=email,
        password=password,
        role="Admin",
        created_by="CLI_PROVISIONER"
    )

    if success:
        print(f"\nAdministrator account '{user_id}' ({email}) created successfully!")
        sys.exit(0)
    else:
        print(f"\nFailed to create user: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
