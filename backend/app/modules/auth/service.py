from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BizException
from app.core.security import create_access_token, verify_password
from app.modules.users.models import User


def authenticate(db: Session, username: str, password: str) -> dict:
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        raise BizException(40101, "用户名或密码错误", 401)
    if not user.is_active:
        raise BizException(40102, "账号已被停用，请联系管理员", 403)

    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.username, user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": user,
    }
