"""
Oracle Validation Functions

Provides standardized comparison and validation functions for testing.
All acceptance criteria should use these functions for consistent,
measurable validation with proper tolerance handling.

Usage:
    from lib.oracle import compare_numbers, compare_vectors, file_exists

    # Compare numbers with tolerance
    compare_numbers(actual=5.001, expected=5.0, tolerance=0.01)  # Passes

    # Validate file exists and not empty
    file_exists(Path("output/render.png"))  # Raises if missing/empty

    # Validate subprocess result
    exit_code_zero(result, context="Render process")
"""

import math
import subprocess
import json
from pathlib import Path
from typing import Any, Tuple, Optional, Union, List


# ============================================================
# NUMBER COMPARISON
# ============================================================

def compare_numbers(
    actual: float,
    expected: float,
    tolerance: float = 0.001,
    message: Optional[str] = None
) -> bool:
    """
    Compare two numbers with absolute tolerance.

    Args:
        actual: The actual value
        expected: The expected value
        tolerance: Acceptable absolute difference (default: 0.001)
        message: Custom error message prefix

    Returns:
        True if within tolerance

    Raises:
        AssertionError: If difference exceeds tolerance

    Examples:
        >>> compare_numbers(5.001, 5.0, tolerance=0.01)
        True
        >>> compare_numbers(5.1, 5.0, tolerance=0.01)
        AssertionError: Number mismatch: actual=5.1, expected=5.0, diff=0.1, tolerance=0.01
    """
    diff = abs(actual - expected)

    if diff > tolerance:
        msg = message or "Number mismatch"
        raise AssertionError(
            f"{msg}: actual={actual}, expected={expected}, "
            f"diff={diff:.6f}, tolerance={tolerance}"
        )

    return True


def compare_numbers_relative(
    actual: float,
    expected: float,
    tolerance_percent: float = 1.0,
    message: Optional[str] = None
) -> bool:
    """
    Compare two numbers with relative (percentage) tolerance.

    Args:
        actual: The actual value
        expected: The expected value
        tolerance_percent: Acceptable percentage difference (default: 1%)
        message: Custom error message prefix

    Returns:
        True if within tolerance

    Raises:
        AssertionError: If relative difference exceeds tolerance
    """
    if expected == 0:
        # Handle zero expected - use absolute tolerance
        return compare_numbers(actual, expected, tolerance=0.001, message=message)

    diff_percent = abs(actual - expected) / abs(expected) * 100

    if diff_percent > tolerance_percent:
        msg = message or "Number mismatch (relative)"
        raise AssertionError(
            f"{msg}: actual={actual}, expected={expected}, "
            f"diff={diff_percent:.2f}%, tolerance={tolerance_percent}%"
        )

    return True


def compare_within_range(
    value: float,
    min_val: float,
    max_val: float,
    message: Optional[str] = None
) -> bool:
    """
    Check if value is within specified range.

    Args:
        value: The value to check
        min_val: Minimum acceptable value (inclusive)
        max_val: Maximum acceptable value (inclusive)
        message: Custom error message prefix

    Returns:
        True if within range

    Raises:
        AssertionError: If value outside range
    """
    if not (min_val <= value <= max_val):
        msg = message or "Value out of range"
        raise AssertionError(
            f"{msg}: value={value}, range=[{min_val}, {max_val}]"
        )

    return True


# ============================================================
# VECTOR COMPARISON
# ============================================================

