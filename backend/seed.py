"""初始化演示数据：python seed.py --reset

数据规模固定，供页面、图表与文档统一引用：
- 4 个账号、6 个项目、24 个样品、60 条检测记录
- 24 条 AI 任务、25 条缺陷记录（累计发生 68 次）
"""

import argparse
from datetime import date, datetime, time, timedelta
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import delete, func, select  # noqa: E402

from app.core.enums import (  # noqa: E402
    AiLevel,
    AiPhase,
    AiTaskStatus,
    DefectSeverity,
    DefectStatus,
    ProjectStatus,
    SampleStatus,
    SampleType,
    Role,
    TestRule,
)
from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.modules import import_all_models  # noqa: E402
from app.modules.ai_ops.models import AiTask, Defect  # noqa: E402
from app.modules.ai_ops.service import compute_failure_score  # noqa: E402
from app.modules.projects.models import Project  # noqa: E402
from app.modules.samples.models import Sample  # noqa: E402
from app.modules.test_records.models import TestRecord  # noqa: E402
from app.modules.test_records.service import judge  # noqa: E402
from app.modules.users.models import User  # noqa: E402

PROJECTS = [
    {
        "code": "XM-2026-001",
        "name": "滨江路综合管廊基坑工程",
        "client": "滨江市城建集团",
        "location": "滨江市江北新区",
        "status": ProjectStatus.IN_PROGRESS,
        "start_date": date(2026, 3, 1),
        "end_date": date(2026, 12, 30),
        "manager": "李建国",
        "description": "综合管廊基坑支护与回填质量检测，重点关注混凝土强度与土方压实度。",
    },
    {
        "code": "XM-2026-002",
        "name": "城北中学教学楼改扩建",
        "client": "城北区教育局",
        "location": "城北市育才路",
        "status": ProjectStatus.IN_PROGRESS,
        "start_date": date(2026, 4, 15),
        "end_date": date(2026, 11, 30),
        "manager": "赵实验",
        "description": "教学楼主体结构施工阶段材料检测，含混凝土、钢筋、砂浆与回填土。",
    },
    {
        "code": "XM-2026-003",
        "name": "高新区人才公寓一期",
        "client": "高新区建设投资有限公司",
        "location": "高新区科创大道",
        "status": ProjectStatus.PLANNING,
        "start_date": date(2026, 12, 1),
        "end_date": date(2027, 10, 30),
        "manager": "周海峰",
        "description": "筹备阶段项目，已完成样品登记，待开工后开展检测。",
    },
    {
        "code": "XM-2025-018",
        "name": "跨江大桥引桥段",
        "client": "市交通建设中心",
        "location": "滨江市跨江大桥北引桥",
        "status": ProjectStatus.ACCEPTED,
        "start_date": date(2025, 8, 10),
        "end_date": date(2026, 9, 30),
        "manager": "陈志远",
        "description": "引桥墩身与桥面铺装检测，包含高强混凝土与沥青混合料。",
    },
    {
        "code": "XM-2025-011",
        "name": "地铁 6 号线盾构区间",
        "client": "市轨道交通集团",
        "location": "滨江市地铁 6 号线",
        "status": ProjectStatus.ACCEPTED,
        "start_date": date(2025, 5, 1),
        "end_date": date(2026, 8, 30),
        "manager": "孙立新",
        "description": "盾构管片混凝土与同步注浆材料检测，重点关注强度与压实质量。",
    },
    {
        "code": "XM-2025-007",
        "name": "老城区雨污分流改造",
        "client": "市水务集团",
        "location": "滨江市老城区",
        "status": ProjectStatus.ARCHIVED,
        "start_date": date(2025, 3, 1),
        "end_date": date(2026, 10, 20),
        "manager": "吴敏",
        "description": "管网改造回填与路面恢复检测，项目已完成归档。",
    },
]

