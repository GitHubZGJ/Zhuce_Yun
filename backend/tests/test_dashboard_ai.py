import pytest

from app.modules.ai_ops.service import compute_failure_score


def test_dashboard_summary(client, viewer_headers):
    response = client.get("/api/dashboard/overview", headers=viewer_headers)
    body = response.json()
    assert response.status_code == 200
    summary = body["data"]["summary"]
    assert summary["project_total"] == 3
    assert summary["active_projects"] == 1
    assert summary["sample_total"] == 4
    assert summary["pending_samples"] == 1
    assert summary["test_total"] == 8
    assert summary["pass_total"] == 6
    assert summary["pass_rate"] == 75.0
    assert summary["open_defect_occurrences"] == 1
    assert summary["task_count"] == 6
    assert summary["avg_failure_score"] == 20.5
    assert summary["success_rate"] == 66.7
    assert summary["reliability"] == 74.4
    assert summary["high_failure_count"] == 2


def test_dashboard_charts(client, viewer_headers):
    data = client.get("/api/dashboard/overview", headers=viewer_headers).json()["data"]

    assert sum(item["count"] for item in data["project_status"]) == 3
    assert sum(item["count"] for item in data["sample_types"]) == 4
    concrete = next(item for item in data["sample_types"] if item["type"] == "CONCRETE")
    assert concrete["count"] == 2
    assert concrete["label"] == "混凝土试块"

    pass_by_type = {item["type"]: item for item in data["pass_rate_by_type"]}
    assert pass_by_type["CONCRETE"]["total"] == 3
    assert pass_by_type["CONCRETE"]["rate"] == 66.7
    assert pass_by_type["SOIL"]["rate"] == 100.0

    assert len(data["monthly_trend"]) == 6
    assert data["monthly_trend"][-1]["month"] == "2026-11"
    assert data["monthly_trend"][-1]["total"] == 1
    assert len(data["recent_records"]) == 6
    assert data["defect_pareto"][0]["category"] == "需求理解偏差"


def test_ai_stats_formula_and_pareto(client, viewer_headers):
    response = client.get("/api/ai/stats", headers=viewer_headers)
    body = response.json()
    assert response.status_code == 200
    summary = body["data"]["summary"]
    assert summary["task_count"] == 6
    assert summary["avg_failure_score"] == 20.5
    assert summary["success_rate"] == 66.7
    assert summary["reliability"] == 74.4
    assert summary["high_failure_count"] == 2
    assert summary["human_minutes"] == 420
    assert summary["defect_occurrences"] == 18
    assert summary["ai_related_rate"] == 88.9
    assert summary["open_rate"] == 5.6

    assert len(body["data"]["by_phase"]) == 6
    detailed = next(item for item in body["data"]["by_phase"] if item["phase"] == "DETAILED_DESIGN")
    assert detailed["avg_failure_score"] == 42.0
    assert detailed["reliability"] == 34.8

    pareto = body["data"]["pareto"]
    assert pareto[0]["category"] == "需求理解偏差"
    assert pareto[0]["occurrences"] == 11
    assert pareto[0]["cumulative"] == 61.1
    assert pareto[-1]["cumulative"] == 100.0

    assert [item["failure_score"] for item in body["data"]["failure_cases"]] == [63.0, 42.0]
    assert body["data"]["level_distribution"] == [
        {"level": "L1", "count": 3},
        {"level": "L2", "count": 3},
        {"level": "L3", "count": 0},
    ]


@pytest.mark.parametrize(
    "scores, expected",
    [
        ((0, 0, 0, 0, 0), 0.0),
        ((5, 5, 5, 5, 5), 100.0),
        ((3, 2, 2, 1, 2), 42.0),
        ((1, 1, 0, 0, 0), 9.0),
    ],
)
def test_failure_score_formula(scores, expected):
    assert compute_failure_score(*scores) == expected


