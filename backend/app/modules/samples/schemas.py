from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.core.enums import SampleStatus, SampleType


class SampleCreate(BaseModel):
    code: str = Field(min_length=3, max_length=40)
    project_id: int = Field(gt=0)
    type: SampleType
    spec: str = Field(min_length=2, max_length=80)
    produced_on: date | None = None
    quantity: int = Field(default=1, ge=1, le=1000)
    status: SampleStatus = SampleStatus.PENDING

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class SampleUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=3, max_length=40)
    project_id: int | None = Field(default=None, gt=0)
    type: SampleType | None = None
    spec: str | None = Field(default=None, min_length=2, max_length=80)
    produced_on: date | None = None
    quantity: int | None = Field(default=None, ge=1, le=1000)
    status: SampleStatus | None = None

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value
