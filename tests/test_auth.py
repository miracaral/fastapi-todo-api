from jose import jwt

from tests.conftest import login, register


def test_register_and_login(client):
    assert register(client, "alice").status_code == 201
    r = login(client, "alice")
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"


def test_password_is_hashed_not_stored(client):
    from database import get_db
    from main import app
    from models import User
    register(client, "alice")
    db = next(app.dependency_overrides[get_db]())
    user = db.query(User).filter_by(username="alice").one()
    assert user.hashed_password != "correct-horse-1"
    assert user.hashed_password.startswith("$2b$")  # bcrypt


def test_wrong_password_rejected(client):
    register(client, "alice")
    assert login(client, "alice", "wrong-password").status_code == 401


def test_duplicate_username_rejected(client):
    register(client, "alice")
    assert register(client, "alice").status_code == 409


def test_cannot_choose_own_role(client):
    register(client, "mallory", role="admin")  # extra field is ignored
    token = login(client, "mallory").json()["access_token"]
    assert jwt.get_unverified_claims(token)["role"] == "user"


def test_short_password_rejected(client):
    assert register(client, "bob", password="short").status_code == 422
