"""
Blender Integration Tests

These tests require a real Blender installation with bpy module.
They test actual Blender operations like:
- Scene creation and manipulation
- Geometry nodes execution
- Material assignment
- Render output

Run with: pytest tests/blender_integration/ -v -m requires_blender
"""

import pytest
import subprocess
import sys
from pathlib import Path

# Check for Blender availability (either in PATH or bpy importable)
try:
    result = subprocess.run(
        ["blender", "--version"],
        capture_output=True,
        timeout=5
    )
    BLENDER_AVAILABLE = result.returncode == 0
except (FileNotFoundError, subprocess.TimeoutExpired):
    BLENDER_AVAILABLE = False

# Try to import bpy - if available, we're running inside Blender
try:
    import bpy
    BPY_AVAILABLE = True
    # If bpy is available, we're definitely in a Blender environment
    BLENDER_AVAILABLE = True
except ImportError:
    BPY_AVAILABLE = False


# Create the requires_blender marker
requires_blender = pytest.mark.skipif(
    not (BLENDER_AVAILABLE and BPY_AVAILABLE),
    reason="Blender and bpy module required"
)

# Skip all tests in this module if Blender not available
pytestmark = pytest.mark.skipif(
    not (BLENDER_AVAILABLE and BPY_AVAILABLE),
    reason="Blender and bpy module required"
)