# code, project_code, type, spec, produced_on, quantity
SAMPLES = [
    ("YP-260301", "XM-2026-001", SampleType.CONCRETE, "C30 150×150×150mm", date(2026, 4, 10), 3),
    ("YP-260302", "XM-2026-001", SampleType.CONCRETE, "C35 150×150×150mm", date(2026, 4, 18), 3),
    ("YP-260303", "XM-2026-001", SampleType.STEEL, "HRB400E Φ20", date(2026, 4, 20), 5),
    ("YP-260304", "XM-2026-001", SampleType.SOIL, "回填土 环刀法 压实度≥93%", date(2026, 4, 22), 1),
    ("YP-260305", "XM-2026-001", SampleType.SOIL, "回填土 环刀法 压实度≥95%", date(2026, 5, 2), 1),
    ("YP-260401", "XM-2026-002", SampleType.CONCRETE, "C30 150×150×150mm", date(2026, 5, 6), 3),
    ("YP-260402", "XM-2026-002", SampleType.CONCRETE, "C40 150×150×150mm", date(2026, 5, 9), 3),
    ("YP-260403", "XM-2026-002", SampleType.STEEL, "HRB400E Φ22", date(2026, 5, 12), 5),
    ("YP-260404", "XM-2026-002", SampleType.MORTAR, "M10 70.7×70.7×70.7mm", date(2026, 5, 15), 6),
    ("YP-260405", "XM-2026-002", SampleType.SOIL, "回填土 环刀法 压实度≥95%", date(2026, 5, 18), 1),
    ("YP-260501", "XM-2026-003", SampleType.CONCRETE, "C35 150×150×150mm", date(2026, 10, 20), 3),
    ("YP-260502", "XM-2026-003", SampleType.STEEL, "HRB400E Φ25", date(2026, 10, 21), 5),
    ("YP-250601", "XM-2025-018", SampleType.CONCRETE, "C40 150×150×150mm", date(2026, 3, 3), 3),
    ("YP-250602", "XM-2025-018", SampleType.CONCRETE, "C40 150×150×150mm", date(2026, 3, 5), 3),
    ("YP-250603", "XM-2025-018", SampleType.STEEL, "HRB400E Φ25", date(2026, 3, 8), 5),
    ("YP-250604", "XM-2025-018", SampleType.ASPHALT, "AC-13 马歇尔试件", date(2026, 3, 10), 4),
    ("YP-250701", "XM-2025-011", SampleType.CONCRETE, "C35 150×150×150mm", date(2026, 2, 6), 3),
    ("YP-250702", "XM-2025-011", SampleType.CONCRETE, "C35 150×150×150mm", date(2026, 2, 8), 3),
    ("YP-250703", "XM-2025-011", SampleType.SOIL, "回填土 环刀法 压实度≥93%", date(2026, 2, 10), 1),
    ("YP-250704", "XM-2025-011", SampleType.STEEL, "HRB400E Φ20", date(2026, 2, 12), 5),
    ("YP-260801", "XM-2025-007", SampleType.CONCRETE, "C30 150×150×150mm", date(2026, 4, 2), 3),
    ("YP-260802", "XM-2025-007", SampleType.CONCRETE, "C25 150×150×150mm", date(2026, 4, 3), 3),
    ("YP-260803", "XM-2025-007", SampleType.MORTAR, "M10 70.7×70.7×70.7mm", date(2026, 4, 5), 6),
    ("YP-260804", "XM-2025-007", SampleType.ASPHALT, "AC-13 马歇尔试件", date(2026, 4, 6), 4),
]

NO_TEST_CODES = {"YP-260305", "YP-260405", "YP-260501", "YP-260502"}

