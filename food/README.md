# Spice Route Kitchen: AI Smart Food Ordering & Restaurant Assistant

A FastAPI backend, a browser frontend, MySQL persistence, and a Gemini-powered chat assistant.
The assistant answers menu, policy, and order questions, and it can propose orders or cancellations
that the customer must confirm.

## Features

- Login with HTTP Basic auth (argon2-hashed passwords). Roles: `CUSTOMER` and `ADMIN`.
- Menu with per-day capacity. Orders lock menu rows, check capacity, snapshot prices, and
  are idempotent through the `Idempotency-Key` header.
- Order lifecycle: customers can cancel while `CONFIRMED`. Admins move orders through
  `PREPARING`, `READY`, `DELIVERED`, or `CANCELLED`. Cancelling restores capacity exactly once.
- Chat assistant (Gemini) with tool calling. Write actions are never executed directly. The
  assistant creates a pending action, and the user confirms or rejects it. Confirmation re-checks
  prices and capacity first.
- Knowledge base (RAG). Admins upload `.txt`, `.pdf`, or `.docx` policy files. Chunks are stored
  in MySQL and retrieved with TF-IDF. Answers cite their source documents.
- Rate limiting on chat, and a uniform error envelope `{code, message, request_id}`.

## Architecture

Layered design, with dependencies pointing inward:

| Layer | Location | Responsibility |
|---|---|---|
| API (routers) | `app/api/` | HTTP, auth dependencies, request and response mapping |
| Services | `app/services/` | Business rules: orders, policy, pending actions, chat, documents |
| Agents | `app/agents/` | Single-agent tool loop and tool registry |
| Repositories | `app/repositories/` | Data access over SQLAlchemy |
| Models | `app/models/` | ORM entities and enums |
| Integrations | `app/integrations/` | Gemini adapter, internal REST client (adapters behind neutral interfaces) |
| RAG | `app/rag/` | Loading, chunking, and retrieval |
| Composition root | `app/main.py`, `app/api/deps.py` | `create_app` factory and dependency injection through `Container` |

Design patterns used: Repository, Service layer, Strategy (`Retriever`, `LLMClient`), Adapter
(`GeminiClient`, `InternalApiClient`), Registry (tool registry, action executors), Command
(`ActionExecutor`), Factory (`create_app`), and Dependency Injection (`Container` plus FastAPI `Depends`).

## Setup

Requirements: Python 3.12, MySQL 8 (or compatible), and a Gemini API key.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Create the databases (utf8mb4):

```sql
CREATE DATABASE food_delivery CHARACTER SET utf8mb4;
CREATE DATABASE food_delivery_test CHARACTER SET utf8mb4;
```

Copy `.env.example` to `.env` and fill in the values. `.env` is git-ignored.

```
DATABASE_URL=mysql+pymysql://USER:PASSWORD@localhost:3306/food_delivery
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-3.5-flash-lite
```

## Run

```bash
.venv/bin/python -m app.seed                                   # tables, menu, sample orders, knowledge base
.venv/bin/uvicorn app.main:create_app --factory --port 8000    # then open http://localhost:8000
```

Seeded accounts:

- Admin: `admin` / `Admin123`
- Demo customer: `customer` / `Customer123`

API docs are available at `http://localhost:8000/docs`.

## Tests

```bash
.venv/bin/python -m pytest
```

Tests use the `food_delivery_test` database (the `_test` suffix on `DATABASE_URL`) and a scripted
fake LLM, so they do not call Gemini. They cover capacity, idempotency, cancel-once behavior, RBAC,
the chat confirm-once flow, and the LLM outage response.

## Notes and deviations from the handbook

- **LLM:** the handbook specifies OpenAI. This project uses Google Gemini, as requested.
  The model is set by `GEMINI_MODEL`.
- **Retrieval:** the handbook suggests ChromaDB. This project uses TF-IDF retrieval over MySQL
  chunks, which avoids a second datastore. The `Retriever` interface makes it straightforward to swap in a vector store.
- **Schema:** tables are created with SQLAlchemy `create_all`. Alembic is not set up.
- **Sample policies:** the knowledge base uses fictional `.txt` files. Upload PDFs or DOCX files
  through the admin panel.
- **Security:** the Gemini key was shared in chat. Rotate it and put the new key in `.env`.
