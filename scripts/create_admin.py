#!/usr/bin/env python3
"""
Create or promote an admin user. Idempotent — safe to run multiple times.

Usage:
  python scripts/create_admin.py --email admin@example.com --password 'secret'
  ADMIN_EMAIL=... ADMIN_PASSWORD=... python scripts/create_admin.py
"""

import argparse
import os
import sys
from typing import Optional

# Project root on sys.path when run as: python scripts/create_admin.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select

from app.core.config import database_url_for_log, settings
from app.core.database import engine
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a new admin user or promote an existing user to admin."
    )
    parser.add_argument(
        "--email",
        default=os.environ.get("ADMIN_EMAIL"),
        help="Admin email (or set ADMIN_EMAIL)",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("ADMIN_PASSWORD"),
        help="Password for new user, or optional reset for existing (ADMIN_PASSWORD)",
    )
    parser.add_argument(
        "--name",
        default=os.environ.get("ADMIN_NAME", "Administrador"),
        help="Full name for new user (default: Administrador, or ADMIN_NAME)",
    )
    args = parser.parse_args()

    if not args.email:
        parser.error("Email is required. Pass --email or set ADMIN_EMAIL.")

    return args


def create_or_promote_admin(email: str, password: Optional[str], full_name: str) -> None:
    print(f"Database: {database_url_for_log(settings.DATABASE_URL)}")

    with Session(engine) as db:
        existing = db.exec(select(User).where(User.email == email)).first()

        if existing is None:
            if not password:
                print("ERROR: Password is required to create a new admin user.", file=sys.stderr)
                print("Set ADMIN_PASSWORD or pass --password.", file=sys.stderr)
                sys.exit(1)

            user_data = UserCreate(
                email=email,
                full_name=full_name,
                password=password,
                role="admin",
                is_admin=True,
            )
            user = AuthService.register_user(db, user_data)
            print(f"Created admin user id={user.id} email={user.email}")
            return

        if existing.role == "admin" and existing.is_admin:
            updated = False
            if password:
                UserService.update_user(
                    db,
                    existing.id,
                    UserUpdate(password=password, role="admin", is_admin=True),
                )
                print(f"Admin user id={existing.id} email={existing.email} — password updated.")
                updated = True
            if not updated:
                print(f"Admin user id={existing.id} email={existing.email} — already admin, no changes.")
            return

        update_data = UserUpdate(role="admin", is_admin=True)
        if password:
            update_data.password = password

        user = UserService.update_user(db, existing.id, update_data)
        if user is None:
            print(f"ERROR: Could not update user id={existing.id}.", file=sys.stderr)
            sys.exit(1)

        msg = f"Promoted user id={user.id} email={user.email} to admin."
        if password:
            msg += " Password updated."
        print(msg)


def main() -> None:
    args = parse_args()
    create_or_promote_admin(args.email, args.password, args.name)


if __name__ == "__main__":
    main()
