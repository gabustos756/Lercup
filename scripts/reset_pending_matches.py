#!/usr/bin/env python3
"""
Reset imported / unplayed matches to pending state.

Use when matches were incorrectly marked as played without results.

Examples:
  # Dry-run: show what would change
  python scripts/reset_pending_matches.py --tournament-id 1 --dry-run

  # Reset all group matches in a tournament that have no winner
  python scripts/reset_pending_matches.py --tournament-id 1

  # Reset only matches wrongly marked played (no winner)
  python scripts/reset_pending_matches.py --tournament-id 1 --only-wrong-played

Railway Shell:
  python scripts/reset_pending_matches.py --tournament-id 1 --only-wrong-played
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select

from app.core.database import engine
from app.models.match import Match


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reset matches to pending state.")
    parser.add_argument("--tournament-id", type=int, required=True)
    parser.add_argument(
        "--stage",
        default="groups",
        help="Match stage to reset (default: groups)",
    )
    parser.add_argument(
        "--only-wrong-played",
        action="store_true",
        help="Only reset match_status='played' rows with winner_id IS NULL",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print matches that would be updated without saving",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with Session(engine) as db:
        query = select(Match).where(
            Match.tournament_id == args.tournament_id,
            Match.stage == args.stage,
        )
        if args.only_wrong_played:
            query = query.where(
                Match.match_status == "played",
                Match.winner_id.is_(None),
            )
        else:
            query = query.where(Match.winner_id.is_(None))

        matches = db.exec(query).all()
        if not matches:
            print("No hay partidos para resetear con los filtros indicados.")
            return

        print(f"Partidos a resetear: {len(matches)}")
        for m in matches:
            print(
                f"  id={m.id} p1={m.player1_id} p2={m.player2_id} "
                f"status={m.match_status!r} winner={m.winner_id} score={m.score!r}"
            )
            if not args.dry_run:
                m.match_status = "pending"
                m.winner_id = None
                m.score = None
                m.proposed_datetime = None
                m.proposed_by_id = None
                m.location_label = None
                m.location_url = None
                db.add(m)

        if args.dry_run:
            print("Dry-run: no se guardaron cambios.")
        else:
            db.commit()
            print("Partidos reseteados a pending correctamente.")


if __name__ == "__main__":
    main()
