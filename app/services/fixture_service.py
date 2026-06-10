import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from sqlmodel import Session, select

from app.models.group_round import GroupRound
from app.models.match import Match
from app.models.registration import TournamentRegistration
from app.models.tournament import Tournament
from app.models.user import User


class FixtureService:
    @staticmethod
    def resolve_player(db: Session, identifier: str) -> User:
        """Resolve a player by email or full_name (case-insensitive)."""
        identifier = identifier.strip()
        user = db.exec(select(User).where(User.email == identifier)).first()
        if user:
            return user
        users = db.exec(select(User)).all()
        lowered = identifier.lower()
        for u in users:
            if u.full_name.lower() == lowered:
                return u
        raise ValueError(f"Jugador no encontrado: {identifier!r}")

    @staticmethod
    def clear_group_fixture(db: Session, tournament_id: int) -> None:
        """Remove group-stage matches and jornada metadata for a tournament."""
        group_matches = db.exec(
            select(Match).where(
                Match.tournament_id == tournament_id,
                Match.stage == "groups",
            )
        ).all()
        for m in group_matches:
            db.delete(m)

        rounds = db.exec(
            select(GroupRound).where(GroupRound.tournament_id == tournament_id)
        ).all()
        for r in rounds:
            db.delete(r)

        db.commit()

    @staticmethod
    def import_group_fixture(
        db: Session,
        tournament_id: int,
        fixture_data: Dict[str, Any],
        *,
        replace: bool = False,
    ) -> Dict[str, Any]:
        """
        Import a pre-defined group fixture from a dict.

        Expected shape:
        {
          "groups": {
            "A": {
              "players": ["email@...", ...],
              "jornadas": [
                {
                  "number": 1,
                  "bye": "email@...",
                  "matches": [
                    {"player1": "...", "player2": "..."},
                    ...
                  ]
                }
              ]
            }
          }
        }
        """
        tournament = db.get(Tournament, tournament_id)
        if not tournament:
            raise ValueError(f"Torneo {tournament_id} no encontrado.")

        groups = fixture_data.get("groups")
        if not groups:
            raise ValueError("El fixture debe incluir la clave 'groups'.")

        existing_rounds = db.exec(
            select(GroupRound).where(GroupRound.tournament_id == tournament_id)
        ).first()
        if existing_rounds and not replace:
            raise ValueError(
                "El torneo ya tiene fixture de grupos cargado. "
                "Usa replace=True o --replace para sobrescribir."
            )

        if replace:
            FixtureService.clear_group_fixture(db, tournament_id)

        stats = {"groups": 0, "jornadas": 0, "matches": 0, "players_assigned": 0}

        for group_label, group_data in groups.items():
            stats["groups"] += 1
            player_ids: Dict[str, int] = {}

            for player_ref in group_data.get("players", []):
                user = FixtureService.resolve_player(db, player_ref)
                player_ids[player_ref] = user.id
                reg = db.exec(
                    select(TournamentRegistration).where(
                        TournamentRegistration.tournament_id == tournament_id,
                        TournamentRegistration.user_id == user.id,
                    )
                ).first()
                if not reg:
                    reg = TournamentRegistration(
                        tournament_id=tournament_id,
                        user_id=user.id,
                        status="approved",
                    )
                    db.add(reg)
                    db.commit()
                    db.refresh(reg)
                reg.group_label = group_label
                reg.status = "approved"
                db.add(reg)
                stats["players_assigned"] += 1

            for jornada in group_data.get("jornadas", []):
                jornada_number = jornada["number"]
                stats["jornadas"] += 1

                bye_id = None
                bye_ref = jornada.get("bye")
                if bye_ref:
                    bye_user = FixtureService.resolve_player(db, bye_ref)
                    bye_id = bye_user.id

                db.add(GroupRound(
                    tournament_id=tournament_id,
                    group_label=group_label,
                    jornada_number=jornada_number,
                    bye_player_id=bye_id,
                ))

                for match_data in jornada.get("matches", []):
                    p1 = FixtureService.resolve_player(db, match_data["player1"])
                    p2 = FixtureService.resolve_player(db, match_data["player2"])
                    if p1.id == p2.id:
                        raise ValueError(
                            f"Jornada {jornada_number} grupo {group_label}: "
                            "un jugador no puede jugar contra sí mismo."
                        )
                    db.add(Match(
                        tournament_id=tournament_id,
                        player1_id=p1.id,
                        player2_id=p2.id,
                        stage="groups",
                        group_label=group_label,
                        jornada_number=jornada_number,
                    ))
                    stats["matches"] += 1

        if tournament.status == "draft":
            tournament.status = "ongoing"
            db.add(tournament)

        db.commit()
        return stats

    @staticmethod
    def import_group_fixture_from_file(
        db: Session,
        tournament_id: int,
        file_path: Union[str, Path],
        *,
        replace: bool = False,
    ) -> Dict[str, Any]:
        path = Path(file_path)
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        tid = data.get("tournament_id", tournament_id)
        if tid != tournament_id:
            raise ValueError(
                f"tournament_id en JSON ({tid}) no coincide con el argumento ({tournament_id})."
            )
        return FixtureService.import_group_fixture(db, tournament_id, data, replace=replace)

    @staticmethod
    def get_group_fixture_view(
        db: Session,
        tournament_id: int,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Return fixture grouped by group_label -> jornadas, each with matches and bye.
        """
        rounds = db.exec(
            select(GroupRound)
            .where(GroupRound.tournament_id == tournament_id)
            .order_by(GroupRound.group_label, GroupRound.jornada_number)
        ).all()

        if not rounds:
            return {}

        matches = db.exec(
            select(Match).where(
                Match.tournament_id == tournament_id,
                Match.stage == "groups",
            )
        ).all()

        matches_by_key: Dict[tuple, List[Match]] = {}
        for m in matches:
            key = (m.group_label, m.jornada_number)
            matches_by_key.setdefault(key, []).append(m)

        result: Dict[str, List[Dict[str, Any]]] = {}
        for rnd in rounds:
            bye_user = db.get(User, rnd.bye_player_id) if rnd.bye_player_id else None
            key = (rnd.group_label, rnd.jornada_number)
            jornada_matches = []
            for m in matches_by_key.get(key, []):
                p1 = db.get(User, m.player1_id)
                p2 = db.get(User, m.player2_id)
                winner = db.get(User, m.winner_id) if m.winner_id else None
                jornada_matches.append({
                    "id": m.id,
                    "player1": p1,
                    "player2": p2,
                    "winner": winner,
                    "score": m.score,
                })

            result.setdefault(rnd.group_label, []).append({
                "number": rnd.jornada_number,
                "bye_player": bye_user,
                "matches": jornada_matches,
            })

        return result
