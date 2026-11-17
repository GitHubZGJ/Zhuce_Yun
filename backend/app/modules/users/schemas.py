from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    role: str
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=64)
    display_name: str = Field(min_length=2, max_length=50)
    role: Role = Role.ENGINEER

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip()


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=50)
    password: str | None = Field(default=None, min_length=6, max_length=64)
    role: Role | None = None
    is_active: bool | None = None


class UserCreateResult(UserOut):
    initial_password: str
