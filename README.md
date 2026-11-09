# Todo API

A REST API built with **FastAPI** and **SQLAlchemy**: users register, log in with a **JWT**, and manage their own todo list. Started during the Google AI & Technology Academy backend track (2025), later fixed, tested and cleaned up.

## Features

- **Authentication:** OAuth2 password flow, passwords hashed with **bcrypt**, signed JWT access tokens (HS256, 60 min).
- **Per-user data:** every todo query is filtered by its owner, so one user can never read, change or delete another user's todo (the API answers `404`, not `403`, so it does not even reveal that the todo exists).
- **Validation:** request bodies are Pydantic models (title length, priority 1–5, valid email, password ≥ 8 characters).
- **Migrations:** the database schema is managed with **Alembic**.
- **Tests:** pytest + FastAPI `TestClient`, each test on a fresh in-memory SQLite database. CI runs migrations and tests on every push.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then set SECRET_KEY
alembic upgrade head          # create the database
uvicorn main:app --reload     # interactive docs at http://127.0.0.1:8000/docs
```

## Endpoints

| Method | Path | Auth | What it does |
| --- | --- | --- | --- |
| POST | `/auth/` | – | Register a user |
| POST | `/auth/token` | – | Log in, returns a bearer token |
| GET | `/todo/` | Bearer | List my todos |
| GET | `/todo/{id}` | Bearer | Get one of my todos |
| POST | `/todo/` | Bearer | Create a todo |
| PUT | `/todo/{id}` | Bearer | Update a todo |
| DELETE | `/todo/{id}` | Bearer | Delete a todo |
| GET | `/health` | – | Health check |

## Tests

```bash
pytest -q
```

What they cover: registration and login, bcrypt hashing, wrong password, duplicate users, short passwords, users not being able to give themselves a role, missing / invalid / expired tokens, the full CRUD flow, input validation, and one user trying to read, edit and delete another user's todo.

## What I fixed in the first version

| Problem | Effect | Fix |
| --- | --- | --- |
| `get_current_user` returned `{'id', user_id, ...}` (commas instead of colons) | That is a Python **set**, not a dict, so every protected route crashed | Return a real dict; covered by the CRUD tests |
| JWT signing key hard-coded in the source | Anyone with the code could forge tokens | Read `SECRET_KEY` from the environment (`.env`), refuse to start without it |
| Users chose their own `role` at sign-up | Anyone could register as `admin` ([write-up](docs/privilege-escalation-fix.md)) | Role is always `user`; test checks it |
| `complete` in the request vs `completed` in the model | Creating a todo failed | One field name, `completed` |
| Routes like `/todo/todo/{id}` | Prefix repeated | `/todo/{id}` |
| Alembic had only an "add column" migration | A fresh database could not be built from migrations | Added the initial migration; CI checks migrations match the models |
