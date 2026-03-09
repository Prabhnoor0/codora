"""User and developer profile models."""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, JSON, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    github_login: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    github_name: Mapped[str | None] = mapped_column(String(200))
    github_email: Mapped[str | None] = mapped_column(String(255))
    github_avatar_url: Mapped[str | None] = mapped_column(String(500))
    github_bio: Mapped[str | None] = mapped_column(Text)
    github_location: Mapped[str | None] = mapped_column(String(200))
    github_company: Mapped[str | None] = mapped_column(String(200))
    github_blog: Mapped[str | None] = mapped_column(String(500))
    github_followers: Mapped[int] = mapped_column(Integer, default=0)
    github_following: Mapped[int] = mapped_column(Integer, default=0)
    github_public_repos: Mapped[int] = mapped_column(Integer, default=0)

    # OAuth tokens
    github_access_token: Mapped[str | None] = mapped_column(String(500))

    # Developer knowledge profile (derived from GitHub data)
    skill_vector: Mapped[dict | None] = mapped_column(JSON)  # {python: 0.9, js: 0.7, ...}
    language_breakdown: Mapped[dict | None] = mapped_column(JSON)  # {Python: 45%, JS: 30%, ...}
    top_languages: Mapped[list | None] = mapped_column(JSON)  # ["Python", "JavaScript", ...]
    contribution_domains: Mapped[list | None] = mapped_column(JSON)  # ["backend", "ml", ...]
    expertise_level: Mapped[str] = mapped_column(String(20), default="beginner")  # beginner/intermediate/advanced
    total_commits: Mapped[int] = mapped_column(Integer, default=0)
    total_prs: Mapped[int] = mapped_column(Integer, default=0)
    total_issues_closed: Mapped[int] = mapped_column(Integer, default=0)
    profile_analyzed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_github_sync: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    learning_paths: Mapped[list["LearningPath"]] = relationship(back_populates="user", lazy="selectin")
    pr_reviews: Mapped[list["PRReview"]] = relationship(back_populates="user")
