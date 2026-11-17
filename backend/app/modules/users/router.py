from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_roles
from app.core.response import ok, page_data
from app.db.session import get_db
from app.modules.users import service
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["用户管理"])
admin_only = require_roles("ADMIN")


@router.get("", summary="用户列表（管理员）")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, max_length=50),
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    items, total = service.list_users(db, page, page_size, q)
    serialized = [UserOut.model_validate(item).model_dump() for item in items]
    return ok(page_data(serialized, total, page, page_size))


@router.post("", summary="新增用户（管理员）")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    created = service.create_user(db, payload)
    data = {
        "id": created.id,
        "username": created.username,
        "display_name": created.display_name,
        "role": created.role,
        "is_active": created.is_active,
        "last_login_at": created.last_login_at,
        "created_at": created.created_at,
        "initial_password": payload.password,
    }
    return ok(data, "用户创建成功")


@router.patch("/{user_id}", summary="更新用户角色/状态/密码（管理员）")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(admin_only),
):
    updated = service.update_user(db, user_id, payload, user)
    return ok(UserOut.model_validate(updated).model_dump(), "用户信息已更新")
