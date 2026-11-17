from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.projects.models import Project
from app.modules.samples.models import Sample
from app.modules.samples.schemas import SampleCreate, SampleUpdate
from app.modules.test_records.models import TestRecord


def _test_counts(db: Session, sample_ids: list[int]) -> dict[int, int]:
    if not sample_ids:
        return {}
    rows = db.execute(
        select(TestRecord.sample_id, func.count(TestRecord.id))
        .where(TestRecord.sample_id.in_(sample_ids))
        .group_by(TestRecord.sample_id)
    ).all()
    return {sample_id: count for sample_id, count in rows}


def serialize(sample: Sample, project: Project | None, test_count: int = 0) -> dict:
    return {
        "id": sample.id,
        "code": sample.code,
        "project_id": sample.project_id,
        "project_code": project.code if project else None,
        "project_name": project.name if project else None,
        "type": sample.type,
        "spec": sample.spec,
        "produced_on": sample.produced_on,
        "quantity": sample.quantity,
        "status": sample.status,
        "test_count": test_count,
        "created_at": sample.created_at,
    }


def list_samples(
    db: Session,
    page: int,
    page_size: int,
    q: str | None = None,
    project_id: int | None = None,
    sample_type: str | None = None,
    status: str | None = None,
):
    stmt = select(Sample, Project).join(Project, Sample.project_id == Project.id)
    if q:
        keyword = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Sample.code.ilike(keyword),
                Sample.spec.ilike(keyword),
                Project.name.ilike(keyword),
            )
        )
    if project_id:
        stmt = stmt.where(Sample.project_id == project_id)
    if sample_type:
        stmt = stmt.where(Sample.type == sample_type)
    if status:
        stmt = stmt.where(Sample.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.order_by(Sample.created_at.desc(), Sample.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    counts = _test_counts(db, [sample.id for sample, _ in rows])
    items = [serialize(sample, project, counts.get(sample.id, 0)) for sample, project in rows]
    return items, total


def get_sample(db: Session, sample_id: int) -> Sample:
    sample = db.get(Sample, sample_id)
    if sample is None:
        raise BizException(40401, "检测样品不存在", 404)
    return sample


def get_detail(db: Session, sample_id: int) -> dict:
    sample = get_sample(db, sample_id)
    project = db.get(Project, sample.project_id)
    counts = _test_counts(db, [sample.id])
    return serialize(sample, project, counts.get(sample.id, 0))


def _ensure_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise BizException(40002, "关联的工程项目不存在", 400)
    return project


def create_sample(db: Session, payload: SampleCreate) -> dict:
    if db.scalar(select(Sample.id).where(Sample.code == payload.code)):
        raise BizException(40901, "样品编号已存在", 409)
    project = _ensure_project(db, payload.project_id)
    sample = Sample(**payload.model_dump(exclude={"status"}), status=payload.status.value)
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return serialize(sample, project, 0)


def update_sample(db: Session, sample_id: int, payload: SampleUpdate) -> dict:
    sample = get_sample(db, sample_id)
    data = payload.model_dump(exclude_unset=True)
    new_code = data.get("code")
    if new_code and new_code != sample.code:
        if db.scalar(select(Sample.id).where(Sample.code == new_code)):
            raise BizException(40901, "样品编号已存在", 409)
    project = _ensure_project(db, data.get("project_id", sample.project_id))
    for field, value in data.items():
        if field == "status" and value is not None:
            value = value.value if hasattr(value, "value") else value
        setattr(sample, field, value)
    db.commit()
    db.refresh(sample)
    counts = _test_counts(db, [sample.id])
    return serialize(sample, project, counts.get(sample.id, 0))


def delete_sample(db: Session, sample_id: int) -> None:
    sample = get_sample(db, sample_id)
    test_count = db.scalar(
        select(func.count()).select_from(TestRecord).where(TestRecord.sample_id == sample_id)
    ) or 0
    if test_count:
        raise BizException(40006, "样品下存在检测记录，无法删除", 400)
    db.delete(sample)
    db.commit()
