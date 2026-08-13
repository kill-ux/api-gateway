"""
Unit tests for the billing proxy routes in app/routes.py.

Covers:
- proxy_to_billing (GET /api/billing/) — forwards requests to the billing
  service and returns its response unchanged.
- Error handling when the billing service is unreachable.
- Method restrictions (only GET is allowed on this route).

Note: POST /api/billing/ is handled by a separate function (queue_order),
covered in test_queue_order.py, not here.
"""

from pytest_mock import MockerFixture
from unittest.mock import Mock
import requests

APP_ROUTES_REQUESTS_GET = "app.routes.requests.get"
API_BILLING = "/api/billing/"

def test_proxy_to_billing_forwards_get(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    Happy path: a GET request should be forwarded to the billing service's
    URL, and the mocked upstream response should be passed back unchanged.

    requests.get() is called with the URL as a positional argument (not a
    keyword), so we read it from call_args.args[0], not call_args.kwargs.
    """
    fake_upstream_response.content = b'{"invoices": []}'
    mock_get = mocker.patch(
        APP_ROUTES_REQUESTS_GET, return_value=fake_upstream_response
    )

    resp = client.get(API_BILLING)

    assert resp.status_code == 200
    called_url = mock_get.call_args.args[0]
    assert called_url == "http://billing:5001/api/billing"


def test_proxy_to_billing_handles_connection_error(client, mocker: MockerFixture):
    """
    If the billing service is down, requests.get() raises ConnectionError.
    The route should catch this and return a 503 with a clear error body,
    rather than letting the exception bubble up as a 500.
    """
    mocker.patch(
        APP_ROUTES_REQUESTS_GET, side_effect=requests.exceptions.ConnectionError
    )

    resp = client.get(API_BILLING)

    assert resp.status_code == 503
    assert resp.get_json() == {"error": "Billing service is down"}


def test_proxy_to_billing_forwards_query_params(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    Query string parameters on the incoming request (e.g. ?user_id=42)
    should be forwarded to the billing service unchanged, via the
    params= kwarg on requests.get().
    """
    mock_get = mocker.patch(
        APP_ROUTES_REQUESTS_GET, return_value=fake_upstream_response
    )

    resp = client.get(f"{API_BILLING}?user_id=42&status=paid")

    assert resp.status_code == 200
    called_params = mock_get.call_args.kwargs["params"]
    assert called_params.get("user_id") == "42"
    assert called_params.get("status") == "paid"


def test_proxy_to_billing_strips_hop_by_hop_headers(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    The route strips hop-by-hop headers (Transfer-Encoding, Content-Length,
    Connection) from the upstream response before returning it, since these
    describe the upstream's own HTTP framing and are invalid/misleading if
    forwarded as-is on the gateway's own response.

    Content-Type should still pass through untouched.
    """
    fake_upstream_response.headers = {
        "Content-Type": "application/json",
        "Transfer-Encoding": "chunked",
        "Content-Length": "50",
        "Connection": "keep-alive",
    }
    mocker.patch(APP_ROUTES_REQUESTS_GET, return_value=fake_upstream_response)

    resp = client.get(API_BILLING)

    assert resp.status_code == 200
    assert "Transfer-Encoding" not in resp.headers
    assert "Connection" not in resp.headers
    assert resp.headers.get("Content-Type") == "application/json"


def test_proxy_to_billing_passes_through_upstream_status_code(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    The gateway is a transparent proxy: whatever status code the billing
    service returns (here, 404) should be passed straight through to the
    caller, not swallowed or translated into something else.
    """
    fake_upstream_response.status_code = 404
    mocker.patch(APP_ROUTES_REQUESTS_GET, return_value=fake_upstream_response)

    resp = client.get(API_BILLING)

    assert resp.status_code == 404


def test_proxy_to_billing_rejects_put(client, mocker: MockerFixture):
    """
    Only GET is registered on /api/billing/ for proxying. Flask's own
    routing should reject PUT with 405 before our view function ever runs
    — asserting requests.get was never called proves the rejection happens
    at the routing layer, not inside our code.
    """
    mock_get = mocker.patch(APP_ROUTES_REQUESTS_GET)

    resp = client.put(API_BILLING, json={"status": "should not work"})

    assert resp.status_code == 405
    mock_get.assert_not_called()


def test_proxy_to_billing_rejects_delete(client, mocker: MockerFixture):
    """
    Same check as test_proxy_to_billing_rejects_put, but for DELETE.
    """
    mock_get = mocker.patch(APP_ROUTES_REQUESTS_GET)

    resp = client.delete(API_BILLING)

    assert resp.status_code == 405
    mock_get.assert_not_called()
