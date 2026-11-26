# NetPulse

NetPulse is a FastAPI device-tracking API with SQLite persistence (Hands-on 3)
and structured JSON logging with request tracing (Hands-on 4).

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
uvicorn app.main:app --reload
python -m pytest -q
```

Data is stored in `netpulse.db` (SQLite, created at startup). The file is
git-ignored. Tests use a temporary database and never touch `netpulse.db`.

## Layers

- `app/routes/` - HTTP only: request parsing and response models
- `app/services/` - business rules; no SQLAlchemy imports
- `app/repositories/` - persistence; `SQLAlchemyDeviceRepository` flushes but never commits
- `app/db/` - engine, `get_session()` (commit on success, rollback on error), ORM models
- `app/middleware/request_id.py` - request ID and `request_completed` event
- `app/logging_config.py` - structlog configuration and redaction

## Logging

Logs are one JSON object per line. They go to stderr (the console) and are also
appended to `netpulse.log` in the project folder (git-ignored); set `NETPULSE_LOG_FILE` to write elsewhere. Tests write to a temp file instead. Uvicorn's own
access log stays on the console only.

Every request gets a `request_id`. A valid incoming `X-Request-ID` header
(`^[A-Za-z0-9_-]{1,64}$`) is reused; otherwise a new one is generated. The ID
is returned in the response's `X-Request-ID` header.

- `request_id` identifies one HTTP request and is in every log line for it.
- `device_id` identifies the device a business event is about.

Events:

- `request_completed` (INFO): `method`, `path` (route template such as
  `/devices/{device_id}/status`), `status_code`, `duration_ms`
- `device_registration_requested`, `device_registered` (INFO)
- `device_status_changed` (INFO): only when the status actually changes
- `offline_alert_created` (INFO)
- `device_not_found`, `device_already_exists` (WARNING): `error_type`, `device_id`
- `unhandled_exception` (ERROR, with stack trace); no `request_completed` is emitted

Sample output for one PATCH sent with `X-Request-ID: lab-trace-401`
(the device goes online to offline; the second identical PATCH adds no alert):

```json
{"device_id": "RTR-401", "old_status": "online", "new_status": "offline", "event": "device_status_changed", "request_id": "lab-trace-401", "level": "info", "timestamp": "2026-11-26T07:18:57.073645Z"}
{"device_id": "RTR-401", "event": "offline_alert_created", "request_id": "lab-trace-401", "level": "info", "timestamp": "2026-11-26T07:18:57.075020Z"}
{"method": "PATCH", "path": "/devices/{device_id}/status", "status_code": 200, "duration_ms": 25.26, "event": "request_completed", "request_id": "lab-trace-401", "level": "info", "timestamp": "2026-11-26T07:18:57.094008Z"}
```

Find every event for one request with `grep lab-trace-401 netpulse.log`
(when output is saved with `tee`) or by searching the console output.

Log levels: use INFO for normal business events, WARNING for expected client
errors (404/409), and ERROR for bugs or unexpected failures.

Safe logging rules:

- Keys named `password`, `token`, `api_key`, `authorization`, or `secret`
  (case-insensitive) are replaced with `***`.
- Do not log secrets under other names. Exception messages are included in
  the stack trace, so they must not contain secrets.

## Trade-offs

- SQLAlchemy is synchronous. Routes that touch the database are plain `def`,
  so FastAPI runs them in a threadpool. The probe route is `async def` but
  calls the synchronous service, which blocks the event loop during its
  database lookup. The probe's simulated delay itself is awaited.
- Tables are created with `Base.metadata.create_all` at startup. There are no migrations.
