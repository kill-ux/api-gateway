from pytest_mock import MockerFixture
from unittest.mock import Mock
import requests


def test_proxy_to_billing_forwards_get(client, mocker: MockerFixture, fake_upstream_response: Mock):
    fake_upstream_response.content = b'{"invoices": []}'
    mock_get = mocker.patch("app.routes.requests.get", return_value=fake_upstream_response)

    resp = client.get("/api/billing/")

    assert resp.status_code == 200
    print(mock_get.call_args.args,mock_get.call_args)
    called_url = mock_get.call_args.args[0] if mock_get.call_args.args else mock_get.call_args.kwargs.get("url")
    assert called_url == "http://billing:5001/api/billing"


def test_proxy_to_billing_handles_connection_error(client, mocker: MockerFixture):
    mocker.patch("app.routes.requests.get", side_effect=requests.exceptions.ConnectionError)

    resp = client.get("/api/billing/")

    assert resp.status_code == 503
    assert resp.get_json() == {"error": "Billing service is down"}


def test_proxy_to_billing_forwards_query_params(client, mocker: MockerFixture, fake_upstream_response: Mock):
    mock_get = mocker.patch("app.routes.requests.get", return_value=fake_upstream_response)

    resp = client.get("/api/billing/?user_id=42&status=paid")

    assert resp.status_code == 200
    called_params = mock_get.call_args.kwargs["params"]
    assert called_params.get("user_id") == "42"
    assert called_params.get("status") == "paid"


def test_proxy_to_billing_strips_hop_by_hop_headers(client, mocker: MockerFixture, fake_upstream_response: Mock):
    fake_upstream_response.headers = {
        "Content-Type": "application/json",
        "Transfer-Encoding": "chunked",
        "Content-Length": "50",
        "Connection": "keep-alive",
    }
    mocker.patch("app.routes.requests.get", return_value=fake_upstream_response)

    resp = client.get("/api/billing/")

    assert resp.status_code == 200
    assert "Transfer-Encoding" not in resp.headers
    assert "Connection" not in resp.headers
    assert resp.headers.get("Content-Type") == "application/json"


def test_proxy_to_billing_passes_through_upstream_status_code(client, mocker: MockerFixture, fake_upstream_response: Mock):
    fake_upstream_response.status_code = 404
    mocker.patch("app.routes.requests.get", return_value=fake_upstream_response)

    resp = client.get("/api/billing/")

    assert resp.status_code == 404


def test_proxy_to_billing_rejects_put(client, mocker: MockerFixture):
    mock_get = mocker.patch("app.routes.requests.get")

    resp = client.put("/api/billing/", json={"status": "should not work"})

    assert resp.status_code == 405
    mock_get.assert_not_called()


def test_proxy_to_billing_rejects_delete(client, mocker: MockerFixture):
    mock_get = mocker.patch("app.routes.requests.get")

    resp = client.delete("/api/billing/")

    assert resp.status_code == 405
    mock_get.assert_not_called()
