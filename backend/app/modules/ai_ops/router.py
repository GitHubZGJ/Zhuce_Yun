from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.enums import AiLevel, AiPhase, AiTaskStatus, DefectSeverity, DefectStatus
from app.core.response import ok, page_data
from app.db.session import get_db
from app.modules.ai_ops import service
from app.modules.ai_ops.schemas import AiTaskCreate, AiTaskUpdate, DefectCreate, DefectUpdate
from app.modules.users.models import User

router = APIRouter(prefix="/ai", tags=["AI 协作监管"])
admin_only = require_roles("ADMIN")


@router.get("/tasks", summary="AI 任务台账分页列表")
def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: str | None = Query(None, max_length=50),
    phase: AiPhase | None = None,
    level: AiLevel | None = None,
    status: AiTaskStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = service.list_tasks(
        db,
        page,
        page_size,
        q,
        phase.value if phase else None,
        level.value if level else None,
        status.value if status else None,
    )
    return ok(page_data(items, total, page, page_size))


@router.post("/tasks", summary="登记 AI 任务（自动计算失效分）")
def create_task(
    payload: AiTaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    return ok(service.create_task(db, payload), "AI 任务已登记并完成评分")


@router.put("/tasks/{task_id}", summary="更新 AI 任务并重新评分")
def update_task(
    task_id: int,
    payload: AiTaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    return ok(service.update_task(db, task_id, payload), "AI 任务已更新")


@router.delete("/tasks/{task_id}", summary="删除 AI 任务（管理员）")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    service.delete_task(db, task_id)
    return ok(None, "AI 任务已删除")


@router.get("/defects", summary="缺陷台账分页列表")
def list_defects(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    q: str | None = Query(None, max_length=50),
    phase: AiPhase | None = None,
    category: str | None = Query(None, max_length=40),
    severity: DefectSeverity | None = None,
    status: DefectStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items, total = service.list_defects(
        db,
        page,
        page_size,
        q,
        phase.value if phase else None,
        category,
        severity.value if severity else None,
        status.value if status else None,
    )
    return ok(page_data(items, total, page, page_size))


@router.post("/defects", summary="登记缺陷（管理员）")
def create_defect(
    payload: DefectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    return ok(service.create_defect(db, payload), "缺陷已登记")


@router.put("/defects/{defect_id}", summary="更新缺陷（管理员）")
def update_defect(
    defect_id: int,
    payload: DefectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    return ok(service.update_defect(db, defect_id, payload), "缺陷已更新")


@router.delete("/defects/{defect_id}", summary="删除缺陷（管理员）")
def delete_defect(
    defect_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    service.delete_defect(db, defect_id)
    return ok(None, "缺陷已删除")


@router.get("/stats", summary="AI 可靠性、失效分布与缺陷帕累托统计")
def ai_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ok(service.stats(db))


@router.get("/grading", summary="AI 分级机制与失效评分规则")
def grading(user: User = Depends(get_current_user)):
    return ok(service.grading_config())
