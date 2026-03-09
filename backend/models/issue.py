"""Issue and recommendation models."""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, JSON, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from database import Base


class IssueDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id"))
    github_issue_id: Mapped[int] = mapped_column(Integer)
    number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(20), default="open")
    labels: Mapped[list | None] = mapped_column(JSON)
    assignees: Mapped[list | None] = mapped_column(JSON)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    github_url: Mapped[str] = mapped_column(String(500))

    # ML predictions
    difficulty: Mapped[IssueDifficulty | None] = mapped_column(Enum(IssueDifficulty))
    difficulty_confidence: Mapped[float | None] = mapped_column(Float)
    predicted_affected_files: Mapped[list | None] = mapped_column(JSON)  # [{path, confidence}]
    required_skills: Mapped[list | None] = mapped_column(JSON)
    required_concepts: Mapped[list | None] = mapped_column(JSON)

    # Embeddings
    embedding_indexed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    github_created_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    repository: Mapped["Repository"] = relationship(back_populates="issues")
    recommendations: Mapped[list["IssueRecommendation"]] = relationship(back_populates="issue")


class IssueRecommendation(Base):
    __tablename__ = "issue_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    issue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("issues.id"))
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id"))

    readiness_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    skill_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty_match_score: Mapped[float] = mapped_column(Float, default=0.0)
    familiarity_score: Mapped[float] = mapped_column(Float, default=0.0)

    missing_skills: Mapped[list | None] = mapped_column(JSON)
    learning_resources: Mapped[list | None] = mapped_column(JSON)
    tutor_content: Mapped[dict | None] = mapped_column(JSON)  # Full issue tutor response

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    issue: Mapped["Issue"] = relationship(back_populates="recommendations")
