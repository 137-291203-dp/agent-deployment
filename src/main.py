"""
Main FastAPI application for Agent LLM Deployment System.

This is the main entry point that creates and configures the FastAPI app
with all routes, middleware, and dependencies for the autonomous AI web developer.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from src.core.config import settings
from src.core.logging import setup_logging
from src.api.routes import router
from src.services.database import DatabaseService
from src.services.github import GitHubService
from src.services.llm import LLMService
from src.agent.orchestrator import TaskOrchestrator

# Setup logging
setup_logging()
logger = structlog.get_logger(__name__)

# Global services
db_service: DatabaseService = None
github_service: GitHubService = None
llm_service: LLMService = None
task_orchestrator: TaskOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    global db_service, github_service, llm_service, task_orchestrator

    # Startup
    logger.info("Starting Agent LLM Deployment System - Autonomous AI Web Developer")

    try:
        # Initialize database service
        db_service = DatabaseService()
        await db_service.initialize()
        logger.info("Database service initialized")

        # Initialize GitHub service
        github_service = GitHubService()
        logger.info("GitHub service initialized")

        # Initialize LLM service with multiple providers
        # Ensure settings are properly loaded first
        from src.core.config import get_settings
        _ = get_settings()  # This ensures settings are initialized
        llm_service = LLMService()
        logger.info("LLM service initialized")

        # Initialize task orchestrator
        task_orchestrator = TaskOrchestrator(
            db_service=db_service,
            github_service=github_service,
            llm_service=llm_service
        )
        logger.info("Task orchestrator initialized")
        
        # Inject services into routes module
        import src.api.routes as routes_module
        routes_module.db_service = db_service
        routes_module.task_orchestrator = task_orchestrator
        logger.info("Services injected into routes")

    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Agent LLM Deployment System")

    try:
        if db_service:
            await db_service.close()
        if github_service:
            await github_service.close()
        if llm_service:
            await llm_service.close()
        if task_orchestrator:
            await task_orchestrator.close()
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Create FastAPI app with lifespan management
    app = FastAPI(
        title="Agent LLM Deployment System",
        description="Autonomous AI Web Developer - Build, Deploy, and Update Web Applications",
        version="1.0.0",
        docs_url="/docs",  # Swagger UI
        redoc_url="/redoc",  # ReDoc
        openapi_url="/openapi.json",  # OpenAPI schema
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router, prefix="/api")

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "services": {
                "database": "connected" if db_service else "disconnected",
                "github": "connected" if github_service else "disconnected",
                "llm": "connected" if llm_service else "disconnected",
                "orchestrator": "ready" if task_orchestrator else "not_ready",
            }
        }

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Agent LLM Deployment System - Autonomous AI Web Developer",
            "docs": "/docs",
            "health": "/health",
            "version": "1.0.0",
            "features": [
                "Autonomous End-to-End Development",
                "Multi-Round Capability",
                "Automated GitHub Deployment",
                "Think-Plan-Act-Review Methodology",
                "Multi-LLM Provider Support"
            ]
        }

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for unhandled errors."""
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)}
        )

    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
