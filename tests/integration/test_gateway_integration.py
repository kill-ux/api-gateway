import requests
import os

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
    payload = {
        "user_id": 103,
        "number_of_items": 2,
        "total_amount": 89.99
    }

    response = requests.post(f"{GATEWAY_URL}/api/billing", json=payload)

    assert response.status_code == 202
    
    body = response.json()
    assert body["message"] == "Order request accepted"
    
