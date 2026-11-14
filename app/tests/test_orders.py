from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from orders_api import main


@pytest.fixture(autouse=True)
def clear_orders():
    main._orders.clear()
    yield
    main._orders.clear()


client = TestClient(main.app)


def test_probes():
    assert client.get("/healthz").json() == {"status": "ok"}
    ready = client.get("/readyz").json()
    assert ready["status"] == "ready"


def test_create_get_and_delete_order():
    created = client.post("/orders", json={"item": "keyboard", "quantity": 2})
    assert created.status_code == 201
    order_id = created.json()["id"]

    fetched = client.get(f"/orders/{order_id}")
    assert fetched.status_code == 200
    assert fetched.json()["item"] == "keyboard"

    assert len(client.get("/orders").json()) == 1

    assert client.delete(f"/orders/{order_id}").status_code == 204
    assert client.get(f"/orders/{order_id}").status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"item": "", "quantity": 1},
        {"item": "mouse", "quantity": 0},
        {"item": "mouse", "quantity": 1001},
        {"quantity": 1},
    ],
)
def test_rejects_invalid_orders(payload):
    assert client.post("/orders", json=payload).status_code == 422


def test_unknown_order_returns_404():
    assert client.get(f"/orders/{uuid4()}").status_code == 404
    assert client.delete(f"/orders/{uuid4()}").status_code == 404


def test_metrics_are_exposed_per_route():
    client.get("/orders")
    body = client.get("/metrics").text
    assert 'http_requests_total{method="GET",route="/orders",status="200"}' in body
    assert "http_request_duration_seconds_bucket" in body
