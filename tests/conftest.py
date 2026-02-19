"""
Pytest Configuration for Blender GSD Cinematic System

This configuration provides:
- Blender availability detection
- Test fixtures for temporary files
- Oracle validation helpers
- Coverage requirements (80%+)

Usage:
    pytest tests/ -v --cov=lib --cov-fail-under=80
"""

import pytest
from pathlib import Path
import subprocess
import sys
import os

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================
# BLENDER AVAILABILITY
# ============================================================

@pytest.fixture(scope="session")
def blender_available():
    """
    Check if Blender is available for integration tests.

    Returns:
        bool: True if Blender executable found and working
    """
    try:
        result = subprocess.run(
            ["blender", "--version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


@pytest.fixture(scope="session")
def blender_version(blender_available):
    """
    Get Blender version string.

    Returns:
        str: Version string like "4.0.2" or None if unavailable
    """
    if not blender_available:
        return None

    result = subprocess.run(
        ["blender", "--version"],
        capture_output=True,
        text=True
    )
    # Parse "Blender 4.0.2" from output
    for line in result.stdout.split('\n'):
        if line.startswith('Blender'):
            return line.split()[1]
    return None


# ============================================================
# TEST DATA PATHS
# ============================================================

@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def baseline_dir():
    """Path to baseline fixtures for regression testing."""
    return Path(__file__).parent / "fixtures" / "baselines"


@pytest.fixture
def current_output_dir():
    """Path to current output for comparison."""
    return Path(__file__).parent / "fixtures" / "current"


@pytest.fixture
def temp_blend_file(tmp_path, blender_available):
    """
    Create a temporary .blend file for testing.

    Requires Blender to be available.
    """
    if not blender_available:
        pytest.skip("Blender not available")

    blend_path = tmp_path / "test_scene.blend"

    # Create minimal blend file via Blender Python
    create_script = f'''
import bpy
bpy.ops.wm.save_as_mainfile(filepath="{blend_path}")
'''

    result = subprocess.run(
        ["blender", "-b", "--python-expr", create_script],
        capture_output=True
    )

    if result.returncode != 0:
        pytest.skip(f"Could not create test blend file")

    return blend_path


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary directory for render outputs."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


# ============================================================
# ORACLE VALIDATION HELPERS
# ============================================================

class OracleValidator:
    """
    Oracle validation functions for test assertions.

    Provides standardized comparison with proper tolerance handling.
    All acceptance criteria should use these functions.
    """

    @staticmethod
    def compare_numbers(actual: float, expected: float, tolerance: float = 0.001) -> bool:
        """
        Compare two numbers with tolerance.

        Args:
            actual: The actual value
            expected: The expected value
            tolerance: Acceptable difference (absolute)

        Returns:
            True if within tolerance

        Raises:
            AssertionError: If difference exceeds tolerance
        """
        diff = abs(actual - expected)
        if diff > tolerance:
            raise AssertionError(
                f"Number mismatch: actual={actual}, expected={expected}, "
                f"diff={diff:.6f}, tolerance={tolerance}"
            )
        return True

    @staticmethod
    def compare_vectors(actual: tuple, expected: tuple, tolerance: float = 0.001) -> bool:
        """Compare two vectors with tolerance."""
        if len(actual) != len(expected):
            raise AssertionError(
                f"Vector length mismatch: {len(actual)} vs {len(expected)}"
            )

        for i, (a, e) in enumerate(zip(actual, expected)):
            diff = abs(a - e)
            if diff > tolerance:
                raise AssertionError(
                    f"Vector component {i} mismatch: actual={a}, expected={e}, "
                    f"diff={diff:.6f}, tolerance={tolerance}"
                )
        return True

    @staticmethod
    def compare_within_range(value: float, min_val: float, max_val: float) -> bool:
        """Check if value is within specified range."""
        if not (min_val <= value <= max_val):
            raise AssertionError(
                f"Value {value} not in range [{min_val}, {max_val}]"
            )
        return True

    @staticmethod
    def file_exists(path: Path, file_type: str = "file") -> bool:
        """Validate that a file exists and is not empty."""
        if not path.exists():
            raise AssertionError(f"{file_type} does not exist: {path}")

        if path.is_file() and path.stat().st_size == 0:
            raise AssertionError(f"{file_type} is empty: {path}")

        return True

    @staticmethod
    def directory_exists(path: Path) -> bool:
        """Validate that a directory exists."""
        if not path.exists():
            raise AssertionError(f"Directory does not exist: {path}")
        if not path.is_dir():
            raise AssertionError(f"Path is not a directory: {path}")
        return True

    @staticmethod
    def exit_code_zero(result: subprocess.CompletedProcess, context: str = "") -> bool:
        """Validate subprocess completed with exit code 0."""
        if result.returncode != 0:
            stderr = result.stderr.decode() if isinstance(result.stderr, bytes) else result.stderr
            raise AssertionError(
                f"Process failed (exit {result.returncode}): {context}\n"
                f"stderr: {stderr}"
            )
        return True

    @staticmethod
    def no_stderr(result: subprocess.CompletedProcess) -> bool:
        """Validate subprocess produced no stderr output."""
        stderr = result.stderr.decode() if isinstance(result.stderr, bytes) else result.stderr
        if stderr and stderr.strip():
            raise AssertionError(f"Unexpected stderr output: {stderr}")
        return True


@pytest.fixture
def oracle():
    """Provide OracleValidator instance for tests."""
    return OracleValidator()


# ============================================================
# CINEMATIC SYSTEM FIXTURES
# ============================================================

@pytest.fixture
def sample_camera_config():
    """Sample camera configuration for testing."""
    from lib.cinematic.types import CameraConfig, Transform3D

    return CameraConfig(
        name="test_camera",
        focal_length=50.0,
        f_stop=4.0,
        focus_distance=3.0,
        transform=Transform3D(
            position=(0, -5, 2),
            rotation=(0, 0, 0)
        )
    )


@pytest.fixture
def sample_light_config():
    """Sample light configuration for testing."""
    from lib.cinematic.types import LightConfig

    return LightConfig(
        name="test_key_light",
        light_type="area",
        intensity=1000.0,
        color=(1.0, 0.95, 0.9),
        position=(2, -2, 3),
        rotation=(45, 0, 0)
    )


@pytest.fixture
def sample_plumb_bob_config():
    """Sample plumb bob configuration for testing."""
    from lib.cinematic.types import PlumbBobConfig

    return PlumbBobConfig(
        mode="auto",
        offset=(0, 0, 0.015)
    )


# ============================================================
# TEST MARKERS
# ============================================================

def pytest_configure(config):
    """Register custom test markers."""

    # Skip if Blender not available
    config.addinivalue_line(
        "markers", "requires_blender: Test requires Blender to be installed"
    )

    # Slow tests (integration, rendering)
    config.addinivalue_line(
        "markers", "slow: Test takes > 5 seconds to run"
    )

    # Visual regression tests
    config.addinivalue_line(
        "markers", "visual: Test produces visual output for regression comparison"
    )

    # Phase-specific markers
    for phase in range(6, 15):
        config.addinivalue_line(
            "markers", f"phase{phase}: Tests for Phase {phase}"
        )


def pytest_collection_modifyitems(config, items):
    """Auto-skip tests based on markers."""

    # Check if Blender is available
    try:
        result = subprocess.run(
            ["blender", "--version"],
            capture_output=True,
            timeout=5
        )
        blender_available = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        blender_available = False

    # Skip requires_blender tests
    skip_blender = pytest.mark.skip(
        reason="Blender not available"
    )

    for item in items:
        if "requires_blender" in item.keywords and not blender_available:
            item.add_marker(skip_blender)


# ============================================================
# COVERAGE CONFIGURATION
# ============================================================

# Coverage is configured via .coveragerc or pyproject.toml
# Target: 80% minimum coverage
# Run: pytest tests/ -v --cov=lib --cov-fail-under=80
