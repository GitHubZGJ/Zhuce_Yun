def test_list_projects_with_sample_count(client, admin_headers):
    response = client.get("/api/projects", headers=admin_headers)
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["total"] == 3
    project = next(item for item in body["data"]["items"] if item["code"] == "XM-T-001")
    assert project["sample_count"] == 2
    assert project["status"] == "IN_PROGRESS"


def test_project_options(client, viewer_headers):
    response = client.get("/api/projects/options", headers=viewer_headers)
    body = response.json()
    assert response.status_code == 200
    assert len(body["data"]) == 3
    assert {item["code"] for item in body["data"]} >= {"XM-T-001", "XM-T-002"}


def test_create_project_normalizes_code_and_defaults(client, engineer_headers):
    response = client.post(
        "/api/projects",
        headers=engineer_headers,
        json={
            "code": "xm-t-100",
            "name": "新建检测项目",
            "client": "某建设公司",
            "location": "滨江市某路",
            "manager": "李工",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["code"] == 0
    assert body["data"]["code"] == "XM-T-100"
    assert body["data"]["status"] == "PLANNING"
    assert body["data"]["sample_count"] == 0


def test_create_project_duplicate_code(client, admin_headers):
    response = client.post(
        "/api/projects",
        headers=admin_headers,
        json={
            "code": "XM-T-001",
            "name": "重复项目",
            "client": "某单位",
            "location": "某地",
            "manager": "某人",
        },
    )
    body = response.json()
    assert response.status_code == 409
    assert body["code"] == 40901
    assert body["message"] == "项目编号已存在"


def test_create_project_invalid_date_range(client, admin_headers):
    response = client.post(
        "/api/projects",
        headers=admin_headers,
        json={
            "code": "XM-T-101",
            "name": "日期错误项目",
            "client": "某单位",
            "location": "某地",
            "manager": "某人",
            "start_date": "2026-12-31",
            "end_date": "2026-01-01",
        },
    )
    body = response.json()
    assert response.status_code == 422
    assert body["code"] == 42201
    assert "结束日期不能早于开始日期" in body["message"]


def test_update_project(client, admin_headers, data):
    project_id = data["projects"]["p2"].id
    response = client.put(
        f"/api/projects/{project_id}",
        headers=admin_headers,
        json={"name": "测试项目二（更新）", "status": "ARCHIVED"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["name"] == "测试项目二（更新）"
    assert body["data"]["status"] == "ARCHIVED"


def test_update_project_duplicate_code(client, admin_headers, data):
    response = client.put(
        f"/api/projects/{data['projects']['p2'].id}",
        headers=admin_headers,
        json={"code": "XM-T-001"},
    )
    body = response.json()
    assert response.status_code == 409
    assert body["message"] == "项目编号已存在"


def test_delete_project_with_samples_is_blocked(client, admin_headers, data):
    response = client.delete(
        f"/api/projects/{data['projects']['p1'].id}", headers=admin_headers
    )
    body = response.json()
    assert response.status_code == 400
    assert body["code"] == 40005
    assert body["message"] == "项目下存在样品，无法删除"


def test_delete_empty_project(client, admin_headers):
    created = client.post(
        "/api/projects",
        headers=admin_headers,
        json={
            "code": "XM-T-102",
            "name": "待删除项目",
            "client": "某单位",
            "location": "某地",
            "manager": "某人",
        },
    )
    project_id = created.json()["data"]["id"]
    deleted = client.delete(f"/api/projects/{project_id}", headers=admin_headers)
    assert deleted.status_code == 200
    assert deleted.json()["code"] == 0

    missing = client.get(f"/api/projects/{project_id}", headers=admin_headers)
    assert missing.status_code == 404
    assert missing.json()["code"] == 40401
    assert missing.json()["message"] == "工程项目不存在"


def test_project_not_found(client, viewer_headers):
    response = client.get("/api/projects/9999", headers=viewer_headers)
    body = response.json()
    assert response.status_code == 404
    assert body["code"] == 40401


def test_filter_projects_by_status(client, viewer_headers):
    response = client.get("/api/projects?status=ACCEPTED", headers=viewer_headers)
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["code"] == "XM-T-002"
