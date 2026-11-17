from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.enums import ProjectStatus


class ProjectCreate(BaseModel):
    code: str = Field(min_length=3, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    client: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=120)
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: date | None = None
    end_date: date | None = None
    manager: str = Field(min_length=2, max_length=50)
    description: str = Field(default="", max_length=1000)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("结束日期不能早于开始日期")
        return self


class ProjectUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=3, max_length=40)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    client: str | None = Field(default=None, min_length=2, max_length=120)
    location: str | None = Field(default=None, min_length=2, max_length=120)
    status: ProjectStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    manager: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = Field(default=None, max_length=1000)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value


