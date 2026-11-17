def test_viewer_cannot_create_project(client, viewer_headers):
    response = client.post(
        "/api/projects",
        headers=viewer_headers,
        json={
            "code": "XM-V-001",
            "name": "越权项目",
            "client": "某单位",
            "location": "某地",
            "manager": "某人",
        },
    )
    body = response.json()
    assert response.status_code == 403
    assert body["code"] == 40301
    assert body["message"] == "没有权限执行该操作"


def test_engineer_and_viewer_cannot_manage_users(client, engineer_headers, viewer_headers):
    for headers in (engineer_headers, viewer_headers):
        response = client.get("/api/users", headers=headers)
        body = response.json()
        assert response.status_code == 403
        assert body["code"] == 40301


def test_admin_can_list_users(client, admin_headers):
    response = client.get("/api/users", headers=admin_headers)
    body = response.json()
    assert response.status_code == 200
    assert body["code"] == 0
    assert body["data"]["total"] == 4
    usernames = {item["username"] for item in body["data"]["items"]}
    assert {"admin", "engineer", "viewer", "disabled"} == usernames


def test_admin_creates_user_and_new_user_can_login(client, admin_headers):
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "username": "inspector",
            "password": "inspect123",
            "display_name": "质量员",
            "role": "ENGINEER",
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["username"] == "inspector"
    assert body["data"]["initial_password"] == "inspect123"

    login = client.post(
        "/api/auth/login", json={"username": "inspector", "password": "inspect123"}
    )
    assert login.status_code == 200
    assert login.json()["data"]["user"]["display_name"] == "质量员"


def test_duplicate_username_returns_conflict(client, admin_headers):
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={
            "username": "engineer",
            "password": "whatever123",
            "display_name": "重复用户",
            "role": "ENGINEER",
        },
    )
    body = response.json()
    assert response.status_code == 409
    assert body["code"] == 40901
    assert body["message"] == "登录名已存在"


def test_admin_cannot_deactivate_self(client, admin_headers, data):
    response = client.patch(
        f"/api/users/{data['users']['admin'].id}",
        headers=admin_headers,
        json={"is_active": False},
    )
    body = response.json()
    assert response.status_code == 400
    assert body["code"] == 40003
    assert body["message"] == "不能停用当前登录账号"


def test_admin_cannot_demote_self(client, admin_headers, data):
    response = client.patch(
        f"/api/users/{data['users']['admin'].id}",
        headers=admin_headers,
        json={"role": "VIEWER"},
    )
    body = response.json()
    assert response.status_code == 400
    assert body["code"] == 40003
    assert body["message"] == "不能降低当前登录账号的管理员角色"
