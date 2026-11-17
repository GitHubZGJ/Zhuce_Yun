from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.modules.samples.models import Sample  # noqa: F401
from app.modules.users.models import User  # noqa: F401


class TestRecord(Base, TimestampMixin):
    __tablename__ = "test_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    sample_id: Mapped[int] = mapped_column(
        ForeignKey("samples.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    item: Mapped[str] = mapped_column(String(60), nullable=False)
    standard_value: Mapped[float] = mapped_column(Float, nullable=False)
    measured_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    rule: Mapped[str] = mapped_column(String(10), default="GTE", nullable=False)
    conclusion: Mapped[str] = mapped_column(String(10), nullable=False)
    tested_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    tested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    remark: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    sample = relationship("Sample", back_populates="test_records")
    tester = relationship("User", back_populates="test_records")
