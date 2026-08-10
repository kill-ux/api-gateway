import pytest
from app import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("INVENTORY_APP_HOST", "inventory")
    monkeypatch.setenv("INVENTORY_APP_PORT", "5000")
    monkeypatch.setenv("BILLING_APP_HOST", "billing")
    monkeypatch.setenv("BILLING_APP_PORT", "5001")
    monkeypatch.setenv("RABBITMQ_HOST", "rabbitmq")
    monkeypatch.setenv("RABBITMQ_QUEUE", "orders")
    monkeypatch.setenv("RABBITMQ_USER", "guest")
    monkeypatch.setenv("RABBITMQ_PASS", "guest")
    monkeypatch.setenv("RABBITMQ_PORT", "5672")

    app = create_app()
    return app.test_client()


@pytest.fixture
def fake_upstream_response(mocker):
    resp = mocker.Mock()
    resp.content = b"{}"
    resp.status_code = 200
    resp.headers = {"Content-Type": "application/json"}
    return resp