AI_TASKS = [
    # phase, task, level, agent, status, c, i, r, m, s, human_minutes, retries, date, notes
    (AiPhase.FEASIBILITY, "五维评分数据汇总与雷达图绘制", AiLevel.L1, "数据可视化Agent", AiTaskStatus.SUCCESS, 0, 0, 0, 0, 0, 5, 0, "2026-08-03", "按 5 分制汇总，脚本一次运行通过。"),
    (AiPhase.FEASIBILITY, "技术栈可行性检索与对比表", AiLevel.L1, "调研Agent", AiTaskStatus.SUCCESS, 0, 1, 0, 0, 0, 12, 0, "2026-08-04", "补充了 SQLite 与 PostgreSQL 的替换成本说明。"),
    (AiPhase.FEASIBILITY, "成本与工期测算底稿", AiLevel.L2, "文档Agent", AiTaskStatus.SUCCESS, 1, 1, 0, 1, 0, 40, 1, "2026-08-04", "人工校准了人力成本单价。"),
    (AiPhase.FEASIBILITY, "风险清单与应对策略草拟", AiLevel.L2, "文档Agent", AiTaskStatus.SUCCESS, 1, 0, 0, 0, 1, 35, 0, "2026-08-05", "补充数据合规与备份策略。"),
    (AiPhase.REQUIREMENTS, "用户故事与用例清单整理", AiLevel.L1, "需求分析Agent", AiTaskStatus.SUCCESS, 0, 0, 0, 0, 0, 5, 0, "2026-08-10", "按角色分组，编号连续。"),
    (AiPhase.REQUIREMENTS, "用例图初稿生成", AiLevel.L1, "图表Agent", AiTaskStatus.SUCCESS, 1, 0, 0, 0, 0, 8, 0, "2026-08-11", "人工调整了布局与连线。"),
    (AiPhase.REQUIREMENTS, "非功能指标量化表", AiLevel.L2, "需求分析Agent", AiTaskStatus.SUCCESS, 1, 1, 0, 1, 0, 30, 0, "2026-08-12", "响应时间与可用性指标由人确认。"),
    (AiPhase.REQUIREMENTS, "权限边界与验收标准评审", AiLevel.L2, "需求分析Agent", AiTaskStatus.PARTIAL, 3, 2, 2, 1, 2, 95, 2, "2026-08-14", "初稿遗漏查阅人员只读与越权写拦截，人工补入并以 403 用例回归验证。"),
    (AiPhase.ARCHITECTURE, "前后端脚手架与模块自动发现", AiLevel.L1, "编码Agent", AiTaskStatus.SUCCESS, 0, 0, 0, 0, 0, 0, 0, "2026-08-20", "目录结构与路由自动注册可用。"),
    (AiPhase.ARCHITECTURE, "系统架构图初稿", AiLevel.L1, "图表Agent", AiTaskStatus.SUCCESS, 0, 1, 0, 0, 0, 10, 0, "2026-08-21", "人工统一了配色与术语。"),
    (AiPhase.ARCHITECTURE, "数据库模型与迁移脚本", AiLevel.L1, "编码Agent", AiTaskStatus.SUCCESS, 1, 0, 0, 1, 0, 15, 0, "2026-08-22", "外键约束与 SQLite 开关已补全。"),
    (AiPhase.ARCHITECTURE, "JWT/RBAC 方案联调", AiLevel.L2, "编码Agent", AiTaskStatus.SUCCESS, 1, 0, 1, 0, 0, 45, 1, "2026-08-25", "人工补充停用账号拦截。"),
    (AiPhase.DETAILED_DESIGN, "UML 类图与 ER 图初稿", AiLevel.L1, "图表Agent", AiTaskStatus.SUCCESS, 0, 0, 0, 0, 0, 8, 0, "2026-09-01", "类、枚举、关系要素完整。"),
    (AiPhase.DETAILED_DESIGN, "ORM 模型与 Schema 生成", AiLevel.L1, "编码Agent", AiTaskStatus.SUCCESS, 0, 1, 0, 0, 0, 6, 0, "2026-09-02", "人工修正日期字段类型。"),
    (AiPhase.DETAILED_DESIGN, "自动判定算法与边界条件", AiLevel.L2, "编码Agent", AiTaskStatus.SUCCESS, 1, 1, 1, 1, 0, 50, 1, "2026-09-03", "补充两位小数比较，消除浮点边界误差。"),
    (AiPhase.DETAILED_DESIGN, "失效评分权重与阈值设计", AiLevel.L2, "评审Agent", AiTaskStatus.PARTIAL, 3, 3, 2, 3, 2, 110, 2, "2026-09-05", "初版权重和文档口径不一致，人工统一为 25/20/25/15/15。"),
    (AiPhase.IMPLEMENTATION, "CRUD 与页面样板生成", AiLevel.L1, "编码Agent", AiTaskStatus.SUCCESS, 0, 0, 0, 1, 0, 10, 0, "2026-09-15", "分页与筛选逻辑可复用。"),
    (AiPhase.IMPLEMENTATION, "种子数据与图表数据生成", AiLevel.L1, "数据Agent", AiTaskStatus.SUCCESS, 1, 0, 0, 0, 0, 8, 0, "2026-09-18", "固定随机种子，结果可复现。"),
    (AiPhase.IMPLEMENTATION, "前后端联调（检测记录字段）", AiLevel.L2, "编码Agent", AiTaskStatus.PARTIAL, 2, 3, 2, 2, 2, 120, 2, "2026-10-09", "前端字段名与后端 Schema 不一致，人工统一为 snake_case 并由 E2E 回归。"),
    (AiPhase.IMPLEMENTATION, "部署脚本与端口配置", AiLevel.L1, "运维Agent", AiTaskStatus.FAILED, 4, 2, 4, 2, 3, 180, 3, "2026-10-25", "硬编码端口且未检测占用，导致启动失败；人工改为可配置端口并记录真实 PID。"),
    (AiPhase.MAINTENANCE, "缺陷分类与帕累托统计", AiLevel.L1, "数据可视化Agent", AiTaskStatus.SUCCESS, 0, 0, 0, 0, 0, 6, 0, "2026-10-28", "分类与累计占比脚本输出稳定。"),
    (AiPhase.MAINTENANCE, "Agent 失效任务聚类", AiLevel.L1, "评审Agent", AiTaskStatus.SUCCESS, 0, 1, 0, 0, 0, 12, 0, "2026-10-30", "按失效分区间聚类，结果与人工复核一致。"),
    (AiPhase.MAINTENANCE, "回归测试与修复验证", AiLevel.L2, "测试Agent", AiTaskStatus.SUCCESS, 1, 0, 1, 0, 0, 40, 1, "2026-11-02", "补齐负向用例，断言错误码与提示文案。"),
    (AiPhase.MAINTENANCE, "可靠性评级材料汇总", AiLevel.L2, "文档Agent", AiTaskStatus.SUCCESS, 1, 1, 0, 1, 1, 60, 0, "2026-11-04", "与系统统计接口核对后归档。"),
]

