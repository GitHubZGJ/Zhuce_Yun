from datetime import date, datetime, time, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import TestConclusion, TestRule
from app.core.exceptions import BizException
from app.modules.projects.models import Project
from app.modules.samples.models import Sample
from app.modules.test_records.models import TestRecord
from app.modules.test_records.schemas import TestRecordCreate, TestRecordUpdate
from app.modules.users.models import User


def judge(standard_value: float, measured_value: float, rule: str) -> str:
    """核心判定算法：保留两位小数后比较，GTE 表示实测值应大于等于标准值。"""
    standard = round(float(standard_value), 2)
    measured = round(float(measured_value), 2)
    if rule == TestRule.GTE.value:
        passed = measured >= standard
    elif rule == TestRule.LTE.value:
        passed = measured <= standard
    else:
        raise BizException(40007, "不支持的判定规则", 400)
    return TestConclusion.PASS.value if passed else TestConclusion.FAIL.value


def serialize(
    record: TestRecord, sample: Sample | None, project: Project | None, tester: User | None
) -> dict:
    return {
        "id": record.id,
        "sample_id": record.sample_id,
        "sample_code": sample.code if sample else None,
        "sample_type": sample.type if sample else None,
        "project_id": project.id if project else None,
        "project_code": project.code if project else None,
        "project_name": project.name if project else None,
        "item": record.item,
        "standard_value": record.standard_value,
        "measured_value": record.measured_value,
        "unit": record.unit,
        "rule": record.rule,
        "conclusion": record.conclusion,
        "tested_by": record.tested_by,
        "tester_name": tester.display_name if tester else None,
        "tested_at": record.tested_at,
        "remark": record.remark,
        "created_at": record.created_at,
    }


def _base_query():
    return (
        select(TestRecord, Sample, Project, User)
        .join(Sample, TestRecord.sample_id == Sample.id)
        .join(Project, Sample.project_id == Project.id)
        .join(User, TestRecord.tested_by == User.id)
    )


def _detail(db: Session, record_id: int) -> dict:
    row = db.execute(_base_query().where(TestRecord.id == record_id)).first()
    if row is None:
        raise BizException(40401, "检测记录不存在", 404)
    return serialize(*row)


def list_records(
    db: Session,
    page: int,
    page_size: int,
    q: str | None = None,
    project_id: int | None = None,
    sample_id: int | None = None,
    conclusion: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
):
    stmt = _base_query()
    if q:
        keyword = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                TestRecord.item.ilike(keyword),
                Sample.code.ilike(keyword),
                Project.name.ilike(keyword),
            )
        )
    if project_id:
        stmt = stmt.where(Sample.project_id == project_id)
    if sample_id:
        stmt = stmt.where(TestRecord.sample_id == sample_id)
    if conclusion:
        stmt = stmt.where(TestRecord.conclusion == conclusion)
    if start_date:
        stmt = stmt.where(TestRecord.tested_at >= datetime.combine(start_date, time.min))
    if end_date:
        stmt = stmt.where(
            TestRecord.tested_at < datetime.combine(end_date + timedelta(days=1), time.min)
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.order_by(TestRecord.tested_at.desc(), TestRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = [serialize(*row) for row in rows]
    return items, total


def create_record(db: Session, payload: TestRecordCreate, tester: User) -> dict:
    sample = db.get(Sample, payload.sample_id)
    if sample is None:
        raise BizException(40002, "关联的检测样品不存在", 400)
    conclusion = judge(payload.standard_value, payload.measured_value, payload.rule.value)
    record = TestRecord(
        sample_id=payload.sample_id,
        item=payload.item,
        standard_value=payload.standard_value,
        measured_value=payload.measured_value,
        unit=payload.unit,
        rule=payload.rule.value,
        conclusion=conclusion,
        tested_by=tester.id,
        tested_at=payload.tested_at or datetime.now(),
        remark=payload.remark,
    )
    db.add(record)
    sample.status = "DONE"
    db.commit()
    db.refresh(record)
    return _detail(db, record.id)


def update_record(db: Session, record_id: int, payload: TestRecordUpdate) -> dict:
    record = db.get(TestRecord, record_id)
    if record is None:
        raise BizException(40401, "检测记录不存在", 404)
    data = payload.model_dump(exclude_unset=True)
    if "rule" in data and data["rule"] is not None:
        data["rule"] = data["rule"].value
    for field, value in data.items():
        if value is not None:
            setattr(record, field, value)
    record.conclusion = judge(record.standard_value, record.measured_value, record.rule)
    db.commit()
    db.refresh(record)
    return _detail(db, record.id)


def delete_record(db: Session, record_id: int) -> None:
    record = db.get(TestRecord, record_id)
    if record is None:
        raise BizException(40401, "检测记录不存在", 404)
    db.delete(record)
    db.commit()