def compare_vectors(
    actual: Tuple[float, ...],
    expected: Tuple[float, ...],
    tolerance: float = 0.001,
    message: Optional[str] = None
) -> bool:
    """
    Compare two vectors with tolerance.

    Args:
        actual: The actual vector (tuple of floats)
        expected: The expected vector (tuple of floats)
        tolerance: Acceptable absolute difference per component
        message: Custom error message prefix

    Returns:
        True if all components within tolerance

    Raises:
        AssertionError: If length mismatch or component difference exceeds tolerance
    """
    if len(actual) != len(expected):
        raise AssertionError(
            f"Vector length mismatch: {len(actual)} vs {len(expected)}"
        )

    for i, (a, e) in enumerate(zip(actual, expected)):
        diff = abs(a - e)
        if diff > tolerance:
            msg = message or "Vector mismatch"
            raise AssertionError(
                f"{msg}: component {i} - actual={a}, expected={e}, "
                f"diff={diff:.6f}, tolerance={tolerance}"
            )

    return True


def compare_vectors_length(
    actual: Tuple[float, ...],
    expected_length: float,
    tolerance: float = 0.001
) -> bool:
    """
    Compare vector length with expected.

    Args:
        actual: The actual vector
        expected_length: Expected magnitude of the vector
        tolerance: Acceptable difference in length

    Returns:
        True if length within tolerance
    """
    actual_length = math.sqrt(sum(x * x for x in actual))
    return compare_numbers(actual_length, expected_length, tolerance, "Vector length")


# ============================================================
# FILE VALIDATION
# ============================================================

def file_exists(
    path: Union[str, Path],
    file_type: str = "file",
    check_non_empty: bool = True
) -> bool:
    """
    Validate that a file exists and optionally check it's not empty.

    Args:
        path: Path to the file
        file_type: Description for error messages
        check_non_empty: If True, fail on empty files

    Returns:
        True if file exists (and is non-empty if checked)

    Raises:
        AssertionError: If file doesn't exist or is empty
    """
    path = Path(path)

    if not path.exists():
        raise AssertionError(f"{file_type} does not exist: {path}")

    if check_non_empty and path.is_file() and path.stat().st_size == 0:
        raise AssertionError(f"{file_type} is empty: {path}")

    return True


def directory_exists(path: Union[str, Path]) -> bool:
    """
    Validate that a directory exists.

    Args:
        path: Path to the directory

    Returns:
        True if directory exists

    Raises:
        AssertionError: If directory doesn't exist or is a file
    """
    path = Path(path)

    if not path.exists():
        raise AssertionError(f"Directory does not exist: {path}")

    if not path.is_dir():
        raise AssertionError(f"Path is not a directory: {path}")

    return True


def files_exist(
    paths: List[Union[str, Path]],
    base_dir: Optional[Union[str, Path]] = None
) -> bool:
    """
    Validate that multiple files exist.

    Args:
        paths: List of file paths
        base_dir: Optional base directory to prefix all paths

    Returns:
        True if all files exist

    Raises:
        AssertionError: If any file is missing (lists all missing)
    """
    base = Path(base_dir) if base_dir else Path(".")

    missing = []
    for p in paths:
        full_path = base / p if not Path(p).is_absolute() else Path(p)
        if not full_path.exists():
            missing.append(str(p))

    if missing:
        raise AssertionError(
            f"Missing files ({len(missing)}):\n" +
            "\n".join(f"  - {m}" for m in missing)
        )

    return True


# ============================================================
# SUBPROCESS VALIDATION
# ============================================================

def exit_code_zero(
    result: subprocess.CompletedProcess,
    context: str = ""
) -> bool:
    """
    Validate subprocess completed with exit code 0.

    Args:
        result: CompletedProcess from subprocess.run()
        context: Description of what was being run

    Returns:
        True if exit code is 0

    Raises:
        AssertionError: If exit code is non-zero (includes stderr)
    """
    if result.returncode != 0:
        stderr = result.stderr
        if isinstance(stderr, bytes):
            stderr = stderr.decode('utf-8', errors='replace')

        raise AssertionError(
            f"Process failed with exit code {result.returncode}"
            f"{f': {context}' if context else ''}\n"
            f"stderr: {stderr or '(empty)'}"
        )

    return True


