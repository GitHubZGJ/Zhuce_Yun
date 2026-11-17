from datetime import date, datetime
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.modules import import_all_models  # noqa: E402
from app.modules.ai_ops.models import AiTask, Defect  # noqa: E402
from app.modules.ai_ops.service import compute_failure_score  # noqa: E402
from app.modules.projects.models import Project  # noqa: E402
from app.modules.samples.models import Sample  # noqa: E402
from app.modules.test_records.models import TestRecord  # noqa: E402
from app.modules.test_records.service import judge  # noqa: E402
from app.modules.users.models import User  # noqa: E402

TEST_PASSWORD = "pass123"
TEST_PASSWORD_HASH = hash_password(TEST_PASSWORD)


def seed_test_data(db):
    """小型固定数据集，便于对数量、合格率和评分公式做精确断言。"""
    admin = User(
        username="admin",
        password_hash=TEST_PASSWORD_HASH,
        display_name="系统管理员",
        role="ADMIN",
    )
    engineer = User(
        username="engineer",
        password_hash=TEST_PASSWORD_HASH,
        display_name="李工",
        role="ENGINEER",
    )
    viewer = User(
        username="viewer",
        password_hash=TEST_PASSWORD_HASH,
        display_name="王审阅",
        role="VIEWER",
    )
    disabled = User(
        username="disabled",
        password_hash=TEST_PASSWORD_HASH,
        display_name="停用账号",
        role="ENGINEER",
        is_active=False,
    )
    db.add_all([admin, engineer, viewer, disabled])
    db.flush()

    p1 = Project(
        code="XM-T-001",
        name="测试项目一",
        client="测试建设单位",
        location="测试路 1 号",
        status="IN_PROGRESS",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        manager="李工",
        description="用于接口测试的项目",
    )
    p2 = Project(
        code="XM-T-002",
        name="测试项目二",
        client="测试建设单位",
        location="测试路 2 号",
        status="ACCEPTED",
        start_date=date(2025, 1, 1),
        end_date=date(2026, 6, 30),
        manager="陈工",
        description="",
    )
    p3 = Project(
        code="XM-T-003",
        name="测试项目三",
        client="测试建设单位",
        location="测试路 3 号",
        status="PLANNING",
        start_date=date(2026, 12, 1),
        end_date=date(2027, 6, 30),
        manager="周工",
        description="无样品的空项目",
    )
    db.add_all([p1, p2, p3])
    db.flush()

    s1 = Sample(
        code="YP-T-001",
        project_id=p1.id,
        type="CONCRETE",
        spec="C30 150×150×150mm",
        produced_on=date(2026, 8, 1),
        quantity=3,
        status="DONE",
    )
    s2 = Sample(
        code="YP-T-002",
        project_id=p1.id,
        type="STEEL",
        spec="HRB400E Φ20",
        produced_on=date(2026, 8, 2),
        quantity=5,
        status="DONE",
    )
    s3 = Sample(
        code="YP-T-003",
        project_id=p2.id,
        type="SOIL",
        spec="回填土 压实度≥93%",
        produced_on=date(2026, 8, 3),
        quantity=1,
        status="DONE",
    )
    s4 = Sample(
        code="YP-T-004",
        project_id=p3.id,
        type="CONCRETE",
        spec="C35 150×150×150mm",
        produced_on=date(2026, 8, 4),
        quantity=3,
        status="PENDING",
    )
    db.add_all([s1, s2, s3, s4])
    db.flush()

    record_specs = [
        (s1, "抗压强度", 30.0, 32.0, "MPa", "GTE", datetime(2026, 9, 1, 9, 0)),
        (s1, "抗压强度", 30.0, 28.0, "MPa", "GTE", datetime(2026, 9, 2, 10, 0)),
        (s1, "抗压强度", 30.0, 35.0, "MPa", "GTE", datetime(2026, 9, 3, 11, 0)),
        (s2, "屈服强度", 400.0, 410.0, "MPa", "GTE", datetime(2026, 10, 1, 9, 0)),
        (s2, "抗拉强度", 540.0, 560.0, "MPa", "GTE", datetime(2026, 10, 2, 9, 0)),
        (s2, "断后伸长率", 16.0, 15.0, "%", "GTE", datetime(2026, 10, 3, 9, 0)),
        (s3, "压实度", 93.0, 94.0, "%", "GTE", datetime(2026, 10, 5, 9, 0)),
        (s3, "含水率", 18.0, 17.0, "%", "LTE", datetime(2026, 11, 1, 9, 0)),
    ]
    for sample, item, standard, measured, unit, rule, tested_at in record_specs:
        db.add(
            TestRecord(
                sample_id=sample.id,
                item=item,
                standard_value=standard,
                measured_value=measured,
                unit=unit,
                rule=rule,
                conclusion=judge(standard, measured, rule),
                tested_by=engineer.id,
                tested_at=tested_at,
                remark="",
            )
        )

    ai_specs = [
        ("FEASIBILITY", "可行性图表", "L1", "图表Agent", "SUCCESS", 0, 0, 0, 0, 0),
        ("REQUIREMENTS", "需求用例整理", "L2", "需求Agent", "SUCCESS", 1, 1, 0, 0, 0),
        ("ARCHITECTURE", "架构图初稿", "L1", "图表Agent", "SUCCESS", 0, 0, 0, 0, 0),
        ("DETAILED_DESIGN", "判定边界设计", "L2", "编码Agent", "PARTIAL", 3, 2, 2, 1, 2),
        ("IMPLEMENTATION", "部署脚本", "L1", "运维Agent", "FAILED", 4, 2, 4, 2, 3),
        ("MAINTENANCE", "复盘材料", "L2", "文档Agent", "SUCCESS", 1, 1, 0, 0, 0),
    ]
    for index, spec in enumerate(ai_specs):
        phase, name, level, agent, status, c, i, r, m, s = spec
        db.add(
            AiTask(
                phase=phase,
                task_name=name,
                level=level,
                agent_name=agent,
                status=status,
                correctness=c,
                completeness=i,
                runnability=r,
                maintainability=m,
                compliance=s,
                failure_score=compute_failure_score(c, i, r, m, s),
                human_minutes=20 * (index + 1),
                retries=0,
                occurred_at=datetime(2026, 8, index + 1, 9, 0),
                notes="",
            )
        )

    defects = [
        ("需求理解偏差一", "REQUIREMENTS", "需求理解偏差", "MAJOR", 6, True, "FIXED", date(2026, 8, 1)),
        ("需求理解偏差二", "REQUIREMENTS", "需求理解偏差", "MINOR", 5, True, "FIXED", date(2026, 8, 2)),
        ("接口契约一", "IMPLEMENTATION", "接口契约不一致", "MAJOR", 4, True, "FIXED", date(2026, 9, 1)),
        ("前端联调一", "IMPLEMENTATION", "前端联调问题", "TRIVIAL", 2, False, "FIXED", date(2026, 9, 2)),
        ("数据模型一", "DETAILED_DESIGN", "数据模型遗漏", "CRITICAL", 1, True, "OPEN", date(2026, 9, 3)),
    ]
    for title, phase, category, severity, occurrences, ai_related, status, found_at in defects:
        db.add(
            Defect(
                title=title,
                phase=phase,
                category=category,
                severity=severity,
                occurrences=occurrences,
                ai_related=ai_related,
                status=status,
                found_at=found_at,
                root_cause="测试根因",
                fix_action="测试修复",
            )
        )

    db.commit()
    return {
        "users": {"admin": admin, "engineer": engineer, "viewer": viewer, "disabled": disabled},
        "projects": {"p1": p1, "p2": p2, "p3": p3},
        "samples": {"s1": s1, "s2": s2, "s3": s3, "s4": s4},
    }


@pytest.fixture()
def db_session():
    import_all_models()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def data(db_session):
    return seed_test_data(db_session)


@pytest.fixture()
def client(db_session, data):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def login_headers(client: TestClient, username: str, password: str = TEST_PASSWORD) -> dict:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(client):
    return login_headers(client, "admin")


@pytest.fixture()
def engineer_headers(client):
    return login_headers(client, "engineer")


@pytest.fixture()
def viewer_headers(client):
    return login_headers(client, "viewer")
