"""
Pydantic models for API requests and responses.

This module contains all the data models used for API validation
and serialization in the Agent LLM Deployment System.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="System health status")
    timestamp: datetime = Field(..., description="Response timestamp")
    version: str = Field(..., description="API version")


class TaskRequest(BaseModel):
    """Task request model for autonomous development."""
    email: str = Field(..., description="Student email address")
    secret: str = Field(..., description="Authentication secret")
    nonce: str = Field(..., description="Unique request identifier")
    task: str = Field(..., description="Unique task identifier")
    round: int = Field(..., description="Round number (1 for new, 2+ for updates)")
    brief: str = Field(..., description="Natural language project brief")
    checks: List[str] = Field(..., description="Evaluation criteria")
    evaluation_url: str = Field(..., description="Callback URL for results")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="File attachments")
    endpoint: Optional[str] = Field(None, description="Student API endpoint")

    @field_validator("round")
    @classmethod
    def validate_round(cls, v):
        """Validate round number."""
        if v < 1:
            raise ValueError("Round must be 1 or greater")
        return v


class TaskResponse(BaseModel):
    """Task response model."""
    task: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Status message")
    nonce: str = Field(..., description="Request nonce")
    estimated_completion_time_minutes: int = Field(..., description="Estimated completion time")


class TaskStatusResponse(BaseModel):
    """Task status response model."""
    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Current task status")
    created_at: datetime = Field(..., description="Task creation time")
    updated_at: datetime = Field(..., description="Last update time")


class EvaluationResult(BaseModel):
    """Evaluation result model."""
    task_id: str = Field(..., description="Task identifier")
    status: str = Field(..., description="Evaluation status")
    repo_url: str = Field(..., description="GitHub repository URL")
    pages_url: str = Field(..., description="GitHub Pages URL")
    checks_passed: List[str] = Field(..., description="Passed checks")
    checks_failed: List[str] = Field(..., description="Failed checks")
    score: float = Field(..., description="Overall score")
    feedback: str = Field(..., description="Detailed feedback")
    logs: Dict[str, Any] = Field(..., description="Execution logs")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


class TaskTemplateModel(BaseModel):
    """Task template model."""
    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    brief_template: str = Field(..., description="Brief template")
    checks_template: List[str] = Field(..., description="Check templates")
    attachments_template: List[Dict[str, Any]] = Field(..., description="Attachment templates")
    is_active: bool = Field(True, description="Whether template is active")


class SubmissionModel(BaseModel):
    """Submission model."""
    id: int = Field(..., description="Submission ID")
    email: str = Field(..., description="Student email")
    endpoint: str = Field(..., description="Student API endpoint")
    secret: str = Field(..., description="Authentication secret")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TaskModel(BaseModel):
    """Task model."""
    id: int = Field(..., description="Task ID")
    submission_id: int = Field(..., description="Associated submission ID")
    task_id: str = Field(..., description="Unique task identifier")
    round: int = Field(..., description="Task round")
    nonce: str = Field(..., description="Task nonce")
    brief: str = Field(..., description="Task brief")
    checks: List[str] = Field(..., description="Evaluation checks")
    attachments: List[Dict[str, Any]] = Field(..., description="Task attachments")
    status: str = Field(..., description="Task status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class RepositoryModel(BaseModel):
    """Repository model."""
    id: int = Field(..., description="Repository ID")
    task_id: int = Field(..., description="Associated task ID")
    repo_url: str = Field(..., description="Repository URL")
    commit_sha: str = Field(..., description="Git commit SHA")
    pages_url: Optional[str] = Field(None, description="GitHub Pages URL")
    submitted_at: datetime = Field(..., description="Submission timestamp")


class EvaluationModel(BaseModel):
    """Evaluation model."""
    id: int = Field(..., description="Evaluation ID")
    repository_id: int = Field(..., description="Associated repository ID")
    check_name: str = Field(..., description="Check name")
    status: str = Field(..., description="Evaluation status")
    score: Optional[float] = Field(None, description="Check score")
    reason: Optional[str] = Field(None, description="Evaluation reason")
    logs: Optional[Dict[str, Any]] = Field(None, description="Evaluation logs")
    evaluated_at: datetime = Field(..., description="Evaluation timestamp")
    duration_seconds: Optional[float] = Field(None, description="Evaluation duration")