DEFECTS = [
    # title, phase, category, severity, occurrences, ai_related, status, found_at, root_cause, fix_action
    ("检测记录自动判定未覆盖 LTE 规则", AiPhase.DETAILED_DESIGN, "需求理解偏差", DefectSeverity.MAJOR, 6, True, DefectStatus.FIXED, "2026-08-14", "Agent 将“达到标准”简单等同于大于等于，遗漏含水率、流值等上限指标。", "增加 rule 字段（GTE/LTE），算法与测试用例同步覆盖。"),
    ("需求用例遗漏查阅人员只读权限", AiPhase.REQUIREMENTS, "需求理解偏差", DefectSeverity.MAJOR, 5, True, DefectStatus.FIXED, "2026-08-14", "权限矩阵未明确查阅人员不可写，越权边界只覆盖了管理员与工程师。", "补充查阅人员只读规则、路由守卫与 403 越权测试，前后端双重校验。"),
    ("验收标准未量化响应时间", AiPhase.REQUIREMENTS, "需求理解偏差", DefectSeverity.MINOR, 4, True, DefectStatus.FIXED, "2026-08-12", "非功能需求只有“快速响应”定性描述。", "量化为常规查询 P95 ≤ 500ms。"),
    ("维护阶段缺陷口径与需求不一致", AiPhase.MAINTENANCE, "需求理解偏差", DefectSeverity.MINOR, 4, False, DefectStatus.OPEN, "2026-11-01", "维护文档仍沿用旧版缺陷等级定义。", "以 enums.py 与评分表为唯一口径重新对齐，待下一次复盘关闭。"),
    ("前端字段名与后端 Schema 不一致", AiPhase.IMPLEMENTATION, "接口契约不一致", DefectSeverity.MAJOR, 5, True, DefectStatus.FIXED, "2026-10-09", "Agent 生成的前端使用 camelCase，后端为 snake_case。", "统一契约并使用联调测试锁定。"),
    ("分页参数 pageSize/page_size 不统一", AiPhase.IMPLEMENTATION, "接口契约不一致", DefectSeverity.MINOR, 4, True, DefectStatus.FIXED, "2026-10-10", "前后端分别生成，缺少共享契约。", "后端统一 page_size，前端请求封装统一转换。"),
    ("错误码与前端提示映射缺失", AiPhase.IMPLEMENTATION, "接口契约不一致", DefectSeverity.MINOR, 3, False, DefectStatus.OPEN, "2026-10-12", "只约定 HTTP 状态，未建立业务错误码字典。", "建立错误码字典并补充前端映射，待回归。"),
    ("日期格式前后端不一致", AiPhase.IMPLEMENTATION, "接口契约不一致", DefectSeverity.TRIVIAL, 2, True, DefectStatus.FIXED, "2026-10-12", "日期字符串直接透传，未统一 ISO 格式。", "统一 ISO 8601，并在前端格式化展示。"),
    ("检测记录弹窗在窄屏溢出", AiPhase.IMPLEMENTATION, "前端联调问题", DefectSeverity.MINOR, 4, False, DefectStatus.FIXED, "2026-10-15", "固定宽度弹窗未做响应式处理。", "设置宽度自适应并补充小屏样式。"),
    ("ECharts 空数据未兜底", AiPhase.IMPLEMENTATION, "前端联调问题", DefectSeverity.MINOR, 3, False, DefectStatus.FIXED, "2026-10-16", "图表组件默认假定数据非空。", "增加空状态占位与零值处理。"),
    ("表格筛选重置未清空分页", AiPhase.IMPLEMENTATION, "前端联调问题", DefectSeverity.TRIVIAL, 2, True, DefectStatus.FIXED, "2026-10-17", "筛选条件变化后页码未回到第一页。", "筛选变更统一重置 page=1。"),
    ("登录过期未统一跳转", AiPhase.IMPLEMENTATION, "前端联调问题", DefectSeverity.MAJOR, 2, True, DefectStatus.FIXED, "2026-10-18", "Axios 拦截器仅弹提示，未清理令牌。", "401 统一清理令牌并跳转登录页。"),
    ("样品删除未校验关联检测记录", AiPhase.DETAILED_DESIGN, "数据模型遗漏", DefectSeverity.CRITICAL, 3, True, DefectStatus.FIXED, "2026-09-20", "Service 直接删除，未检查子表。", "增加关联计数校验并返回业务错误码。"),
    ("用户停用后历史记录显示为空", AiPhase.IMPLEMENTATION, "数据模型遗漏", DefectSeverity.MINOR, 2, False, DefectStatus.FIXED, "2026-09-22", "查询使用内连接且未保留用户快照。", "改为按用户 ID 查询展示名，停用不影响历史记录。"),
    ("项目编号大小写未归一", AiPhase.IMPLEMENTATION, "数据模型遗漏", DefectSeverity.MINOR, 2, True, DefectStatus.FIXED, "2026-09-25", "唯一索引对大小写敏感，产生重复编号。", "写入前统一转大写并补唯一性测试。"),
    ("AI 任务日期字段类型不一致", AiPhase.DETAILED_DESIGN, "数据模型遗漏", DefectSeverity.TRIVIAL, 1, True, DefectStatus.FIXED, "2026-09-28", "Schema 使用 date，ORM 使用 DateTime。", "统一转换并修复类型标注。"),
    ("实测值等于标准值时判定不稳定", AiPhase.DETAILED_DESIGN, "边界条件缺失", DefectSeverity.MAJOR, 3, True, DefectStatus.OPEN, "2026-09-30", "浮点数直接比较产生精度误差。", "保留两位小数后比较，补充边界测试，待复盘关闭。"),
    ("零记录页面出现除零", AiPhase.IMPLEMENTATION, "边界条件缺失", DefectSeverity.MINOR, 2, True, DefectStatus.FIXED, "2026-10-02", "合格率计算未判断分母为 0。", "统一空集返回 0.0 并补测试。"),
    ("重复提交检测记录未拦截", AiPhase.IMPLEMENTATION, "边界条件缺失", DefectSeverity.MINOR, 2, True, DefectStatus.OPEN, "2026-10-05", "未做幂等或重复提示。", "增加前端防抖与后端重复校验，待回归。"),
    ("角色名称中英文混用", AiPhase.IMPLEMENTATION, "文案与样式", DefectSeverity.TRIVIAL, 2, True, DefectStatus.FIXED, "2026-10-20", "字典未统一维护。", "建立统一字典并在前端集中引用。"),
    ("移动端表格操作列拥挤", AiPhase.IMPLEMENTATION, "文案与样式", DefectSeverity.TRIVIAL, 2, False, DefectStatus.FIXED, "2026-10-21", "操作按钮未折叠。", "改为下拉操作菜单。"),
    ("空状态文案缺失", AiPhase.IMPLEMENTATION, "文案与样式", DefectSeverity.TRIVIAL, 1, False, DefectStatus.FIXED, "2026-10-22", "表格与图表未配置空状态。", "补充统一空状态组件。"),
    ("启动脚本端口被占用未提示", AiPhase.IMPLEMENTATION, "部署配置错误", DefectSeverity.MAJOR, 2, True, DefectStatus.FIXED, "2026-10-25", "脚本未检测端口占用，直接启动失败。", "启动前检测端口并输出可操作提示。"),
    ("SQLite 相对路径导致数据文件位置漂移", AiPhase.IMPLEMENTATION, "部署配置错误", DefectSeverity.MAJOR, 1, True, DefectStatus.FIXED, "2026-10-26", "数据库 URL 使用相对路径。", "改为基于 backend 目录的绝对路径。"),
    ("前端构建产物未拷入 static", AiPhase.IMPLEMENTATION, "部署配置错误", DefectSeverity.MAJOR, 1, True, DefectStatus.FIXED, "2026-10-26", "构建输出目录与后端静态目录脱节。", "Vite 构建直接输出到 backend/app/static。"),
]


