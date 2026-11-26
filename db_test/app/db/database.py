from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import Request
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


def ensure_database(database_url: str) -> None:
    """Create the MySQL database named in the URL if it does not exist yet."""
    url = make_url(database_url)
    if url.get_backend_name() != "mysql" or not url.database:
        return
    server_url = URL.create(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        query=url.query,
    )
    server = create_engine(server_url, isolation_level="AUTOCOMMIT")
    try:
        with server.connect() as conn:
            name = server.dialect.identifier_preparer.quote(url.database)
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {name} CHARACTER SET utf8mb4"))
    finally:
        server.dispose()


def unit_of_work(session_factory) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session(request: Request) -> Iterator[Session]:
    yield from unit_of_work(request.app.state.session_factory)
