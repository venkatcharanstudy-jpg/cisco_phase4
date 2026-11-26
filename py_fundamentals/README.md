# NetPulse

Hands-on 2 extends the Hands-on 1 API with a device summary, centralized
409/404 error handlers, and a simulated asynchronous device probe.

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
python -m examples.async_probe_demo
```

## In-memory data

Storage is in memory only. Restarting the server resets all devices and alerts
to empty. Persistence is added in Hands-on 3.
