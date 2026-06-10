from typing import List, Optional, Dict, Any
import random
from itertools import combinations
from sqlmodel import Session, select
from app.models.tournament import Tournament
from app.models.match import Match
from app.models.user import User
from app.models.registration import TournamentRegistration
from app.models.tournament_format import TournamentFormat
from app.schemas.tournament import TournamentCreate, TournamentUpdate
from app.services.match_service import MatchService

class TournamentService:
    @staticmethod
    def get_all_tournaments(db: Session) -> List[Tournament]:
        """Fetch all tournaments from the database."""
        return db.exec(select(Tournament).order_by(Tournament.start_date.desc())).all()

    @staticmethod
    def get_tournament_by_id(db: Session, tournament_id: int) -> Optional[Tournament]:
        """Fetch a specific tournament by ID."""
        return db.get(Tournament, tournament_id)

    @staticmethod
    def create_tournament(db: Session, tournament_data: TournamentCreate, creator_id: int) -> Tournament:
        """Create a new tournament."""
        db_tournament = Tournament(
            name=tournament_data.name,
            description=tournament_data.description,
            start_date=tournament_data.start_date,
            end_date=tournament_data.end_date,
            surface=tournament_data.surface,
            status=tournament_data.status,
            creator_id=creator_id,
            format_id=tournament_data.format_id,
            category=tournament_data.category
        )
        db.add(db_tournament)
        db.commit()
        db.refresh(db_tournament)
        return db_tournament

    @staticmethod
    def update_tournament(db: Session, tournament_id: int, tournament_data: TournamentUpdate) -> Optional[Tournament]:
        """Update tournament properties."""
        db_tournament = db.get(Tournament, tournament_id)
        if not db_tournament:
            return None
        
        if tournament_data.name is not None:
            db_tournament.name = tournament_data.name
        if tournament_data.description is not None:
            db_tournament.description = tournament_data.description
        if tournament_data.start_date is not None:
            db_tournament.start_date = tournament_data.start_date
        if tournament_data.end_date is not None:
            db_tournament.end_date = tournament_data.end_date
        if tournament_data.surface is not None:
            db_tournament.surface = tournament_data.surface
        if tournament_data.status is not None:
            db_tournament.status = tournament_data.status
        if tournament_data.format_id is not None:
            db_tournament.format_id = tournament_data.format_id
        if tournament_data.category is not None:
            db_tournament.category = tournament_data.category
            
        db.add(db_tournament)
        db.commit()
        db.refresh(db_tournament)
        return db_tournament

    @staticmethod
    def delete_tournament(db: Session, tournament_id: int) -> bool:
        """Delete a tournament and its matches."""
        db_tournament = db.get(Tournament, tournament_id)
        if not db_tournament:
            return False
        
        # Delete related matches
        matches = db.exec(select(Match).where(Match.tournament_id == tournament_id)).all()
        for match in matches:
            db.delete(match)
            
        db.delete(db_tournament)
        db.commit()
        return True

    @staticmethod
    def get_tournament_matches(db: Session, tournament_id: int) -> List[Dict[str, Any]]:
        """Fetch all matches in a tournament with detailed user info."""
        matches = db.exec(
            select(Match).where(Match.tournament_id == tournament_id).order_by(Match.match_date.desc())
        ).all()
        
        results = []
        for m in matches:
            p1 = db.get(User, m.player1_id)
            p2 = db.get(User, m.player2_id)
            winner = db.get(User, m.winner_id) if m.winner_id else None
            
            results.append({
                "id": m.id,
                "player1": p1,
                "player2": p2,
                "winner": winner,
                "score": m.score,
                "match_date": m.match_date
            })
        return results

    @staticmethod
    def add_match(
        db: Session, 
        tournament_id: int, 
        player1_id: int, 
        player2_id: int, 
        winner_id: Optional[int] = None, 
        score: Optional[str] = None,
        stage: str = "groups",
        group_label: Optional[str] = None,
        cup_name: Optional[str] = None,
        round_name: Optional[str] = None
    ) -> Match:
        """Add a match to a tournament."""
        if player1_id == player2_id:
            raise ValueError("Un jugador no puede jugar contra sí mismo.")
            
        db_match = Match(
            tournament_id=tournament_id,
            player1_id=player1_id,
            player2_id=player2_id,
            winner_id=winner_id,
            score=score,
            stage=stage,
            group_label=group_label,
            cup_name=cup_name,
            round_name=round_name,
            match_status="pending",
        )
        MatchService.apply_result_status(db_match, winner_id, score)
        db.add(db_match)
        db.commit()
        db.refresh(db_match)
        return db_match

    @staticmethod
    def delete_match(db: Session, match_id: int) -> bool:
        """Delete a match by its ID."""
        match = db.get(Match, match_id)
        if not match:
            return False
        db.delete(match)
        db.commit()
        return True

    @staticmethod
    def assign_player_to_group(db: Session, registration_id: int, group_label: Optional[str]) -> bool:
        reg = db.get(TournamentRegistration, registration_id)
        if not reg:
            return False
        reg.group_label = group_label
        db.add(reg)
        db.commit()
        return True

    @staticmethod
    def get_group_standings(db: Session, tournament_id: int, group_label: str) -> List[Dict[str, Any]]:
        # Get all approved registrations in this group
        regs = db.exec(
            select(TournamentRegistration).where(
                TournamentRegistration.tournament_id == tournament_id,
                TournamentRegistration.group_label == group_label,
                TournamentRegistration.status == "approved"
            )
        ).all()
        
        # Get all completed matches in group stage for this group
        matches = db.exec(
            select(Match).where(
                Match.tournament_id == tournament_id,
                Match.stage == "groups",
                Match.group_label == group_label,
                Match.winner_id != None
            )
        ).all()
        
        standings = {}
        for reg in regs:
            u = db.get(User, reg.user_id)
            if u:
                standings[u.id] = {
                    "user": u,
                    "played": 0,
                    "won": 0,
                    "lost": 0,
                    "points": 0
                }
                
        for m in matches:
            if m.player1_id in standings and m.player2_id in standings:
                standings[m.player1_id]["played"] += 1
                standings[m.player2_id]["played"] += 1
                if m.winner_id == m.player1_id:
                    standings[m.player1_id]["won"] += 1
                    standings[m.player1_id]["points"] += 1
                    standings[m.player2_id]["lost"] += 1
                elif m.winner_id == m.player2_id:
                    standings[m.player2_id]["won"] += 1
                    standings[m.player2_id]["points"] += 1
                    standings[m.player1_id]["lost"] += 1
                    
        # Sort by points (descending), then won matches (descending), then played matches (ascending)
        sorted_standings = sorted(
            standings.values(),
            key=lambda x: (x["points"], x["won"], -x["played"]),
            reverse=True
        )
        return sorted_standings

    @staticmethod
    def _get_approved_registrations(db: Session, tournament_id: int) -> List[TournamentRegistration]:
        return db.exec(
            select(TournamentRegistration).where(
                TournamentRegistration.tournament_id == tournament_id,
                TournamentRegistration.status == "approved"
            )
        ).all()

    @staticmethod
    def get_tournament_progress(db: Session, tournament_id: int) -> Dict[str, Any]:
        """Return workflow flags for the tournament detail UI."""
        t = db.get(Tournament, tournament_id)
        if not t:
            return {}

        regs = TournamentService._get_approved_registrations(db, tournament_id)
        draw_done = bool(regs) and all(r.group_label for r in regs)
        group_matches = db.exec(
            select(Match).where(
                Match.tournament_id == tournament_id,
                Match.stage == "groups"
            )
        ).all()
        playoff_matches = db.exec(
            select(Match).where(
                Match.tournament_id == tournament_id,
                Match.stage == "playoffs"
            )
        ).all()
        group_complete = TournamentService.is_group_stage_complete(db, tournament_id)
        is_groups_format = bool(t.format and t.format.format_type == "groups_to_playoffs")

        return {
            "registrations_open": t.status == "draft",
            "registered_count": len(regs),
            "draw_done": draw_done,
            "has_group_matches": len(group_matches) > 0,
            "group_stage_complete": group_complete,
            "has_playoffs": len(playoff_matches) > 0,
            "is_groups_format": is_groups_format,
            "can_close_registrations": t.status == "draft" and len(regs) >= 2,
            "can_perform_draw": (
                is_groups_format
                and t.status != "draft"
                and not draw_done
                and len(regs) >= 2
            ),
            "can_generate_playoffs": (
                is_groups_format
                and draw_done
                and group_complete
            ),
        }

    @staticmethod
    def close_registrations(db: Session, tournament_id: int) -> bool:
        t = db.get(Tournament, tournament_id)
        if not t or t.status != "draft":
            return False

        regs = TournamentService._get_approved_registrations(db, tournament_id)
        if len(regs) < 2:
            return False

        t.status = "ongoing"
        db.add(t)
        db.commit()
        return True

    @staticmethod
    def perform_group_draw(db: Session, tournament_id: int) -> bool:
        """Random sorteo: assign players to groups A/B and generate round-robin fixtures."""
        t = db.get(Tournament, tournament_id)
        if not t or not t.format or t.format.format_type != "groups_to_playoffs":
            return False
        if t.status == "draft":
            return False

        regs = TournamentService._get_approved_registrations(db, tournament_id)
        if len(regs) < 2:
            return False
        if any(r.group_label for r in regs):
            return False

        existing_group_matches = db.exec(
            select(Match).where(
                Match.tournament_id == tournament_id,
                Match.stage == "groups"
            )
        ).first()
        if existing_group_matches:
            return False

        shuffled = list(regs)
        random.shuffle(shuffled)
        mid = (len(shuffled) + 1) // 2

        for r in shuffled[:mid]:
            r.group_label = "A"
            db.add(r)
        for r in shuffled[mid:]:
            r.group_label = "B"
            db.add(r)

        for group_label in ("A", "B"):
            player_ids = [r.user_id for r in shuffled if r.group_label == group_label]
            for p1_id, p2_id in combinations(player_ids, 2):
                db.add(Match(
                    tournament_id=tournament_id,
                    player1_id=p1_id,
                    player2_id=p2_id,
                    winner_id=None,
                    score=None,
                    stage="groups",
                    group_label=group_label,
                    match_status="pending",
                    proposed_datetime=None,
                    proposed_by_id=None,
                ))

        db.commit()
        return True

    @staticmethod
    def is_group_stage_complete(db: Session, tournament_id: int) -> bool:
        t = db.get(Tournament, tournament_id)
        if not t or not t.format or t.format.format_type != "groups_to_playoffs":
            return False

        for group_label in ("A", "B"):
            regs = db.exec(
                select(TournamentRegistration).where(
                    TournamentRegistration.tournament_id == tournament_id,
                    TournamentRegistration.group_label == group_label,
                    TournamentRegistration.status == "approved"
                )
            ).all()
            n = len(regs)
            if n < 2:
                continue

            expected = n * (n - 1) // 2
            matches = db.exec(
                select(Match).where(
                    Match.tournament_id == tournament_id,
                    Match.stage == "groups",
                    Match.group_label == group_label
                )
            ).all()
            if len(matches) < expected:
                return False
            if any(m.winner_id is None for m in matches):
                return False

        regs_with_group = db.exec(
            select(TournamentRegistration).where(
                TournamentRegistration.tournament_id == tournament_id,
                TournamentRegistration.group_label != None,
                TournamentRegistration.status == "approved"
            )
        ).all()
        return len(regs_with_group) >= 2

    @staticmethod
    def get_playoff_bracket(db: Session, tournament_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Organize playoff matches into rounds for bracket display."""
        playoff_matches = db.exec(
            select(Match).where(
                Match.tournament_id == tournament_id,
                Match.stage == "playoffs"
            ).order_by(Match.id)
        ).all()

        bracket: Dict[str, Dict[str, List]] = {"Oro": {}, "Plata": {}, "Bronce": {}}
        round_order = ["Semifinal", "Final", "3° puesto"]

        for m in playoff_matches:
            cup = m.cup_name or "Oro"
            rnd = m.round_name or "Playoff"
            if cup not in bracket:
                bracket[cup] = {}
            if rnd not in bracket[cup]:
                bracket[cup][rnd] = []

            p1 = db.get(User, m.player1_id)
            p2 = db.get(User, m.player2_id)
            w = db.get(User, m.winner_id) if m.winner_id else None
            bracket[cup][rnd].append({
                "match": m,
                "player1": p1,
                "player2": p2,
                "winner": w,
                "score": m.score
            })

        result = {}
        for cup, rounds in bracket.items():
            if not rounds:
                continue
            result[cup] = [
                {"round_name": rnd, "matches": rounds[rnd]}
                for rnd in round_order
                if rnd in rounds
            ]
        return result

    @staticmethod
    def generate_initial_elimination_round(db: Session, tournament_id: int) -> bool:
        # Check if matches already exist
        existing = db.exec(select(Match).where(Match.tournament_id == tournament_id)).first()
        if existing:
            return False
            
        regs = db.exec(
            select(TournamentRegistration).where(
                TournamentRegistration.tournament_id == tournament_id,
                TournamentRegistration.status == "approved"
            )
        ).all()
        
        players = [db.get(User, r.user_id) for r in regs if db.get(User, r.user_id)]
        if len(players) < 2:
            return False
            
        num_pairs = len(players) // 2
        for i in range(num_pairs):
            p1 = players[2 * i]
            p2 = players[2 * i + 1]
            db_match = Match(
                tournament_id=tournament_id,
                player1_id=p1.id,
                player2_id=p2.id,
                stage="first_round",
                round_name="Primera Ronda"
            )
            db.add(db_match)
        db.commit()
        return True

    @staticmethod
    def generate_playoff_bracket(db: Session, tournament_id: int) -> bool:
        t = db.get(Tournament, tournament_id)
        if not t or not t.format_id:
            return False
            
        fmt = db.get(TournamentFormat, t.format_id)
        if not fmt:
            return False
            
        # Check if playoffs are already generated
        playoff_matches = db.exec(
            select(Match).where(
                Match.tournament_id == tournament_id,
                Match.stage == "playoffs"
            )
        ).all()
        
        if not playoff_matches:
            # Generate initial playoffs
            if fmt.format_type == "groups_to_playoffs":
                if not TournamentService.is_group_stage_complete(db, tournament_id):
                    return False
                if fmt.groups_count == 2:
                    standings_A = TournamentService.get_group_standings(db, tournament_id, "A")
                    standings_B = TournamentService.get_group_standings(db, tournament_id, "B")
                    
                    gold_limit = fmt.gold_qualifiers
                    silver_limit = fmt.silver_qualifiers
                    bronze_limit = fmt.bronze_qualifiers
                    
                    # Gold SF:
                    if len(standings_A) >= gold_limit and len(standings_B) >= gold_limit:
                        if gold_limit >= 2:
                            p1_a = standings_A[0]["user"]
                            p2_b = standings_B[1]["user"]
                            p1_b = standings_B[0]["user"]
                            p2_a = standings_A[1]["user"]
                            
                            db.add(Match(tournament_id=tournament_id, player1_id=p1_a.id, player2_id=p2_b.id, stage="playoffs", cup_name="Oro", round_name="Semifinal"))
                            db.add(Match(tournament_id=tournament_id, player1_id=p1_b.id, player2_id=p2_a.id, stage="playoffs", cup_name="Oro", round_name="Semifinal"))
                        elif gold_limit == 1:
                            p1_a = standings_A[0]["user"]
                            p1_b = standings_B[0]["user"]
                            db.add(Match(tournament_id=tournament_id, player1_id=p1_a.id, player2_id=p1_b.id, stage="playoffs", cup_name="Oro", round_name="Final"))
                            
                    # Silver SF:
                    if len(standings_A) >= (gold_limit + silver_limit) and len(standings_B) >= (gold_limit + silver_limit):
                        if silver_limit >= 2:
                            p3_a = standings_A[gold_limit]["user"]
                            p4_b = standings_B[gold_limit + 1]["user"]
                            p3_b = standings_B[gold_limit]["user"]
                            p4_a = standings_A[gold_limit + 1]["user"]
                            
                            db.add(Match(tournament_id=tournament_id, player1_id=p3_a.id, player2_id=p4_b.id, stage="playoffs", cup_name="Plata", round_name="Semifinal"))
                            db.add(Match(tournament_id=tournament_id, player1_id=p3_b.id, player2_id=p4_a.id, stage="playoffs", cup_name="Plata", round_name="Semifinal"))
                        elif silver_limit == 1:
                            p3_a = standings_A[gold_limit]["user"]
                            p3_b = standings_B[gold_limit]["user"]
                            db.add(Match(tournament_id=tournament_id, player1_id=p3_a.id, player2_id=p3_b.id, stage="playoffs", cup_name="Plata", round_name="Final"))
                            
                    # Bronze:
                    if len(standings_A) >= (gold_limit + silver_limit + bronze_limit) and len(standings_B) >= (gold_limit + silver_limit + bronze_limit):
                        p5_a = standings_A[gold_limit + silver_limit]["user"]
                        p5_b = standings_B[gold_limit + silver_limit]["user"]
                        db.add(Match(tournament_id=tournament_id, player1_id=p5_a.id, player2_id=p5_b.id, stage="playoffs", cup_name="Bronce", round_name="Final"))
                
                db.commit()
                return True
                
            elif fmt.format_type == "elimination_with_consolation":
                first_round_matches = db.exec(
                    select(Match).where(
                        Match.tournament_id == tournament_id,
                        Match.stage == "first_round"
                    )
                ).all()
                
                if not first_round_matches or any(m.winner_id is None for m in first_round_matches):
                    return False
                    
                winners = []
                losers = []
                for m in first_round_matches:
                    if m.winner_id == m.player1_id:
                        winners.append(m.player1_id)
                        losers.append(m.player2_id)
                    else:
                        winners.append(m.player2_id)
                        losers.append(m.player1_id)
                
                # Gold SF:
                if len(winners) >= 4:
                    db.add(Match(tournament_id=tournament_id, player1_id=winners[0], player2_id=winners[1], stage="playoffs", cup_name="Oro", round_name="Semifinal"))
                    db.add(Match(tournament_id=tournament_id, player1_id=winners[2], player2_id=winners[3], stage="playoffs", cup_name="Oro", round_name="Semifinal"))
                elif len(winners) == 2:
                    db.add(Match(tournament_id=tournament_id, player1_id=winners[0], player2_id=winners[1], stage="playoffs", cup_name="Oro", round_name="Final"))
                    
                # Silver SF (Consolation):
                if len(losers) >= 4:
                    db.add(Match(tournament_id=tournament_id, player1_id=losers[0], player2_id=losers[1], stage="playoffs", cup_name="Plata", round_name="Semifinal"))
                    db.add(Match(tournament_id=tournament_id, player1_id=losers[2], player2_id=losers[3], stage="playoffs", cup_name="Plata", round_name="Semifinal"))
                elif len(losers) == 2:
                    db.add(Match(tournament_id=tournament_id, player1_id=losers[0], player2_id=losers[1], stage="playoffs", cup_name="Plata", round_name="Final"))
                    
                db.commit()
                return True
                
            return False
            
        else:
            # Playoffs exist. Check if we need to generate Finals / 3rd place
            cups = ["Oro", "Plata"]
            generated_any = False
            
            for cup in cups:
                semis = [m for m in playoff_matches if m.cup_name == cup and m.round_name == "Semifinal"]
                if not semis or len(semis) < 2:
                    continue
                    
                # Check if all semis have winners
                if any(s.winner_id is None for s in semis):
                    continue
                    
                # Check if final already exists
                final_exists = any(m for m in playoff_matches if m.cup_name == cup and m.round_name in ["Final", "3° puesto"])
                if final_exists:
                    continue
                    
                # Generate Final and 3rd place
                s1, s2 = semis[0], semis[1]
                w1 = s1.winner_id
                l1 = s1.player2_id if s1.winner_id == s1.player1_id else s1.player1_id
                w2 = s2.winner_id
                l2 = s2.player2_id if s2.winner_id == s2.player1_id else s2.player1_id
                
                db.add(Match(tournament_id=tournament_id, player1_id=w1, player2_id=w2, stage="playoffs", cup_name=cup, round_name="Final"))
                if fmt.has_third_place:
                    db.add(Match(tournament_id=tournament_id, player1_id=l1, player2_id=l2, stage="playoffs", cup_name=cup, round_name="3° puesto"))
                
                generated_any = True
                
            if generated_any:
                db.commit()
                return True
                
            return False
            
        return False