def no_stderr(
    result: subprocess.CompletedProcess,
    allow_patterns: Optional[List[str]] = None
) -> bool:
    """
    Validate subprocess produced no unexpected stderr output.

    Args:
        result: CompletedProcess from subprocess.run()
        allow_patterns: List of regex patterns to allow in stderr

    Returns:
        True if no unexpected stderr

    Raises:
        AssertionError: If unexpected stderr output found
    """
    import re

    stderr = result.stderr
    if isinstance(stderr, bytes):
        stderr = stderr.decode('utf-8', errors='replace')

    if not stderr or not stderr.strip():
        return True

    # Check if all lines match allowed patterns
    if allow_patterns:
        lines = stderr.strip().split('\n')
        for line in lines:
            if not any(re.search(p, line) for p in allow_patterns):
                raise AssertionError(f"Unexpected stderr output: {stderr}")
        return True

    raise AssertionError(f"Unexpected stderr output: {stderr}")


# ============================================================
# IMAGE VALIDATION
# ============================================================

def image_not_blank(path: Union[str, Path]) -> bool:
    """
    Validate that an image is not blank (all same color).

    Args:
        path: Path to image file

    Returns:
        True if image has variation

    Raises:
        AssertionError: If image is blank (single color)
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("PIL required for image validation: pip install Pillow")

    path = Path(path)
    file_exists(path, "Image")

    img = Image.open(path)
    pixels = list(img.getdata())

    if len(pixels) == 0:
        raise AssertionError(f"Image has no pixels: {path}")

    first_pixel = pixels[0]
    all_same = all(p == first_pixel for p in pixels)

    if all_same:
        raise AssertionError(f"Image is blank (all pixels same color): {path}")

    return True


def image_resolution(
    path: Union[str, Path],
    expected_width: int,
    expected_height: int
) -> bool:
    """
    Validate image has expected resolution.

    Args:
        path: Path to image file
        expected_width: Expected width in pixels
        expected_height: Expected height in pixels

    Returns:
        True if resolution matches

    Raises:
        AssertionError: If resolution doesn't match
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("PIL required for image validation: pip install Pillow")

    path = Path(path)
    file_exists(path, "Image")

    img = Image.open(path)

    if img.size != (expected_width, expected_height):
        raise AssertionError(
            f"Image resolution mismatch: {path}\n"
            f"  actual: {img.size}\n"
            f"  expected: ({expected_width}, {expected_height})"
        )

    return True