def reset_database(db) -> None:
    for model in (TestRecord, Sample, Project, AiTask, Defect, User):
        db.execute(delete(model))
    db.commit()


def build_templates(sample: Sample):
    if sample.type == SampleType.CONCRETE.value:
        standard = 30.0
        for token in sample.spec.split():
            if token.startswith("C") and token[1:].isdigit():
                standard = float(token[1:])
                break
        return [("抗压强度（28d）", standard, "MPa", TestRule.GTE)] * 3
    if sample.type == SampleType.STEEL.value:
        return [
            ("屈服强度", 400.0, "MPa", TestRule.GTE),
            ("抗拉强度", 540.0, "MPa", TestRule.GTE),
            ("断后伸长率", 16.0, "%", TestRule.GTE),
        ]
    if sample.type == SampleType.SOIL.value:
        standard = 95.0 if "95%" in sample.spec else 93.0
        return [
            ("压实度", standard, "%", TestRule.GTE),
            ("含水率", 18.0, "%", TestRule.LTE),
            ("压实度", standard, "%", TestRule.GTE),
        ]
    if sample.type == SampleType.MORTAR.value:
        return [("抗压强度（28d）", 10.0, "MPa", TestRule.GTE)] * 3
    return [
        ("马歇尔稳定度", 8.0, "kN", TestRule.GTE),
        ("流值", 4.0, "mm", TestRule.LTE),
        ("空隙率", 6.0, "%", TestRule.LTE),
    ]


