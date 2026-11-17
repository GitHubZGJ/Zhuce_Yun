def test_health_check(client):
    response = client.get("/api/health")
    body = response.json()
    assert response.status_code == 200
    assert body["code"] == 0
    assert body["data"]["status"] == "up"


def test_unknown_api_route_returns_envelope(client):
    response = client.get("/api/does-not-exist")
    body = response.json()
    assert response.status_code == 404
    assert body["code"] == 40401
    assert body["message"] == "请求的资源不存在"


def test_method_not_allowed_returns_envelope(client):
    response = client.delete("/api/health")
    body = response.json()
    assert response.status_code == 405
    assert body["code"] == 40501
    assert body["message"] == "请求方法不被支持"
