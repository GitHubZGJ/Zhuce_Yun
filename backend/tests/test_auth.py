import pytest


def test_login_success(client):
    response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "pass123"}
    )
    body = response.json()
    assert response.status_code == 200
    assert body["code"] == 0
    assert body["message"] == "登录成功"
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["user"]["username"] == "admin"
    assert body["data"]["user"]["role"] == "ADMIN"


def test_login_wrong_password(client):
    response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "wrong123"}
    )
    body = response.json()
    assert response.status_code == 401
    assert body["code"] == 40101
    assert body["message"] == "用户名或密码错误"


def test_login_inactive_account(client):
    response = client.post(
        "/api/auth/login", json={"username": "disabled", "password": "pass123"}
    )
    body = response.json()
    assert response.status_code == 403
    assert body["code"] == 40102
    assert body["message"] == "账号已被停用，请联系管理员"


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "ab", "password": "pass123"},
        {"username": "admin", "password": "123"},
        {"username": "admin"},
    ],
)
def test_login_validation(client, payload):
    response = client.post("/api/auth/login", json=payload)
    body = response.json()
    assert response.status_code == 422
    assert body["code"] == 42201
    assert "参数校验失败" in body["message"]


def test_me_requires_token(client):
    response = client.get("/api/auth/me")
    body = response.json()
    assert response.status_code == 401
    assert body["code"] == 40101
    assert body["message"] == "请先登录后再访问"


def test_me_with_invalid_token(client):
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    body = response.json()
    assert response.status_code == 401
    assert body["code"] == 40101
    assert body["message"] == "登录凭证无效，请重新登录"


def test_me_and_logout(client, admin_headers):
    me = client.get("/api/auth/me", headers=admin_headers)
    assert me.status_code == 200
    assert me.json()["data"]["display_name"] == "系统管理员"

    logout = client.post("/api/auth/logout", headers=admin_headers)
    assert logout.status_code == 200
    assert logout.json()["code"] == 0
    assert logout.json()["message"] == "已退出登录"
