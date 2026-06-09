import logging
from sqlmodel import create_engine, Session, SQLModel
from app.core.config import settings, database_url_for_log

logger = logging.getLogger(__name__)

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.ENV == "development",
    connect_args=connect_args,
)

logger.info(
    "Database engine: dialect=%s url=%s env=%s",
    engine.dialect.name,
    database_url_for_log(settings.DATABASE_URL),
    settings.ENV,
)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    import app.models  # noqa: F401 — register all models on metadata

    if settings.ENV == "development":
        SQLModel.metadata.create_all(engine)

    from app.services.format_service import FormatService
    with Session(engine) as session:
        FormatService.prepopulate_default_formats(session)
