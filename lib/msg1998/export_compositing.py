"""
MSG 1998 - Export to Compositing

Export renders and metadata for compositing phase.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

from .types import CompositeLayer


def export_for_compositing(
    location_id: str,
    scene_id: str,
    output_dir: Path
) -> Dict[str, Path]:
    """
    Export all renders and masks for compositing.

    Args:
        location_id: Location identifier
        scene_id: Scene identifier
        output_dir: Output directory

    Returns:
        Dict mapping pass names to file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    renders_dir = output_dir / "location_renders"
    masks_dir = output_dir / "masks"

    renders_dir.mkdir(exist_ok=True)
    masks_dir.mkdir(exist_ok=True)

    output_files = {
        "beauty": renders_dir / f"{location_id}_beauty.exr",
        "depth": renders_dir / f"{location_id}_depth.exr",
        "normal": renders_dir / f"{location_id}_normal.exr",
        "object_id": renders_dir / f"{location_id}_object_id.exr",
        "bg_mask": masks_dir / f"{location_id}_bg_mask.png",
        "mg_mask": masks_dir / f"{location_id}_mg_mask.png",
        "fg_mask": masks_dir / f"{location_id}_fg_mask.png",
    }

    return output_files


def generate_metadata(
    render_settings: Dict[str, Any],
    camera_settings: Dict[str, Any],
    layer_config: Dict[str, str]
) -> Dict[str, Any]:
    """
    Generate metadata.json for compositing phase.

    Args:
        render_settings: Render configuration
        camera_settings: Camera configuration
        layer_config: Layer descriptions

    Returns:
        Metadata dict
    """
    return {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "render_settings": {
            "resolution": render_settings.get("resolution", [4096, 1716]),
            "frame_rate": render_settings.get("frame_rate", 24),
            "color_space": render_settings.get("color_space", "ACEScg"),
            "samples": render_settings.get("samples", 256),
        },
        "camera": {
            "focal_length_mm": camera_settings.get("focal_length_mm", 35),
            "sensor_width_mm": camera_settings.get("sensor_width_mm", 36),
            "fov_degrees": camera_settings.get("fov_degrees", 54.4),
        },
        "layers": layer_config,
        "passes": ["beauty", "depth", "normal", "object_id", "diffuse", "shadow", "ao"],
        "cryptomatte_layers": ["object", "material"],
    }


def write_metadata(output_path: Path, metadata: Dict[str, Any]) -> None:
    """Write metadata to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)


def create_compositing_handoff(
    location_id: str,
    scene_id: str,
    render_dir: Path,
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create complete handoff package for compositing.

    Args:
        location_id: Location identifier
        scene_id: Scene identifier
        render_dir: Directory containing renders
        metadata: Metadata dict

    Returns:
        Handoff package info
    """
    handoff = {
        "location_id": location_id,
        "scene_id": scene_id,
        "render_dir": str(render_dir),
        "passes": {},
        "masks": {},
        "metadata": metadata,
        "ready_for_compositing": True,
    }

    # Check for expected files
    expected_passes = ["beauty", "depth", "normal", "object_id"]
    for pass_name in expected_passes:
        pass_file = render_dir / "location_renders" / f"{location_id}_{pass_name}.exr"
        if pass_file.exists():
            handoff["passes"][pass_name] = str(pass_file)
        else:
            handoff["ready_for_compositing"] = False

    expected_masks = ["bg", "mg", "fg"]
    for mask_name in expected_masks:
        mask_file = render_dir / "masks" / f"{location_id}_{mask_name}_mask.png"
        if mask_file.exists():
            handoff["masks"][mask_name] = str(mask_file)

    return handoff


def validate_compositing_readiness(output_dir: Path) -> Dict[str, Any]:
    """
    Check if output directory has all required files for compositing.

    Args:
        output_dir: Output directory to check

    Returns:
        Validation result
    """
    required_passes = ["beauty", "depth", "normal", "object_id"]
    required_masks = ["bg", "mg", "fg"]

    missing = []
    found = []

    renders_dir = output_dir / "location_renders"
    masks_dir = output_dir / "masks"

    for pass_name in required_passes:
        pass_file = renders_dir / f"*_{pass_name}.exr"
        if not list(renders_dir.glob(f"*_{pass_name}.exr")):
            missing.append(f"pass:{pass_name}")
        else:
            found.append(f"pass:{pass_name}")

    for mask_name in required_masks:
        mask_file = masks_dir / f"*_{mask_name}_mask.png"
        if not list(masks_dir.glob(f"*_{mask_name}_mask.png")):
            missing.append(f"mask:{mask_name}")
        else:
            found.append(f"mask:{mask_name}")

    # Check metadata
    metadata_file = output_dir / "metadata.json"
    if not metadata_file.exists():
        missing.append("metadata.json")

    return {
        "ready": len(missing) == 0,
        "missing": missing,
        "found": found,
        "pass_count": len([f for f in found if f.startswith("pass:")]),
        "mask_count": len([f for f in found if f.startswith("mask:")]),
    }
