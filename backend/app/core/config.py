from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """应用配置，可通过 ZHCE_ 前缀环境变量覆盖。"""

    app_name: str = "筑测云 · 工程检测数据管理平台"
    app_version: str = "1.0.0"
    api_prefix: str = "/api"
    secret_key: str = "zhuce-cloud-demo-secret-please-change-in-production"
    access_token_expire_minutes: int = 720
    database_url: str = f"sqlite:///{(DATA_DIR / 'app.db').as_posix()}"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    model_config = SettingsConfigDict(env_prefix="ZHCE_", env_file=".env", extra="ignore")


settings = Settings()
