from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.modules.projects.models import Project
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate
from app.modules.samples.models import Sample


def _sample_counts(db: Session, project_ids: list[int]) -> dict[int, int]:
    if not project_ids:
        return {}
    rows = db.execute(
        select(Sample.project_id, func.count(Sample.id))
        .where(Sample.project_id.in_(project_ids))
        .group_by(Sample.project_id)
    ).all()
    return {project_id: count for project_id, count in rows}


def serialize(project: Project, sample_count: int = 0) -> dict:
    return {
        "id": project.id,
        "code": project.code,
        "name": project.name,
        "client": project.client,
        "location": project.location,
        "status": project.status,
        "start_date": project.start_date,
        "end_date": project.end_date,
        "manager": project.manager,
        "description": project.description,
        "sample_count": sample_count,
        "created_at": project.created_at,
    }


def list_projects(
    db: Session,
    page: int,
    page_size: int,
    q: str | None = None,
    status: str | None = None,
):
    stmt = select(Project)
    if q:
        keyword = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Project.code.ilike(keyword),
                Project.name.ilike(keyword),
                Project.client.ilike(keyword),
            )
        )
    if status:
        stmt = stmt.where(Project.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Project.created_at.desc(), Project.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    counts = _sample_counts(db, [item.id for item in items])
    return [serialize(item, counts.get(item.id, 0)) for item in items], total


def get_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise BizException(40401, "工程项目不存在", 404)
    return project


def create_project(db: Session, payload: ProjectCreate) -> dict:
    exists = db.scalar(select(Project.id).where(Project.code == payload.code))
    if exists:
        raise BizException(40901, "项目编号已存在", 409)
    project = Project(**payload.model_dump(exclude={"status"}), status=payload.status.value)
    db.add(project)
    db.commit()
    db.refresh(project)
    return serialize(project, 0)


def update_project(db: Session, project_id: int, payload: ProjectUpdate) -> dict:
    project = get_project(db, project_id)
    data = payload.model_dump(exclude_unset=True)
    new_code = data.get("code")
    if new_code and new_code != project.code:
        exists = db.scalar(select(Project.id).where(Project.code == new_code))
        if exists:
            raise BizException(40901, "项目编号已存在", 409)

    start = data.get("start_date", project.start_date)
    end = data.get("end_date", project.end_date)
    if start and end and end < start:
        raise BizException(40001, "结束日期不能早于开始日期", 400)

    for field, value in data.items():
        if field == "status" and value is not None:
            value = value.value if hasattr(value, "value") else value
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    counts = _sample_counts(db, [project.id])
    return serialize(project, counts.get(project.id, 0))


def delete_project(db: Session, project_id: int) -> None:
    project = get_project(db, project_id)
    sample_count = db.scalar(
        select(func.count()).select_from(Sample).where(Sample.project_id == project_id)
    ) or 0
    if sample_count:
        raise BizException(40005, "项目下存在样品，无法删除", 400)
    db.delete(project)
    db.commit()


def list_options(db: Session) -> list[dict]:
    projects = db.scalars(
        select(Project).where(Project.status != "ARCHIVED").order_by(Project.code.desc())
    ).all()
    return [
        {"id": project.id, "code": project.code, "name": project.name}
        for project in projects
    ]
