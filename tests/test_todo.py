from datetime import timedelta

from routers.auth import create_access_token
from tests.conftest import auth_header

TODO = {"title": "Learn FastAPI", "description": "Dependencies and routers", "priority": 3}


def test_requires_token(client):
    assert client.get("/todo/").status_code == 401


def test_invalid_token_rejected(client):
    assert client.get("/todo/", headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401


def test_expired_token_rejected(client):
    token = create_access_token("alice", 1, "user", timedelta(minutes=-1))
    assert client.get("/todo/", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_crud_flow(client):
    h = auth_header(client, "alice")
    created = client.post("/todo/", json=TODO, headers=h)
    assert created.status_code == 201
    tid = created.json()["id"]

    assert client.get(f"/todo/{tid}", headers=h).json()["title"] == "Learn FastAPI"

    updated = {**TODO, "title": "Learn FastAPI well", "completed": True}
    assert client.put(f"/todo/{tid}", json=updated, headers=h).status_code == 204
    got = client.get(f"/todo/{tid}", headers=h).json()
    assert got["title"] == "Learn FastAPI well" and got["completed"] is True

    assert client.delete(f"/todo/{tid}", headers=h).status_code == 204
    assert client.get(f"/todo/{tid}", headers=h).status_code == 404


def test_validation(client):
    h = auth_header(client, "alice")
    assert client.post("/todo/", json={**TODO, "priority": 9}, headers=h).status_code == 422
    assert client.post("/todo/", json={**TODO, "title": "x"}, headers=h).status_code == 422


def test_users_cannot_touch_each_others_todos(client):
    alice, bob = auth_header(client, "alice"), auth_header(client, "bob")
    tid = client.post("/todo/", json=TODO, headers=alice).json()["id"]

    assert client.get("/todo/", headers=bob).json() == []
    assert client.get(f"/todo/{tid}", headers=bob).status_code == 404
    assert client.put(f"/todo/{tid}", json=TODO, headers=bob).status_code == 404
    assert client.delete(f"/todo/{tid}", headers=bob).status_code == 404
    assert client.get(f"/todo/{tid}", headers=alice).status_code == 200
