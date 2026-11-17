from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.enums import TestConclusion
from app.core.response import ok, page_data
from app.db.session import get_db
from app.modules.test_records import service
from app.modules.test_records.schemas import TestRecordCreate, TestRecordUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/test-records", tags=["检测记录"])
can_edit = require_roles("ADMIN", "ENGINEER")


@router.get("", summary="检测记录分页列表")
def list_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: str | None = Query(None, max_length=50),
    project_id: int | None = Query(None, gt=0),
    sample_id: int | None = Query(None, gt=0),
    conclusion: TestConclusion | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = service.list_records(
        db,
        page,
        page_size,
        q,
        project_id,
        sample_id,
        conclusion.value if conclusion else None,
        start_date,
        end_date,
    )
    return ok(page_data(items, total, page, page_size))


@router.get("/{record_id}", summary="检测记录详情")
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ok(service._detail(db, record_id))


@router.post("", summary="录入检测记录并自动判定")
def create_record(
    payload: TestRecordCreate,
    db: Session = Depends(get_db),
    user: User = Depends(can_edit),
):
    return ok(service.create_record(db, payload, user), "检测记录已保存并完成判定")


@router.put("/{record_id}", summary="修正检测记录并重新判定")
def update_record(
    record_id: int,
    payload: TestRecordUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(can_edit),
):
    return ok(service.update_record(db, record_id, payload), "检测记录已更新")


@router.delete("/{record_id}", summary="删除检测记录（管理员）")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN")),
):
    service.delete_record(db, record_id)
    return ok(None, "检测记录已删除")
