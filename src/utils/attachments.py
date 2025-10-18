"""
Attachment utilities for handling data URIs.

This module provides functions to decode and process data URI attachments
from task requests.
"""

import base64
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from src.core.logging import get_logger

logger = get_logger(__name__)


def decode_data_uri(data_uri: str) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """
    Decode a data URI into its components.
    
    Args:
        data_uri: Data URI string (e.g., "data:image/png;base64,iVBORw...")
        
    Returns:
        Tuple of (content_bytes, mime_type, encoding)
    """
    try:
        # Parse data URI format: data:[<mime-type>][;base64],<data>
        match = re.match(r'data:([^;,]+)?(;base64)?,(.+)', data_uri)
        
        if not match:
            logger.error("Invalid data URI format")
            return None, None, None
        
        mime_type = match.group(1) or "text/plain"
        is_base64 = match.group(2) is not None
        data = match.group(3)
        
        if is_base64:
            content = base64.b64decode(data)
            encoding = "base64"
        else:
            content = data.encode('utf-8')
            encoding = "utf-8"
        
        return content, mime_type, encoding
        
    except Exception as e:
        logger.error(f"Failed to decode data URI: {e}")
        return None, None, None


def save_attachment(attachment: Dict[str, str], workspace_path: str) -> Optional[str]:
    """
    Save an attachment to the workspace.
    
    Args:
        attachment: Dict with 'name' and 'url' (data URI)
        workspace_path: Path to workspace directory
        
    Returns:
        Relative path to saved file, or None on error
    """
    try:
        name = attachment.get("name")
        url = attachment.get("url")
        
        if not name or not url:
            logger.error("Attachment missing name or url")
            return None
        
        # Decode data URI
        content, mime_type, encoding = decode_data_uri(url)
        
        if content is None:
            return None
        
        # Save to workspace
        file_path = Path(workspace_path) / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Saved attachment {name} ({len(content)} bytes, {mime_type})")
        return name
        
    except Exception as e:
        logger.error(f"Failed to save attachment: {e}")
        return None


def save_all_attachments(attachments: List[Dict[str, str]], workspace_path: str) -> List[str]:
    """
    Save all attachments to the workspace.
    
    Args:
        attachments: List of attachment dicts
        workspace_path: Path to workspace directory
        
    Returns:
        List of saved file paths
    """
    saved_files = []
    
    for attachment in attachments:
        file_path = save_attachment(attachment, workspace_path)
        if file_path:
            saved_files.append(file_path)
    
    return saved_files


def get_attachment_content(attachment: Dict[str, str]) -> Optional[str]:
    """
    Get the decoded content of an attachment as a string.
    
    Args:
        attachment: Dict with 'name' and 'url' (data URI)
        
    Returns:
        Decoded content as string, or None on error
    """
    try:
        url = attachment.get("url")
        if not url:
            return None
        
        content, mime_type, encoding = decode_data_uri(url)
        
        if content is None:
            return None
        
        # Try to decode as text
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            # Binary content, return base64
            return base64.b64encode(content).decode('ascii')
            
    except Exception as e:
        logger.error(f"Failed to get attachment content: {e}")
        return None
