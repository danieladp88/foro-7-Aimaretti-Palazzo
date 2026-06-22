import time

import requests


API_URL = "http://localhost:8000"
FRONT_URL = "http://localhost:8080"


def test_api_health_check():
    response = requests.get(f"{API_URL}/health", timeout=5)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_can_write_and_read_from_database():
    title = f"ticket-test-db-{int(time.time())}"

    create_response = requests.post(
        f"{API_URL}/tickets",
        json={
            "title": title,
            "description": "Prueba de integración con base de datos",
            "priority": "Media",
        },
        timeout=5,
    )

    assert create_response.status_code == 201

    list_response = requests.get(f"{API_URL}/tickets", timeout=5)

    assert list_response.status_code == 200

    tickets = list_response.json()

    assert any(ticket["title"] == title for ticket in tickets)


def test_end_to_end_front_proxy_api_database_flow():
    title = f"ticket-test-e2e-{int(time.time())}"

    create_response = requests.post(
        f"{FRONT_URL}/api/tickets",
        json={
            "title": title,
            "description": "Prueba pasando por frontend nginx, API y DB",
            "priority": "Alta",
        },
        timeout=5,
    )

    assert create_response.status_code == 201

    list_response = requests.get(f"{FRONT_URL}/api/tickets", timeout=5)

    assert list_response.status_code == 200

    tickets = list_response.json()

    assert any(ticket["title"] == title for ticket in tickets)