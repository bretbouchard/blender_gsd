"""
MSG 1998 - SD Configuration

Load and validate SD configs from FDX GSD.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .types import ControlNetConfig, SDShotConfig


def load_sd_config(config_path: Path) -> SDShotConfig:
    """
    Load SD config from FDX handoff.

    Args:
        config_path: Path to SD config JSON

    Returns:
        SDShotConfig object
    """
    if not config_path.exists():
        return SDShotConfig(shot_id="", scene_id="")

    try:
        with open(config_path) as f:
            data = json.load(f)
    except json.JSONDecodeError:
        return SDShotConfig(shot_id="", scene_id="")

    # Parse ControlNet config
    cn_data = data.get("controlnet", {})
    controlnet_config = ControlNetConfig(
        depth_model=cn_data.get("depth_model", "control_v11f1p_sd15_depth"),
        depth_weight=cn_data.get("depth_weight", 1.0),
        normal_model=cn_data.get("normal_model", "control_v11p_sd15_normalbae"),
        normal_weight=cn_data.get("normal_weight", 0.8),
        guidance_start=cn_data.get("guidance_start", 0.0),
        guidance_end=cn_data.get("guidance_end", 1.0),
    )

    return SDShotConfig(
        shot_id=data.get("shot_id", ""),
        scene_id=data.get("scene_id", ""),
        seeds=data.get("seeds", {}),
        positive_prompt=data.get("positive_prompt", ""),
        negative_prompt=data.get("negative_prompt", ""),
        controlnet_config=controlnet_config,
        layer_configs=data.get("layer_configs", {}),
        steps=data.get("steps", 30),
        cfg_scale=data.get("cfg_scale", 7.0),
        sampler=data.get("sampler", "DPM++ 2M Karras"),
    )


def validate_sd_config(config: SDShotConfig) -> List[str]:
    """
    Validate SD config has all required fields.

    Args:
        config: Config to validate

    Returns:
        List of validation errors
    """
    errors = []

    if not config.shot_id:
        errors.append("Missing shot_id")

    if not config.scene_id:
        errors.append("Missing scene_id")

    if not config.seeds:
        errors.append("No seeds defined")

    if not config.positive_prompt:
        errors.append("Missing positive_prompt")

    if config.steps < 1 or config.steps > 150:
        errors.append(f"Steps out of range (1-150): {config.steps}")

    if config.cfg_scale < 1.0 or config.cfg_scale > 30.0:
        errors.append(f"CFG scale out of range (1-30): {config.cfg_scale}")

    return errors


def create_default_sd_config(
    shot_id: str,
    scene_id: str,
    base_seed: int
) -> SDShotConfig:
    """
    Create default SD config with sensible defaults.

    Args:
        shot_id: Shot identifier
        scene_id: Scene identifier
        base_seed: Base seed for generation

    Returns:
        SDShotConfig with defaults
    """
    from .prompts_1998 import POSITIVE_BASE, NEGATIVE_BASE

    return SDShotConfig(
        shot_id=shot_id,
        scene_id=scene_id,
        seeds={
            "background": base_seed,
            "midground": base_seed + 1,
            "foreground": base_seed + 2,
        },
        positive_prompt=POSITIVE_BASE,
        negative_prompt=NEGATIVE_BASE,
        controlnet_config=ControlNetConfig(),
        steps=30,
        cfg_scale=7.0,
        sampler="DPM++ 2M Karras",
    )


def merge_prompts(
    base_positive: str,
    scene_type: str,
    layer_name: str
) -> str:
    """
    Merge base prompt with scene and layer additions.

    Args:
        base_positive: Base positive prompt
        scene_type: Type of scene
        layer_name: Layer being generated

    Returns:
        Combined prompt string
    """
    from .prompts_1998 import SCENE_PROMPTS, build_prompt

    return build_prompt(base_positive, scene_type, layer_name)


def get_layer_seed(config: SDShotConfig, layer_name: str) -> int:
    """
    Get seed for specific layer.

    Args:
        config: SD config
        layer_name: Layer name

    Returns:
        Seed value (0 if not found)
    """
    return config.seeds.get(layer_name, 0)


def export_sd_config_for_api(config: SDShotConfig) -> Dict[str, Any]:
    """
    Export config in format suitable for SD API.

    Args:
        config: SD config

    Returns:
        API-compatible dict
    """
    return {
        "prompt": config.positive_prompt,
        "negative_prompt": config.negative_prompt,
        "steps": config.steps,
        "cfg_scale": config.cfg_scale,
        "sampler_name": config.sampler,
        "seed": list(config.seeds.values())[0] if config.seeds else -1,
        "controlnet_units": [
            {
                "model": config.controlnet_config.depth_model,
                "weight": config.controlnet_config.depth_weight,
                "module": "depth_anything",
            },
            {
                "model": config.controlnet_config.normal_model,
                "weight": config.controlnet_config.normal_weight,
                "module": "normalbae",
            }
        ]
    }
