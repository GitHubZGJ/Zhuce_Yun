import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("zhuce")


class BizException(Exception):
    """业务异常：以统一响应包返回可读错误。"""

    def __init__(self, code: int, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _envelope(code: int, message: str, data=None) -> dict:
    return {"code": code, "message": message, "data": data}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BizException)
    async def handle_biz_exception(request: Request, exc: BizException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        details = []
        for error in exc.errors():
            location = ".".join(
                str(part) for part in error.get("loc", ()) if part not in ("body", "query", "path")
            )
            details.append(f"{location}: {error.get('msg', '参数不合法')}")
        message = "参数校验失败" + (f"（{'；'.join(details)}）" if details else "")
        return JSONResponse(status_code=422, content=_envelope(42201, message))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        default_messages = {
            404: "请求的资源不存在",
            405: "请求方法不被支持",
            401: "未登录或登录已失效",
            403: "没有权限执行该操作",
        }
        if exc.status_code in default_messages:
            message = default_messages[exc.status_code]
        elif isinstance(exc.detail, str):
            message = exc.detail
        else:
            message = "请求处理失败"
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.status_code * 100 + 1, message),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content=_envelope(50000, "服务器内部错误，请稍后重试"),
        )
