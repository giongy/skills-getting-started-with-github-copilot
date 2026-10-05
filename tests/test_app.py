from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def isolated_activities(monkeypatch):
    activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(isolated_activities):
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_all_activities(client, isolated_activities):
    # Arrange
    expected_activities = deepcopy(isolated_activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, isolated_activities):
    # Arrange
    activity_name = "Soccer Team"
    email = "student@mergington.edu"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in isolated_activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client, isolated_activities):
    # Arrange
    activity_name = "Chess Club"
    email = isolated_activities[activity_name]["participants"][0]
    participants_before = isolated_activities[activity_name]["participants"].copy()
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert isolated_activities[activity_name]["participants"] == participants_before


def test_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_path, params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_signup_removes_participant(client, isolated_activities):
    # Arrange
    activity_name = "Chess Club"
    email = isolated_activities[activity_name]["participants"][0]
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in isolated_activities[activity_name]["participants"]


def test_remove_signup_returns_not_found_for_unregistered_participant(
    client, isolated_activities
):
    # Arrange
    activity_name = "Soccer Team"
    email = "student@mergington.edu"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert email not in isolated_activities[activity_name]["participants"]


def test_remove_signup_returns_not_found_for_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(
        signup_path, params={"email": "student@mergington.edu"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"