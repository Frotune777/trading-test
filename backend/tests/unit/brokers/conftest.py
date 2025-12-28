"""
Pytest configuration for broker tests
Simplified conftest that doesn't require database imports
"""

import pytest
import sys
from pathlib import Path

# Add app directory to Python path - go up 3 levels from conftest.py to get to /app
# /app/tests/unit/brokers/conftest.py -> /app
app_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(app_dir))

# Verify the path was added correctly
print(f"Added to sys.path: {app_dir}")
print(f"sys.path: {sys.path[:3]}")

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
