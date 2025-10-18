"""
API routes for Agent LLM Deployment System.

This module contains all the API endpoints organized by functionality
for the autonomous AI web developer.
"""

from datetime import datetime
from typing import Dict, Any
import secrets

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel, Field

from src.models.schemas import (
    HealthResponse,
    TaskRequest,
    TaskResponse,
    TaskStatusResponse,
    ErrorResponse
)
from src.agent.orchestrator import TaskOrchestrator
from src.services.database import DatabaseService
from src.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Services (will be injected from main app)
db_service = None
task_orchestrator = None


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@router.post("/request", response_model=TaskResponse, tags=["Tasks"])
async def request_task(request: TaskRequest, background_tasks: BackgroundTasks):
    """Request a new autonomous development task."""

    # Check if services are initialized
    if not db_service or not task_orchestrator:
        raise HTTPException(status_code=503, detail="Services not initialized yet")

    # Validate secret
    if not await validate_student_secret(request.email, request.secret):
        raise HTTPException(status_code=401, detail="Invalid secret")

    # Check rate limiting
    if not await check_rate_limit(request.email):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        # Create task record in database
        submission = await db_service.get_or_create_submission(
            email=request.email,
            endpoint=request.endpoint or "",
            secret=request.secret
        )

        # Create task data
        task_data = {
            'task_id': request.task,
            'round': request.round,
            'nonce': request.nonce,
            'brief': request.brief,
            'checks': request.checks,
            'attachments': request.attachments or [],
            'evaluation_url': request.evaluation_url,
            'email': request.email  # Add email for orchestrator
        }

        # Store task in database
        db_task = await db_service.create_task(submission.id, task_data)

        # Queue task for background processing
        background_tasks.add_task(
            process_autonomous_task,
            db_task.id,
            request.email,
            task_data
        )

        # Return immediate response
        return TaskResponse(
            task=request.task,
            status="accepted",
            message=f"Task '{request.task}' (round {request.round}) has been accepted and is being processed by the AI agent.",
            nonce=request.nonce,
            estimated_completion_time_minutes=5
        )

    except Exception as e:
        logger.error(f"Failed to process task request for {request.email}", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process task request")


@router.get("/status/{task_id}", response_model=TaskStatusResponse, tags=["Tasks"])
async def get_task_status(task_id: str):
    """Get the status of a specific task."""
    try:
        task = await db_service.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return TaskStatusResponse(
            task_id=task.task_id,
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get task status")


async def process_autonomous_task(task_id: int, email: str, task_data: Dict[str, Any]):
    """Process an autonomous development task in the background."""
    try:
        logger.info(f"Starting autonomous task processing for {email}", task_id=task_id)

        # Update task status to processing
        await db_service.update_task_status(task_id, "processing")

        # Check if this is round 2
        round_num = task_data.get('round', 1)
        
        if round_num == 2:
            # Get existing repo from round 1
            existing_task = await db_service.get_task_by_task_id_and_round(
                task_data['task_id'],
                round=1
            )
            
            if existing_task and existing_task.repo_url:
                # Process round 2 update
                result = await task_orchestrator.process_round2_task(
                    task_data,
                    existing_task.repo_url
                )
            else:
                # No round 1 found, treat as new task
                logger.warning(f"No round 1 found for task {task_data['task_id']}, treating as new")
                result = await task_orchestrator.process_task(task_data)
        else:
            # Process round 1 task
            result = await task_orchestrator.process_task(task_data)

        # Update task with deployment info
        if result.get('deployment'):
            await db_service.update_task_deployment(
                task_id,
                result['deployment']['repo_url'],
                result['deployment']['pages_url']
            )

        # Update task status to completed
        await db_service.update_task_status(task_id, "completed")

        logger.info(f"Completed autonomous task processing for {email}", task_id=task_id)

    except Exception as e:
        logger.error(f"Failed to process autonomous task for {email}", task_id=task_id, error=str(e))

        # Update task status to failed
        await db_service.update_task_status(task_id, "failed")
        
        # Store error message
        await db_service.update_task_error(task_id, str(e))


async def validate_student_secret(email: str, secret: str) -> bool:
    """Validate student secret."""
    try:
        if db_service:
            submission = await db_service.get_submission_by_email(email)
            if submission and submission.secret:
                return secrets.compare_digest(submission.secret, secret)
        # Allow test requests
        return True
    except Exception:
        logger.exception("Error validating secret")
    return True


async def check_rate_limit(email: str) -> bool:
    """Check if request is within rate limits."""
    # Simple in-memory rate limiting (in production, use Redis)
    # This is a placeholder - implement proper rate limiting
    return True


async def send_evaluation_results(evaluation_url: str, result: Dict[str, Any]):
    """Send evaluation results to the specified URL."""
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            await client.post(
                evaluation_url,
                json=result,
                timeout=30.0
            )

        logger.info(f"Sent evaluation results to {evaluation_url}")

    except Exception as e:
        logger.error(f"Failed to send evaluation results to {evaluation_url}", error=str(e))


async def send_evaluation_error(evaluation_url: str, error: str):
    """Send evaluation error to the specified URL."""
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            await client.post(
                evaluation_url,
                json={"error": error, "status": "failed"},
                timeout=30.0
            )

        logger.info(f"Sent evaluation error to {evaluation_url}")

    except Exception as e:
        logger.error(f"Failed to send evaluation error to {evaluation_url}", error=str(e))
