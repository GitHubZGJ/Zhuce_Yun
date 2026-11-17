from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import ok
from app.db.session import get_db
from app.modules.dashboard import service
from app.modules.users.models import User

router = APIRouter(prefix="/dashboard", tags=["数据看板"])


@router.get("/overview", summary="看板总览数据")
def overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ok(service.overview(db))
