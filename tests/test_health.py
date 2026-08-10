def test_health_return_ok(client):
    resp = client.get("/health")
    
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
