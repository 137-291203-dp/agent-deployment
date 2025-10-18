"""
Real code generator for web applications.

This module generates actual working HTML, CSS, and JavaScript code
based on task briefs and requirements.
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from src.core.logging import get_logger
from src.services.llm import LLMService
from src.utils.attachments import save_all_attachments, get_attachment_content

logger = get_logger(__name__)


class CodeGenerator:
    """Generates working web application code."""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    async def generate_application(
        self,
        task_data: Dict[str, Any],
        workspace_path: str
    ) -> Dict[str, str]:
        """
        Generate complete web application.
        
        Args:
            task_data: Task information (brief, checks, attachments)
            workspace_path: Path to workspace directory
            
        Returns:
            Dict of filename -> content
        """
        logger.info("Starting code generation")
        
        # Save attachments first
        attachments = task_data.get('attachments', [])
        saved_attachments = save_all_attachments(attachments, workspace_path)
        
        # Generate HTML
        html_content = await self._generate_html(task_data, saved_attachments)
        
        # Generate CSS
        css_content = await self._generate_css(task_data)
        
        # Generate JavaScript
        js_content = await self._generate_javascript(task_data, saved_attachments)
        
        files = {
            'index.html': html_content,
            'style.css': css_content,
            'script.js': js_content
        }
        
        # Save generated files
        for filename, content in files.items():
            file_path = Path(workspace_path) / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Generated {filename} ({len(content)} chars)")
        
        return files
    
    async def _generate_html(
        self,
        task_data: Dict[str, Any],
        attachments: List[str]
    ) -> str:
        """Generate HTML content."""
        
        brief = task_data['brief']
        checks = task_data['checks']
        task_id = task_data['task_id']
        
        prompt = f"""
        Generate a complete, production-ready HTML file for this web application:
        
        Brief: {brief}
        
        Requirements:
        {chr(10).join(f'- {check}' for check in checks)}
        
        Attachments available: {', '.join(attachments) if attachments else 'None'}
        
        Generate ONLY the HTML code with:
        1. Proper DOCTYPE and HTML5 structure
        2. Semantic HTML elements
        3. Links to style.css and script.js
        4. All required IDs and classes mentioned in requirements
        5. Bootstrap 5 from CDN if needed
        6. Professional, clean structure
        7. Responsive meta tags
        
        Title should be: {task_id}
        
        Return ONLY the HTML code, no explanations.
        """
        
        system_message = """You are an expert frontend developer. Generate clean, semantic, 
        production-ready HTML5 code. Follow best practices and accessibility standards."""
        
        html = await self.llm_service.generate_response(
            prompt=prompt,
            system_message=system_message,
            max_tokens=2000,
            temperature=0.2
        )
        
        # Clean up the response
        html = self._extract_code(html, 'html')
        
        # Ensure proper structure
        if '<!DOCTYPE html>' not in html:
            html = '<!DOCTYPE html>\n' + html
        
        return html
    
    async def _generate_css(self, task_data: Dict[str, Any]) -> str:
        """Generate CSS content."""
        
        brief = task_data['brief']
        checks = task_data['checks']
        
        prompt = f"""
        Generate professional CSS for this web application:
        
        Brief: {brief}
        
        Requirements:
        {chr(10).join(f'- {check}' for check in checks)}
        
        Generate CSS with:
        1. Modern, clean design
        2. Responsive layout (mobile-first)
        3. Professional color scheme
        4. Proper spacing and typography
        5. Smooth transitions
        6. All required IDs and classes
        
        Return ONLY the CSS code, no explanations.
        """
        
        system_message = """You are an expert CSS developer. Generate modern, responsive, 
        production-ready CSS. Follow best practices and design principles."""
        
        css = await self.llm_service.generate_response(
            prompt=prompt,
            system_message=system_message,
            max_tokens=1500,
            temperature=0.2
        )
        
        return self._extract_code(css, 'css')
    
    async def _generate_javascript(
        self,
        task_data: Dict[str, Any],
        attachments: List[str]
    ) -> str:
        """Generate JavaScript content."""
        
        brief = task_data['brief']
        checks = task_data['checks']
        
        # Get attachment content for context
        attachment_info = ""
        if task_data.get('attachments'):
            for att in task_data['attachments']:
                content = get_attachment_content(att)
                if content and len(content) < 500:
                    attachment_info += f"\n{att['name']}: {content[:200]}..."
        
        prompt = f"""
        Generate functional JavaScript for this web application:
        
        Brief: {brief}
        
        Requirements:
        {chr(10).join(f'- {check}' for check in checks)}
        
        Attachments: {', '.join(attachments) if attachments else 'None'}
        {attachment_info}
        
        Generate JavaScript with:
        1. Modern ES6+ syntax
        2. Proper error handling
        3. All required functionality
        4. Event listeners for user interactions
        5. Fetch API for external data if needed
        6. DOM manipulation for all required elements
        7. Comments explaining key logic
        
        Return ONLY the JavaScript code, no explanations.
        """
        
        system_message = """You are an expert JavaScript developer. Generate clean, modern, 
        production-ready JavaScript. Follow best practices and use ES6+ features."""
        
        js = await self.llm_service.generate_response(
            prompt=prompt,
            system_message=system_message,
            max_tokens=2000,
            temperature=0.2
        )
        
        return self._extract_code(js, 'javascript')
    
    def _extract_code(self, text: str, language: str) -> str:
        """Extract code from markdown code blocks."""
        
        # Try to find code block
        patterns = [
            f'```{language}\n(.*?)\n```',
            f'```\n(.*?)\n```',
            '```html\n(.*?)\n```',
            '```css\n(.*?)\n```',
            '```js\n(.*?)\n```',
            '```javascript\n(.*?)\n```'
        ]
        
        import re
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # If no code block found, return as-is (might already be clean code)
        return text.strip()
    
    async def update_application(
        self,
        task_data: Dict[str, Any],
        workspace_path: str,
        existing_files: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Update existing application for round 2.
        
        Args:
            task_data: New task data with round 2 requirements
            workspace_path: Path to workspace
            existing_files: Current file contents
            
        Returns:
            Updated file contents
        """
        logger.info("Updating application for round 2")
        
        brief = task_data['brief']
        checks = task_data['checks']
        
        # Save new attachments
        attachments = task_data.get('attachments', [])
        saved_attachments = save_all_attachments(attachments, workspace_path)
        
        updated_files = {}
        
        # Update each file
        for filename, current_content in existing_files.items():
            prompt = f"""
            Update this {filename} file to add new features:
            
            New Requirements: {brief}
            
            New Checks:
            {chr(10).join(f'- {check}' for check in checks)}
            
            Current Code:
            ```
            {current_content}
            ```
            
            New Attachments: {', '.join(saved_attachments) if saved_attachments else 'None'}
            
            Modify the code to:
            1. Keep all existing functionality
            2. Add the new features
            3. Maintain code quality
            4. Ensure all new checks pass
            
            Return ONLY the updated code, no explanations.
            """
            
            system_message = f"""You are an expert developer updating existing code. 
            Preserve working functionality while adding new features."""
            
            updated_content = await self.llm_service.generate_response(
                prompt=prompt,
                system_message=system_message,
                max_tokens=2500,
                temperature=0.2
            )
            
            # Extract and save
            file_type = filename.split('.')[-1]
            updated_content = self._extract_code(updated_content, file_type)
            updated_files[filename] = updated_content
            
            # Save to workspace
            file_path = Path(workspace_path) / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
        
        logger.info("Application updated successfully")
        return updated_files
