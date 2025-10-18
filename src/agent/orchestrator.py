"""
Task orchestrator for Agent LLM Deployment System.

This module implements the core AI agent that follows the
"Think -> Plan -> Act -> Review" methodology for autonomous web development.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from src.core.logging import get_logger
from src.services.database import DatabaseService
from src.services.github import GitHubService
from src.services.llm import LLMService
from src.agent.tools import AgentTools
from src.agent.code_generator import CodeGenerator
from src.agent.generators import generate_mit_license, generate_readme, generate_code_explanation
from src.agent.evaluator import PlaywrightEvaluator
from src.utils.retry import post_with_retry

logger = get_logger(__name__)


class TaskOrchestrator:
    """Orchestrates autonomous web development tasks."""

    def __init__(
        self,
        db_service: DatabaseService,
        github_service: GitHubService,
        llm_service: LLMService
    ):
        self.db_service = db_service
        self.github_service = github_service
        self.llm_service = llm_service
        self.tools = AgentTools()
        self.code_generator = CodeGenerator(llm_service)

    async def close(self):
        """Close orchestrator resources."""
        if self.tools:
            await self.tools.close()

    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an autonomous development task using Think-Plan-Act-Review methodology."""

        logger.info(f"Starting autonomous task processing", task_id=task_data.get('task_id'))

        try:
            # Phase 1: THINK - Analyze requirements and plan approach
            logger.info("Phase 1: THINK - Analyzing requirements")
            analysis = await self._think_phase(task_data)

            # Phase 2: PLAN - Create detailed development plan
            logger.info("Phase 2: PLAN - Creating development plan")
            plan = await self._plan_phase(task_data, analysis)

            # Phase 3: ACT - Execute the development plan
            logger.info("Phase 3: ACT - Executing development")
            result = await self._act_phase(task_data, plan)

            # Phase 4: REVIEW - Quality assurance and validation
            logger.info("Phase 4: REVIEW - Quality assurance")
            final_result = await self._review_phase(task_data, result)

            logger.info("Task completed successfully", task_id=task_data.get('task_id'))
            return final_result

        except Exception as e:
            logger.error("Task failed during processing", task_id=task_data.get('task_id'), error=str(e))
            raise

    async def _think_phase(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 1: Think - Analyze requirements and understand the task."""

        prompt = f"""
        Analyze this web development task and provide a comprehensive understanding:

        Task Brief: {task_data['brief']}
        Requirements: {json.dumps(task_data['checks'])}
        Round: {task_data['round']}

        Provide analysis in the following format:
        {{
            "technologies": ["list", "of", "technologies"],
            "complexity": "low|medium|high",
            "estimated_effort": "X hours",
            "key_components": ["component1", "component2"],
            "potential_challenges": ["challenge1", "challenge2"],
            "success_criteria": ["criteria1", "criteria2"]
        }}
        """

        system_message = """
        You are an expert web developer analyzing project requirements.
        Provide detailed, structured analysis of the task requirements.
        """

        analysis_text = await self.llm_service.generate_response(
            prompt=prompt,
            system_message=system_message,
            max_tokens=800,
            temperature=0.3
        )

        try:
            analysis = json.loads(analysis_text)
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            analysis = {
                "technologies": ["HTML", "CSS", "JavaScript"],
                "complexity": "medium",
                "estimated_effort": "2-3 hours",
                "key_components": ["User interface", "Functionality"],
                "potential_challenges": ["Cross-browser compatibility"],
                "success_criteria": task_data['checks'][:2]
            }

        return analysis

    async def _plan_phase(self, task_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Plan - Create detailed development plan."""

        prompt = f"""
        Create a detailed development plan for this web application:

        Analysis: {json.dumps(analysis)}
        Requirements: {json.dumps(task_data['checks'])}
        Round: {task_data['round']}

        Provide a step-by-step plan in the following format:
        {{
            "steps": [
                {{
                    "step": 1,
                    "description": "Detailed description",
                    "estimated_time": "30 minutes",
                    "dependencies": ["step1", "step2"],
                    "tools": ["tool1", "tool2"]
                }}
            ],
            "file_structure": {{
                "index.html": "Main HTML file",
                "style.css": "CSS styles",
                "script.js": "JavaScript functionality"
            }},
            "testing_strategy": "How to test each component"
        }}
        """

        system_message = """
        You are a senior software architect creating development plans.
        Provide detailed, actionable plans that a developer can follow.
        """

        plan_text = await self.llm_service.generate_response(
            prompt=prompt,
            system_message=system_message,
            max_tokens=1000,
            temperature=0.4
        )

        try:
            plan = json.loads(plan_text)
        except json.JSONDecodeError:
            # Fallback plan structure
            plan = {
                "steps": [
                    {
                        "step": 1,
                        "description": "Create HTML structure",
                        "estimated_time": "30 minutes",
                        "dependencies": [],
                        "tools": ["HTML editor"]
                    },
                    {
                        "step": 2,
                        "description": "Add CSS styling",
                        "estimated_time": "45 minutes",
                        "dependencies": ["step 1"],
                        "tools": ["CSS editor"]
                    },
                    {
                        "step": 3,
                        "description": "Implement JavaScript functionality",
                        "estimated_time": "60 minutes",
                        "dependencies": ["step 1", "step 2"],
                        "tools": ["JavaScript editor"]
                    }
                ],
                "file_structure": {
                    "index.html": "Main application file",
                    "style.css": "Application styles",
                    "script.js": "Application logic"
                },
                "testing_strategy": "Manual testing in browser"
            }

        return plan

    async def _act_phase(self, task_data: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Act - Execute the development plan."""

        logger.info("Starting development execution", task_id=task_data.get('task_id'))

        # Create workspace for development
        workspace_id = str(uuid.uuid4())
        workspace_path = f"/tmp/workspace_{workspace_id}"

        try:
            # Create workspace
            await self.tools.create_workspace(workspace_path)

            # Generate application code
            logger.info("Generating application code")
            files = await self.code_generator.generate_application(task_data, workspace_path)
            
            # Generate LICENSE
            license_content = generate_mit_license()
            files['LICENSE'] = license_content
            
            # Generate code explanation
            code_explanation = await generate_code_explanation(
                task_data['brief'],
                files,
                self.llm_service
            )
            
            # Generate README
            readme_content = generate_readme(
                task_id=task_data['task_id'],
                brief=task_data['brief'],
                checks=task_data['checks'],
                repo_url="",  # Will be updated after deployment
                pages_url="",  # Will be updated after deployment
                files=list(files.keys()),
                code_explanation=code_explanation
            )
            files['README.md'] = readme_content

            # Deploy the application
            deployment_result = await self._deploy_application(task_data, files)
            
            # Update README with actual URLs
            readme_content = generate_readme(
                task_id=task_data['task_id'],
                brief=task_data['brief'],
                checks=task_data['checks'],
                repo_url=deployment_result['repo_url'],
                pages_url=deployment_result['pages_url'],
                files=list(files.keys()),
                code_explanation=code_explanation
            )
            
            # Update README in repo
            await self.github_service.update_repository(
                deployment_result['repo_url'],
                {'README.md': readme_content}
            )

            return {
                "workspace_id": workspace_id,
                "files_generated": len(files),
                "deployment": deployment_result,
                "status": "completed"
            }

        finally:
            # Clean up workspace
            await self.tools.cleanup_workspace(workspace_path)

    async def _send_evaluation_callback(
        self,
        task_data: Dict[str, Any],
        deployment_result: Dict[str, Any]
    ) -> None:
        """Send evaluation callback with retry logic."""
        
        evaluation_url = task_data.get('evaluation_url')
        if not evaluation_url:
            logger.warning("No evaluation URL provided")
            return
        
        payload = {
            "email": task_data.get('email', ''),
            "task": task_data['task_id'],
            "round": task_data['round'],
            "nonce": task_data['nonce'],
            "repo_url": deployment_result['repo_url'],
            "commit_sha": deployment_result['commit_sha'],
            "pages_url": deployment_result['pages_url']
        }
        
        logger.info(f"Sending evaluation callback to {evaluation_url}")
        
        try:
            response = await post_with_retry(
                url=evaluation_url,
                json_data=payload,
                max_attempts=5,
                timeout=30.0
            )
            logger.info(f"Evaluation callback successful: {response.status_code}")
        except Exception as e:
            logger.error(f"Evaluation callback failed after retries: {e}")
            # Don't raise - deployment was successful even if callback failed
    
    async def process_round2_task(self, task_data: Dict[str, Any], existing_repo_url: str) -> Dict[str, Any]:
        """Process a round 2 task update."""
        
        logger.info(f"Processing round 2 task", task_id=task_data.get('task_id'))
        
        workspace_id = str(uuid.uuid4())
        workspace_path = f"/tmp/workspace_{workspace_id}"
        
        try:
            # Create workspace
            await self.tools.create_workspace(workspace_path)
            
            # Get existing files from repo
            # For now, we'll regenerate - in production, fetch from GitHub
            existing_files = {
                'index.html': '',
                'style.css': '',
                'script.js': ''
            }
            
            # Update application code
            logger.info("Updating application code for round 2")
            updated_files = await self.code_generator.update_application(
                task_data,
                workspace_path,
                existing_files
            )
            
            # Update README
            code_explanation = await generate_code_explanation(
                task_data['brief'],
                updated_files,
                self.llm_service
            )
            
            readme_content = generate_readme(
                task_id=task_data['task_id'],
                brief=task_data['brief'],
                checks=task_data['checks'],
                repo_url=existing_repo_url,
                pages_url=existing_repo_url.replace('github.com', 'github.io').replace('.git', '/'),
                files=list(updated_files.keys()),
                code_explanation=code_explanation
            )
            updated_files['README.md'] = readme_content
            
            # Update repository
            commit_sha = await self.github_service.update_repository(
                existing_repo_url,
                updated_files,
                f"Round 2 update: {task_data['brief'][:50]}"
            )
            
            # Get pages URL
            owner_repo = existing_repo_url.replace('https://github.com/', '').replace('.git', '')
            pages_url = f"https://{owner_repo.split('/')[0]}.github.io/{owner_repo.split('/')[1]}/"
            
            deployment_result = {
                'repo_url': existing_repo_url,
                'commit_sha': commit_sha,
                'pages_url': pages_url
            }
            
            # Send evaluation callback
            await self._send_evaluation_callback(task_data, deployment_result)
            
            return {
                "workspace_id": workspace_id,
                "files_updated": len(updated_files),
                "deployment": deployment_result,
                "status": "completed"
            }
            
        finally:
            await self.tools.cleanup_workspace(workspace_path)

    async def _deploy_application(
        self,
        task_data: Dict[str, Any],
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Deploy the completed application."""

        logger.info("Deploying application to GitHub")
        
        # Deploy to GitHub with Pages
        deployment_result = await self.github_service.deploy_application(
            task_id=task_data['task_id'],
            files=files,
            description=task_data['brief'][:100]
        )
        
        logger.info(f"Deployed to {deployment_result['pages_url']}")
        
        # Send evaluation callback
        await self._send_evaluation_callback(task_data, deployment_result)
        
        return deployment_result

    async def _review_phase(self, task_data: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Review - Quality assurance and validation."""

        # Run quality checks
        quality_checks = await self._run_quality_checks(result, task_data)

        # Generate final report
        final_report = {
            "task_id": task_data['task_id'],
            "status": "completed",
            "deployment": result.get('deployment'),
            "quality_score": quality_checks.get('overall_score', 0),
            "checks_passed": quality_checks.get('passed', []),
            "checks_failed": quality_checks.get('failed', []),
            "recommendations": quality_checks.get('recommendations', []),
            "completed_at": datetime.now(timezone.utc).isoformat()
        }

        return final_report

    async def _run_quality_checks(self, result: Dict[str, Any], task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run quality checks on the completed application."""

        logger.info("Running quality checks with Playwright")
        
        try:
            # Use Playwright to evaluate the deployed page
            async with PlaywrightEvaluator() as evaluator:
                eval_result = await evaluator.evaluate_page(
                    pages_url=result['deployment']['pages_url'],
                    checks=task_data['checks'],
                    timeout=30000
                )
                
                return {
                    "overall_score": eval_result['score'],
                    "passed": eval_result['checks_passed'],
                    "failed": [f['check'] for f in eval_result['checks_failed']],
                    "recommendations": [
                        "Application deployed successfully",
                        f"Passed {len(eval_result['checks_passed'])}/{eval_result['total_checks']} checks"
                    ],
                    "screenshot": eval_result.get('screenshot')
                }
        except Exception as e:
            logger.error(f"Quality checks failed: {e}")
            return {
                "overall_score": 0.5,
                "passed": [],
                "failed": task_data['checks'],
                "recommendations": [f"Evaluation error: {str(e)}"]
            }
