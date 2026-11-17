from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.enums import SampleStatus, SampleType
from app.core.response import ok, page_data
from app.db.session import get_db
from app.modules.samples import service
from app.modules.samples.schemas import SampleCreate, SampleUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/samples", tags=["检测样品"])
can_edit = require_roles("ADMIN", "ENGINEER")


@router.get("", summary="样品分页列表")
def list_samples(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: str | None = Query(None, max_length=50),
    project_id: int | None = Query(None, gt=0),
    sample_type: SampleType | None = Query(None, alias="type"),
    status: SampleStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = service.list_samples(
        db,
        page,
        page_size,
        q,
        project_id,
        sample_type.value if sample_type else None,
        status.value if status else None,
    )
    return ok(page_data(items, total, page, page_size))


@router.get("/{sample_id}", summary="样品详情")
def get_sample(
    sample_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ok(service.get_detail(db, sample_id))


@router.post("", summary="登记样品")
def create_sample(
    payload: SampleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(can_edit),
):
    return ok(service.create_sample(db, payload), "样品登记成功")


@router.put("/{sample_id}", summary="更新样品")
def update_sample(
    sample_id: int,
    payload: SampleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(can_edit),
):
    return ok(service.update_sample(db, sample_id, payload), "样品已更新")


@router.delete("/{sample_id}", summary="删除样品（管理员）")
def delete_sample(
    sample_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN")),
):
    service.delete_sample(db, sample_id)
    return ok(None, "样品已删除")
