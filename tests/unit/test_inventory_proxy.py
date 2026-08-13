"""
Unit tests for the inventory proxy route in app/routes.py.

proxy_to_inventory handles GET/POST/PUT/DELETE on /api/movies/ and
/api/movies/<subpath>, forwarding requests to the inventory service and
returning its response unchanged (a transparent proxy). These tests mock
requests.request so no real network calls happen.
"""

from pytest_mock import MockerFixture
from unittest.mock import Mock

APP_ROUTES_REQUESTS_REQUEST = "app.routes.requests.request"
API_INVENTORY = "/api/movies"


def test_proxy_to_inventory_forwards_get(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    Happy path: a GET with no subpath is forwarded to the inventory
    service's base movies URL, and the mocked response is returned as-is.
    """
    fake_upstream_response.content = b'{"movies": []}'
    mock_request = mocker.patch(
        APP_ROUTES_REQUESTS_REQUEST, return_value=fake_upstream_response
    )

    resp = client.get(f"{API_INVENTORY}/")
    assert resp.status_code == 200
    mock_request.assert_called_once()
    called_url = mock_request.call_args.kwargs["url"]
    assert called_url == "http://inventory:5000/api/movies"


def test_proxy_to_inventory_handles_connection_error(client, mocker: MockerFixture):
    """
    If the inventory service is unreachable, requests.request() raises
    ConnectionError. The route should catch this and return 503 with a
    clear error body instead of letting it surface as a 500.

    Note: side_effect (not return_value) is required here — return_value
    would make the mock return the exception object instead of raising it.
    """
    import requests

    mocker.patch(
        APP_ROUTES_REQUESTS_REQUEST, side_effect=requests.exceptions.ConnectionError
    )

    resp = client.get(f"{API_INVENTORY}/")

    assert resp.status_code == 503
    assert resp.get_json() == {"error": "Inventory service is down"}


def test_proxy_to_inventory_forwards_get_with_subpath(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    A subpath (e.g. /api/movies/123) should be appended to the forwarded
    URL, confirming the route's URL-building logic handles single-resource
    lookups correctly, not just the collection endpoint.
    """
    fake_upstream_response.content = (
        b'{ "id": 123, "title": "Interstellar", "description": "Space exploration"}'
    )

    mock_request = mocker.patch(
        APP_ROUTES_REQUESTS_REQUEST, return_value=fake_upstream_response
    )
    resp = client.get(f"{API_INVENTORY}/123")

    assert resp.status_code == 200
    called_url = mock_request.call_args.kwargs["url"]
    assert called_url == "http://inventory:5000/api/movies/123"


def test_proxy_to_inventory_forwards_post_with_json_body(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    When the incoming request has a JSON body, it should be forwarded
    unchanged as the json= kwarg to requests.request (the request.is_json
    branch in the route).
    """
    mock_request = mocker.patch(
        APP_ROUTES_REQUESTS_REQUEST, return_value=fake_upstream_response
    )
    body = {"title": "Inception"}
    client.post(f"{API_INVENTORY}/", json=body)
    assert mock_request.call_args.kwargs["json"] == body
    assert mock_request.call_args.kwargs["method"] == "POST"


def test_proxy_to_inventory_forwards_request_with_no_json_body(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    When the incoming request has no JSON body, json=None should be
    forwarded — the else branch of request.is_json in the route. Also
    checks a non-200 (201) upstream status passes through correctly.
    """
    fake_upstream_response.status_code = 201
    mock_request = mocker.patch(
        APP_ROUTES_REQUESTS_REQUEST, return_value=fake_upstream_response
    )
    resp = client.post(f"{API_INVENTORY}/")
    assert mock_request.call_args.kwargs["json"] == None
    assert resp.status_code == 201


def test_proxy_to_inventory_forwards_query_params(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    Query string parameters on the incoming request should be forwarded
    unchanged via the params= kwarg.
    """
    mock_request = mocker.patch(
        APP_ROUTES_REQUESTS_REQUEST, return_value=fake_upstream_response
    )
    resp = client.get(f"{API_INVENTORY}/?year=2020&genre=scifi")

    assert resp.status_code == 200
    called_params = mock_request.call_args.kwargs["params"]
    assert called_params.get("year") == "2020"
    assert called_params.get("genre") == "scifi"


def test_proxy_to_inventory_forwards_put_method(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    PUT is only registered on the subpath route (/api/movies/<subpath>),
    not the collection route — this confirms it works correctly there,
    with the right HTTP method and URL forwarded.
    """
    mock_request = mocker.patch(
        APP_ROUTES_REQUESTS_REQUEST, return_value=fake_upstream_response
    )

    resp = client.put(f"{API_INVENTORY}/123", json={"title": "Updated Title"})

    assert resp.status_code == 200
    assert mock_request.call_args.kwargs["method"] == "PUT"
    called_url = mock_request.call_args.kwargs["url"]
    assert called_url == "http://inventory:5000/api/movies/123"


def test_proxy_to_inventory_forwards_delete_method(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    DELETE should forward correctly and pass through a non-200 (204 No
    Content) status from the upstream service unchanged.
    """
    fake_upstream_response.status_code = 204
    mock_request = mocker.patch(
        APP_ROUTES_REQUESTS_REQUEST, return_value=fake_upstream_response
    )
    resp = client.delete(f"{API_INVENTORY}/123")

    assert resp.status_code == 204
    assert mock_request.call_args.kwargs["method"] == "DELETE"


def test_proxy_to_inventory_rejects_put_without_subpath(client, mocker: MockerFixture):
    """
    PUT is NOT registered on the no-subpath collection route
    (/api/movies/), so Flask's own routing should reject it with 405
    before the view function runs at all — asserting requests.request
    was never called proves the rejection happens at routing, not in
    our code.
    """
    mock_request = mocker.patch(APP_ROUTES_REQUESTS_REQUEST)

    resp = client.put(f"{API_INVENTORY}/", json={"title": "Should not work"})
    assert resp.status_code == 405
    mock_request.assert_not_called()


def test_proxy_to_inventory_strips_hop_by_hop_headers(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    Hop-by-hop headers (Transfer-Encoding, Content-Length, Connection)
    describe the upstream response's own HTTP framing and must not be
    forwarded as-is on the gateway's response. Content-Type should still
    pass through untouched.
    """
    fake_upstream_response.headers = {
        "Content-Type": "application/json",
        "Transfer-Encoding": "chunked",
        "Content-Length": "123",
        "Connection": "keep-alive",
    }

    mocker.patch(APP_ROUTES_REQUESTS_REQUEST, return_value=fake_upstream_response)

    resp = client.get(f"{API_INVENTORY}/")
    assert resp.status_code == 200
    assert "Transfer-Encoding" not in resp.headers
    assert (
        "Content-Length" not in resp.headers
        or resp.headers.get("Content-Length") != "123"
    )
    assert "Connection" not in resp.headers
    assert resp.headers.get("Content-Type") == "application/json"


def test_proxy_to_inventory_passes_through_upstream_status_code(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    """
    The gateway is a transparent proxy: an error status from the upstream
    (here, 404) should pass straight through to the caller unchanged.
    """
    fake_upstream_response.status_code = 404
    mocker.patch(APP_ROUTES_REQUESTS_REQUEST, return_value=fake_upstream_response)

    resp = client.get(f"{API_INVENTORY}/999")

    assert resp.status_code == 404
