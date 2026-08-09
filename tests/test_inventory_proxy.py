
def test_proxy_to_inventory_forwards_get(client, mocker):
    fake_response = mocker.Mock()
    fake_response.content = b'{"movies": []}'
    fake_response.status_code = 200
    fake_response.headers = {"Content-Type": "application/json"}
    
    mock_request = mocker.patch('app.routes.requests.request')