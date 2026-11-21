import pytest
from fastapi.testclient import TestClient

import src.app as app_module


TEST_ACTIVITY_NAME = "Test Activity"
UNKNOWN_ACTIVITY_NAME = "Unknown Activity"
EXISTING_EMAIL = "existing@mergington.edu"
NEW_EMAIL = "student@mergington.edu"


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        TEST_ACTIVITY_NAME: {
            "description": "A test activity",
            "schedule": "Mondays at 3:00 PM",
            "max_participants": 5,
            "participants": [],
        }
    }
    monkeypatch.setattr(app_module, "activities", test_activities)
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_homepage_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {
        TEST_ACTIVITY_NAME: {
            "description": "A test activity",
            "schedule": "Mondays at 3:00 PM",
            "max_participants": 5,
            "participants": [],
        }
    }


def test_signup_adds_participant(client):
    response = client.post(
        f"/activities/{TEST_ACTIVITY_NAME}/signup",
        params={"email": NEW_EMAIL},
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {NEW_EMAIL} for {TEST_ACTIVITY_NAME}"
    assert NEW_EMAIL in app_module.activities[TEST_ACTIVITY_NAME]["participants"]


def test_signup_rejects_duplicate_participant(client):
    app_module.activities[TEST_ACTIVITY_NAME]["participants"].append(EXISTING_EMAIL)

    response = client.post(
        f"/activities/{TEST_ACTIVITY_NAME}/signup",
        params={"email": EXISTING_EMAIL},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert app_module.activities[TEST_ACTIVITY_NAME]["participants"].count(EXISTING_EMAIL) == 1


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        f"/activities/{UNKNOWN_ACTIVITY_NAME}/signup",
        params={"email": NEW_EMAIL},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    app_module.activities[TEST_ACTIVITY_NAME]["participants"].append(EXISTING_EMAIL)

    response = client.delete(
        f"/activities/{TEST_ACTIVITY_NAME}/signup",
        params={"email": EXISTING_EMAIL},
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {EXISTING_EMAIL} from {TEST_ACTIVITY_NAME}"
    assert EXISTING_EMAIL not in app_module.activities[TEST_ACTIVITY_NAME]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        f"/activities/{UNKNOWN_ACTIVITY_NAME}/signup",
        params={"email": NEW_EMAIL},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant(client):
    response = client.delete(
        f"/activities/{TEST_ACTIVITY_NAME}/signup",
        params={"email": NEW_EMAIL},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
