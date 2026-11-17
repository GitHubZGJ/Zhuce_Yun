import importlib
import pkgutil

from fastapi import APIRouter


def iter_module_routers() -> list[APIRouter]:
    """自动发现 app.modules 下每个子模块的 router，实现模块化注册。"""
    import app.modules as modules_package

    routers: list[APIRouter] = []
    for info in pkgutil.iter_modules(modules_package.__path__):
        if not info.ispkg:
            continue
        router_module = importlib.import_module(f"{modules_package.__name__}.{info.name}.router")
        router = getattr(router_module, "router", None)
        if isinstance(router, APIRouter):
            routers.append(router)
    return routers


def import_all_models() -> None:
    """导入所有模块的模型，确保 SQLAlchemy 元数据完整（Alembic/建表使用）。"""
    import app.modules as modules_package

    for info in pkgutil.iter_modules(modules_package.__path__):
        if not info.ispkg:
            continue
        try:
            importlib.import_module(f"{modules_package.__name__}.{info.name}.models")
        except ModuleNotFoundError as exc:
            if exc.name != f"{modules_package.__name__}.{info.name}.models":
                raise
