#!/usr/bin/env python3
"""
Reset a user's password without email. Does not change role or admin flags.

Local:
  python scripts/reset_user_password.py --email jugador@example.com --password 'nueva-clave'

Railway (recommended — Shell inside the deployed Lercup service):
  python scripts/reset_user_password.py --email jugador@example.com --password 'nueva-clave'

From your Mac (use Postgres public URL, not postgres.railway.internal):
  DATABASE_URL="<DATABASE_PUBLIC_URL>" \\
    python scripts/reset_user_password.py --email jugador@example.com --password 'nueva-clave'
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func
from sqlalchemy.exc import OperationalError
from sqlmodel import Session, select

from app.core.config import database_url_for_log, settings
from app.core.database import engine
from app.models.user import User
from app.schemas.user import UserUpdate
from app.services.user_service import UserService

RAILWAY_INTERNAL_HINT = """
Cannot connect: DATABASE_URL uses postgres.railway.internal, which only
resolves inside Railway containers — not from your local machine.

Fix (pick one):
  1. Railway Dashboard -> Lercup service -> Shell, then run:
       python scripts/reset_user_password.py --email ... --password ...

  2. From your Mac, copy DATABASE_PUBLIC_URL from the Postgres service and run:
       DATABASE_URL="<public-url>" python scripts/reset_user_password.py ...
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset a user's password (one-off, no email required)."
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email of the user to reset",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="New password (min. 6 characters)",
    )
    return parser.parse_args()


def reset_password(email: str, password: str) -> None:
    if len(password) < 6:
        print("ERROR: Password must be at least 6 characters.", file=sys.stderr)
        sys.exit(1)

    normalized = email.strip().lower()
    print(f"Database: {database_url_for_log(settings.DATABASE_URL)}")

    try:
        with Session(engine) as db:
            user = db.exec(
                select(User).where(func.lower(User.email) == normalized)
            ).first()
            if not user:
                print(f"ERROR: No user found with email {email!r}.", file=sys.stderr)
                sys.exit(1)

            UserService.update_user(db, user.id, UserUpdate(password=password))
            print(f"Password updated for user id={user.id} email={user.email}")
    except OperationalError as exc:
        if "railway.internal" in settings.DATABASE_URL or "could not translate host name" in str(exc):
            print(RAILWAY_INTERNAL_HINT, file=sys.stderr)
        raise SystemExit(1) from exc


def main() -> None:
    args = parse_args()
    reset_password(args.email, args.password)


if __name__ == "__main__":
    main()
