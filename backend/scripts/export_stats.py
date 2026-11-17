"""导出运行中系统的统计快照，供图表与文档引用。"""
import json
import sys
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)
login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
login.raise_for_status()
token = login.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

snapshot = {
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "dashboard": client.get("/api/dashboard/overview", headers=headers).json()["data"],
    "ai_stats": client.get("/api/ai/stats", headers=headers).json()["data"],
    "grading": client.get("/api/ai/grading", headers=headers).json()["data"],
}

out = ROOT_DIR / "evidence" / "api_snapshot.json"
out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

summary = snapshot["dashboard"]["summary"]
ai = snapshot["ai_stats"]["summary"]
print("统计快照已写入", out)
print("项目/样品/记录:", summary["project_total"], summary["sample_total"], summary["test_total"])
print("合格:", summary["pass_total"], f'{summary["pass_rate"]}%')
print("AI 任务:", ai["task_count"], "平均失效分:", ai["avg_failure_score"], "可靠性:", ai["reliability"])
print("缺陷:", ai["defect_records"], "条 /", ai["defect_occurrences"], "次；AI 相关:", ai["ai_related_rate"], "%")
