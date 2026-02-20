"""
Production Loader

Load production configurations from YAML files and directories.

Requirements:
- REQ-ORCH-01: Load complete production from YAML
- Reference resolution and preset loading

Part of Phase 14.1: Production Orchestrator
"""

from __future__ import annotations
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

from .production_types import (
    ProductionConfig,
    ProductionMeta,
    CharacterConfig,
    LocationConfig,
    ShotConfig,
    StyleConfig,
    RenderSettings,
    OutputFormat,
    RetroConfig,
    get_output_format_preset,
)


def load_yaml(path: str) -> Dict[str, Any]:
    """
    Load YAML file with safe loader.

    Args:
        path: Path to YAML file

    Returns:
        Parsed YAML data as dictionary
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(data: Dict[str, Any], path: str) -> None:
    """
    Save dictionary to YAML file.

    Args:
        data: Data to save
        path: Output path
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def load_production(yaml_path: str) -> ProductionConfig:
    """
    Load production from YAML file.

    Args:
        yaml_path: Path to production YAML file

    Returns:
        ProductionConfig instance
    """
    data = load_yaml(yaml_path)

    # Store base path for resolving relative paths
    data["base_path"] = str(Path(yaml_path).parent.absolute())

    # Parse production section if present
    if "production" in data:
        data = _flatten_production_data(data)

    config = ProductionConfig.from_dict(data)
    return config


def load_production_from_dir(dir_path: str) -> ProductionConfig:
    """
    Load production from directory (multiple YAMLs).

    Loads production.yaml as main config, then merges:
    - characters.yaml
    - locations.yaml
    - shots.yaml
    - outputs.yaml

    Args:
        dir_path: Path to production directory

    Returns:
        ProductionConfig instance
    """
    dir_path = Path(dir_path)
    config_data: Dict[str, Any] = {
        "base_path": str(dir_path.absolute()),
    }

    # Load main production file
    main_file = dir_path / "production.yaml"
    if main_file.exists():
        main_data = load_yaml(str(main_file))
        if "production" in main_data:
            main_data = _flatten_production_data(main_data)
        config_data.update(main_data)

    # Load characters file
    chars_file = dir_path / "characters.yaml"
    if chars_file.exists():
        chars_data = load_yaml(str(chars_file))
        if "characters" in chars_data:
            config_data["characters"] = chars_data["characters"]

    # Load locations file
    locs_file = dir_path / "locations.yaml"
    if locs_file.exists():
        locs_data = load_yaml(str(locs_file))
        if "locations" in locs_data:
            config_data["locations"] = locs_data["locations"]

    # Load shots file
    shots_file = dir_path / "shots.yaml"
    if shots_file.exists():
        shots_data = load_yaml(str(shots_file))
        if "shots" in shots_data:
            config_data["shots"] = shots_data["shots"]

    # Load outputs file
    outputs_file = dir_path / "outputs.yaml"
    if outputs_file.exists():
        outputs_data = load_yaml(str(outputs_file))
        if "outputs" in outputs_data:
            config_data["outputs"] = outputs_data["outputs"]

    return ProductionConfig.from_dict(config_data)


