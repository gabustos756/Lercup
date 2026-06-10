from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, or_
from app.models.user import User
from app.models.player_profile import PlayerProfile
from app.models.match import Match
from app.models.tournament import Tournament
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password

class UserService:
    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        """Fetch all users from the database."""
        return db.exec(select(User).order_by(User.id)).all()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Fetch a specific user by ID."""
        return db.get(User, user_id)

    @staticmethod
    def create_user(
        db: Session, 
        user_data: UserCreate, 
        category: str = "B2", 
        nickname: Optional[str] = None,
        hand_preference: str = "right"
    ) -> User:
        """Create a new user with hashed password and associated tennis PlayerProfile."""
        existing = db.exec(select(User).where(User.email == user_data.email)).first()
        if existing:
            raise ValueError("El correo electrónico ya está registrado.")
        
        hashed = hash_password(user_data.password)
        role_val = user_data.role
        is_admin_val = user_data.is_admin
        if role_val == "admin":
            is_admin_val = True
        elif is_admin_val:
            role_val = "admin"

        db_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            city=user_data.city,
            phone_number=user_data.phone_number,
            avatar_url=user_data.avatar_url,
            hashed_password=hashed,
            is_admin=is_admin_val,
            role=role_val
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create associated tennis profile
        profile = PlayerProfile(
            user_id=db_user.id,
            sport="tennis",
            category=category,
            nickname=nickname,
            hand_preference=hand_preference
        )
        db.add(profile)
        db.commit()
        db.refresh(db_user) # Load profiles relationship
        
        return db_user

    @staticmethod
    def update_user(
        db: Session, 
        user_id: int, 
        user_data: UserUpdate, 
        category: Optional[str] = None, 
        nickname: Optional[str] = None,
        hand_preference: Optional[str] = None
    ) -> Optional[User]:
        """Update user properties and their associated tennis PlayerProfile."""
        db_user = db.get(User, user_id)
        if not db_user:
            return None
        
        if user_data.email is not None and user_data.email != db_user.email:
            existing = db.exec(select(User).where(User.email == user_data.email)).first()
            if existing:
                raise ValueError("El correo electrónico ya está registrado por otro usuario.")
            db_user.email = user_data.email
            
        if user_data.full_name is not None:
            db_user.full_name = user_data.full_name
            
        if user_data.city is not None:
            db_user.city = user_data.city

        if user_data.phone_number is not None:
            db_user.phone_number = user_data.phone_number
            
        if user_data.avatar_url is not None:
            db_user.avatar_url = user_data.avatar_url
            
        if user_data.password is not None and user_data.password.strip() != "":
            db_user.hashed_password = hash_password(user_data.password)
            
        if user_data.role is not None:
            db_user.role = user_data.role
            if db_user.role == "admin":
                db_user.is_admin = True
            else:
                db_user.is_admin = False

        if user_data.is_admin is not None:
            db_user.is_admin = user_data.is_admin
            if db_user.is_admin:
                db_user.role = "admin"
            elif db_user.role == "admin":
                db_user.role = "player"
            
        db.add(db_user)
        
        # Update or create associated tennis profile
        tennis_profile = None
        for prof in db_user.profiles:
            if prof.sport == "tennis":
                tennis_profile = prof
                break
                
        if not tennis_profile:
            # If they didn't have a tennis profile, create it now
            tennis_profile = PlayerProfile(
                user_id=db_user.id,
                sport="tennis",
                category=category or "B2",
                nickname=nickname,
                hand_preference=hand_preference or "right"
            )
            db.add(tennis_profile)
        else:
            if category is not None:
                tennis_profile.category = category
            if nickname is not None:
                tennis_profile.nickname = nickname
            if hand_preference is not None:
                tennis_profile.hand_preference = hand_preference
            db.add(tennis_profile)
            
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete a user from the database."""
        db_user = db.get(User, user_id)
        if not db_user:
            return False
        db.delete(db_user)
        db.commit()
        return True

    @staticmethod
    def _finished_matches_filter(user_id: int):
        """Matches with a recorded result (winner_id set)."""
        return (
            or_(Match.player1_id == user_id, Match.player2_id == user_id),
            Match.winner_id.isnot(None),
        )

    @staticmethod
    def get_user_stats(db: Session, user_id: int) -> Dict[str, Any]:
        """Calculate tennis statistics for a user based on finished matches."""
        matches = db.exec(
            select(Match).where(*UserService._finished_matches_filter(user_id))
        ).all()

        played = len(matches)
        won = sum(1 for m in matches if m.winner_id == user_id)
        lost = sum(1 for m in matches if m.winner_id != user_id)
        win_rate = (won / played * 100) if played > 0 else 0.0
        
        return {
            "played": played,
            "won": won,
            "lost": lost,
            "win_rate": round(win_rate, 1)
        }
    
    @staticmethod
    def _enrich_match_for_user(db: Session, m: Match, user_id: int) -> Dict[str, Any]:
        opponent_id = m.player2_id if m.player1_id == user_id else m.player1_id
        opponent = db.get(User, opponent_id)
        tournament = db.get(Tournament, m.tournament_id)
        return {
            "match": m,
            "opponent_name": opponent.full_name if opponent else "Desconocido",
            "opponent_id": opponent_id,
            "opponent_phone": opponent.phone_number if opponent else None,
            "tournament_name": tournament.name if tournament else f"Torneo #{m.tournament_id}",
            "tournament_start": tournament.start_date if tournament else None,
            "tournament_end": tournament.end_date if tournament else None,
            "i_proposed": m.proposed_by_id == user_id,
        }

    @staticmethod
    def get_user_upcoming_matches(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Fetch non-played matches for a user with scheduling context."""
        matches = db.exec(
            select(Match)
            .where(
                or_(Match.player1_id == user_id, Match.player2_id == user_id),
                Match.winner_id.is_(None),
            )
            .order_by(Match.match_date.asc())
        ).all()
        return [UserService._enrich_match_for_user(db, m, user_id) for m in matches]

    @staticmethod
    def get_user_played_matches(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Fetch finished matches with opponent name and score details."""
        matches = db.exec(
            select(Match)
            .where(*UserService._finished_matches_filter(user_id))
            .order_by(Match.match_date.desc())
        ).all()

        results = []
        for m in matches:
            row = UserService._enrich_match_for_user(db, m, user_id)
            row["is_winner"] = m.winner_id == user_id
            row["score"] = m.score or "—"
            results.append(row)
        return results
