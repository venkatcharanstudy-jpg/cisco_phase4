"""Create the NetPulse MySQL database and its tables if they are missing.

Set NETPULSE_DATABASE_URL first, then run from the project root with:
    python -m app.db.init_db
"""

from sqlalchemy import inspect

import app.db.models  # noqa: F401  registers tables on Base.metadata
from app.db.database import Base, build_engine, ensure_database
from app.main import DEFAULT_DATABASE_URL


def main() -> None:
    ensure_database(DEFAULT_DATABASE_URL)
    engine = build_engine(DEFAULT_DATABASE_URL)
    Base.metadata.create_all(engine)
    print(f"Database ready. Tables: {sorted(inspect(engine).get_table_names())}")
    engine.dispose()


if __name__ == "__main__":
    main()
