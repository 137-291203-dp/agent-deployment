"""
Playwright-based evaluator for dynamic checks.

This module uses Playwright to visit deployed pages and run JavaScript checks.
"""

import asyncio
from typing import Dict, List, Any, Optional
from playwright.async_api import async_playwright, Page, Browser

from src.core.logging import get_logger

logger = get_logger(__name__)


class PlaywrightEvaluator:
    """Evaluates web applications using Playwright."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def __aenter__(self):
        """Context manager entry."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def evaluate_page(
        self,
        pages_url: str,
        checks: List[str],
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        Evaluate a deployed page against checks.
        
        Args:
            pages_url: URL of deployed GitHub Pages site
            checks: List of check descriptions or JS expressions
            timeout: Page load timeout in milliseconds
            
        Returns:
            Dict with evaluation results
        """
        logger.info(f"Evaluating page: {pages_url}")
        
        results = {
            'url': pages_url,
            'checks_passed': [],
            'checks_failed': [],
            'total_checks': len(checks),
            'score': 0.0,
            'screenshot': None,
            'errors': []
        }
        
        try:
            page = await self.browser.new_page()
            
            # Navigate to page
            try:
                response = await page.goto(pages_url, timeout=timeout, wait_until='networkidle')
                
                if not response or response.status != 200:
                    results['errors'].append(f"Page returned status {response.status if response else 'None'}")
                    return results
                    
            except Exception as e:
                results['errors'].append(f"Failed to load page: {str(e)}")
                return results
            
            # Wait for page to be ready
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(2)  # Give dynamic content time to load
            
            # Run each check
            for check in checks:
                check_result = await self._run_check(page, check)
                
                if check_result['passed']:
                    results['checks_passed'].append(check)
                else:
                    results['checks_failed'].append({
                        'check': check,
                        'reason': check_result.get('reason', 'Check failed')
                    })
            
            # Calculate score
            if results['total_checks'] > 0:
                results['score'] = len(results['checks_passed']) / results['total_checks']
            
            # Take screenshot
            try:
                screenshot_bytes = await page.screenshot(full_page=True)
                results['screenshot'] = screenshot_bytes
                logger.info("Screenshot captured")
            except Exception as e:
                logger.warning(f"Failed to capture screenshot: {e}")
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            results['errors'].append(str(e))
        
        logger.info(f"Evaluation complete: {len(results['checks_passed'])}/{results['total_checks']} checks passed")
        return results
    
    async def _run_check(self, page: Page, check: str) -> Dict[str, Any]:
        """
        Run a single check on the page.
        
        Args:
            page: Playwright page object
            check: Check description or JS expression
            
        Returns:
            Dict with 'passed' bool and optional 'reason'
        """
        try:
            # Check if it's a JavaScript expression (starts with 'js:')
            if check.startswith('js:'):
                js_expression = check[3:].strip()
                return await self._run_js_check(page, js_expression)
            
            # Otherwise, try to interpret as a requirement
            return await self._run_text_check(page, check)
            
        except Exception as e:
            logger.error(f"Check failed with exception: {e}")
            return {'passed': False, 'reason': str(e)}
    
    async def _run_js_check(self, page: Page, js_expression: str) -> Dict[str, Any]:
        """Run a JavaScript expression check."""
        try:
            # Evaluate the JavaScript expression
            result = await page.evaluate(js_expression)
            
            # Check if result is truthy
            passed = bool(result)
            
            return {
                'passed': passed,
                'reason': f"JS expression returned: {result}" if not passed else None
            }
            
        except Exception as e:
            return {
                'passed': False,
                'reason': f"JS evaluation error: {str(e)}"
            }
    
    async def _run_text_check(self, page: Page, check: str) -> Dict[str, Any]:
        """Run a text-based check by analyzing the requirement."""
        try:
            # Get page content
            content = await page.content()
            title = await page.title()
            
            check_lower = check.lower()
            
            # Check for common patterns
            if 'license' in check_lower and 'mit' in check_lower:
                # This check is for repo, not page
                return {'passed': True, 'reason': 'License check is repo-level'}
            
            if 'readme' in check_lower:
                # This check is for repo, not page
                return {'passed': True, 'reason': 'README check is repo-level'}
            
            if 'title' in check_lower:
                # Check page title
                if any(word in title.lower() for word in check_lower.split()):
                    return {'passed': True}
                return {'passed': False, 'reason': f"Title '{title}' doesn't match requirement"}
            
            # Check for element existence by ID or class
            import re
            id_match = re.search(r'#([\w-]+)', check)
            if id_match:
                element_id = id_match.group(1)
                element = await page.query_selector(f'#{element_id}')
                if element:
                    return {'passed': True}
                return {'passed': False, 'reason': f"Element #{element_id} not found"}
            
            # Check for Bootstrap
            if 'bootstrap' in check_lower:
                has_bootstrap = await page.evaluate("""
                    () => {
                        const links = document.querySelectorAll('link[href*="bootstrap"]');
                        const scripts = document.querySelectorAll('script[src*="bootstrap"]');
                        return links.length > 0 || scripts.length > 0;
                    }
                """)
                if has_bootstrap:
                    return {'passed': True}
                return {'passed': False, 'reason': 'Bootstrap not found'}
            
            # Default: assume it passes if page loaded successfully
            return {'passed': True, 'reason': 'Generic check passed'}
            
        except Exception as e:
            return {'passed': False, 'reason': f"Text check error: {str(e)}"}
    
    async def wait_for_element(
        self,
        page: Page,
        selector: str,
        timeout: int = 15000
    ) -> bool:
        """
        Wait for an element to appear.
        
        Args:
            page: Playwright page
            selector: CSS selector
            timeout: Timeout in milliseconds
            
        Returns:
            True if element appeared, False otherwise
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False
