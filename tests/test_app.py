import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activity_data():
    return {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["student@mergington.edu"],
        },
    }


@pytest.fixture
def client(activity_data, monkeypatch):
    monkeypatch.setattr(app_module, "activities", activity_data)
    return TestClient(app_module.app)


def test_get_activities_returns_activity_data_without_caching(client, activity_data):
    # Arrange
    expected = activity_data

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client, activity_data):
    # Arrange
    activity_name = "Chess Club"
    email = "new-student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activity_data[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client, activity_data):
    # Arrange
    activity_name = "Chess Club"
    email = activity_data[activity_name]["participants"][0]
    original_participants = activity_data[activity_name]["participants"].copy()

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Student already signed up for this activity"
    )
    assert activity_data[activity_name]["participants"] == original_participants


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client, activity_data):
    # Arrange
    activity_name = "Chess Club"
    email = activity_data[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activity_data[activity_name]["participants"]


def test_unregister_returns_not_found_for_unregistered_participant(
    client,
    activity_data,
):
    # Arrange
    activity_name = "Chess Club"
    email = "not-registered@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Student is not signed up for this activity"
    )
    assert activity_data[activity_name]["participants"] == [
        "student@mergington.edu"
    ]


def test_unregister_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
