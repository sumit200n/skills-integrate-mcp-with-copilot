import json

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    salt = "dGVzdC1zYWx0"
    credentials_path = tmp_path / "teachers.json"
    credentials_path.write_text(
        json.dumps(
            {
                "teachers": [
                    {
                        "username": "teacher1",
                        "password_hash": app_module.hash_password("correct-password", salt),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(app_module, "TEACHERS_FILE", credentials_path)
    monkeypatch.setattr(
        app_module,
        "activities",
        {
            "Chess Club": {
                "description": "Play chess",
                "schedule": "Fridays",
                "max_participants": 12,
                "participants": ["student@mergington.edu"],
            }
        },
    )
    return TestClient(app_module.app)


def test_activity_roster_is_public_but_mutations_require_teacher(client):
    activities_response = client.get("/activities")
    assert activities_response.status_code == 200
    assert activities_response.json()["Chess Club"]["participants"] == ["student@mergington.edu"]

    signup_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new-student@mergington.edu"},
    )
    unregister_response = client.delete(
        "/activities/Chess Club/unregister",
        params={"email": "student@mergington.edu"},
    )

    assert signup_response.status_code == 401
    assert unregister_response.status_code == 401
    assert client.get("/activities").json()["Chess Club"]["participants"] == [
        "student@mergington.edu"
    ]


def test_teacher_login_allows_mutations_until_logout(client):
    login_response = client.post(
        "/auth/login",
        json={"username": "teacher1", "password": "correct-password"},
    )
    assert login_response.status_code == 200
    assert login_response.json() == {"authenticated": True, "username": "teacher1"}
    assert login_response.cookies.get(app_module.SESSION_COOKIE)

    signup_response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new-student@mergington.edu"},
    )
    unregister_response = client.delete(
        "/activities/Chess Club/unregister",
        params={"email": "student@mergington.edu"},
    )

    assert signup_response.status_code == 200
    assert unregister_response.status_code == 200
    assert client.get("/auth/session").json() == {
        "authenticated": True,
        "username": "teacher1",
    }

    client.post("/auth/logout")
    assert client.get("/auth/session").json() == {"authenticated": False, "username": None}
    assert client.post(
        "/activities/Chess Club/signup",
        params={"email": "another-student@mergington.edu"},
    ).status_code == 401


def test_invalid_teacher_credentials_do_not_create_a_session(client):
    response = client.post(
        "/auth/login",
        json={"username": "teacher1", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert client.get("/auth/session").json() == {"authenticated": False, "username": None}