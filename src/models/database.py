"""
Database models for Agent LLM Deployment System.

This module defines SQLAlchemy models for the database schema
with async support for the autonomous AI web developer.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    Integer, String, Text, Boolean, Float, ForeignKey, JSON, Enum, UniqueConstraint
)
from sqlalchemy.types import DateTime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""
    pass


class TaskStatus(str):
    """Enumeration of task statuses."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationStatus(str):
    """Enumeration of evaluation statuses."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class Submission(Base):
    """Model for storing student submissions and API endpoints."""

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    github_username: Mapped[Optional[str]] = mapped_column(String(255))
    github_repo_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="submission", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint('email', 'endpoint', name='unique_submission'),
    )


class Task(Base):
    """Model for storing autonomous development tasks."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    submission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("submissions.id"), nullable=False
    )

    # Task identification
    task_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    round: Mapped[int] = mapped_column(Integer, nullable=False)
    nonce: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Task content
    brief: Mapped[str] = mapped_column(Text, nullable=False)
    checks: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    attachments: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    evaluation_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Task lifecycle
    status: Mapped[str] = mapped_column(String(50), default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Results
    repo_url: Mapped[Optional[str]] = mapped_column(String(500))
    pages_url: Mapped[Optional[str]] = mapped_column(String(500))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="tasks")
    repositories: Mapped[List["Repository"]] = relationship(
        "Repository", back_populates="task", cascade="all, delete-orphan"
    )


class Repository(Base):
    """Model for storing repository information."""

    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False)

    # Repository details
    repo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    pages_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Timing
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="repositories")
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation", back_populates="repository", cascade="all, delete-orphan"
    )


class Evaluation(Base):
    """Model for storing evaluation results."""

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id"), nullable=False
    )

    # Evaluation details
    check_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    logs: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON)

    # Metadata
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)

    # Relationships
    repository: Mapped["Repository"] = relationship("Repository", back_populates="evaluations")
    # Note: Task can be accessed via repository.task


class TaskTemplate(Base):
    """Model for storing task templates used to generate tasks."""

    __tablename__ = "task_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    # Template content
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Round 1 configuration
    brief_template: Mapped[str] = mapped_column(Text, nullable=False)
    checks_template: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    attachments_template: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)

    # Round 2 configuration (optional)
    round2_brief_template: Mapped[Optional[str]] = mapped_column(Text)
    round2_checks_template: Mapped[Optional[List[str]]] = mapped_column(JSON)
    round2_attachments_template: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON)

    # Template metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Seed configuration for randomization
    seed_config: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)


class SystemConfig(Base):
    """Model for storing system-wide configuration."""

    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    value: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
