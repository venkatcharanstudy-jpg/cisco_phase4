from datetime import UTC, datetime

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    """Naive UTC timestamp, matching the DATETIME columns used in MySQL."""
    return datetime.now(UTC).replace(tzinfo=None)


def create_db_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True, pool_recycle=3600)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
