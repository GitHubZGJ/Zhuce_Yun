def test_sample_list_filters(client, viewer_headers):
    by_type = client.get("/api/samples?type=CONCRETE", headers=viewer_headers)
    body = by_type.json()
    assert by_type.status_code == 200
    assert body["data"]["total"] == 2
    assert {item["code"] for item in body["data"]["items"]} == {"YP-T-001", "YP-T-004"}

    by_project = client.get("/api/samples?project_id=1", headers=viewer_headers)
    assert by_project.json()["data"]["total"] == 2


def test_create_sample_validations(client, engineer_headers, data):
    unknown_project = client.post(
        "/api/samples",
        headers=engineer_headers,
        json={
            "code": "YP-T-010",
            "project_id": 9999,
            "type": "CONCRETE",
            "spec": "C30 150×150×150mm",
        },
    )
    body = unknown_project.json()
    assert unknown_project.status_code == 400
    assert body["code"] == 40002
    assert body["message"] == "关联的工程项目不存在"

    duplicate = client.post(
        "/api/samples",
        headers=engineer_headers,
        json={
            "code": "YP-T-001",
            "project_id": data["projects"]["p1"].id,
            "type": "CONCRETE",
            "spec": "C30 150×150×150mm",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == 40901
    assert duplicate.json()["message"] == "样品编号已存在"


def test_create_sample_normalizes_code(client, engineer_headers, data):
    response = client.post(
        "/api/samples",
        headers=engineer_headers,
        json={
            "code": "yp-t-005",
            "project_id": data["projects"]["p3"].id,
            "type": "ASPHALT",
            "spec": "AC-13 马歇尔试件",
            "quantity": 4,
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["code"] == "YP-T-005"
    assert body["data"]["status"] == "PENDING"
    assert body["data"]["project_code"] == "XM-T-003"


def test_delete_sample_with_records_is_blocked(client, admin_headers, data):
    response = client.delete(
        f"/api/samples/{data['samples']['s1'].id}", headers=admin_headers
    )
    body = response.json()
    assert response.status_code == 400
    assert body["code"] == 40006
    assert body["message"] == "样品下存在检测记录，无法删除"


def test_delete_sample_without_records(client, admin_headers, data):
    sample_id = data["samples"]["s4"].id
    response = client.delete(f"/api/samples/{sample_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["code"] == 0
    missing = client.get(f"/api/samples/{sample_id}", headers=admin_headers)
    assert missing.status_code == 404
    assert missing.json()["message"] == "检测样品不存在"


def test_create_record_gte_boundary_passes_and_updates_sample(client, engineer_headers, data):
    sample_id = data["samples"]["s4"].id
    response = client.post(
        "/api/test-records",
        headers=engineer_headers,
        json={
            "sample_id": sample_id,
            "item": "抗压强度（28d）",
            "standard_value": 30.0,
            "measured_value": 30.0,
            "unit": "MPa",
            "rule": "GTE",
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["code"] == 0
    assert body["data"]["conclusion"] == "PASS"

    sample = client.get(f"/api/samples/{sample_id}", headers=engineer_headers)
    assert sample.json()["data"]["status"] == "DONE"


def test_create_record_gte_failure(client, engineer_headers, data):
    response = client.post(
        "/api/test-records",
        headers=engineer_headers,
        json={
            "sample_id": data["samples"]["s4"].id,
            "item": "抗压强度（28d）",
            "standard_value": 30.0,
            "measured_value": 29.99,
            "unit": "MPa",
            "rule": "GTE",
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["conclusion"] == "FAIL"


def test_create_record_lte_boundaries(client, engineer_headers, data):
    sample_id = data["samples"]["s4"].id
    passed = client.post(
        "/api/test-records",
        headers=engineer_headers,
        json={
            "sample_id": sample_id,
            "item": "含水率",
            "standard_value": 18.0,
            "measured_value": 18.0,
            "unit": "%",
            "rule": "LTE",
        },
    )
    assert passed.json()["data"]["conclusion"] == "PASS"

    failed = client.post(
        "/api/test-records",
        headers=engineer_headers,
        json={
            "sample_id": sample_id,
            "item": "含水率",
            "standard_value": 18.0,
            "measured_value": 18.01,
            "unit": "%",
            "rule": "LTE",
        },
    )
    assert failed.json()["data"]["conclusion"] == "FAIL"


def test_create_record_unknown_sample(client, engineer_headers):
    response = client.post(
        "/api/test-records",
        headers=engineer_headers,
        json={
            "sample_id": 9999,
            "item": "抗压强度",
            "standard_value": 30.0,
            "measured_value": 31.0,
            "unit": "MPa",
        },
    )
    body = response.json()
    assert response.status_code == 400
    assert body["code"] == 40002
    assert body["message"] == "关联的检测样品不存在"


def test_create_record_validation_error(client, engineer_headers, data):
    response = client.post(
        "/api/test-records",
        headers=engineer_headers,
        json={"sample_id": data["samples"]["s1"].id, "item": "抗压强度"},
    )
    body = response.json()
    assert response.status_code == 422
    assert body["code"] == 42201
    assert "参数校验失败" in body["message"]


def test_update_record_recomputes_conclusion(client, engineer_headers, data):
    created = client.post(
        "/api/test-records",
        headers=engineer_headers,
        json={
            "sample_id": data["samples"]["s4"].id,
            "item": "抗压强度（28d）",
            "standard_value": 30.0,
            "measured_value": 29.0,
            "unit": "MPa",
        },
    )
    record_id = created.json()["data"]["id"]
    assert created.json()["data"]["conclusion"] == "FAIL"

    updated = client.put(
        f"/api/test-records/{record_id}",
        headers=engineer_headers,
        json={"measured_value": 31.0, "remark": "复检合格"},
    )
    body = updated.json()
    assert updated.status_code == 200
    assert body["data"]["conclusion"] == "PASS"
    assert body["data"]["remark"] == "复检合格"


def test_list_records_filter_conclusion(client, viewer_headers):
    response = client.get("/api/test-records?conclusion=FAIL", headers=viewer_headers)
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["total"] == 2
    assert all(item["conclusion"] == "FAIL" for item in body["data"]["items"])


def test_viewer_cannot_create_record(client, viewer_headers, data):
    response = client.post(
        "/api/test-records",
        headers=viewer_headers,
        json={
            "sample_id": data["samples"]["s1"].id,
            "item": "抗压强度",
            "standard_value": 30.0,
            "measured_value": 31.0,
            "unit": "MPa",
        },
    )
    body = response.json()
    assert response.status_code == 403
    assert body["code"] == 40301
