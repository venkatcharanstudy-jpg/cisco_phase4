import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

import app.db.models  # noqa: F401  registers tables on Base.metadata
from app.db.database import Base, ensure_database
from app.main import create_app


@pytest.fixture
def db_url() -> str:
    url = os.environ.get("NETPULSE_TEST_DATABASE_URL")
    if not url:
        pytest.skip("set NETPULSE_TEST_DATABASE_URL to a disposable MySQL database")
    ensure_database(url)
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    yield url
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(db_url: str):
    with TestClient(create_app(db_url)) as test_client:
        yield test_client
