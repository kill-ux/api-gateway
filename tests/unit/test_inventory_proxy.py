from pytest_mock import MockerFixture
from unittest.mock import Mock


def test_proxy_to_inventory_forwards_get(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    fake_upstream_response.content = b'{"movies": []}'
    mock_request = mocker.patch(
        "app.routes.requests.request", return_value=fake_upstream_response
    )

    resp = client.get("/api/movies/")
    assert resp.status_code == 200
    mock_request.assert_called_once()
    called_url = mock_request.call_args.kwargs["url"]
    assert called_url == "http://inventory:5000/api/movies"


def test_proxy_to_inventory_handles_connection_error(client, mocker: MockerFixture):
    import requests

    mock_request = mocker.patch(
        "app.routes.requests.request", side_effect=requests.exceptions.ConnectionError
    )

    resp = client.get("/api/movies/")

    assert resp.status_code == 503
    assert resp.get_json() == {"error": "Inventory service is down"}


def test_proxy_to_inventory_forwards_get_with_subpath(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    fake_upstream_response.content = (
        b'{ "id": 123, "title": "Interstellar", "description": "Space exploration"}'
    )

    mock_request = mocker.patch(
        "app.routes.requests.request", return_value=fake_upstream_response
    )
    resp = client.get("/api/movies/123")

    assert resp.status_code == 200
    called_url = mock_request.call_args.kwargs["url"]
    assert called_url == "http://inventory:5000/api/movies/123"


def test_proxy_to_inventory_forwards_post_with_json_body(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    mock_request = mocker.patch(
        "app.routes.requests.request", return_value=fake_upstream_response
    )
    body = {"title": "Inception"}
    resp = client.post("/api/movies/", json=body)
    assert mock_request.call_args.kwargs["json"] == body
    assert mock_request.call_args.kwargs["method"] == "POST"


def test_proxy_to_inventory_forwards_request_with_no_json_body(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    fake_upstream_response.status_code = 201
    mock_request = mocker.patch(
        "app.routes.requests.request", return_value=fake_upstream_response
    )
    resp = client.post("/api/movies/")
    assert mock_request.call_args.kwargs["json"] == None
    assert resp.status_code == 201


def test_proxy_to_inventory_forwards_query_params(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    mock_request = mocker.patch(
        "app.routes.requests.request", return_value=fake_upstream_response
    )
    resp = client.get("/api/movies/?year=2020&genre=scifi")

    assert resp.status_code == 200
    called_params = mock_request.call_args.kwargs["params"]
    assert called_params.get("year") == "2020"
    assert called_params.get("genre") == "scifi"


def test_proxy_to_inventory_forwards_put_method(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    mock_request = mocker.patch(
        "app.routes.requests.request", return_value=fake_upstream_response
    )

    resp = client.put("/api/movies/123", json={"title": "Updated Title"})

    assert resp.status_code == 200
    assert mock_request.call_args.kwargs["method"] == "PUT"
    called_url = mock_request.call_args.kwargs["url"]
    assert called_url == "http://inventory:5000/api/movies/123"


def test_proxy_to_inventory_forwards_delete_method(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    fake_upstream_response.status_code = 204
    mock_request = mocker.patch(
        "app.routes.requests.request", return_value=fake_upstream_response
    )
    resp = client.delete("/api/movies/123")

    assert resp.status_code == 204
    assert mock_request.call_args.kwargs["method"] == "DELETE"


def test_proxy_to_inventory_rejects_put_without_subpath(client, mocker: MockerFixture):
    mock_request = mocker.patch("app.routes.requests.request")

    resp = client.put("/api/movies/", json={"title": "Should not work"})
    assert resp.status_code == 405
    mock_request.assert_not_called()


def test_proxy_to_inventory_strips_hop_by_hop_headers(
    client, mocker: MockerFixture, fake_upstream_response: Mock
):
    fake_upstream_response.headers = {
        "Content-Type": "application/json",
        "Transfer-Encoding": "chunked",
        "Content-Length": "123",
        "Connection": "keep-alive",
    }

    mocker.patch("app.routes.requests.request", return_value=fake_upstream_response)

    resp = client.get("/api/movies/")
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
    fake_upstream_response.status_code = 404
    mocker.patch("app.routes.requests.request", return_value=fake_upstream_response)

    resp = client.get("/api/movies/999")

    assert resp.status_code == 404