def seed(reset: bool = False) -> None:
    import_all_models()
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        existing_users = db.scalar(select(func.count()).select_from(User)) or 0
        if existing_users and not reset:
            print("数据库已有数据，跳过初始化。需要重建请执行：python seed.py --reset")
            return
        if reset:
            reset_database(db)

        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            display_name="系统管理员",
            role=Role.ADMIN.value,
            is_active=True,
        )
        engineer = User(
            username="engineer",
            password_hash=hash_password("engineer123"),
            display_name="李工",
            role=Role.ENGINEER.value,
            is_active=True,
        )
        engineer2 = User(
            username="engineer2",
            password_hash=hash_password("engineer123"),
            display_name="陈工",
            role=Role.ENGINEER.value,
            is_active=True,
        )
        viewer = User(
            username="viewer",
            password_hash=hash_password("viewer123"),
            display_name="王审阅",
            role=Role.VIEWER.value,
            is_active=True,
        )
        db.add_all([admin, engineer, engineer2, viewer])
        db.flush()

        project_map: dict[str, Project] = {}
        for item in PROJECTS:
            project = Project(
                code=item["code"],
                name=item["name"],
                client=item["client"],
                location=item["location"],
                status=item["status"].value,
                start_date=item["start_date"],
                end_date=item["end_date"],
                manager=item["manager"],
                description=item["description"],
            )
            db.add(project)
            project_map[project.code] = project
        db.flush()

        sample_map: dict[str, Sample] = {}
        for code, project_code, sample_type, spec, produced_on, quantity in SAMPLES:
            sample = Sample(
                code=code,
                project_id=project_map[project_code].id,
                type=sample_type.value,
                spec=spec,
                produced_on=produced_on,
                quantity=quantity,
                status=(
                    SampleStatus.PENDING.value
                    if code not in NO_TEST_CODES
                    else SampleStatus.TESTING.value
                    if code == "YP-260405"
                    else SampleStatus.PENDING.value
                ),
            )
            db.add(sample)
            sample_map[code] = sample
        db.flush()

        testers = [admin, engineer, engineer2]
        record_index = 0
        for sample in sample_map.values():
            if sample.code in NO_TEST_CODES:
                continue
            sample.status = SampleStatus.DONE.value
            templates = build_templates(sample)
            for offset, (item, standard, unit, rule) in enumerate(templates):
                is_fail = record_index % 7 == 3
                if rule == TestRule.GTE:
                    ratio = 0.03 + (record_index % 4) * 0.01 if is_fail else 0.02 + (record_index % 6) * 0.01
                    measured = round(standard * (1 - ratio if is_fail else 1 + ratio), 2)
                else:
                    ratio = 0.03 + (record_index % 4) * 0.01 if is_fail else 0.02 + (record_index % 6) * 0.01
                    measured = round(standard * (1 + ratio if is_fail else 1 - ratio), 2)

                month_index = record_index // 10
                month = 6 + month_index
                if month == 11:
                    day = 1 + (record_index % 5)
                    hour = 9 + (record_index % 3)
                else:
                    day = 3 + (record_index % 10) * 2
                    hour = 9 + (record_index % 6)
                tested_at = datetime(2026, month, day, hour, 20, 0)

                record = TestRecord(
                    sample_id=sample.id,
                    item=item,
                    standard_value=standard,
                    measured_value=measured,
                    unit=unit,
                    rule=rule.value,
                    conclusion=judge(standard, measured, rule.value),
                    tested_by=testers[record_index % len(testers)].id,
                    tested_at=tested_at,
                    remark="依据 GB/T 50081 / GB 50007 等标准检测" if offset == 0 else "",
                )
                db.add(record)
                record_index += 1

        for item in AI_TASKS:
            phase, task_name, level, agent_name, status, c, i, r, m, s, minutes, retries, day, notes = item
            task = AiTask(
                phase=phase.value,
                task_name=task_name,
                level=level.value,
                agent_name=agent_name,
                status=status.value,
                correctness=c,
                completeness=i,
                runnability=r,
                maintainability=m,
                compliance=s,
                failure_score=compute_failure_score(c, i, r, m, s),
                human_minutes=minutes,
                retries=retries,
                occurred_at=datetime.combine(date.fromisoformat(day), time(9, 0)),
                notes=notes,
            )
            db.add(task)

        for item in DEFECTS:
            title, phase, category, severity, occurrences, ai_related, status, found_at, root_cause, fix_action = item
            db.add(
                Defect(
                    title=title,
                    phase=phase.value,
                    category=category,
                    severity=severity.value,
                    occurrences=occurrences,
                    ai_related=ai_related,
                    status=status.value,
                    found_at=date.fromisoformat(found_at),
                    root_cause=root_cause,
                    fix_action=fix_action,
                )
            )

        db.commit()
        print("演示数据初始化完成：4 用户 / 6 项目 / 24 样品 / 60 检测记录 / 24 AI 任务 / 25 缺陷记录")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="清空并重建演示数据")
    args = parser.parse_args()
    seed(reset=args.reset)
