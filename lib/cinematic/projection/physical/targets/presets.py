"""
Target preset loading utilities.

Provides functions to load and list target presets from YAML configuration files.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any

from .types import ProjectionTarget, ProjectionSurface, TargetType, SurfaceMaterial


# Default presets directory
PRESETS_DIR = Path(__file__).parent.parent / "configs/cinematic/projection/targets"


def load_target_preset(name: str) -> ProjectionTarget:
    """
    Load a target preset by name.

    Args:
        name: Name of the preset (e.g., "reading_room", "garage_door")

    Returns:
        ProjectionTarget instance

    Raises:
        FileNotFoundError: If preset file not found
        KeyError: If preset name not in file
    """
    preset_path = PRESETS_DIR / f"{name}.yaml"

    if not preset_path.exists():
        raise FileNotFoundError(f"Preset file not found: {preset_path}")

    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML required: pip install pyyaml")

    with open(preset_path) as f:
        data = yaml.safe_load(f)

    # Check if it preset has the specified name
    if 'name' in data:
        preset_name = data['name']
    elif 'name' in data:
        preset_name = data['name']
    else:
        # Check for surfaces with matching name
        for surface in data.get('surfaces', []):
            if surface.get('name') == name:
                preset_name = name
                break

    if preset_name != name:
        raise KeyError(f"Preset '{name}' not found in {preset_path}")

    return ProjectionTarget.from_dict(data)


def list_target_presets(preset_dir: Optional[str] = None) -> List[str]:
    """
    List available target presets.

    Args:
        preset_dir: Optional directory to search for presets

    Returns:
        List of preset names
    """
    search_dir = preset_dir or PRESETS_DIR

    presets = []
    for yaml_file in search_dir.glob("*.yaml"):
        try:
            import yaml
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
                name = data.get('name', data.get('target_name', 'unknown'))
                presets.append(name)
        except Exception:
            pass

    return sorted(presets)


def create_reading_room_target(
    upper_width: float = 2.5,
    upper_height: float = 0.2,
    lower_width: float = 2.5,
    lower_height: float = 0.2,
    desk_width: float = 2.0,
    desk_height: float = 0.5,
) -> ProjectionTarget:
    """Create the reading room target with cabinets and desk."""
    return ProjectionTarget(
        name="reading_room",
        description="Reading room with cabinets and desks",
        target_type=TargetType.MULTI_SURFACE,
        surfaces=[
            ProjectionSurface(
                name="upper_cabinet",
                surface_type=TargetType.PLANAR,
                position=(0, 0, 1.2),
                dimensions=(upper_width, upper_height),
                area_m2=upper_width * upper_height,
                material=SurfaceMaterial.WHITE_PAINT,
            ),
            ProjectionSurface(
                name="lower_cabinet",
                surface_type=TargetType.PLANAR,
                position=(0, 0, 0.3),
                dimensions=(lower_width, lower_height),
                area_m2=lower_width * lower_height,
                material=SurfaceMaterial.WHITE_PAINT,
            ),
            ProjectionSurface(
                name="desk_surface",
                surface_type=TargetType.PLANAR,
                position=(0, 0.4, 0.6),
                dimensions=(desk_width, desk_height),
                area_m2=desk_width * desk_height,
                material=SurfaceMaterial.WOOD,
            ),
        ],
        width_m=upper_width,
        height_m=1.8,  # Upper + lower combined
        depth_m=0.6,
        recommended_calibration="four_point_dlt",
        preset_measurements={
            "cabinet_depth": 0.3,
            "desk_height": 0.75,
        },
    )


def create_garage_door_target(
    width: float = 4.88,
    height: float = 2.13,
) -> ProjectionTarget:
    """Create a standard garage door target (7ft x 16ft)."""
    return ProjectionTarget(
        name="garage_door",
        description=f"Standard garage door ({width}m x {height}m)",
        target_type=TargetType.PLANAR,
        surfaces=[
            ProjectionSurface(
                name="door_panel",
                surface_type=TargetType.PLANAR,
                position=(0, 0, height / 2),
                dimensions=(width, height),
                area_m2=width * height,
                material=SurfaceMaterial.WHITE_PAINT,
            ),
        ],
        width_m=width,
        height_m=height,
        recommended_calibration="three_point",
        preset_measurements={
            "frame_width": 0.05,
            "panel_gap": 0.02,
            "handle_height": 1.0,
        },
    )


def create_building_facade_target(
    width: float = 20.0,
    height: float = 15.0,
) -> ProjectionTarget:
    """Create a building facade target for large-scale projection."""
    return ProjectionTarget(
        name="building_facade",
        description=f"Building facade ({width}m x {height}m)",
        target_type=TargetType.MULTI_SURFACE,
        surfaces=[
            ProjectionSurface(
                name="main_facade",
                surface_type=TargetType.PLANAR,
                position=(0, 0, height / 2),
                dimensions=(width, height),
                area_m2=width * height,
                material=SurfaceMaterial.GRAY_PAINT,
            ),
            ProjectionSurface(
                name="window_row_1",
                surface_type=TargetType.PLANAR,
                position=(0, 0.1, height * 0.6),
                dimensions=(width * 0.9, height * 0.15),
                area_m2=width * 0.9 * height * 0.15,
                material=SurfaceMaterial.GLASS,
            ),
            ProjectionSurface(
                name="window_row_2",
                surface_type=TargetType.PLANAR,
                position=(0, 0.1, height * 0.3),
                dimensions=(width * 0.9, height * 0.15),
                area_m2=width * 0.9 * height * 0.15,
                material=SurfaceMaterial.GLASS,
            ),
        ],
        width_m=width,
        height_m=height,
        depth_m=0.5,
        recommended_calibration="four_point_dlt",
        preset_measurements={
            "window_width": 1.5,
            "window_height": 2.0,
            "window_spacing": 2.5,
            "floor_height": 3.5,
        },
    )
