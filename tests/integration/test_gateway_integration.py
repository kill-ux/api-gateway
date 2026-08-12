import requests, pika, json, os

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://api-gateway:3000")


def test_gateway_forwards_get_request_to_inventory():
    """GET through gateway reaches inventory-app and returns the item."""
    response = requests.get(f"{GATEWAY_URL}/api/movies")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["id"] == 1


def test_gateway_forwards_get_request_to_billing():
    """GET through gateway reaches billing-app and returns the item."""
    response = requests.get(f"{GATEWAY_URL}/api/billing")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["id"] == 1


def test_gateway_forwards_post_request_to_billing():
    """POST through gateway reaches billing-app and creates a new billing item."""
    payload = {"user_id": 103, "number_of_items": 2, "total_amount": 89.99}

    response = requests.post(f"{GATEWAY_URL}/api/billing", json=payload)

    assert response.status_code == 202

    body = response.json()
    assert body["message"] == "Order request accepted"


def test_gateway_post_billing_publishes_correct_message_to_rabbitmq():
    payload = {"user_id": 999, "number_of_items": 7, "total_amount": 12.34}
    response = requests.post(f"{GATEWAY_URL}/api/billing", json=payload)
    assert response.status_code == 202

    credentials = pika.PlainCredentials("rabbit", "rabbit")
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq", port=5672, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue="rabbit", durable=True, arguments={"x-queue-type": "quorum"})

    method, properties, body = channel.basic_get(queue="rabbit", auto_ack=True)
    assert method is not None, "No message found in queue"
    message = json.loads(body)
    assert message == payload

    connection.close()