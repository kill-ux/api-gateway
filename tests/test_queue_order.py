from pytest_mock import MockerFixture
import pika.exceptions


def test_queue_order_missing_rabbitmq_host_returns_500(client, monkeypatch):
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
    mock_connection = mocker.patch("app.routes.pika.BlockingConnection")
    resp = client.post("/api/billing/", json={"user_id": 1, "number_of_items": 2})

    assert resp.status_code == 400


def test_queue_order_uses_correct_credentials(client, mocker: MockerFixture):
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
