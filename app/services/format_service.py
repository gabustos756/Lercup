from typing import List, Optional
from sqlmodel import Session, select
from app.models.tournament_format import TournamentFormat

class FormatService:
    @staticmethod
    def get_format(db: Session, format_id: int) -> Optional[TournamentFormat]:
        return db.get(TournamentFormat, format_id)

    @staticmethod
    def get_all_formats(db: Session) -> List[TournamentFormat]:
        return db.exec(select(TournamentFormat)).all()

    @staticmethod
    def create_format(db: Session, format_data: TournamentFormat) -> TournamentFormat:
        db.add(format_data)
        db.commit()
        db.refresh(format_data)
        return format_data

    @staticmethod
    def update_format(db: Session, format_id: int, data: dict) -> Optional[TournamentFormat]:
        fmt = db.get(TournamentFormat, format_id)
        if not fmt:
            return None
        
        for key, value in data.items():
            if hasattr(fmt, key):
                setattr(fmt, key, value)
        
        db.add(fmt)
        db.commit()
        db.refresh(fmt)
        return fmt

    @staticmethod
    def delete_format(db: Session, format_id: int) -> bool:
        fmt = db.get(TournamentFormat, format_id)
        if not fmt:
            return False
        db.delete(fmt)
        db.commit()
        return True

    @staticmethod
    def prepopulate_default_formats(db: Session):
        """Seed default tournament formats if none exist."""
        existing = db.exec(select(TournamentFormat)).first()
        if existing:
            return

        defaults = [
            TournamentFormat(
                name="Fase de Grupos (10 Jugadores: Oro, Plata y Bronce)",
                description="2 grupos de 5 jugadores. Los primeros 2 pasan a Copa de Oro. Del 3° al 4° pasan a Copa de Plata. El 5° juega la Final de Bronce.",
                format_type="groups_to_playoffs",
                groups_count=2,
                gold_qualifiers=2,
                silver_qualifiers=2,
                bronze_qualifiers=1,
                has_third_place=True
            ),
            TournamentFormat(
                name="Eliminación Directa con Consolación (Copa de Plata)",
                description="Eliminación directa. Los perdedores del primer partido pasan a competir en un cuadro paralelo (Copa de Plata).",
                format_type="elimination_with_consolation",
                groups_count=0,
                gold_qualifiers=0,
                silver_qualifiers=0,
                bronze_qualifiers=0,
                has_third_place=True
            ),
            TournamentFormat(
                name="Fase de Grupos Estándar (2 grupos, pasan 2 a Semis)",
                description="2 grupos. Clasifican los 2 mejores de cada grupo directamente a semifinales de Copa de Oro.",
                format_type="groups_to_playoffs",
                groups_count=2,
                gold_qualifiers=2,
                silver_qualifiers=0,
                bronze_qualifiers=0,
                has_third_place=True
            )
        ]

        for d in defaults:
            db.add(d)
        db.commit()
