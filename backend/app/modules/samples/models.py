from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.modules.projects.models import Project  # noqa: F401


class Sample(Base, TimestampMixin):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    spec: Mapped[str] = mapped_column(String(80), nullable=False)
    produced_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)

    project = relationship("Project", back_populates="samples")
    test_records = relationship("TestRecord", back_populates="sample")
