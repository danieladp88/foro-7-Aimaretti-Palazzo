import time

import requests


API_URL = "http://localhost:8000"
FRONT_URL = "http://localhost:8080"


def test_api_health_check():
    response = requests.get(f"{API_URL}/health", timeout=5)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_can_write_and_read_from_database():
    note_text = f"nota-test-db-{int(time.time())}"

    create_response = requests.post(
        f"{API_URL}/notes",
        json={"text": note_text},
        timeout=5,
    )

    assert create_response.status_code == 201

    list_response = requests.get(f"{API_URL}/notes", timeout=5)

    assert list_response.status_code == 200

    notes = list_response.json()

    assert any(note["text"] == note_text for note in notes)


def test_end_to_end_front_proxy_api_database_flow():
    note_text = f"nota-test-e2e-{int(time.time())}"

    create_response = requests.post(
        f"{FRONT_URL}/api/notes",
        json={"text": note_text},
        timeout=5,
    )

    assert create_response.status_code == 201

    list_response = requests.get(f"{FRONT_URL}/api/notes", timeout=5)

    assert list_response.status_code == 200

    notes = list_response.json()

    assert any(note["text"] == note_text for note in notes)