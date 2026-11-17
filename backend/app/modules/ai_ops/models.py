from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AiTask(Base, TimestampMixin):
    __tablename__ = "ai_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    phase: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    task_name: Mapped[str] = mapped_column(String(160), nullable=False)
    level: Mapped[str] = mapped_column(String(5), index=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    correctness: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completeness: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    runnability: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    maintainability: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    compliance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    human_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)


class Defect(Base, TimestampMixin):
    __tablename__ = "defects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    phase: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    occurrences: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ai_related: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(10), default="OPEN", nullable=False)
    found_at: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, default="", nullable=False)
    fix_action: Mapped[str] = mapped_column(Text, default="", nullable=False)
