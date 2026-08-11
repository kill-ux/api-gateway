import requests
import os
import time
import pytest

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://api-gateway:3000")


def test_gateway_forwards_get_request_to_inventory():
    """GET through gateway reaches inventory-app and returns the item."""
    response = requests.get(f"{GATEWAY_URL}/api/movies")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1

# def test_gateway_forwards_get_request_to_billing():
#     """GET through gateway reaches billing-app and returns the item."""
#     response = requests.get(f"{GATEWAY_URL}/api/movies/1")

#     assert response.status_code == 200
#     body = response.json()
#     assert body["id"] == 1