def images_similar(
    path1: Union[str, Path],
    path2: Union[str, Path],
    pixel_tolerance: float = 0.01,
    color_threshold: int = 10
) -> Tuple[bool, float]:
    """
    Compare two images with tolerance.

    Args:
        path1: Path to first image
        path2: Path to second image
        pixel_tolerance: Maximum ratio of different pixels (0.01 = 1%)
        color_threshold: Maximum color difference per channel

    Returns:
        Tuple of (matches, diff_ratio)

    Raises:
        AssertionError: If images differ more than tolerance
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("PIL required for image validation: pip install Pillow")

    path1, path2 = Path(path1), Path(path2)

    file_exists(path1, "Image 1")
    file_exists(path2, "Image 2")

    img1 = Image.open(path1)
    img2 = Image.open(path2)

    if img1.size != img2.size:
        raise AssertionError(
            f"Image size mismatch: {img1.size} vs {img2.size}"
        )

    pixels1 = list(img1.getdata())
    pixels2 = list(img2.getdata())

    total = len(pixels1)
    different = 0

    for p1, p2 in zip(pixels1, pixels2):
        if not _pixels_similar(p1, p2, color_threshold):
            different += 1

    diff_ratio = different / total

    if diff_ratio > pixel_tolerance:
        raise AssertionError(
            f"Images differ by {diff_ratio:.2%} (max: {pixel_tolerance:.0%})\n"
            f"  {path1}\n  {path2}"
        )

    return True, diff_ratio


def _pixels_similar(p1: tuple, p2: tuple, threshold: int) -> bool:
    """Check if two pixels are similar within threshold."""
    if len(p1) != len(p2):
        return False
    return all(abs(a - b) <= threshold for a, b in zip(p1, p2))


# ============================================================
# VIDEO VALIDATION
# ============================================================

def video_valid(path: Union[str, Path]) -> bool:
    """
    Validate that a video file is valid and playable.

    Args:
        path: Path to video file

    Returns:
        True if video is valid

    Raises:
        AssertionError: If video is invalid or ffprobe unavailable
    """
    path = Path(path)
    file_exists(path, "Video")

    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error",
             "-select_streams", "v:0",
             "-show_entries", "stream=codec_name",
             "-of", "json", str(path)],
            capture_output=True,
            timeout=30
        )

        if result.returncode != 0:
            raise AssertionError(f"Invalid video file: {path}")

        data = json.loads(result.stdout)
        if not data.get("streams"):
            raise AssertionError(f"Video has no streams: {path}")

        return True

    except FileNotFoundError:
        raise AssertionError("ffprobe not available - cannot validate video")
    except subprocess.TimeoutExpired:
        raise AssertionError(f"ffprobe timeout on video: {path}")


def video_properties(
    path: Union[str, Path],
    codec: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None
) -> bool:
    """
    Validate video file properties.

    Args:
        path: Path to video file
        codec: Expected codec name (e.g., "h264")
        width: Expected width in pixels
        height: Expected height in pixels
        min_duration: Minimum duration in seconds
        max_duration: Maximum duration in seconds

    Returns:
        True if all specified properties match

    Raises:
        AssertionError: If any property doesn't match
    """
    path = Path(path)

    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error",
             "-select_streams", "v:0",
             "-show_entries", "stream=codec_name,width,height,duration",
             "-of", "json", str(path)],
            capture_output=True,
            timeout=30
        )

        exit_code_zero(result, "ffprobe")

        data = json.loads(result.stdout)
        stream = data["streams"][0]

        if codec and stream.get("codec_name") != codec:
            raise AssertionError(
                f"Video codec mismatch: {stream.get('codec_name')} vs expected {codec}"
            )

        if width:
            compare_numbers(
                int(stream.get("width", 0)), width, tolerance=0,
                message="Video width"
            )

        if height:
            compare_numbers(
                int(stream.get("height", 0)), height, tolerance=0,
                message="Video height"
            )

        if min_duration or max_duration:
            duration = float(stream.get("duration", 0))
            if min_duration:
                compare_within_range(duration, min_duration, max_duration or float('inf'))
            elif max_duration:
                compare_within_range(duration, 0, max_duration)

        return True

    except FileNotFoundError:
        raise AssertionError("ffprobe not available - cannot validate video properties")


# ============================================================
# ORACLE CLASS WRAPPER
# ============================================================

class Oracle:
    """
    Class-based wrapper for oracle validation functions.

    Provides assert_* style methods for use in unit tests.

    Usage:
        from oracle import Oracle

        Oracle.assert_equal(actual, expected)
        Oracle.assert_not_none(value)
        Oracle.assert_greater_than(value, threshold)
    """

    @staticmethod
    def assert_equal(actual: Any, expected: Any, message: str = "") -> bool:
        """Assert two values are equal."""
        if actual != expected:
            msg = f"Expected {expected!r} but got {actual!r}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_not_equal(actual: Any, expected: Any, message: str = "") -> bool:
        """Assert two values are not equal."""
        if actual == expected:
            msg = f"Expected values to differ, both are {actual!r}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_not_none(value: Any, message: str = "") -> bool:
        """Assert value is not None."""
        if value is None:
            msg = "Expected non-None value"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_none(value: Any, message: str = "") -> bool:
        """Assert value is None."""
        if value is not None:
            msg = f"Expected None but got {value!r}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_true(value: Any, message: str = "") -> bool:
        """Assert value is True."""
        if not value:
            msg = f"Expected True but got {value!r}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_false(value: Any, message: str = "") -> bool:
        """Assert value is False."""
        if value:
            msg = f"Expected False but got {value!r}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_greater_than(actual: float, threshold: float, message: str = "") -> bool:
        """Assert actual > threshold."""
        if not actual > threshold:
            msg = f"Expected {actual} > {threshold}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_greater_than_or_equal(actual: float, threshold: float, message: str = "") -> bool:
        """Assert actual >= threshold."""
        if not actual >= threshold:
            msg = f"Expected {actual} >= {threshold}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_less_than(actual: float, threshold: float, message: str = "") -> bool:
        """Assert actual < threshold."""
        if not actual < threshold:
            msg = f"Expected {actual} < {threshold}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_less_than_or_equal(actual: float, threshold: float, message: str = "") -> bool:
        """Assert actual <= threshold."""
        if not actual <= threshold:
            msg = f"Expected {actual} <= {threshold}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_in(item: Any, container: Any, message: str = "") -> bool:
        """Assert item is in container."""
        if item not in container:
            msg = f"Expected {item!r} to be in {container!r}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_not_in(item: Any, container: Any, message: str = "") -> bool:
        """Assert item is not in container."""
        if item in container:
            msg = f"Expected {item!r} to not be in {container!r}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_length(container: Any, expected_length: int, message: str = "") -> bool:
        """Assert container has expected length."""
        actual_len = len(container)
        if actual_len != expected_length:
            msg = f"Expected length {expected_length} but got {actual_len}"
            if message:
                msg = f"{message}: {msg}"
            raise AssertionError(msg)
        return True

    @staticmethod
    def assert_almost_equal(actual: float, expected: float, tolerance: float = 0.001, message: str = "") -> bool:
        """Assert two numbers are equal within tolerance."""
        return compare_numbers(actual, expected, tolerance, message)

    @staticmethod
    def assert_vector_equal(actual: Tuple[float, ...], expected: Tuple[float, ...], tolerance: float = 0.001, message: str = "") -> bool:
        """Assert two vectors are equal within tolerance."""
        return compare_vectors(actual, expected, tolerance, message)

    @staticmethod
    def assert_file_exists(path: Union[str, Path], message: str = "") -> bool:
        """Assert file exists."""
        return file_exists(path, message or "File")

    @staticmethod
    def assert_directory_exists(path: Union[str, Path], message: str = "") -> bool:
        """Assert directory exists."""
        return directory_exists(path)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def all_pass(validations: List[callable]) -> bool:
    """
    Run multiple validations and collect all failures.

    Args:
        validations: List of validation functions to call

    Returns:
        True if all pass

    Raises:
        AssertionError: With all failures listed
    """
    failures = []

    for validation in validations:
        try:
            validation()
        except AssertionError as e:
            failures.append(str(e))

    if failures:
        raise AssertionError(
            f"Validation failures ({len(failures)}):\n" +
            "\n".join(f"  - {f}" for f in failures)
        )

    return True


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    print("Testing oracle functions...")

    # Test number comparison
    assert compare_numbers(5.0, 5.0, tolerance=0.001)
    assert compare_numbers(5.001, 5.0, tolerance=0.01)

    try:
        compare_numbers(5.1, 5.0, tolerance=0.001)
        assert False, "Should have raised"
    except AssertionError:
        pass

    # Test vector comparison
    assert compare_vectors((1.0, 2.0, 3.0), (1.0, 2.0, 3.0))
    assert compare_vectors((1.001, 2.0, 3.0), (1.0, 2.0, 3.0), tolerance=0.01)

    try:
        compare_vectors((1.0, 2.0), (1.0, 2.0, 3.0))
        assert False, "Should have raised"
    except AssertionError:
        pass

    # Test range
    assert compare_within_range(5.0, 0.0, 10.0)

    try:
        compare_within_range(15.0, 0.0, 10.0)
        assert False, "Should have raised"
    except AssertionError:
        pass

    print("All oracle self-tests passed!")
