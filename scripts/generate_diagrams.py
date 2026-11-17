"""生成用例图、架构图、UML 类图、程序流程图与 ER 图。"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from diagram_lib import (
    ACCENT,
    BG,
    BLUE,
    GOLD,
    GREEN,
    INK,
    LINE,
    MUTED,
    NAVY,
    NAVY_LIGHT,
    RED,
    SOFT_BLUE,
    SOFT_GOLD,
    SOFT_GREEN,
    SOFT_RED,
    SOFT_TEAL,
    TEAL,
    WHITE,
    actor,
    add_title,
    arrow,
    diamond,
    new_canvas,
    rounded_box,
    save,
    use_case,
)


def diagram_use_case():
    fig, ax = new_canvas(160, 100)
    add_title(
        ax,
        "REQUIREMENTS · USE CASE",
        "系统用例图",
        "筑测云 · 工程检测数据管理平台 / 角色：检测工程师、管理员、查阅人员",
    )

    boundary = FancyBboxPatch(
        (34, 12),
        94,
        68,
        boxstyle="round,pad=0,rounding_size=1.6",
        facecolor=SOFT_BLUE,
        edgecolor=BLUE,
        linewidth=1.2,
        alpha=0.34,
        zorder=1,
    )
    ax.add_patch(boundary)
    ax.text(81, 76.2, "筑测云 · 工程检测数据管理平台", fontsize=10, color=NAVY, fontweight="bold", ha="center", zorder=5)
    ax.plot([64, 98], [74.7, 74.7], color=BLUE, lw=0.7, alpha=0.5, zorder=2)

    cases = {
        "login": (51, 68, "登录认证", SOFT_GOLD, GOLD),
        "project": (81, 68, "工程项目管理", SOFT_BLUE, BLUE),
        "sample": (48, 57, "样品登记", SOFT_TEAL, TEAL),
        "record": (74, 57, "检测数据录入", SOFT_TEAL, TEAL),
        "judge": (103, 57, "结果自动判定", SOFT_GREEN, GREEN),
        "dashboard": (48, 44, "数据看板", SOFT_BLUE, BLUE),
        "ai": (74, 44, "AI 协作监管", SOFT_GOLD, GOLD),
        "defect": (103, 44, "缺陷与可靠性分析", SOFT_RED, RED),
        "users": (89, 29, "用户与权限管理", SOFT_BLUE, BLUE),
        "read": (48, 29, "基础数据查阅", SOFT_TEAL, TEAL),
    }
    for x, y, label, fc, ec in cases.values():
        use_case(ax, x, y, label, w=25, h=8, fc=fc, ec=ec)

    actor(ax, 15, 57, "检测工程师", color=NAVY, scale=0.92)
    actor(ax, 15, 25, "查阅人员", color=TEAL, scale=0.92)
    actor(ax, 145, 58, "管理员", color=ACCENT, scale=0.92)

    def connect(actor_pos, case_key, color, side="left"):
        case_x, case_y = cases[case_key][0], cases[case_key][1]
        edge_x = case_x - 12.5 if side == "left" else case_x + 12.5
        ax.plot(
            [actor_pos[0] + (2 if side == "left" else -2), edge_x],
            [actor_pos[1] + 6, case_y],
            color=color,
            lw=0.65,
            alpha=0.30,
            zorder=1.8,
        )

    engineer_pos = (15, 57)
    for key in ["login", "project", "sample", "record", "dashboard", "ai"]:
        connect(engineer_pos, key, NAVY, side="left")
    viewer_pos = (15, 25)
    for key in ["login", "dashboard", "ai", "read"]:
        connect(viewer_pos, key, TEAL, side="left")
    admin_pos = (145, 58)
    for key in ["project", "users", "defect"]:
        connect(admin_pos, key, ACCENT, side="right")

    arrow(ax, (86.5, 57), (90.5, 57), color=TEAL, lw=0.9, ls="--", style="-|>", mutation=8, label="«include»", label_offset=(0, 1.6), label_fs=6.5)
    arrow(ax, (86.5, 44), (90.5, 44), color=GOLD, lw=0.9, ls="--", style="-|>", mutation=8, label="«include»", label_offset=(0, 1.6), label_fs=6.5)

    ax.text(34, 6.2, "实线：参与者与用例的关联    虚线：«include» 包含关系", fontsize=7.3, color=MUTED, ha="left")
    ax.text(34, 3.2, "注：所有角色均需登录认证；管理员与检测工程师共享项目、看板与 AI 监管能力，图中仅画主要差异。", fontsize=6.8, color=MUTED, ha="left")
    save(fig, "02_use_case")


def diagram_architecture():
    fig, ax = new_canvas(160, 100)
    add_title(
        ax,
        "ARCHITECTURE · LAYERED",
        "系统总体架构图",
        "前后端分离 · 单进程演示部署 · 分层解耦 · AI 协作监管内嵌",
    )

    layers = [
        ("用户层", 72, 10, NAVY, WHITE, "Web 浏览器（桌面 / 移动端）· 单页应用入口"),
        ("表现层", 59, 10, BLUE, WHITE, "Vue 3 SPA  |  Element Plus  |  ECharts  |  Axios 拦截器（JWT / 错误码）"),
        ("接口层", 46, 10, TEAL, WHITE, "FastAPI Routers（自动发现）  |  JWT + RBAC  |  统一响应 {code,message,data}  |  全局异常处理"),
        ("业务层", 28, 16, GOLD, WHITE, ""),
        ("数据层", 13, 10, ACCENT, WHITE, "SQLAlchemy 2.0 ORM  |  Alembic 版本迁移  |  SQLite app.db（可替换 PostgreSQL）"),
    ]
    for name, y, h, color, text_color, content in layers:
        tag = FancyBboxPatch(
            (9, y),
            18,
            h,
            boxstyle="round,pad=0,rounding_size=1.0",
            facecolor=color,
            edgecolor="none",
            zorder=3,
        )
        ax.add_patch(tag)
        ax.text(18, y + h / 2, name, fontsize=8.8, color=text_color, fontweight="bold", ha="center", va="center", zorder=4)
        rounded_box(ax, 27, y, 95, h, fc=WHITE, ec=LINE, lw=0.9)
        if content:
            ax.text(31, y + h / 2, content, fontsize=7.4 if name != "表现层" else 7.3, color="#36454f", ha="left", va="center", zorder=4)

    modules = ["认证", "用户", "项目", "样品", "检测记录", "看板", "AI 监管"]
    module_width = 11.6
    for index, module in enumerate(modules):
        x = 30 + index * (module_width + 0.9)
        rounded_box(
            ax, x, 31.2, module_width, 9.6,
            heading=module, fc=SOFT_GOLD if module == "AI 监管" else SOFT_BLUE,
            ec=GOLD if module == "AI 监管" else BLUE, heading_fs=7.4, lw=0.8, zorder=4,
        )

    for y1, y2 in [(72, 69), (59, 56), (46, 44), (28, 23)]:
        arrow(ax, (61, y1), (61, y2), color=NAVY_LIGHT, lw=1.0, mutation=8)
        arrow(ax, (93, y2), (93, y1), color=MUTED, lw=0.8, ls="--", mutation=7)

    ax.text(62.2, 70.6, "HTTP", fontsize=6.8, color=MUTED, va="center")
    ax.text(62.2, 57.6, "REST / JSON", fontsize=6.8, color=MUTED, va="center")
    ax.text(62.2, 45.0, "Service 调用", fontsize=6.8, color=MUTED, va="center")
    ax.text(62.2, 25.6, "ORM / 事务", fontsize=6.8, color=MUTED, va="center")
    ax.text(94.2, 70.6, "统一响应", fontsize=6.4, color=MUTED, va="center")

    rounded_box(
        ax, 127, 56, 27, 26,
        heading="质量保障",
        lines=[
            "pytest：56 个用例全通过",
            "语句覆盖率：88%",
            "Edge E2E：12 张截图",
            "图表脚本：PNG + SVG",
            "Alembic：版本化迁移",
        ],
        fc=SOFT_GREEN, ec="#cfe5d9", heading_color=GREEN, accent=GREEN, align="left", body_fs=7.0, lw=0.9,
    )
    rounded_box(
        ax, 127, 22, 27, 30,
        heading="AI 治理",
        lines=[
            "L1 / L2 / L3 分级",
            "五维失效评分 FS",
            "可靠性：85.3 / 100",
            "高失效任务：4 项",
            "缺陷帕累托：68 次",
            "人工介入：910 分钟",
        ],
        fc=SOFT_GOLD, ec="#efdfbc", heading_color="#8a641c", accent=GOLD, align="left", body_fs=7.0, lw=0.9,
    )
    arrow(ax, (127, 69), (122.5, 69), color=GREEN, lw=0.9, ls="--", mutation=7)
    arrow(ax, (127, 37), (122.5, 37), color=GOLD, lw=0.9, ls="--", mutation=7)

    ax.text(9, 8.2, "部署形态：uvicorn 单进程，FastAPI 同时托管 API 与 Vue 构建产物；开发期 Vite 代理 /api。", fontsize=7.5, color=MUTED)
    ax.text(9, 4.6, "安全边界：JWT 无状态认证、角色最小权限、SQLite 外键约束开启、数据库文件位于 backend/data。", fontsize=7.5, color=MUTED)
    save(fig, "03_architecture")


def diagram_class():
    fig, ax = new_canvas(150, 105)
    add_title(
        ax,
        "DETAILED DESIGN · UML CLASS",
        "领域模型 UML 类图",
        "实体关系：Project 1—* Sample 1—* TestRecord；User 1—* TestRecord",
        y=99.5,
    )

    boxes = {
        "User": (
            5, 59, 41, 25, BLUE, SOFT_BLUE,
            ["PK  id: int", "UQ  username: str", "      display_name: str", "      role: Role", "      is_active: bool", "      last_login_at: datetime"],
        ),
        "Project": (
            5, 31, 41, 24, NAVY_LIGHT, SOFT_BLUE,
            ["PK  id: int", "UQ  code: str", "      name / client", "      location", "      status: ProjectStatus", "      start_date / end_date", "      manager"],
        ),
        "Sample": (
            5, 3, 41, 24, TEAL, SOFT_TEAL,
            ["PK  id: int", "UQ  code: str", "FK  project_id → projects.id", "      type: SampleType", "      spec / quantity", "      status / produced_on"],
        ),
        "TestRecord": (
            51, 59, 41, 25, TEAL, SOFT_TEAL,
            ["PK  id: int", "FK  sample_id → samples.id", "FK  tested_by → users.id", "      item / unit", "      standard_value / measured_value", "      rule: GTE | LTE", "      conclusion: PASS | FAIL", "      tested_at"],
        ),
        "AiTask": (
            51, 31, 41, 24, GOLD, SOFT_GOLD,
            ["PK  id: int", "      phase / task_name", "      level: L1 | L2 | L3", "      status: SUCCESS / PARTIAL / FAILED", "      C / I / R / M / S: 0–5", "      failure_score: float", "      human_minutes / retries"],
        ),
        "Defect": (
            51, 3, 41, 24, ACCENT, SOFT_RED,
            ["PK  id: int", "      title / category", "      phase / severity", "      occurrences: int", "      ai_related: bool", "      status: OPEN | FIXED", "      root_cause / fix_action"],
        ),
    }
    for name, (x, y, w, h, color, fc, lines) in boxes.items():
        rounded_box(
            ax, x, y, w, h, heading=name, lines=lines,
            fc=fc, ec=color, heading_color=color, accent=color, align="left",
            heading_fs=9.2, body_fs=6.55, lw=1.0,
        )

    arrow(ax, (46, 71.5), (51, 71.5), color=NAVY_LIGHT, lw=1.1, style="-", mutation=1)
    ax.text(47.2, 73.2, "1", fontsize=6.2, color=MUTED, ha="center")
    ax.text(49.8, 73.2, "N", fontsize=6.2, color=MUTED, ha="center")

    ax.plot([25.5, 25.5], [31, 27], color=NAVY_LIGHT, lw=1.1, zorder=2)
    ax.text(26.3, 29.2, "1..*", fontsize=6.3, color=MUTED, ha="left")

    ax.plot([46, 48.7, 48.7, 51], [27, 27, 59, 59], color=NAVY_LIGHT, lw=1.0, zorder=2)
    arrow(ax, (48.7, 59), (51, 59), color=NAVY_LIGHT, lw=1.0, style="-|>", mutation=7)
    ax.text(48.9, 43, "1..*", fontsize=6.3, color=MUTED, rotation=90, va="center", ha="center", bbox=dict(facecolor=BG, edgecolor="none", pad=0.6))

    enum_lines = [
        "Role",
        "  ADMIN · ENGINEER · VIEWER",
        "ProjectStatus",
        "  PLANNING · IN_PROGRESS",
        "  ACCEPTED · ARCHIVED",
        "SampleType",
        "  CONCRETE · STEEL · SOIL",
        "  MORTAR · ASPHALT",
        "SampleStatus",
        "  PENDING · TESTING · DONE",
        "TestConclusion",
        "  PASS · FAIL",
        "AiLevel / AiTaskStatus",
        "  L1 · L2 · L3",
        "  SUCCESS · PARTIAL · FAILED",
        "AiPhase",
        "  6 个软件工程阶段",
        "DefectSeverity",
        "  CRITICAL · MAJOR · MINOR",
        "  TRIVIAL",
        "DefectStatus",
        "  OPEN · FIXED",
    ]
    rounded_box(
        ax, 97, 3, 46, 81, heading="枚举类型 Enums", lines=enum_lines,
        fc="#faf8f1", ec=LINE, heading_color=NAVY, accent=GOLD, align="left",
        heading_fs=9.0, body_fs=6.2, lw=1.0,
    )
    ax.text(120, 6.5, "枚举字段由各实体引用", fontsize=6.2, color=MUTED, ha="center")
    save(fig, "04_class_diagram")


def diagram_flow():
    fig, ax = new_canvas(150, 126)
    add_title(
        ax,
        "IMPLEMENTATION · PROCESS",
        "检测记录录入与自动判定流程",
        "主流程、鉴权分支、参数异常分支与统一响应",
        y=119.5,
    )

    cx = 56
    bw = 62
    x0 = cx - bw / 2
    steps = [
        ("开始（已登录的检测工程师）", 100, 7, SOFT_BLUE, BLUE, "round"),
        ("选择样品并填写检测项目、标准值、实测值与规则", 88.5, 8.5, SOFT_BLUE, BLUE, "round"),
        ("前端实时预览 GTE / LTE 判定结果", 77.5, 8, SOFT_BLUE, BLUE, "round"),
        ("提交 POST /api/test-records", 66.5, 8, SOFT_BLUE, BLUE, "round"),
    ]
    for text, y, h, fc, ec, _ in steps:
        rounded_box(ax, x0, y - h / 2, bw, h, heading=text, fc=fc, ec=ec, heading_fs=7.4, lw=1.0)

    diamond(ax, cx, 55, 46, 9.5, "JWT 有效且角色允许？", fc=SOFT_GOLD, ec=GOLD, fontsize=7.0)
    diamond(ax, cx, 42, 46, 9.5, "样品存在且参数合法？", fc=SOFT_GOLD, ec=GOLD, fontsize=7.0)

    rounded_box(ax, x0, 24.5, bw, 9.5, heading="保留两位小数比较 → 生成 PASS / FAIL", fc=SOFT_GREEN, ec=GREEN, heading_color=GREEN, heading_fs=7.4, lw=1.0)
    rounded_box(ax, x0, 14, bw, 8.5, heading="保存记录，样品状态置为 DONE", fc=SOFT_GREEN, ec=GREEN, heading_color=GREEN, heading_fs=7.4, lw=1.0)
    rounded_box(ax, cx - 20, 4.5, 40, 6.5, heading="结束：返回统一响应并刷新看板", fc=SOFT_GREEN, ec=GREEN, heading_color=GREEN, heading_fs=7.2, lw=1.0)

    spine = [(cx, 96.5), (cx, 92.8), (cx, 81.8), (cx, 70.5), (cx, 59.8), (cx, 46.8), (cx, 34.0), (cx, 22.5), (cx, 11.0)]
    for start, end in zip(spine[:-1], spine[1:]):
        arrow(ax, start, end, color=NAVY_LIGHT, lw=1.05, mutation=8)

    ax.text(cx - 2.0, 62.0, "是", fontsize=6.6, color=GREEN)
    ax.text(cx - 2.0, 48.5, "是", fontsize=6.6, color=GREEN)

    arrow(ax, (79, 55), (104, 55), color=RED, lw=0.9, mutation=7, label="否", label_offset=(0, 1.2), label_color=RED)
    arrow(ax, (79, 42), (104, 42), color=RED, lw=0.9, mutation=7, label="否", label_offset=(0, 1.2), label_color=RED)

    rounded_box(ax, 104, 50.5, 40, 9, heading="401 / 403", lines=["未登录或无权限"], fc=SOFT_RED, ec=RED, heading_color=RED, heading_fs=8.2, body_fs=6.8, lw=0.9)
    rounded_box(ax, 104, 37.5, 40, 9, heading="400 / 422", lines=["关联缺失或参数校验失败"], fc=SOFT_RED, ec=RED, heading_color=RED, heading_fs=8.2, body_fs=6.8, lw=0.9)
    ax.text(104, 28.5, "注：两类异常均返回统一响应包 {code, message, data}，\n前端拦截器负责提示并清理失效令牌。", fontsize=6.8, color=MUTED, ha="left", va="top", linespacing=1.6)
    ax.text(9, 2.2, "判定算法：round(实测值, 2) 与 round(标准值, 2) 比较；GTE 为达标下限，LTE 为上限控制。", fontsize=7.0, color=MUTED)
    save(fig, "05_program_flowchart")


def diagram_er():
    fig, ax = new_canvas(160, 100)
    add_title(
        ax,
        "DETAILED DESIGN · ER",
        "物理数据模型（ER 图）",
        "SQLite（app.db）· Alembic 迁移 · 外键 ON DELETE RESTRICT",
    )

    tables = {
        "users · 用户表": (
            6, 55, 44, 27, BLUE, SOFT_BLUE,
            ["PK  id INTEGER", "UQ  username VARCHAR(50)", "      password_hash VARCHAR(255)", "      display_name / role", "      is_active / last_login_at", "      created_at / updated_at"],
        ),
        "projects · 项目表": (
            58, 55, 44, 27, NAVY_LIGHT, SOFT_BLUE,
            ["PK  id INTEGER", "UQ  code VARCHAR(40)", "      name / client", "      location / manager", "      status VARCHAR(20)", "      start_date / end_date", "      created_at / updated_at"],
        ),
        "samples · 样品表": (
            110, 55, 44, 27, TEAL, SOFT_TEAL,
            ["PK  id INTEGER", "UQ  code VARCHAR(40)", "FK  project_id → projects.id", "      type VARCHAR(20)", "      spec / quantity", "      status / produced_on", "      created_at / updated_at"],
        ),
        "test_records · 检测记录表": (
            6, 8, 50, 30, TEAL, SOFT_TEAL,
            ["PK  id INTEGER", "FK  sample_id → samples.id", "FK  tested_by → users.id", "      item / unit", "      standard_value / measured_value", "      rule / conclusion", "      tested_at / remark", "      created_at / updated_at"],
        ),
        "ai_tasks · AI 任务表": (
            64, 8, 44, 30, GOLD, SOFT_GOLD,
            ["PK  id INTEGER", "      phase / task_name", "      level / agent_name / status", "      C / I / R / M / S INTEGER", "      failure_score FLOAT", "      human_minutes / retries", "      occurred_at / notes", "      created_at / updated_at"],
        ),
        "defects · 缺陷表": (
            116, 8, 38, 30, ACCENT, SOFT_RED,
            ["PK  id INTEGER", "      title / category", "      phase / severity", "      occurrences / ai_related", "      status / found_at", "      root_cause / fix_action", "      created_at / updated_at"],
        ),
    }
    for name, (x, y, w, h, color, fc, lines) in tables.items():
        rounded_box(
            ax, x, y, w, h, heading=name, lines=lines,
            fc=fc, ec=color, heading_color=color, accent=color, align="left",
            heading_fs=8.1, body_fs=6.4, lw=0.95,
        )

    def cardinality(x, y, label):
        ax.text(x, y, label, fontsize=6.8, color=MUTED, ha="center", va="center", bbox=dict(facecolor=BG, edgecolor="none", pad=0.8))

    ax.plot([102, 110], [68.5, 68.5], color=NAVY_LIGHT, lw=1.0, zorder=2)
    arrow(ax, (106, 68.5), (110, 68.5), color=NAVY_LIGHT, lw=1.0, style="-|>", mutation=6)
    cardinality(103.5, 70.4, "1")
    cardinality(108.5, 70.4, "N")

    ax.plot([132, 132, 56, 56], [55, 47, 47, 38], color=TEAL, lw=1.0, zorder=2)
    arrow(ax, (56, 43), (56, 38), color=TEAL, lw=1.0, style="-|>", mutation=6)
    cardinality(133.2, 51, "1")
    cardinality(57.2, 41.5, "N")

    ax.plot([28, 28], [55, 38], color=BLUE, lw=1.0, zorder=2)
    arrow(ax, (28, 43), (28, 38), color=BLUE, lw=1.0, style="-|>", mutation=6)
    cardinality(29.2, 51, "1")
    cardinality(29.2, 40.5, "N")

    ax.text(6, 3.2, "PK 主键 · FK 外键 · UQ 唯一约束", fontsize=7.2, color=MUTED)
    ax.text(154, 3.2, "6 张表", fontsize=7.2, color=MUTED, ha="right")
    save(fig, "07_er_diagram")


if __name__ == "__main__":
    diagram_use_case()
    diagram_architecture()
    diagram_class()
    diagram_flow()
    diagram_er()
