#!/usr/bin/env python3
"""
Import a pre-defined group-stage fixture from a JSON file.

Local:
  python scripts/import_group_fixture.py --tournament-id 1 --file fixtures/mi_torneo.json

Railway (Shell inside web service):
  python scripts/import_group_fixture.py --tournament-id 1 --file fixtures/mi_torneo.json

Use --replace to overwrite an existing group fixture.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from app.services.fixture_service import FixtureService
from sqlmodel import Session


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import group fixture from JSON.")
    parser.add_argument("--tournament-id", type=int, required=True, help="Tournament ID")
    parser.add_argument("--file", required=True, help="Path to JSON fixture file")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing group fixture (deletes group matches and jornadas)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with Session(engine) as db:
        stats = FixtureService.import_group_fixture_from_file(
            db,
            args.tournament_id,
            args.file,
            replace=args.replace,
        )
    print("Fixture importado correctamente:")
    print(f"  Grupos:           {stats['groups']}")
    print(f"  Jornadas:         {stats['jornadas']}")
    print(f"  Partidos:         {stats['matches']}")
    print(f"  Jugadores asign.: {stats['players_assigned']}")


if __name__ == "__main__":
    main()
