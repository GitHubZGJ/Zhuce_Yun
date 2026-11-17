from datetime import date

from pydantic import BaseModel, Field

from app.core.enums import AiLevel, AiPhase, AiTaskStatus, DefectSeverity, DefectStatus


class AiTaskCreate(BaseModel):
    phase: AiPhase
    task_name: str = Field(min_length=2, max_length=160)
    level: AiLevel
    agent_name: str = Field(min_length=2, max_length=60)
    status: AiTaskStatus
    correctness: int = Field(ge=0, le=5)
    completeness: int = Field(ge=0, le=5)
    runnability: int = Field(ge=0, le=5)
    maintainability: int = Field(ge=0, le=5)
    compliance: int = Field(ge=0, le=5)
    human_minutes: int = Field(default=0, ge=0, le=100000)
    retries: int = Field(default=0, ge=0, le=100)
    occurred_at: date | None = None
    notes: str = Field(default="", max_length=2000)


class AiTaskUpdate(BaseModel):
    phase: AiPhase | None = None
    task_name: str | None = Field(default=None, min_length=2, max_length=160)
    level: AiLevel | None = None
    agent_name: str | None = Field(default=None, min_length=2, max_length=60)
    status: AiTaskStatus | None = None
    correctness: int | None = Field(default=None, ge=0, le=5)
    completeness: int | None = Field(default=None, ge=0, le=5)
    runnability: int | None = Field(default=None, ge=0, le=5)
    maintainability: int | None = Field(default=None, ge=0, le=5)
    compliance: int | None = Field(default=None, ge=0, le=5)
    human_minutes: int | None = Field(default=None, ge=0, le=100000)
    retries: int | None = Field(default=None, ge=0, le=100)
    occurred_at: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class DefectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    phase: AiPhase
    category: str = Field(min_length=2, max_length=40)
    severity: DefectSeverity
    occurrences: int = Field(default=1, ge=1, le=1000)
    ai_related: bool = False
    status: DefectStatus = DefectStatus.OPEN
    found_at: date | None = None
    root_cause: str = Field(default="", max_length=2000)
    fix_action: str = Field(default="", max_length=2000)


class DefectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    phase: AiPhase | None = None
    category: str | None = Field(default=None, min_length=2, max_length=40)
    severity: DefectSeverity | None = None
    occurrences: int | None = Field(default=None, ge=1, le=1000)
    ai_related: bool | None = None
    status: DefectStatus | None = None
    found_at: date | None = None
    root_cause: str | None = Field(default=None, max_length=2000)
    fix_action: str | None = Field(default=None, max_length=2000)
