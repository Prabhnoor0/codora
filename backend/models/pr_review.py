"""PR Review models."""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, JSON, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class PRReview(Base):
    __tablename__ = "pr_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    repository_full_name: Mapped[str] = mapped_column(String(300))
    pr_number: Mapped[int] = mapped_column(Integer)
    pr_title: Mapped[str | None] = mapped_column(String(500))
    pr_url: Mapped[str | None] = mapped_column(String(500))

    # Review results
    overall_assessment: Mapped[str | None] = mapped_column(Text)
    quality_score: Mapped[float | None] = mapped_column(Float)  # 0-100
    issues_found: Mapped[list | None] = mapped_column(JSON)  # [{type, severity, file, line, message, suggestion}]
    bugs: Mapped[list | None] = mapped_column(JSON)
    security_issues: Mapped[list | None] = mapped_column(JSON)
    performance_issues: Mapped[list | None] = mapped_column(JSON)
    style_issues: Mapped[list | None] = mapped_column(JSON)
    architecture_violations: Mapped[list | None] = mapped_column(JSON)
    positive_aspects: Mapped[list | None] = mapped_column(JSON)
    suggestions: Mapped[list | None] = mapped_column(JSON)

    files_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    lines_reviewed: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship(back_populates="pr_reviews")
