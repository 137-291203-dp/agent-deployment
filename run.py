#!/usr/bin/env python3
"""
Entry point for Agent LLM Deployment System.

This script sets up the Python path and starts the FastAPI application.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set environment variables for proper module loading
os.environ.setdefault("PYTHONPATH", str(src_path))

try:
    from src.main import app
    import uvicorn

    if __name__ == "__main__":
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
        )

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Error starting server: {e}")
    sys.exit(1)
