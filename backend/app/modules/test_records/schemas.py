from datetime import datetime
from math import isfinite

from pydantic import BaseModel, Field, field_validator

from app.core.enums import TestRule


def _validate_number(value: float) -> float:
    if not isfinite(value):
        raise ValueError("数值必须为有限数字")
    return value


class TestRecordCreate(BaseModel):
    sample_id: int = Field(gt=0)
    item: str = Field(min_length=2, max_length=60)
    standard_value: float = Field(gt=0)
    measured_value: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=20)
    rule: TestRule = TestRule.GTE
    tested_at: datetime | None = None
    remark: str = Field(default="", max_length=255)

    @field_validator("standard_value", "measured_value")
    @classmethod
    def numbers_finite(cls, value: float) -> float:
        return _validate_number(value)


class TestRecordUpdate(BaseModel):
    item: str | None = Field(default=None, min_length=2, max_length=60)
    standard_value: float | None = Field(default=None, gt=0)
    measured_value: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    rule: TestRule | None = None
    tested_at: datetime | None = None
    remark: str | None = Field(default=None, max_length=255)

    @field_validator("standard_value", "measured_value")
    @classmethod
    def numbers_finite(cls, value: float | None) -> float | None:
        return None if value is None else _validate_number(value)
