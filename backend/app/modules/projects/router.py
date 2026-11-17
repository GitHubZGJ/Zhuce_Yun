from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.enums import ProjectStatus
from app.core.response import ok, page_data
from app.db.session import get_db
from app.modules.projects import service
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/projects", tags=["工程项目"])
can_edit = require_roles("ADMIN", "ENGINEER")


@router.get("", summary="项目分页列表")
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: str | None = Query(None, max_length=50),
    status: ProjectStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = service.list_projects(
        db, page, page_size, q, status.value if status else None
    )
    return ok(page_data(items, total, page, page_size))


@router.get("/options", summary="项目下拉选项")
def project_options(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ok(service.list_options(db))


@router.get("/{project_id}", summary="项目详情")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = service.get_project(db, project_id)
    return ok(service.serialize(project))


@router.post("", summary="新建项目")
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(can_edit),
):
    return ok(service.create_project(db, payload), "项目创建成功")


@router.put("/{project_id}", summary="更新项目")
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(can_edit),
):
    return ok(service.update_project(db, project_id, payload), "项目已更新")


@router.delete("/{project_id}", summary="删除项目（管理员）")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN")),
):
    service.delete_project(db, project_id)
    return ok(None, "项目已删除")
