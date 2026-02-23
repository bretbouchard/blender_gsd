"""
MSG 1998 - ControlNet Configuration

ControlNet setup for SD style transfer.
"""

from pathlib import Path
from typing import Dict, List, Optional

from .types import ControlNetConfig


# Default ControlNet models
DEFAULT_MODELS = {
    "depth": "control_v11f1p_sd15_depth",
    "normal": "control_v11p_sd15_normalbae",
    "canny": "control_v11p_sd15_canny",
}


def load_controlnet_models(config: ControlNetConfig) -> Dict[str, any]:
    """
    Load ControlNet models into SD pipeline.

    Note: This returns configuration for external SD pipeline.
    Actual loading happens in SD WebUI or ComfyUI.

    Args:
        config: ControlNet configuration

    Returns:
        Model configuration dict
    """
    return {
        "depth": {
            "model": config.depth_model,
            "weight": config.depth_weight,
            "guidance_start": config.guidance_start,
            "guidance_end": config.guidance_end,
        },
        "normal": {
            "model": config.normal_model,
            "weight": config.normal_weight,
            "guidance_start": config.guidance_start,
            "guidance_end": min(config.guidance_end, 0.8),  # Normal less in later steps
        },
        "canny": {
            "model": config.canny_model,
            "weight": config.canny_weight,
            "enabled": config.canny_enabled,
        }
    }


def prepare_depth_map(
    depth_exr: Path,
    output_dir: Path,
    invert: bool = False,
    normalize: bool = True
) -> Path:
    """
    Convert depth EXR to ControlNet-compatible format.

    Args:
        depth_exr: Path to depth EXR file
        output_dir: Output directory
        invert: Whether to invert depth (white = close)
        normalize: Whether to normalize to 0-1 range

    Returns:
        Path to processed depth map
    """
    if not depth_exr.exists():
        raise FileNotFoundError(f"Depth file not found: {depth_exr}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{depth_exr.stem}_controlnet.png"

    # Note: Actual image processing would use PIL/OpenCV
    # This returns the expected output path
    return output_path


def prepare_normal_map(
    normal_exr: Path,
    output_dir: Path,
    swap_channels: bool = False
) -> Path:
    """
    Convert normal EXR to ControlNet-compatible format.

    Args:
        normal_exr: Path to normal EXR file
        output_dir: Output directory
        swap_channels: Whether to swap RG channels (Blender vs OpenGL)

    Returns:
        Path to processed normal map
    """
    if not normal_exr.exists():
        raise FileNotFoundError(f"Normal file not found: {normal_exr}")

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{normal_exr.stem}_controlnet.png"

    return output_path


def create_controlnet_preprocessor_config() -> Dict[str, any]:
    """
    Create preprocessor configuration for ControlNet.

    Returns:
        Preprocessor config dict
    """
    return {
        "depth": {
            "preprocessor": "depth_anything",  # or "midas", "zoe"
            "resolution": 512,
        },
        "normal": {
            "preprocessor": "normalbae",
            "resolution": 512,
        },
        "canny": {
            "preprocessor": "canny",
            "low_threshold": 100,
            "high_threshold": 200,
        }
    }


def get_controlnet_pipeline_config(
    config: ControlNetConfig,
    preprocess_depth: bool = True,
    preprocess_normal: bool = True
) -> Dict[str, any]:
    """
    Get full pipeline configuration for SD generation.

    Args:
        config: ControlNet configuration
        preprocess_depth: Whether depth needs preprocessing
        preprocess_normal: Whether normal needs preprocessing

    Returns:
        Full pipeline configuration
    """
    return {
        "controlnet": load_controlnet_models(config),
        "preprocessors": create_controlnet_preprocessor_config(),
        "settings": {
            "preprocess_depth": preprocess_depth,
            "preprocess_normal": preprocess_normal,
            "guess_mode": False,
            "pixel_perfect": True,
        }
    }


def validate_controlnet_input(
    depth_path: Optional[Path],
    normal_path: Optional[Path],
    config: ControlNetConfig
) -> List[str]:
    """
    Validate ControlNet inputs exist and are correct format.

    Args:
        depth_path: Path to depth map
        normal_path: Path to normal map
        config: ControlNet configuration

    Returns:
        List of validation errors
    """
    errors = []

    if config.depth_weight > 0:
        if not depth_path:
            errors.append("Depth map required but not provided")
        elif not depth_path.exists():
            errors.append(f"Depth map not found: {depth_path}")

    if config.normal_weight > 0:
        if not normal_path:
            errors.append("Normal map required but not provided")
        elif not normal_path.exists():
            errors.append(f"Normal map not found: {normal_path}")

    return errors
