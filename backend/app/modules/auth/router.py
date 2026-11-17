from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import ok
from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.schemas import LoginRequest, UserBrief
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", summary="账号登录")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    result = service.authenticate(db, payload.username, payload.password)
    result["user"] = UserBrief.model_validate(result["user"]).model_dump()
    return ok(result, "登录成功")


@router.get("/me", summary="获取当前登录用户")
def me(user: User = Depends(get_current_user)):
    return ok(UserBrief.model_validate(user).model_dump())


@router.post("/logout", summary="退出登录（前端清理令牌）")
def logout(user: User = Depends(get_current_user)):
    return ok(None, "已退出登录")
