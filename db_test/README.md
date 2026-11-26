# NetPulse

Hands-on 3 stores devices and alerts in MySQL through SQLAlchemy 2.x. The
Hands-on 2 API, the `DeviceRepository` Protocol, and the `DeviceService`
business rules are unchanged; only the repository implementation was swapped.

## Architecture

- `app/main.py` - `create_app()` builds the engine and sessionmaker. On startup it creates the database and tables if they are missing.
- `app/db/database.py` - `Base`, engine helpers, `ensure_database`, and `unit_of_work` (commit on success, rollback on error).
- `app/db/models.py` - ORM tables `devices` and `alerts`.
- `app/db/init_db.py` - command to create the database and tables without starting the server.
- `app/repositories/sqlalchemy_device_repository.py` - SQLAlchemy implementation of the Protocol. It only flushes; the unit of work commits.
- `app/repositories/device_repository.py` - the in-memory repository, kept for the Hands-on 2 tests.

ASGI note: FastAPI is an ASGI application and Uvicorn is the ASGI server. The
sync routes run in a threadpool, so database access does not block the event loop.
Trade-off: the `async` probe route calls the synchronous `service.get()`
directly, which briefly blocks the loop. This is acceptable for a small lab
but should move to a threadpool or an async driver in production.

## Configuration

The connection URL is read from `NETPULSE_DATABASE_URL`. Do not commit passwords.

```bash
export NETPULSE_DATABASE_URL="mysql+pymysql://admin:<password>@127.0.0.1:3306/netpulse"
export NETPULSE_TEST_DATABASE_URL="mysql+pymysql://admin:<password>@127.0.0.1:3306/netpulse_test"
```

The user needs permission to create databases, or the `netpulse` database must already exist.

## Endpoints

- `POST /devices` - register a device (409 if the ID already exists)
- `GET /devices` - list devices
- `GET /devices/summary` - totals, online/offline counts, sorted unique device types
- `GET /devices/{device_id}` - get one device (404 if missing)
- `PATCH /devices/{device_id}/status` - update status; online to offline creates one alert
- `GET /devices/{device_id}/probe` - simulated probe; does not change status or alerts
- `GET /alerts` - list alerts
- `GET /health` - health check

## Running

```bash
pip install -r requirements.txt
python -m app.db.init_db          # creates database "netpulse" and tables
uvicorn app.main:app --reload
python -m pytest -q               # needs NETPULSE_TEST_DATABASE_URL
python -m examples.mysql_crud_demo
python -m examples.async_probe_demo
```

Tests reset the tables in `NETPULSE_TEST_DATABASE_URL` before and after each
test, so point it only at a disposable database. Without it, the database tests
are skipped.

## Data

Restarting the server keeps devices and alerts. The CRUD demo writes to the
configured database and removes its demo device and alerts when it finishes.
