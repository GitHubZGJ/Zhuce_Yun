from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.enums import SAMPLE_TYPE_LABELS, SampleType
from app.modules.ai_ops.models import AiTask, Defect
from app.modules.ai_ops.service import pareto_data, reliability_overview
from app.modules.projects.models import Project
from app.modules.samples.models import Sample
from app.modules.test_records.models import TestRecord
from app.modules.test_records.service import serialize as serialize_record
from app.modules.users.models import User

SAMPLE_TYPE_ORDER = {sample_type.value: index for index, sample_type in enumerate(SampleType)}


def _month_keys(count: int = 6) -> list[str]:
    today = date.today()
    keys = []
    year, month = today.year, today.month
    for _ in range(count):
        keys.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(keys))


def overview(db: Session) -> dict:
    project_total = db.scalar(select(func.count()).select_from(Project)) or 0
    active_projects = db.scalar(
        select(func.count()).select_from(Project).where(Project.status == "IN_PROGRESS")
    ) or 0
    sample_total = db.scalar(select(func.count()).select_from(Sample)) or 0
    pending_samples = db.scalar(
        select(func.count()).select_from(Sample).where(Sample.status == "PENDING")
    ) or 0
    test_total = db.scalar(select(func.count()).select_from(TestRecord)) or 0
    pass_total = db.scalar(
        select(func.count()).select_from(TestRecord).where(TestRecord.conclusion == "PASS")
    ) or 0
    pass_rate = round(pass_total / test_total * 100, 1) if test_total else 0.0

    tasks = db.scalars(select(AiTask)).all()
    ai_summary = reliability_overview(tasks)
    open_defect_occurrences = db.scalar(
        select(func.coalesce(func.sum(Defect.occurrences), 0)).where(Defect.status == "OPEN")
    ) or 0

    summary = {
        "project_total": project_total,
        "active_projects": active_projects,
        "sample_total": sample_total,
        "pending_samples": pending_samples,
        "test_total": test_total,
        "pass_total": pass_total,
        "pass_rate": pass_rate,
        "open_defect_occurrences": int(open_defect_occurrences),
        **ai_summary,
    }

    project_status = [
        {"status": status, "count": count}
        for status, count in db.execute(
            select(Project.status, func.count(Project.id)).group_by(Project.status)
        ).all()
    ]

    sample_types = [
        {"type": sample_type, "label": SAMPLE_TYPE_LABELS.get(sample_type, sample_type), "count": count}
        for sample_type, count in db.execute(
            select(Sample.type, func.count(Sample.id)).group_by(Sample.type)
        ).all()
    ]
    sample_types.sort(key=lambda item: SAMPLE_TYPE_ORDER.get(item["type"], 99))

    pass_by_type_rows = db.execute(
        select(
            Sample.type,
            func.count(TestRecord.id),
            func.sum(case((TestRecord.conclusion == "PASS", 1), else_=0)),
        )
        .join(TestRecord, TestRecord.sample_id == Sample.id)
        .group_by(Sample.type)
    ).all()
    pass_rate_by_type = [
        {
            "type": sample_type,
            "label": SAMPLE_TYPE_LABELS.get(sample_type, sample_type),
            "total": total,
            "pass": int(passed or 0),
            "rate": round(int(passed or 0) / total * 100, 1) if total else 0.0,
        }
        for sample_type, total, passed in pass_by_type_rows
    ]
    pass_rate_by_type.sort(key=lambda item: SAMPLE_TYPE_ORDER.get(item["type"], 99))

    month_rows = db.execute(
        select(
            func.strftime("%Y-%m", TestRecord.tested_at).label("month"),
            TestRecord.conclusion,
            func.count(TestRecord.id),
        ).group_by("month", TestRecord.conclusion)
    ).all()
    month_map: dict[str, dict] = {}
    for month, conclusion, count in month_rows:
        bucket = month_map.setdefault(month, {"total": 0, "pass": 0, "fail": 0})
        bucket["total"] += count
        if conclusion == "PASS":
            bucket["pass"] += count
        else:
            bucket["fail"] += count
    monthly_trend = [
        {"month": month, **month_map.get(month, {"total": 0, "pass": 0, "fail": 0})}
        for month in _month_keys(6)
    ]

    recent_rows = db.execute(
        select(TestRecord, Sample, Project, User)
        .join(Sample, TestRecord.sample_id == Sample.id)
        .join(Project, Sample.project_id == Project.id)
        .join(User, TestRecord.tested_by == User.id)
        .order_by(TestRecord.tested_at.desc(), TestRecord.id.desc())
        .limit(6)
    ).all()
    recent_records = [serialize_record(*row) for row in recent_rows]

    return {
        "summary": summary,
        "project_status": project_status,
        "sample_types": sample_types,
        "pass_rate_by_type": pass_rate_by_type,
        "monthly_trend": monthly_trend,
        "recent_records": recent_records,
        "defect_pareto": pareto_data(db),
    }
