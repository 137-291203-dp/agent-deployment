"""
GitHub service for Agent LLM Deployment System.

This module handles GitHub integration including repository validation,
creation, and deployment for the autonomous AI web developer.
"""

import re
from typing import Dict, Any, Optional
import asyncio
from urllib.parse import urlparse

from github import Github, GithubException
from src.core.logging import get_logger
from src.core.config import settings

logger = get_logger(__name__)


class GitHubService:
    """Service for GitHub operations in autonomous AI web development."""

    def __init__(self):
        self.github = None
        if settings.github.personal_access_token:
            try:
                self.github = Github(settings.github.personal_access_token)
                logger.info("GitHub service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize GitHub client: {e}")
                self.github = None

    async def close(self):
        """Close GitHub connection."""
        if self.github:
            # GitHub client doesn't need explicit closing
            pass

    async def validate_repository(self, repo_url: str) -> Dict[str, Any]:
        """Validate a GitHub repository URL and return information."""
        if not self.github:
            return {
                'valid': False,
                'error': 'GitHub integration not available'
            }

        try:
            # Parse GitHub URL
            if not self._is_valid_github_url(repo_url):
                return {
                    'valid': False,
                    'error': 'Invalid GitHub URL format'
                }

            # Extract owner and repo name
            owner, repo_name = self._parse_github_url(repo_url)

            # Get repository
            repo = self.github.get_repo(f"{owner}/{repo_name}")

            # Check if repository exists and is accessible
            try:
                # Try to get basic info
                languages = repo.get_languages()
                has_license = repo.license is not None
                has_readme = False

                try:
                    repo.get_readme()
                    has_readme = True
                except GithubException:
                    pass

                # Check GitHub Pages
                pages_info = None
                pages_enabled = False
                pages_url = None

                try:
                    pages_info = repo.get_pages()
                    if pages_info and pages_info.status == "built":
                        pages_enabled = True
                        pages_url = pages_info.html_url
                except GithubException:
                    pass

                return {
                    'valid': True,
                    'has_license': has_license,
                    'has_readme': has_readme,
                    'languages': languages,
                    'pages_enabled': pages_enabled,
                    'pages_url': pages_url
                }

            except GithubException as e:
                logger.error(f"Error accessing repository {owner}/{repo_name}: {e}")
                return {
                    'valid': False,
                    'error': f'Repository not accessible: {str(e)}'
                }

        except Exception as e:
            logger.error(f"Error validating repository {repo_url}: {e}")
            return {
                'valid': False,
                'error': f'Validation failed: {str(e)}'
            }

    def _is_valid_github_url(self, url: str) -> bool:
        """Check if URL is a valid GitHub repository URL."""
        github_pattern = r'^https?://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+/?$'
        return bool(re.match(github_pattern, url))

    def _parse_github_url(self, url: str) -> tuple[str, str]:
        """Parse GitHub URL to extract owner and repository name."""
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')

        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1]
            return owner, repo

        raise ValueError(f"Invalid GitHub URL format: {url}")

    async def create_repository(
        self, name: str, description: str = "", private: bool = False
    ) -> Dict[str, Any]:
        """Create a new GitHub repository for autonomous deployment."""
        if not self.github:
            raise ValueError("GitHub integration not available")

        try:
            user = self.github.get_user()
            repo = user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=True,
                license_template="mit"
            )

            # Add initial commit with README
            await self._initialize_repository(repo)

            return {
                'id': repo.id,
                'name': repo.name,
                'full_name': repo.full_name,
                'html_url': repo.html_url,
                'clone_url': repo.clone_url,
                'ssh_url': repo.ssh_url,
                'created': True
            }

        except GithubException as e:
            logger.error(f"Failed to create repository {name}: {e}")
            raise ValueError(f"Failed to create repository: {str(e)}")

    async def _initialize_repository(self, repo) -> None:
        """Initialize repository with basic files."""
        try:
            # Create README.md
            readme_content = f"""# {repo.name}

Auto-generated web application created by Agent LLM Deployment System.

## Description

This application was automatically generated and deployed by an autonomous AI web developer.

## Deployment

- **Repository**: {repo.html_url}
- **Live Site**: Deployed via GitHub Pages

## Generated Files

- `index.html` - Main application file
- `style.css` - Application styles
- `script.js` - Application functionality

---

*Generated by Agent LLM Deployment System - Autonomous AI Web Developer*
"""

            # Create initial commit
            repo.create_file(
                path="README.md",
                message="Initial commit: Add README",
                content=readme_content,
                branch="main"
            )

        except GithubException as e:
            logger.warning(f"Failed to initialize repository {repo.name}: {e}")

    async def enable_pages(self, repo_url: str) -> str:
        """Enable GitHub Pages for a repository."""
        if not self.github:
            raise ValueError("GitHub integration not available")

        try:
            owner, repo_name = self._parse_github_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")

            # Enable Pages using direct API call
            try:
                # Use the underlying GitHub API directly
                url = f"{repo.url}/pages"
                headers, data = repo._requester.requestJsonAndCheck(
                    "POST",
                    url,
                    input={
                        "source": {
                            "branch": "main",
                            "path": "/"
                        }
                    }
                )
                logger.info("GitHub Pages enabled successfully")
            except GithubException as e:
                # Pages might already be enabled (409) or other error
                if e.status == 409:
                    logger.info("GitHub Pages already enabled")
                elif e.status == 404:
                    # Endpoint not available, Pages might already be on
                    logger.info("Pages API not available, checking if already enabled")
                else:
                    logger.warning(f"Could not automatically enable Pages: {e}")
                    logger.info("Repository created. Enable Pages manually in Settings > Pages")

            # Wait for Pages to be available
            await asyncio.sleep(5)

            # Get Pages URL
            try:
                pages = repo.get_pages()
                return pages.html_url
            except:
                # Pages not available yet, use default GitHub Pages URL
                return f"https://{owner}.github.io/{repo_name}/"

        except Exception as e:
            logger.error(f"Failed to enable Pages for {repo_url}: {e}")
            raise ValueError(f"Failed to enable Pages: {str(e)}")

    async def commit_files(self, repo_url: str, files: Dict[str, str], commit_message: str) -> bool:
        """Commit multiple files to a repository."""
        if not self.github:
            raise ValueError("GitHub integration not available")

        try:
            owner, repo_name = self._parse_github_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")

            # Get the main branch
            branch = repo.get_branch("main")

            # Create files
            for file_path, content in files.items():
                try:
                    repo.create_file(
                        path=file_path,
                        message=f"Add {file_path}",
                        content=content,
                        branch="main"
                    )
                except GithubException as e:
                    if e.status != 422:  # File already exists
                        logger.warning(f"Failed to create file {file_path}: {e}")

            logger.info(f"Committed {len(files)} files to {repo_url}")
            return True

        except Exception as e:
            logger.error(f"Failed to commit files to {repo_url}", error=str(e))
            return False
    
    async def deploy_application(
        self,
        task_id: str,
        files: Dict[str, str],
        description: str = ""
    ) -> Dict[str, Any]:
        """Deploy a complete application to GitHub with Pages."""
        if not self.github:
            raise ValueError("GitHub integration not available")
        
        try:
            # Create repository
            repo_name = task_id.replace('_', '-').lower()
            user = self.github.get_user()
            
            logger.info(f"Creating repository: {repo_name}")
            repo = user.create_repo(
                name=repo_name,
                description=description or f"Auto-generated application for {task_id}",
                private=False,
                auto_init=False
            )
            
            # Wait for repo to be ready
            await asyncio.sleep(2)
            
            # Create all files
            for file_path, content in files.items():
                try:
                    repo.create_file(
                        path=file_path,
                        message=f"Add {file_path}",
                        content=content,
                        branch="main"
                    )
                    logger.info(f"Created file: {file_path}")
                except GithubException as e:
                    logger.error(f"Failed to create {file_path}: {e}")
                    raise
            
            # Get latest commit SHA
            commits = repo.get_commits()
            commit_sha = commits[0].sha if commits.totalCount > 0 else "unknown"
            
            # Enable GitHub Pages using direct API call
            logger.info("Enabling GitHub Pages")
            try:
                # Use the underlying GitHub API directly
                url = f"{repo.url}/pages"
                headers, data = repo._requester.requestJsonAndCheck(
                    "POST",
                    url,
                    input={
                        "source": {
                            "branch": "main",
                            "path": "/"
                        }
                    }
                )
                logger.info("GitHub Pages enabled successfully")
            except GithubException as e:
                if e.status == 409:
                    logger.info("GitHub Pages already enabled")
                elif e.status == 404:
                    logger.info("Pages API not available, checking if already enabled")
                else:
                    logger.warning(f"Could not automatically enable Pages: {e}")
                    logger.info("Repository created. Enable Pages manually in Settings > Pages")

            # Wait for Pages to deploy
            await asyncio.sleep(5)

            # Get Pages URL
            try:
                pages = repo.get_pages()
                pages_url = pages.html_url
            except:
                # Pages not available yet, use default GitHub Pages URL
                pages_url = f"https://{user.login}.github.io/{repo_name}/"
            
            result = {
                'repo_url': repo.html_url,
                'commit_sha': commit_sha,
                'pages_url': pages_url,
                'repo_name': repo_name,
                'owner': user.login
            }
            
            logger.info(f"Deployment complete: {pages_url}")
            return result
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise ValueError(f"Failed to deploy application: {str(e)}")
    
    async def update_repository(
        self,
        repo_url: str,
        files: Dict[str, str],
        commit_message: str = "Update application"
    ) -> str:
        """Update files in an existing repository."""
        if not self.github:
            raise ValueError("GitHub integration not available")
        
        try:
            owner, repo_name = self._parse_github_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # Update each file
            for file_path, new_content in files.items():
                try:
                    # Try to get existing file
                    contents = repo.get_contents(file_path, ref="main")
                    
                    # Update file
                    repo.update_file(
                        path=file_path,
                        message=f"Update {file_path}",
                        content=new_content,
                        sha=contents.sha,
                        branch="main"
                    )
                    logger.info(f"Updated file: {file_path}")
                    
                except GithubException as e:
                    if e.status == 404:
                        # File doesn't exist, create it
                        repo.create_file(
                            path=file_path,
                            message=f"Add {file_path}",
                            content=new_content,
                            branch="main"
                        )
                        logger.info(f"Created new file: {file_path}")
                    else:
                        raise
            
            # Get latest commit SHA
            commits = repo.get_commits()
            commit_sha = commits[0].sha if commits.totalCount > 0 else "unknown"
            
            logger.info(f"Repository updated: {commit_sha}")
            return commit_sha
            
        except Exception as e:
            logger.error(f"Failed to update repository: {e}")
            raise ValueError(f"Failed to update repository: {str(e)}")

    async def get_repository_info(self, repo_url: str) -> Dict[str, Any]:
        """Get detailed information about a repository."""
        if not self.github:
            raise ValueError("GitHub integration not available")

        try:
            owner, repo_name = self._parse_github_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")

            return {
                'id': repo.id,
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'language': repo.language,
                'languages': repo.get_languages(),
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'open_issues': repo.open_issues_count,
                'created_at': repo.created_at.isoformat() if repo.created_at else None,
                'updated_at': repo.updated_at.isoformat() if repo.updated_at else None,
                'html_url': repo.html_url,
                'clone_url': repo.clone_url,
            }

        except Exception as e:
            logger.error(f"Failed to get repository info for {repo_url}", error=str(e))
            raise ValueError(f"Failed to get repository info: {str(e)}")