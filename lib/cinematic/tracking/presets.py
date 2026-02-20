"""
Tracking Preset Loader

Provides functions to load tracking presets from YAML configuration.
Presets control feature detection and tracking parameters.

Presets:
- high_quality: Maximum accuracy, slower processing
- balanced: Good trade-off (default)
- fast: Quick results, lower accuracy
- architectural: Optimized for buildings/interiors
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Optional, List
import os

# Try importing yaml, fall back to None
try:
    import yaml
except ImportError:
    yaml = None

# Default preset directory
PRESET_DIR = Path(__file__).parent.parent.parent.parent / "configs" / "cinematic" / "tracking"


def load_tracking_preset(preset_name: str) -> Dict[str, Any]:
    """
    Load a tracking preset by name.

    Args:
        preset_name: Name of preset (e.g., 'balanced', 'high_quality')

    Returns:
        Dict with preset parameters

    Raises:
        FileNotFoundError: If preset file or preset name not found
        RuntimeError: If PyYAML not installed
    """
    preset_file = PRESET_DIR / "tracking_presets.yaml"

    if not preset_file.exists():
        raise FileNotFoundError(f"Tracking presets file not found: {preset_file}")

    if yaml is None:
        raise RuntimeError("PyYAML not installed. Install with: pip install pyyaml")

    with open(preset_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    presets = data.get("presets", {})

    if preset_name not in presets:
        available = list(presets.keys())
        raise ValueError(f"Preset '{preset_name}' not found. Available: {available}")

    return presets[preset_name]


def get_tracking_preset(preset_name: str = "balanced") -> Dict[str, Any]:
    """
    Get tracking preset with defaults applied.

    Convenience wrapper that returns the preset dict with
    all parameters resolved.

    Args:
        preset_name: Name of preset

    Returns:
        Dict with detection and tracking parameters
    """
    return load_tracking_preset(preset_name)


def get_detection_params(preset_name: str = "balanced") -> Dict[str, Any]:
    """
    Get detection-specific parameters from preset.

    Args:
        preset_name: Name of preset

    Returns:
        Dict with detection parameters (threshold, margin, min_distance, etc.)
    """
    preset = load_tracking_preset(preset_name)
    return preset.get("detection", {})


def get_tracking_params(preset_name: str = "balanced") -> Dict[str, Any]:
    """
    Get tracking-specific parameters from preset.

    Args:
        preset_name: Name of preset

    Returns:
        Dict with tracking parameters (correlation_threshold, etc.)
    """
    preset = load_tracking_preset(preset_name)
    return preset.get("tracking", {})


def get_clean_params(preset_name: str = "balanced") -> Dict[str, Any]:
    """
    Get track cleaning parameters from preset.

    Args:
        preset_name: Name of preset

    Returns:
        Dict with clean parameters (frames, error threshold)
    """
    preset = load_tracking_preset(preset_name)
    return preset.get("clean", {})


def list_tracking_presets() -> List[str]:
    """
    List all available tracking presets.

    Returns:
        List of preset names
    """
    preset_file = PRESET_DIR / "tracking_presets.yaml"

    if not preset_file.exists():
        return []

    if yaml is None:
        return []

    with open(preset_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return list(data.get("presets", {}).keys())


def get_preset_description(preset_name: str) -> str:
    """
    Get the description of a preset.

    Args:
        preset_name: Name of preset

    Returns:
        Preset description string
    """
    preset = load_tracking_preset(preset_name)
    return preset.get("description", "")


def merge_preset_with_overrides(
    preset_name: str,
    detection_overrides: Optional[Dict[str, Any]] = None,
    tracking_overrides: Optional[Dict[str, Any]] = None,
    clean_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Load a preset and merge with parameter overrides.

    Args:
        preset_name: Base preset name
        detection_overrides: Detection parameter overrides
        tracking_overrides: Tracking parameter overrides
        clean_overrides: Clean parameter overrides

    Returns:
        Merged preset dictionary
    """
    preset = load_tracking_preset(preset_name)

    if detection_overrides:
        preset["detection"] = {**preset.get("detection", {}), **detection_overrides}

    if tracking_overrides:
        preset["tracking"] = {**preset.get("tracking", {}), **tracking_overrides}

    if clean_overrides:
        preset["clean"] = {**preset.get("clean", {}), **clean_overrides}

    return preset


def get_motion_model(preset_name: str = "balanced") -> str:
    """
    Get the motion model from a tracking preset.

    Args:
        preset_name: Name of preset

    Returns:
        Motion model string (e.g., "Perspective", "LocRot")
    """
    tracking_params = get_tracking_params(preset_name)
    return tracking_params.get("motion_model", "Perspective")


def get_correlation_threshold(preset_name: str = "balanced") -> float:
    """
    Get the minimum correlation threshold from a tracking preset.

    Args:
        preset_name: Name of preset

    Returns:
        Correlation threshold (0-1)
    """
    tracking_params = get_tracking_params(preset_name)
    return tracking_params.get("correlation_min", 0.7)


# Preset validation

def validate_preset(preset_name: str) -> List[str]:
    """
    Validate a preset for completeness.

    Args:
        preset_name: Name of preset to validate

    Returns:
        List of validation warnings (empty if valid)
    """
    warnings = []

    try:
        preset = load_tracking_preset(preset_name)
    except (FileNotFoundError, ValueError) as e:
        return [str(e)]

    # Check for required sections
    if "detection" not in preset:
        warnings.append("Missing 'detection' section")

    if "tracking" not in preset:
        warnings.append("Missing 'tracking' section")

    # Check detection parameters
    detection = preset.get("detection", {})
    required_detection = ["threshold", "margin", "min_distance"]
    for param in required_detection:
        if param not in detection:
            warnings.append(f"Missing detection parameter: {param}")

    # Check tracking parameters
    tracking = preset.get("tracking", {})
    required_tracking = ["motion_model", "correlation_min"]
    for param in required_tracking:
        if param not in tracking:
            warnings.append(f"Missing tracking parameter: {param}")

    # Validate ranges
    if "threshold" in detection:
        t = detection["threshold"]
        if not 0 <= t <= 1:
            warnings.append(f"Detection threshold {t} out of range [0, 1]")

    if "correlation_min" in tracking:
        c = tracking["correlation_min"]
        if not 0 <= c <= 1:
            warnings.append(f"Correlation threshold {c} out of range [0, 1]")

    return warnings


__all__ = [
    "load_tracking_preset",
    "get_tracking_preset",
    "get_detection_params",
    "get_tracking_params",
    "get_clean_params",
    "list_tracking_presets",
    "get_preset_description",
    "merge_preset_with_overrides",
    "get_motion_model",
    "get_correlation_threshold",
    "validate_preset",
    "PRESET_DIR",
]
