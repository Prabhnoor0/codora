"""Repository and analysis job models."""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, JSON, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from database import Base


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DifficultyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(300), unique=True, nullable=False)  # owner/repo
    owner: Mapped[str] = mapped_column(String(150), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(500))
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    language: Mapped[str | None] = mapped_column(String(100))
    topics: Mapped[list | None] = mapped_column(JSON)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)
    open_issues_count: Mapped[int] = mapped_column(Integer, default=0)
    license: Mapped[str | None] = mapped_column(String(100))

    # Analysis results
    analysis_status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus), default=AnalysisStatus.PENDING
    )
    analysis_progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    analysis_stage: Mapped[str | None] = mapped_column(String(100))

    # Derived intelligence
    purpose: Mapped[str | None] = mapped_column(Text)
    tech_stack: Mapped[list | None] = mapped_column(JSON)
    architecture_summary: Mapped[str | None] = mapped_column(Text)
    main_modules: Mapped[list | None] = mapped_column(JSON)
    subsystems: Mapped[list | None] = mapped_column(JSON)  # [{name, files, description, complexity}]
    architecture_diagram: Mapped[dict | None] = mapped_column(JSON)  # React Flow nodes/edges
    difficulty_level: Mapped[DifficultyLevel | None] = mapped_column(Enum(DifficultyLevel))
    contribution_areas: Mapped[list | None] = mapped_column(JSON)
    learning_prerequisites: Mapped[list | None] = mapped_column(JSON)
    file_tree: Mapped[dict | None] = mapped_column(JSON)

    # Embeddings indexed?
    embeddings_indexed: Mapped[bool] = mapped_column(Boolean, default=False)
    graph_built: Mapped[bool] = mapped_column(Boolean, default=False)
    issues_analyzed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_analyzed: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    issues: Mapped[list["Issue"]] = relationship(back_populates="repository")
    learning_paths: Mapped[list["LearningPath"]] = relationship(back_populates="repository")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id"))
    celery_task_id: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[AnalysisStatus] = mapped_column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_stage: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
