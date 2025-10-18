"""
Agent tools for Agent LLM Deployment System.

This module provides tools that the AI agent can use to interact with
the development environment, file system, and external services.
"""

import os
import json
import asyncio
import tempfile
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class AgentTools:
    """Collection of tools available to the AI agent."""

    def __init__(self):
        self.workspaces = {}

    async def close(self):
        """Clean up all workspaces."""
        for workspace_path in self.workspaces.values():
            await self.cleanup_workspace(workspace_path)

    async def create_workspace(self, workspace_path: str) -> str:
        """Create a new development workspace."""
        try:
            # Create directory
            Path(workspace_path).mkdir(parents=True, exist_ok=True)

            # Initialize git repository
            await self._run_command("git init", workspace_path)
            await self._run_command("git config user.name 'AI Agent'", workspace_path)
            await self._run_command("git config user.email 'agent@llm-deployment.com'", workspace_path)

            # Store workspace reference
            self.workspaces[workspace_path] = workspace_path

            logger.info(f"Created workspace at {workspace_path}")
            return workspace_path

        except Exception as e:
            logger.error(f"Failed to create workspace {workspace_path}", error=str(e))
            raise

    async def cleanup_workspace(self, workspace_path: str):
        """Clean up a development workspace."""
        try:
            if os.path.exists(workspace_path):
                shutil.rmtree(workspace_path)
                logger.info(f"Cleaned up workspace {workspace_path}")

            # Remove from tracking
            self.workspaces.pop(workspace_path, None)

        except Exception as e:
            logger.error(f"Failed to cleanup workspace {workspace_path}", error=str(e))

    async def write_file(self, workspace_path: str, filename: str, content: str) -> bool:
        """Write content to a file in the workspace."""
        try:
            file_path = Path(workspace_path) / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Wrote file {filename} ({len(content)} chars)")
            return True

        except Exception as e:
            logger.error(f"Failed to write file {filename}", error=str(e))
            return False

    async def read_file(self, workspace_path: str, filename: str) -> Optional[str]:
        """Read content from a file in the workspace."""
        try:
            file_path = Path(workspace_path) / filename

            if not file_path.exists():
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.info(f"Read file {filename} ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"Failed to read file {filename}", error=str(e))
            return None

    async def list_files(self, workspace_path: str) -> List[str]:
        """List files in the workspace."""
        try:
            path_obj = Path(workspace_path)

            if not path_obj.exists():
                return []

            files = []
            for file_path in path_obj.rglob("*"):
                if file_path.is_file():
                    files.append(str(file_path.relative_to(path_obj)))

            logger.info(f"Listed {len(files)} files in workspace")
            return files

        except Exception as e:
            logger.error(f"Failed to list files in {workspace_path}", error=str(e))
            return []

    async def run_command(self, command: str, workspace_path: str) -> Dict[str, Any]:
        """Run a shell command in the workspace."""
        try:
            # Change to workspace directory
            old_cwd = os.getcwd()
            os.chdir(workspace_path)

            result = await self._run_command(command, workspace_path)

            # Restore original directory
            os.chdir(old_cwd)

            return result

        except Exception as e:
            logger.error(f"Failed to run command {command}", error=str(e))
            return {"success": False, "error": str(e)}

    async def _run_command(self, command: str, workspace_path: str) -> Dict[str, Any]:
        """Internal method to run shell commands."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace_path
            )

            stdout, stderr = await process.communicate()

            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore')
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def validate_html(self, html_content: str) -> Dict[str, Any]:
        """Validate HTML content using tidy or similar tools."""
        # Placeholder for HTML validation
        # In a real implementation, this would use HTML Tidy or similar

        return {
            "valid": True,
            "errors": [],
            "warnings": []
        }

    async def validate_css(self, css_content: str) -> Dict[str, Any]:
        """Validate CSS content."""
        # Placeholder for CSS validation
        return {
            "valid": True,
            "errors": [],
            "warnings": []
        }

    async def validate_javascript(self, js_content: str) -> Dict[str, Any]:
        """Validate JavaScript content."""
        # Placeholder for JavaScript validation
        return {
            "valid": True,
            "errors": [],
            "warnings": []
        }

    async def check_accessibility(self, html_content: str) -> Dict[str, Any]:
        """Check accessibility of HTML content."""
        # Placeholder for accessibility checking
        return {
            "score": 0.8,
            "issues": [],
            "recommendations": ["Add alt text to images"]
        }

    async def run_browser_test(self, url: str) -> Dict[str, Any]:
        """Run browser-based tests on a deployed application."""
        # Placeholder for browser testing using Playwright
        return {
            "tests_passed": 5,
            "tests_failed": 0,
            "coverage": 0.85,
            "performance_score": 0.9
        }

    async def generate_screenshot(self, url: str) -> Optional[str]:
        """Generate a screenshot of the deployed application."""
        # Placeholder for screenshot generation
        return f"screenshot_{url.replace('/', '_')}.png"

    async def search_codebase(self, query: str, workspace_path: str) -> List[Dict[str, Any]]:
        """Search the codebase for specific patterns or content."""
        # Placeholder for code search functionality
        return [
            {
                "file": "index.html",
                "line": 10,
                "content": f"Found: {query}",
                "context": "Line with search term"
            }
        ]

    async def get_project_structure(self, workspace_path: str) -> Dict[str, Any]:
        """Get the current project structure and file organization."""
        files = await self.list_files(workspace_path)

        structure = {
            "root_files": [],
            "directories": {},
            "total_files": len(files)
        }

        for file_path in files:
            path_obj = Path(file_path)

            if path_obj.parent == Path("."):
                structure["root_files"].append(file_path)
            else:
                dir_name = str(path_obj.parent)
                if dir_name not in structure["directories"]:
                    structure["directories"][dir_name] = []
                structure["directories"][dir_name].append(path_obj.name)

        return structure

    async def create_backup(self, workspace_path: str) -> str:
        """Create a backup of the current workspace."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{workspace_path}_backup_{timestamp}"

        try:
            shutil.copytree(workspace_path, backup_path)
            logger.info(f"Created backup at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup", error=str(e))
            raise

    async def restore_backup(self, backup_path: str, target_path: str) -> bool:
        """Restore from a backup."""
        try:
            if os.path.exists(target_path):
                shutil.rmtree(target_path)

            shutil.copytree(backup_path, target_path)
            logger.info(f"Restored backup from {backup_path} to {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup", error=str(e))
            return False
