#!/usr/bin/env python3
"""
Backfill match_status from winner_id for all existing matches.

Idempotent and safe to run multiple times in production:
  - winner_id IS NOT NULL  -> match_status = "played"
  - winner_id IS NULL      -> match_status = "pending"

Examples:
  python scripts/fix_match_status.py --dry-run
  python scripts/fix_match_status.py

Railway Shell:
  python scripts/fix_match_status.py
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select

from app.core.database import engine
from app.models.match import Match


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill match_status from winner_id for all matches."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without committing",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with Session(engine) as db:
        matches = db.exec(select(Match).order_by(Match.id)).all()
        if not matches:
            print("No hay partidos en la base de datos.")
            return

        to_played = 0
        to_pending = 0
        unchanged = 0

        for match in matches:
            expected = "played" if match.winner_id is not None else "pending"
            if match.match_status == expected:
                unchanged += 1
                continue

            print(
                f"  id={match.id}: {match.match_status!r} -> {expected!r} "
                f"(winner_id={match.winner_id})"
            )
            if expected == "played":
                to_played += 1
            else:
                to_pending += 1

            if not args.dry_run:
                match.match_status = expected
                db.add(match)

        print(f"Total: {len(matches)} | played: {to_played} | pending: {to_pending} | sin cambios: {unchanged}")

        if args.dry_run:
            print("Dry-run: no se guardaron cambios.")
        elif to_played or to_pending:
            db.commit()
            print("match_status actualizado correctamente.")
        else:
            print("Todos los partidos ya tenían el estado correcto.")


if __name__ == "__main__":
    main()
