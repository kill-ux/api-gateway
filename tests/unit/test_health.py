"""
Unit tests for the health check route in app/routes.py.

This is the simplest route in the gateway — no proxying, no external
dependencies — so this test needs no mocking, just a direct call
through the Flask test client.
"""


def test_health_return_ok(client):
    """
    GET /health should always return 200 with a simple status payload.
    Used by orchestration/monitoring tools (e.g. ECS health checks,
    load balancer target group checks) to confirm the service is up.
    """
    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
