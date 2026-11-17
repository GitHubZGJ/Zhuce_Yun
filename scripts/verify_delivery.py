"""交付前自动核验：文件、数据库、统计口径、测试与文档链接。"""

import json
import re
import sqlite3
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
checks = []


def check(name, condition, detail=""):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    print(("PASS " if condition else "FAIL ") + name + (f" :: {detail}" if detail else ""))


def main():
    required = [
        "README.md",
        "backend/app/main.py",
        "backend/data/app.db",
        "backend/seed.py",
        "backend/requirements.txt",
        "backend/tests/conftest.py",
        "frontend/package.json",
        "frontend/src/main.js",
        "frontend/e2e/ui-check.mjs",
        "scripts/start.bat",
        "scripts/stop.bat",
        "scripts/start_server.ps1",
        "scripts/stop_server.ps1",
        "scripts/generate_charts.py",
        "scripts/generate_diagrams.py",
        "scripts/build_report.py",
        "scripts/render_report.py",
        "deliverable/学号-班级-姓名.docx",
        "deliverable/学号-班级-姓名.pdf",
        "evidence/api_snapshot.json",
        "evidence/pytest_full.txt",
        "evidence/ui/e2e_result.json",
        "evidence/ui/e2e_summary.txt",
        "evidence/report_render.json",
        "evidence/tests/term_pytest.png",
        "evidence/tests/term_coverage.png",
        "evidence/tests/func_01_project_create.png",
        "evidence/tests/func_02_record_create_pass.png",
        "evidence/tests/func_03_viewer_readonly.png",
    ]
    for rel in required:
        check(f"文件存在：{rel}", (ROOT / rel).exists(), rel)

    diagrams = [
        "01_feasibility_radar", "02_use_case", "03_architecture", "04_class_diagram",
        "05_program_flowchart", "06_defect_pareto", "07_er_diagram", "08_ai_reliability",
    ]
    for diagram in diagrams:
        check(f"图表 PNG：{diagram}", (ROOT / "diagrams" / f"{diagram}.png").exists())
        check(f"图表 SVG：{diagram}", (ROOT / "diagrams" / f"{diagram}.svg").exists())

    docs = [
        "00_摘要与项目概述.md", "01_可行性分析报告.md", "02_需求规格说明书.md",
        "03_总体设计说明书.md", "04_详细设计说明书.md", "05_实现与测试说明.md",
        "06_维护与Agent失效复盘.md", "07_AI分级机制表.md", "08_评级监管设计说明.md",
        "09_演示与答辩脚本.md", "10_交付物清单.md", "99_项目实施方案.md",
    ]
    for doc in docs:
        check(f"文档：{doc}", (ROOT / "docs" / doc).exists())

    db_path = ROOT / "backend" / "data" / "app.db"
    with sqlite3.connect(db_path) as conn:
        tables = {
            "users": 4, "projects": 6, "samples": 24,
            "test_records": 60, "ai_tasks": 24, "defects": 25,
        }
        for table, expected in tables.items():
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            check(f"数据库行数 {table}", count == expected, f"{count} / 期望 {expected}")
        occurrences = conn.execute("SELECT COALESCE(SUM(occurrences), 0) FROM defects").fetchone()[0]
        check("缺陷累计发生 68 次", occurrences == 68, str(occurrences))
        open_occurrences = conn.execute("SELECT COALESCE(SUM(occurrences), 0) FROM defects WHERE status='OPEN'").fetchone()[0]
        check("待修复 12 次", open_occurrences == 12, str(open_occurrences))

    snapshot = json.loads((ROOT / "evidence" / "api_snapshot.json").read_text(encoding="utf-8"))
    summary = snapshot["ai_stats"]["summary"]
    check("可靠性 85.3", summary["reliability"] == 85.3, str(summary["reliability"]))
    check("平均失效分 13.4", summary["avg_failure_score"] == 13.4, str(summary["avg_failure_score"]))
    check("高失效任务 4 项", summary["high_failure_count"] == 4, str(summary["high_failure_count"]))
    check("帕累托前四类 76.5%", snapshot["ai_stats"]["pareto"][3]["cumulative"] == 76.5)
    check("检测记录 60 条", snapshot["dashboard"]["summary"]["test_total"] == 60)
    check("合格率 85.0%", snapshot["dashboard"]["summary"]["pass_rate"] == 85.0)

    pytest_text = (ROOT / "evidence" / "pytest_full.txt").read_text(encoding="utf-8", errors="ignore")
    check("pytest 56 passed", "56 passed" in pytest_text)
    check("覆盖率 88%", "88%" in pytest_text)

    e2e = json.loads((ROOT / "evidence" / "ui" / "e2e_result.json").read_text(encoding="utf-8"))
    check("E2E 状态通过", e2e.get("status") == "passed")
    check("E2E 12 张截图", len(e2e.get("steps", [])) == 12, str(len(e2e.get("steps", []))))
    check("E2E 无控制台错误", not e2e.get("consoleErrors"))
    check("E2E 无 API 错误", not e2e.get("apiErrors"))

    report = Document(ROOT / "deliverable" / "学号-班级-姓名.docx")
    check("Word 图片 22 张", len(report.inline_shapes) == 22, str(len(report.inline_shapes)))
    check("Word 表格 ≥ 90", len(report.tables) >= 90, str(len(report.tables)))
    check("Word 双节（封面+正文）", len(report.sections) == 2, str(len(report.sections)))
    cover_text = "\n".join(p.text for p in report.paragraphs[:40])
    check("报告第一页含仓库链接", "github.com/GitHubZGJ/Zhuce_Yun" in cover_text)
    pdf_size = (ROOT / "deliverable" / "学号-班级-姓名.pdf").stat().st_size
    check("PDF 体积 > 1 MB", pdf_size > 1_000_000, f"{pdf_size} bytes")
    render = json.loads((ROOT / "evidence" / "report_render.json").read_text(encoding="utf-8"))
    check("Word/PDF 页数 ≥ 50", render["pages"] >= 50, str(render["pages"]))

    md_files = [ROOT / "README.md"] + list((ROOT / "docs").glob("*.md"))
    broken = []
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        for match in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path = (md.parent / target).resolve()
            if not path.exists():
                broken.append(f"{md.relative_to(ROOT)} -> {target}")
    check("Markdown 相对链接完整", not broken, "; ".join(broken[:5]))

    passed = all(item["passed"] for item in checks)
    output = {"passed": passed, "total": len(checks), "failed": [item for item in checks if not item["passed"]], "checks": checks}
    (ROOT / "evidence" / "delivery_check.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n{'ALL CHECKS PASSED' if passed else 'CHECKS FAILED'} :: {len(checks)} items")
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