def test_grading_config(client, viewer_headers):
    body = client.get("/api/ai/grading", headers=viewer_headers).json()["data"]
    assert len(body["levels"]) == 3
    assert [item["code"] for item in body["levels"]] == ["L1", "L2", "L3"]
    assert len(body["table"]) == 6
    assert all({"phase", "l1", "l2", "l3"} <= set(row) for row in body["table"])
    assert len(body["rules"]) == 5
    assert len(body["rubric"]) == 5
    assert sum(item["weight"] for item in body["rubric"]) == 100
    assert len(body["thresholds"]) == 4


def test_create_ai_task_computes_score_and_band(client, admin_headers):
    response = client.post(
        "/api/ai/tasks",
        headers=admin_headers,
        json={
            "phase": "REQUIREMENTS",
            "task_name": "新增评分任务",
            "level": "L2",
            "agent_name": "需求Agent",
            "status": "SUCCESS",
            "correctness": 2,
            "completeness": 2,
            "runnability": 2,
            "maintainability": 2,
            "compliance": 2,
            "human_minutes": 30,
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["failure_score"] == 40.0
    assert body["data"]["failure_band"]["level"] == "HIGH"
    assert body["data"]["reliability"] == 60.0


def test_update_ai_task_rescores(client, admin_headers):
    created = client.post(
        "/api/ai/tasks",
        headers=admin_headers,
        json={
            "phase": "IMPLEMENTATION",
            "task_name": "待修正任务",
            "level": "L1",
            "agent_name": "编码Agent",
            "status": "FAILED",
            "correctness": 5,
            "completeness": 5,
            "runnability": 5,
            "maintainability": 5,
            "compliance": 5,
        },
    )
    task_id = created.json()["data"]["id"]
    assert created.json()["data"]["failure_score"] == 100.0

    updated = client.put(
        f"/api/ai/tasks/{task_id}",
        headers=admin_headers,
        json={
            "status": "SUCCESS",
            "correctness": 0,
            "completeness": 0,
            "runnability": 0,
            "maintainability": 0,
            "compliance": 0,
        },
    )
    body = updated.json()
    assert body["data"]["failure_score"] == 0.0
    assert body["data"]["failure_band"]["level"] == "LOW"


def test_ai_task_permissions_and_filters(client, engineer_headers, viewer_headers):
    denied = client.post(
        "/api/ai/tasks",
        headers=engineer_headers,
        json={
            "phase": "IMPLEMENTATION",
            "task_name": "越权任务",
            "level": "L1",
            "agent_name": "编码Agent",
            "status": "SUCCESS",
            "correctness": 0,
            "completeness": 0,
            "runnability": 0,
            "maintainability": 0,
            "compliance": 0,
        },
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == 40301

    filtered = client.get("/api/ai/tasks?level=L2", headers=viewer_headers).json()
    assert filtered["data"]["total"] == 3
    assert all(item["level"] == "L2" for item in filtered["data"]["items"])


def test_create_defect_and_pareto_updates(client, admin_headers):
    response = client.post(
        "/api/ai/defects",
        headers=admin_headers,
        json={
            "title": "部署端口冲突",
            "phase": "IMPLEMENTATION",
            "category": "部署配置错误",
            "severity": "MAJOR",
            "occurrences": 3,
            "ai_related": True,
            "status": "OPEN",
            "root_cause": "端口硬编码",
            "fix_action": "改为配置项",
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["data"]["category"] == "部署配置错误"
    assert body["data"]["occurrences"] == 3

    stats = client.get("/api/ai/stats", headers=admin_headers).json()["data"]
    assert stats["summary"]["defect_occurrences"] == 21
    assert len(stats["pareto"]) == 5
    assert dict((item["category"], item["occurrences"]) for item in stats["pareto"])[
        "部署配置错误"
    ] == 3


def test_viewer_cannot_create_defect(client, viewer_headers):
    response = client.post(
        "/api/ai/defects",
        headers=viewer_headers,
        json={
            "title": "越权缺陷",
            "phase": "MAINTENANCE",
            "category": "文案与样式",
            "severity": "TRIVIAL",
            "occurrences": 1,
        },
    )
    assert response.status_code == 403
    assert response.json()["code"] == 40301