def _flatten_production_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten production section to top level.

    Converts:
        production:
            title: "My Film"
            characters: {...}
    To:
        title: "My Film"
        characters: {...}
    """
    result = data.copy()
    if "production" in result:
        prod_section = result.pop("production")
        if isinstance(prod_section, dict):
            result.update(prod_section)
    return result


def resolve_production(config: ProductionConfig) -> ProductionConfig:
    """
    Resolve all references and presets in production.

    - Resolves output format presets
    - Resolves character wardrobe references
    - Resolves location presets
    - Resolves style presets

    Args:
        config: Production configuration

    Returns:
        Resolved ProductionConfig instance
    """
    # Resolve output format presets
    resolved_outputs = []
    for output in config.outputs:
        if output.format and not output.resolution:
            # Try to resolve preset
            preset = get_output_format_preset(output.format)
            if preset:
                # Merge with override values
                resolved = OutputFormat(
                    name=output.name or preset.name,
                    format=preset.format,
                    codec=output.codec or preset.codec,
                    resolution=output.resolution if output.resolution != (1920, 1080) else preset.resolution,
                    frame_rate=output.frame_rate or preset.frame_rate,
                    retro_config=output.retro_config or preset.retro_config,
                    output_path=output.output_path,
                )
                resolved_outputs.append(resolved)
            else:
                resolved_outputs.append(output)
        else:
            resolved_outputs.append(output)

    config.outputs = resolved_outputs

    # Resolve paths relative to base_path
    if config.base_path:
        config = _resolve_paths(config)

    return config


def _resolve_paths(config: ProductionConfig) -> ProductionConfig:
    """
    Resolve relative paths to absolute paths.

    Args:
        config: Production configuration

    Returns:
        ProductionConfig with resolved paths
    """
    base = Path(config.base_path)

    # Resolve script path
    if config.script_path and not os.path.isabs(config.script_path):
        config.script_path = str((base / config.script_path).resolve())

    # Resolve shot list path
    if config.shot_list_path and not os.path.isabs(config.shot_list_path):
        config.shot_list_path = str((base / config.shot_list_path).resolve())

    # Resolve character model paths
    for name, char in config.characters.items():
        if char.model and not os.path.isabs(char.model):
            char.model = str((base / char.model).resolve())

    # Resolve output paths
    for output in config.outputs:
        if output.output_path and not os.path.isabs(output.output_path):
            output.output_path = str((base / output.output_path).resolve())

    return config


def expand_shots(config: ProductionConfig) -> ProductionConfig:
    """
    Expand shot list from script or templates.

    If shot_list_path is set, loads shots from that file.
    Generates shot names if not provided.

    Args:
        config: Production configuration

    Returns:
        ProductionConfig with expanded shots
    """
    # Load external shot list if specified
    if config.shot_list_path and os.path.exists(config.shot_list_path):
        shot_data = load_yaml(config.shot_list_path)
        if "shots" in shot_data:
            config.shots = [ShotConfig.from_dict(s) for s in shot_data["shots"]]

    # Generate names for unnamed shots
    for i, shot in enumerate(config.shots):
        if not shot.name:
            shot.name = f"shot_{i + 1:03d}"

    # Auto-assign scene numbers from template if needed
    current_scene = 1
    for shot in config.shots:
        if shot.scene == 0:
            shot.scene = current_scene
        else:
            current_scene = shot.scene

    return config


def save_production(config: ProductionConfig, path: str) -> None:
    """
    Save production configuration to YAML file.

    Args:
        config: Production configuration
        path: Output path
    """
    data = config.to_dict()

    # Remove base_path from saved data
    data.pop("base_path", None)

    # Wrap in production section
    save_data = {"production": data}
    save_yaml(save_data, path)


def create_production_from_template(
    name: str,
    template: str = "short_film",
    output_dir: Optional[str] = None
) -> ProductionConfig:
    """
    Create new production from template.

    Args:
        name: Production name
        template: Template name (short_film, commercial, game_assets)
        output_dir: Optional output directory

    Returns:
        ProductionConfig instance
    """
    templates = {
        "short_film": _create_short_film_template,
        "commercial": _create_commercial_template,
        "game_assets": _create_game_assets_template,
    }

    creator = templates.get(template, _create_short_film_template)
    config = creator(name)

    if output_dir:
        config.base_path = output_dir
        save_production(config, os.path.join(output_dir, "production.yaml"))

    return config


def _create_short_film_template(name: str) -> ProductionConfig:
    """Create short film template."""
    return ProductionConfig(
        meta=ProductionMeta(
            title=name,
            author="",
            description="Short film production",
        ),
        style=StyleConfig(
            preset="cinematic",
            mood="dramatic",
        ),
        render_settings=RenderSettings(
            engine="CYCLES",
            samples=128,
            resolution_x=1920,
            resolution_y=1080,
            quality_tier="production",
        ),
        outputs=[
            OutputFormat(
                name="Master",
                format="streaming_1080p",
                codec="prores_4444",
                resolution=(1920, 1080),
                output_path="output/master/",
            ),
        ],
    )


def _create_commercial_template(name: str) -> ProductionConfig:
    """Create commercial template."""
    return ProductionConfig(
        meta=ProductionMeta(
            title=name,
            author="",
            description="Commercial production",
        ),
        style=StyleConfig(
            preset="product_hero",
            mood="bright",
        ),
        render_settings=RenderSettings(
            engine="CYCLES",
            samples=256,
            resolution_x=1920,
            resolution_y=1080,
            quality_tier="production",
        ),
        outputs=[
            OutputFormat(
                name="Master",
                format="streaming_1080p",
                codec="prores_4444",
                resolution=(1920, 1080),
                output_path="output/master/",
            ),
            OutputFormat(
                name="Social",
                format="social_square",
                codec="h264",
                resolution=(1080, 1080),
                output_path="output/social/",
            ),
        ],
    )


def _create_game_assets_template(name: str) -> ProductionConfig:
    """Create game assets template."""
    return ProductionConfig(
        meta=ProductionMeta(
            title=name,
            author="",
            description="Game asset production",
        ),
        style=StyleConfig(
            preset="stylized",
            mood="bright",
        ),
        render_settings=RenderSettings(
            engine="BLENDER_EEVEE_NEXT",
            samples=32,
            resolution_x=1024,
            resolution_y=1024,
            quality_tier="preview",
        ),
        outputs=[
            OutputFormat(
                name="16-bit",
                format="16bit_game",
                codec="png",
                resolution=(256, 256),
                output_path="output/16bit/",
                retro_config=RetroConfig(
                    enabled=True,
                    palette="snes",
                    dither="error_diffusion",
                ),
            ),
            OutputFormat(
                name="8-bit",
                format="8bit_game",
                codec="png",
                resolution=(128, 128),
                output_path="output/8bit/",
                retro_config=RetroConfig(
                    enabled=True,
                    palette="nes",
                    dither="ordered",
                ),
            ),
        ],
    )


def list_productions(directory: str = ".") -> List[Dict[str, Any]]:
    """
    List all productions in a directory.

    Args:
        directory: Directory to search

    Returns:
        List of production info dictionaries
    """
    productions = []
    dir_path = Path(directory)

    # Look for production.yaml files
    for yaml_file in dir_path.rglob("production.yaml"):
        try:
            data = load_yaml(str(yaml_file))
            if "production" in data:
                meta = data["production"].get("meta", {})
            else:
                meta = data.get("meta", {})

            productions.append({
                "path": str(yaml_file),
                "title": meta.get("title", "Untitled"),
                "version": meta.get("version", "1.0.0"),
                "author": meta.get("author", ""),
                "description": meta.get("description", ""),
            })
        except Exception:
            continue

    return productions


def get_production_info(yaml_path: str) -> Dict[str, Any]:
    """
    Get production info without full loading.

    Args:
        yaml_path: Path to production YAML

    Returns:
        Dictionary with production info
    """
    data = load_yaml(yaml_path)

    if "production" in data:
        data = _flatten_production_data(data)

    meta = data.get("meta", {})
    characters = data.get("characters", {})
    locations = data.get("locations", {})
    shots = data.get("shots", [])
    outputs = data.get("outputs", [])

    return {
        "path": yaml_path,
        "title": meta.get("title", "Untitled"),
        "version": meta.get("version", "1.0.0"),
        "author": meta.get("author", ""),
        "description": meta.get("description", ""),
        "character_count": len(characters),
        "location_count": len(locations),
        "shot_count": len(shots),
        "output_format_count": len(outputs),
        "has_script": bool(data.get("script_path")),
    }


def estimate_production_time(config: ProductionConfig) -> Dict[str, Any]:
    """
    Estimate production execution time.

    Args:
        config: Production configuration

    Returns:
        Dictionary with time estimates
    """
    # Base time estimates (in seconds) per phase
    phase_times = {
        "validate": 5,
        "prepare": 30,
        "characters": 60 * len(config.characters),
        "locations": 120 * len(config.locations),
        "shots": 0,  # Calculated below
        "post_process": 10 * len(config.shots),
        "export": 30 * len(config.outputs),
        "finalize": 60,
    }

    # Estimate shot rendering time
    # Based on render settings and shot count
    samples_factor = config.render_settings.samples / 64.0
    resolution_factor = (config.render_settings.resolution_x * config.render_settings.resolution_y) / (1920 * 1080)

    # Base: 60 seconds per shot for production quality
    base_shot_time = 60 * samples_factor * resolution_factor
    shot_count = config.get_shot_count()
    phase_times["shots"] = base_shot_time * shot_count

    total_time = sum(phase_times.values())

    return {
        "total_seconds": total_time,
        "total_minutes": total_time / 60,
        "total_hours": total_time / 3600,
        "phase_times": phase_times,
        "shot_count": shot_count,
        "character_count": len(config.characters),
        "location_count": len(config.locations),
        "output_count": len(config.outputs),
    }
