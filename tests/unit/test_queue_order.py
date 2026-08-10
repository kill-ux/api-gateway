"""
Unit tests for the queue_order route (POST /api/billing/) in app/routes.py.

This route publishes order requests to RabbitMQ via pika rather than
proxying to another HTTP service, so pika.BlockingConnection is mocked
instead of requests. Tests cover config validation, the happy path,
queue setup, required-field validation, and both connection- and
publish-time failure modes.
"""

from pytest_mock import MockerFixture
import pika.exceptions


def test_queue_order_missing_rabbitmq_host_returns_500(client, monkeypatch):
    """
    RABBITMQ_HOST is read as a module-level constant at import time, not
    per-request — so to simulate it being unset we must patch the module
    attribute directly (app.routes.RABBITMQ_HOST), not just the env var
    via monkeypatch.setenv/delenv, which would have no effect here.

    Confirms the route fails fast with 500 before attempting any
    connection to RabbitMQ.
    """
    monkeypatch.setattr("app.routes.RABBITMQ_HOST", None)
    resp = client.post(
        "/api/billing/",
        json={
            "user_id": 1,
            "number_of_items": 2,
            "total_amount": 99.99,
        },
    )

    assert resp.status_code == 500
    assert resp.get_json() == {"error": "RabbitMQ host not configured"}


def test_queue_order_publishes_successfully(client, mocker: MockerFixture):
    """
    Happy path: with a valid body, the route should connect, publish the
    message, close the connection, and return 202 Accepted.

    mock_channel is obtained via mock_connection.channel.return_value
    (not mock_connection.return_value) because connection.channel() is a
    method call in the route, not calling connection itself.
    """
    mock_connection = mocker.patch("app.routes.pika.BlockingConnection").return_value
    mock_channel = mock_connection.channel.return_value

    resp = client.post(
        "/api/billing/",
        json={"user_id": 1, "number_of_items": 2, "total_amount": 99.99},
    )

    assert resp.status_code == 202
    mock_channel.basic_publish.assert_called_once()
    mock_connection.close.assert_called_once()


def test_queue_order_declares_durable_quorum_queue(client, mocker: MockerFixture):
    """
    Confirms the queue is declared with durable=True and the
    x-queue-type: quorum argument — important for making sure orders
    survive a RabbitMQ node restart, not just that *a* queue gets
    declared.
    """
    mock_connection = mocker.patch("app.routes.pika.BlockingConnection").return_value
    mock_channel = mock_connection.channel.return_value

    resp = client.post(
        "/api/billing/",
        json={"user_id": 1, "number_of_items": 2, "total_amount": 99.99},
    )
    call_args = mock_channel.queue_declare.call_args.kwargs
    assert call_args["durable"] == True
    assert call_args["arguments"]["x-queue-type"] == "quorum"


def test_queue_order_missing_required_fields_returns_400(client, mocker: MockerFixture):
    """
    If total_amount (or any of user_id/number_of_items/total_amount) is
    missing from the body, the route should return 400 rather than
    publishing a partial/invalid message.

    pika.BlockingConnection is still mocked here because the connection
    and channel are opened *before* the required-fields check runs in the
    route — without mocking it, this test would attempt a real network
    connection to RabbitMQ.
    """
    mock_connection = mocker.patch("app.routes.pika.BlockingConnection")
    resp = client.post("/api/billing/", json={"user_id": 1, "number_of_items": 2})

    assert resp.status_code == 400


def test_queue_order_uses_correct_credentials(client, mocker: MockerFixture):
    """
    Confirms pika.ConnectionParameters is built with the expected host,
    port, and credentials.

    Values are hardcoded here (not re-read via os.getenv) rather than
    compared against live env vars, since RABBITMQ_* are baked into
    app.routes as module-level constants at import time — reading them
    "live" in the test would just be comparing the constant to itself and
    wouldn't catch a real regression.
    """
    mock_connection = mocker.patch("app.routes.pika.BlockingConnection")

    resp = client.post(
        "/api/billing/",
        json={"user_id": 1, "number_of_items": 2, "total_amount": 99.99},
    )

    assert mock_connection.call_args.args[0].host == "rabbitmq"
    assert mock_connection.call_args.args[0].port == 5672
    assert mock_connection.call_args.args[0].credentials.username == "guest"
    assert mock_connection.call_args.args[0].credentials.password == "guest"


def test_queue_order_connection_error_returns_503(client, mocker: MockerFixture):
    """
    Simulates a real RabbitMQ connection failure using pika's own
    AMQPConnectionError (rather than a generic Exception), so this test
    reflects an actual failure mode and is distinguishable from
    test_queue_order_publish_error_returns_503 below.
    """
    mock_connection = mocker.patch(
        "app.routes.pika.BlockingConnection",
        side_effect=pika.exceptions.AMQPConnectionError("Connection refused"),
    )

    resp = client.post(
        "/api/billing/",
        json={"user_id": 1, "number_of_items": 2, "total_amount": 99.99},
    )

    assert resp.status_code == 503
    body = resp.get_json()
    assert "AMQPConnectionError" in body["error"]


def test_queue_order_publish_error_returns_503(client, mocker: MockerFixture):
    """
    Simulates a failure at publish time rather than connection time (the
    connection succeeds, but channel.basic_publish itself raises). Both
    failure modes are caught by the same generic except block in the
    route, so this confirms that path works too, not just the connection
    failure case above.
    """
    mock_connection_class = mocker.patch("app.routes.pika.BlockingConnection")
    mock_connection = mock_connection_class.return_value
    mock_channel = mock_connection.channel.return_value
    mock_channel.basic_publish.side_effect = Exception("bomm")

    resp = client.post(
        "/api/billing/",
        json={"user_id": 1, "number_of_items": 2, "total_amount": 99.99},
    )

    assert resp.status_code == 503
    body = resp.get_json()
    assert "bomm" in body["error"]

