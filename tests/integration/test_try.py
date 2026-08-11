# tests/integration/test_gateway_integration.py
import requests

GATEWAY_URL = "http://api-gateway:3000"


def test_gateway_inventory_list():
    """Verify gateway forwards GET /api/movies to inventory mock."""
    response = requests.get(
        f"{GATEWAY_URL}/api/movies",
        timeout=5,
    )

    assert response.status_code == 200
    assert "movies" in response.json()


