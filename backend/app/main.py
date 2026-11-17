from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.response import ok
from app.modules import iter_module_routers

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="筑测云：工程项目—样品—检测记录—AI 协作监管一体化 Demo 系统",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

for module_router in iter_module_routers():
    app.include_router(module_router, prefix=settings.api_prefix)


@app.get("/api/health", tags=["系统"], summary="健康检查")
def health():
    return ok({"status": "up", "app": settings.app_name, "version": settings.app_version})


if (STATIC_DIR / "index.html").exists():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="请求的资源不存在")
        candidate = STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
