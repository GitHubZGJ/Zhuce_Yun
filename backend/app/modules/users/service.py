from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import Role
from app.core.exceptions import BizException
from app.core.security import hash_password
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserUpdate


def list_users(db: Session, page: int, page_size: int, q: str | None = None):
    stmt = select(User)
    if q:
        keyword = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.username.ilike(keyword), User.display_name.ilike(keyword)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(User.id.asc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return items, total


def create_user(db: Session, payload: UserCreate) -> User:
    exists = db.scalar(
        select(User).where(func.lower(User.username) == payload.username.lower())
    )
    if exists:
        raise BizException(40901, "登录名已存在", 409)
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role=payload.role.value,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, payload: UserUpdate, operator: User) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise BizException(40401, "用户不存在", 404)

    if user.id == operator.id and payload.is_active is False:
        raise BizException(40003, "不能停用当前登录账号", 400)
    if user.id == operator.id and payload.role is not None and payload.role != Role.ADMIN:
        raise BizException(40003, "不能降低当前登录账号的管理员角色", 400)

    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if payload.role is not None:
        user.role = payload.role.value
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return user
