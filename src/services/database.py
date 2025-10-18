"""
Database service for Agent LLM Deployment System.

This module provides async database operations using SQLAlchemy
and manages database connections for the autonomous AI web developer.
"""

import asyncio
from typing import Optional, List, Dict, Any
import json
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_, or_

from src.core.config import settings
from src.core.logging import get_logger
from src.models.database import (
    Base, Submission, Task, Repository, Evaluation, TaskTemplate,
    TaskStatus, EvaluationStatus
)

logger = get_logger(__name__)


class DatabaseService:
    """Async database service for autonomous AI web developer."""

    def __init__(self):
        self.engine = None
        self.async_session = None

    async def initialize(self):
        """Initialize database connection and create tables."""
        import asyncio
        
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                db_url = settings.DATABASE_URL
                
                # Convert to async driver based on database type
                if db_url.startswith('sqlite:///'):
                    async_db_url = db_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
                elif db_url.startswith('postgresql://'):
                    async_db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
                else:
                    # Already has async driver specified
                    async_db_url = db_url
                
                # Create async engine
                self.engine = create_async_engine(
                    async_db_url,
                    echo=settings.DEBUG,
                    future=True,
                )

                # Create tables with retry
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                # Create session factory
                self.async_session = async_sessionmaker(
                    self.engine, class_=AsyncSession, expire_on_commit=False
                )

                # Initialize with default templates
                await self._initialize_default_templates()

                logger.info("Database service initialized")
                return

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Database connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to initialize database after {max_retries} attempts: {e}")
                    raise

    async def close(self):
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()

    def get_session(self) -> AsyncSession:
        """Get database session context manager."""
        if not self.async_session:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.async_session()

    async def get_or_create_submission(
        self, email: str, endpoint: str, secret: str
    ) -> Submission:
        """Get existing submission or create new one."""
        async with self.get_session() as session:
            # Try to find existing submission
            result = await session.execute(
                select(Submission).where(Submission.email == email)
            )
            submission = result.scalar_one_or_none()

            if submission:
                return submission

            # Create new submission
            submission = Submission(
                email=email,
                endpoint=endpoint,
                secret=secret
            )
            session.add(submission)
            await session.commit()
            await session.refresh(submission)
            return submission

    async def get_submission_by_email(self, email: str) -> Optional[Submission]:
        """Get submission by email."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Submission).where(Submission.email == email)
            )
            return result.scalar_one_or_none()

    async def create_task(self, submission_id: int, task_data: Dict[str, Any]) -> Task:
        """Create a new task."""
        async with self.get_session() as session:
            # Remove email from task_data as it's not a Task field
            task_dict = {k: v for k, v in task_data.items() if k != 'email'}
            task = Task(submission_id=submission_id, **task_dict)
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task

    async def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Get task by task_id."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Task).where(Task.task_id == task_id)
            )
            return result.scalar_one_or_none()

    async def update_task_status(self, task_id: int, status: str):
        """Update task status."""
        async with self.get_session() as session:
            task = await session.get(Task, task_id)
            if task:
                task.status = status
                if status == "processing":
                    task.started_at = datetime.now(timezone.utc)
                elif status == "completed":
                    task.completed_at = datetime.now(timezone.utc)
                await session.commit()

    async def create_repository(self, task_id: int, repo_data: Dict[str, Any]) -> Repository:
        """Create a new repository record."""
        async with self.get_session() as session:
            repo = Repository(task_id=task_id, **repo_data)
            session.add(repo)
            await session.commit()
            await session.refresh(repo)
            return repo

    async def _initialize_default_templates(self):
        """Initialize database with default task templates."""
        templates_data = [
            {
                'template_id': 'markdown-to-html',
                'name': 'Markdown to HTML Converter',
                'description': 'Create an app that converts Markdown to HTML with syntax highlighting',
                'brief_template': 'Create a single-page web application that allows a user to type Markdown text in a textarea and see the rendered HTML in real-time in a preview pane next to it. Use a popular library like Showdown.js or Marked.js from a CDN. The layout should be professional, with the textarea on the left and the preview on the right.',
                'checks_template': [
                    'The application must have an index.html, a script.js, and a style.css file.',
                    'The page must use a CDN link for a Markdown parsing library.',
                    'The HTML preview must update automatically as the user types in the textarea.',
                    'The final README.md file must be updated with deployment links and a screenshot.'
                ],
                'attachments_template': []
            },
            {
                'template_id': 'sales-summary',
                'name': 'Sales Summary Application',
                'description': 'Create an app that processes CSV data and displays sales summaries',
                'brief_template': 'Publish a single-page site that fetches data.csv from attachments, sums its sales column, sets the title to "Sales Summary {seed}", displays the total inside #total-sales, and loads Bootstrap 5 from jsdelivr.',
                'checks_template': [
                    'js: document.title === `Sales Summary {seed}`',
                    'js: !!document.querySelector("link[href*=\'bootstrap\']")',
                    'js: Math.abs(parseFloat(document.querySelector("#total-sales").textContent) - {result}) < 0.01'
                ],
                'attachments_template': [
                    {
                        'name': 'data.csv',
                        'url': 'data:text/csv;base64,{seed}'
                    }
                ]
            },
            {
                'template_id': 'github-user-info',
                'name': 'GitHub User Information',
                'description': 'Create an app that fetches and displays GitHub user information',
                'brief_template': 'Publish a Bootstrap page with form id="github-user-{seed}" that fetches a GitHub username, optionally uses ?token=, and displays the account creation date in YYYY-MM-DD UTC inside #github-created-at.',
                'checks_template': [
                    'js: document.querySelector("#github-user-{seed}").tagName === "FORM"',
                    'js: document.querySelector("#github-created-at").textContent.includes("20")',
                    'js: !!document.querySelector("script").textContent.includes("https://api.github.com/users/")'
                ],
                'attachments_template': []
            }
        ]

        async with self.get_session() as session:
            for template_data in templates_data:
                # Check if template exists
                result = await session.execute(
                    select(TaskTemplate).where(
                        TaskTemplate.template_id == template_data['template_id']
                    )
                )
                existing = result.scalar_one_or_none()

                if not existing:
                    template = TaskTemplate(**template_data)
                    session.add(template)

            await session.commit()

        logger.info("Database templates initialized")
    
    async def get_task_by_task_id_and_round(self, task_id: str, round: int):
        """Get task by task_id and round number."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Task).where(
                    Task.task_id == task_id,
                    Task.round == round
                )
            )
            return result.scalar_one_or_none()
    
    async def update_task_deployment(self, task_id: int, repo_url: str, pages_url: str):
        """Update task with deployment information."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if task:
                task.repo_url = repo_url
                task.pages_url = pages_url
                task.updated_at = datetime.now(timezone.utc)
                await session.commit()
    
    async def update_task_error(self, task_id: int, error_message: str):
        """Update task with error message."""
        async with self.get_session() as session:
            result = await session.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalar_one_or_none()
            
            if task:
                task.error_message = error_message
                task.updated_at = datetime.now(timezone.utc)
                await session.commit()
