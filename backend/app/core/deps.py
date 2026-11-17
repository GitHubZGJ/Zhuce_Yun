from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.users.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise BizException(40101, "请先登录后再访问", 401)
    payload = decode_access_token(credentials.credentials)
    try:
        user_id = int(payload.get("sub", "0"))
    except (TypeError, ValueError) as exc:
        raise BizException(40101, "登录凭证无效，请重新登录", 401) from exc
    user = db.get(User, user_id)
    if user is None:
        raise BizException(40101, "账号不存在，请重新登录", 401)
    if not user.is_active:
        raise BizException(40102, "账号已被停用，请联系管理员", 403)
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise BizException(40301, "没有权限执行该操作", 403)
        return user

    return dependency
