import os

from app.config.settings import Settings

# Point the app at the separate test database (same server and credentials, "_test" suffix).
os.environ["DATABASE_URL"] = Settings().database_url + "_test"
os.environ.setdefault("GEMINI_API_KEY", "test-key")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401  (registers all ORM models on Base.metadata)
from app.config.database import Base, create_db_engine  # noqa: E402
from app.config.settings import get_settings  # noqa: E402
from app.integrations.internal_api import InternalApiClient  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models.enums import Role  # noqa: E402
from app.models.menu_item import MenuItem  # noqa: E402
from app.models.user import User  # noqa: E402
from app.security import hash_password  # noqa: E402


class ScriptedLLM:
    """Returns pre-scripted replies (or raises) in order, so chat tests are deterministic."""

    def __init__(self, *replies):
        self._replies = list(replies)

    def generate(self, system, turns, tools):
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


@pytest.fixture
def make_app():
    """Builds a fresh schema and a test app. The app's own REST API serves the chat tools' internal calls."""
    engine = create_db_engine(get_settings().database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    engine.dispose()

    def _make(llm=None):
        app = create_app(settings=get_settings(), llm_client=llm or ScriptedLLM())
        client = TestClient(app)
        app.state.container.internal_api = InternalApiClient("http://testserver", http=client)
        return app, client

    return _make


@pytest.fixture
def seeded(make_app):
    """Returns (app, client, ids): an admin, a customer, dosa (capacity 2) and biryani (capacity 5)."""
    app, client = make_app()
    with app.state.container.session_factory() as session:
        session.add(User(username="admin", password_hash=hash_password("Admin123"), role=Role.ADMIN))
        session.add(User(username="alice", password_hash=hash_password("Alice123"), role=Role.CUSTOMER))
        dosa = MenuItem(title="Masala Dosa", category="Breakfast", vegetarian=True, price="90.00", capacity=2)
        biryani = MenuItem(title="Paneer Biryani", category="Main course", vegetarian=True, price="180.00", capacity=5)
        session.add_all([dosa, biryani])
        session.commit()
        ids = {"dosa": dosa.id, "biryani": biryani.id}
    return app, client, ids
