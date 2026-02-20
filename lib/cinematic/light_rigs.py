"""
Light Rigs Module

Provides pre-configured lighting rig presets and positioning utilities
for cinematic product visualization.

Light rigs are collections of lights positioned relative to a subject
to achieve specific lighting effects. Common rigs include:
- Three-point lighting (soft and hard variants)
- Product hero lighting
- Studio high-key and low-key setups
- Control surface specific rigs

Usage:
    from lib.cinematic.light_rigs import (
        create_light_rig,
        create_three_point_soft,
        create_product_hero,
        position_key_light,
        position_fill_light,
        position_back_light,
    )

    # Create three-point soft lighting
    lights = create_three_point_soft((0, 0, 0.5))

    # Create rig from preset
    rig = create_light_rig("product_hero", (0, 0, 0))
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
import math

from .types import LightConfig, Transform3D, LightRigConfig
from .preset_loader import get_lighting_rig_preset

# Guarded bpy import
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False


# Default rig parameters
DEFAULT_KEY_ANGLE = 45.0  # degrees from front
DEFAULT_KEY_ELEVATION = 30.0  # degrees from horizontal
DEFAULT_KEY_DISTANCE = 1.5  # meters from subject
DEFAULT_FILL_RATIO = 0.4  # fill:key intensity ratio
DEFAULT_BACK_ELEVATION = 45.0  # degrees from horizontal


def position_key_light(
    base_config: LightConfig,
    subject_position: Tuple[float, float, float],
    angle: float = DEFAULT_KEY_ANGLE,
    elevation: float = DEFAULT_KEY_ELEVATION,
    distance: float = DEFAULT_KEY_DISTANCE
) -> LightConfig:
    """
    Position key light relative to subject.

    The key light is the primary light source that defines the main
    illumination direction and shadow pattern.

    Args:
        base_config: Base LightConfig to modify
        subject_position: World position of subject (x, y, z)
        angle: Horizontal angle in degrees (0 = front, positive = camera left)
        elevation: Vertical angle in degrees from horizontal
        distance: Distance from subject in meters

    Returns:
        Modified LightConfig with updated position and rotation
    """
    # Convert angles to radians
    angle_rad = math.radians(angle)
    elevation_rad = math.radians(elevation)

    # Calculate position in camera space
    # X = right, Y = away from camera, Z = up
    x = subject_position[0] + distance * math.sin(angle_rad)
    y = subject_position[1] - distance * math.cos(angle_rad)
    z = subject_position[2] + distance * math.sin(elevation_rad)

    # Calculate rotation to point at subject
    dx = subject_position[0] - x
    dy = subject_position[1] - y
    dz = subject_position[2] - z

    # Calculate rotation angles (pointing down and towards subject)
    horizontal_angle = math.degrees(math.atan2(dx, -dy))
    vertical_angle = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))

    rotation = (vertical_angle + 90, 0.0, horizontal_angle)

    # Create new config with updated transform
    return LightConfig(
        name=base_config.name,
        light_type=base_config.light_type,
        intensity=base_config.intensity,
        color=base_config.color,
        transform=Transform3D(
            position=(x, y, z),
            rotation=rotation,
            scale=base_config.transform.scale
        ),
        shape=base_config.shape,
        size=base_config.size,
        size_y=base_config.size_y,
        spread=base_config.spread,
        spot_size=base_config.spot_size,
        spot_blend=base_config.spot_blend,
        shadow_soft_size=base_config.shadow_soft_size,
        use_shadow=base_config.use_shadow,
        use_temperature=base_config.use_temperature,
        temperature=base_config.temperature
    )


def position_fill_light(
    base_config: LightConfig,
    key_config: LightConfig,
    ratio: float = DEFAULT_FILL_RATIO
) -> LightConfig:
    """
    Position fill light based on key light position.

    The fill light is positioned opposite the key light to fill in
    shadows. Intensity is typically a fraction of the key light.

    Args:
        base_config: Base LightConfig to modify
        key_config: Key light configuration (for positioning reference)
        ratio: Fill:key intensity ratio (0.4 = fill is 40% of key)

    Returns:
        Modified LightConfig with updated position, rotation, and intensity
    """
    # Get key light position
    key_pos = key_config.transform.position

    # Fill is typically opposite key on horizontal plane
    # Calculate angle from origin to key, then mirror it
    dx = key_pos[0]
    dy = key_pos[1]

    key_angle = math.atan2(dx, -dy)
    fill_angle = key_angle + math.pi  # Opposite side

    # Use similar distance but slightly further back
    key_distance = math.sqrt(dx*dx + dy*dy)
    fill_distance = key_distance * 1.3

    # Lower elevation for fill
    key_z = key_pos[2]
    fill_z = key_z * 0.5

    # Calculate new position (assuming subject at origin for simplicity)
    x = fill_distance * math.sin(fill_angle)
    y = -fill_distance * math.cos(fill_angle)
    z = fill_z

    # Calculate rotation to point at origin
    horizontal_angle = math.degrees(math.atan2(x, -y))
    vertical_angle = math.degrees(math.atan2(z, math.sqrt(x*x + y*y)))

    rotation = (vertical_angle + 90, 0.0, horizontal_angle)

    return LightConfig(
        name=base_config.name,
        light_type=base_config.light_type,
        intensity=key_config.intensity * ratio,
        color=base_config.color,
        transform=Transform3D(
            position=(x, y, z),
            rotation=rotation,
            scale=base_config.transform.scale
        ),
        shape=base_config.shape,
        size=base_config.size * 1.5,  # Larger for softer fill
        size_y=base_config.size_y * 1.5,
        spread=base_config.spread,
        spot_size=base_config.spot_size,
        spot_blend=base_config.spot_blend,
        shadow_soft_size=base_config.shadow_soft_size * 2,  # Softer shadows
        use_shadow=base_config.use_shadow,
        use_temperature=base_config.use_temperature,
        temperature=base_config.temperature
    )


def position_back_light(
    base_config: LightConfig,
    subject_position: Tuple[float, float, float],
    elevation: float = DEFAULT_BACK_ELEVATION
) -> LightConfig:
    """
    Position back/rim light for subject separation.

    The back light creates a rim of light around the subject to
    separate them from the background.

    Args:
        base_config: Base LightConfig to modify
        subject_position: World position of subject (x, y, z)
        elevation: Vertical angle in degrees from horizontal

    Returns:
        Modified LightConfig with updated position and rotation
    """
    # Back light is positioned behind subject, slightly elevated
    distance = 1.5
    angle = 160.0  # degrees from front (behind and to side)

    angle_rad = math.radians(angle)
    elevation_rad = math.radians(elevation)

    x = subject_position[0] + distance * math.sin(angle_rad)
    y = subject_position[1] - distance * math.cos(angle_rad)
    z = subject_position[2] + distance * math.sin(elevation_rad)

    # Point towards subject
    dx = subject_position[0] - x
    dy = subject_position[1] - y
    dz = subject_position[2] - z

    horizontal_angle = math.degrees(math.atan2(dx, -dy))
    vertical_angle = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))

    rotation = (vertical_angle + 90, 0.0, horizontal_angle)

    return LightConfig(
        name=base_config.name,
        light_type=base_config.light_type,
        intensity=base_config.intensity,
        color=base_config.color,
        transform=Transform3D(
            position=(x, y, z),
            rotation=rotation,
            scale=base_config.transform.scale
        ),
        shape=base_config.shape,
        size=base_config.size,
        size_y=base_config.size_y,
        spread=base_config.spread,
        spot_size=base_config.spot_size,
        spot_blend=base_config.spot_blend,
        shadow_soft_size=base_config.shadow_soft_size,
        use_shadow=base_config.use_shadow,
        use_temperature=base_config.use_temperature,
        temperature=base_config.temperature
    )


def create_three_point_soft(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    key_intensity: float = 1000.0
) -> List[LightConfig]:
    """
    Create soft three-point lighting configuration.

    Classic 3-point lighting with soft shadows:
    - Key light: Primary illumination at 45 degrees
    - Fill light: Shadow fill at -45 degrees (40% key)
    - Rim light: Separation from background at 160 degrees

    Args:
        subject_position: Center position for lighting rig
        key_intensity: Intensity of key light in watts

    Returns:
        List of LightConfig objects for key, fill, and rim lights
    """
    # Key light - main illumination
    key_config = position_key_light(
        LightConfig(
            name="key_light",
            light_type="area",
            intensity=key_intensity,
            shape="RECTANGLE",
            size=2.0,
            size_y=1.0,
            shadow_soft_size=0.5
        ),
        subject_position,
        angle=45.0,
        elevation=30.0,
        distance=1.5
    )

    # Fill light - shadow fill
    fill_config = position_fill_light(
        LightConfig(
            name="fill_light",
            light_type="area",
            intensity=400.0,
            shape="RECTANGLE",
            size=3.0,
            size_y=2.0,
            shadow_soft_size=0.8
        ),
        key_config,
        ratio=0.4
    )

    # Rim light - separation
    rim_config = position_back_light(
        LightConfig(
            name="rim_light",
            light_type="area",
            intensity=700.0,
            shape="RECTANGLE",
            size=1.5,
            size_y=1.0,
            shadow_soft_size=0.3
        ),
        subject_position,
        elevation=45.0
    )

    return [key_config, fill_config, rim_config]


def create_three_point_hard(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    key_intensity: float = 1500.0
) -> List[LightConfig]:
    """
    Create hard three-point lighting configuration.

    Dramatic 3-point lighting with hard shadows:
    - Key light: Harsh main light at 45 degrees
    - Fill light: Minimal fill at -45 degrees (20% key)
    - Rim light: Strong separation at 160 degrees

    Args:
        subject_position: Center position for lighting rig
        key_intensity: Intensity of key light in watts

    Returns:
        List of LightConfig objects for key, fill, and rim lights
    """
    # Key light - harsh illumination
    key_config = position_key_light(
        LightConfig(
            name="key_light",
            light_type="spot",
            intensity=key_intensity,
            spot_size=0.524,  # 30 degrees
            spot_blend=0.1,
            shadow_soft_size=0.1
        ),
        subject_position,
        angle=45.0,
        elevation=45.0,
        distance=1.2
    )

    # Fill light - minimal
    fill_config = position_fill_light(
        LightConfig(
            name="fill_light",
            light_type="area",
            intensity=300.0,
            shape="RECTANGLE",
            size=2.0,
            size_y=1.0,
            shadow_soft_size=0.3
        ),
        key_config,
        ratio=0.2
    )

    # Rim light - strong
    rim_config = position_back_light(
        LightConfig(
            name="rim_light",
            light_type="spot",
            intensity=1000.0,
            spot_size=0.349,  # 20 degrees
            spot_blend=0.2,
            shadow_soft_size=0.1
        ),
        subject_position,
        elevation=60.0
    )

    return [key_config, fill_config, rim_config]


def create_product_hero(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1500.0
) -> List[LightConfig]:
    """
    Create product hero lighting configuration.

    Clean product photography with:
    - Overhead softbox: Primary illumination from above
    - Side fill cards: Subtle fill for shape definition
    - Optional rim for edge definition

    Args:
        subject_position: Center position for product
        intensity: Primary light intensity in watts

    Returns:
        List of LightConfig objects for product hero lighting
    """
    # Overhead softbox - main light
    overhead_config = LightConfig(
        name="overhead_softbox",
        light_type="area",
        intensity=intensity,
        shape="RECTANGLE",
        size=2.0,
        size_y=2.0,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1],
                subject_position[2] + 2.0
            ),
            rotation=(-90, 0, 0)  # Pointing straight down
        ),
        shadow_soft_size=0.8
    )

    # Left fill card
    left_fill_config = LightConfig(
        name="fill_card_left",
        light_type="area",
        intensity=200.0,
        shape="RECTANGLE",
        size=0.5,
        size_y=1.0,
        transform=Transform3D(
            position=(
                subject_position[0] - 1.0,
                subject_position[1],
                subject_position[2] + 0.5
            ),
            rotation=(0, 60, 0)  # Angled towards subject
        ),
        shadow_soft_size=1.0
    )

    # Right fill card
    right_fill_config = LightConfig(
        name="fill_card_right",
        light_type="area",
        intensity=200.0,
        shape="RECTANGLE",
        size=0.5,
        size_y=1.0,
        transform=Transform3D(
            position=(
                subject_position[0] + 1.0,
                subject_position[1],
                subject_position[2] + 0.5
            ),
            rotation=(0, -60, 0)  # Angled towards subject
        ),
        shadow_soft_size=1.0
    )

    return [overhead_config, left_fill_config, right_fill_config]


def create_studio_high_key(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 800.0
) -> List[LightConfig]:
    """
    Create high-key studio lighting configuration.

    Bright, minimal shadows lighting for clean commercial look:
    - Large overhead fill
    - Side fills for wraparound light
    - Generally even illumination

    Args:
        subject_position: Center position for subject
        intensity: Base intensity in watts

    Returns:
        List of LightConfig objects for high-key lighting
    """
    # Large overhead fill
    overhead_config = LightConfig(
        name="overhead_fill",
        light_type="area",
        intensity=intensity,
        shape="RECTANGLE",
        size=5.0,
        size_y=5.0,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1],
                subject_position[2] + 3.0
            ),
            rotation=(-90, 0, 0)
        ),
        shadow_soft_size=1.0
    )

    # Front fill
    front_config = LightConfig(
        name="front_fill",
        light_type="area",
        intensity=intensity * 0.6,
        shape="RECTANGLE",
        size=3.0,
        size_y=2.0,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 2.0,
                subject_position[2] + 1.0
            ),
            rotation=(-30, 0, 0)
        ),
        shadow_soft_size=1.0
    )

    # Side fills
    left_config = LightConfig(
        name="left_fill",
        light_type="area",
        intensity=intensity * 0.5,
        shape="RECTANGLE",
        size=2.0,
        size_y=3.0,
        transform=Transform3D(
            position=(
                subject_position[0] - 2.0,
                subject_position[1],
                subject_position[2] + 0.5
            ),
            rotation=(0, 45, 0)
        ),
        shadow_soft_size=1.0
    )

    right_config = LightConfig(
        name="right_fill",
        light_type="area",
        intensity=intensity * 0.5,
        shape="RECTANGLE",
        size=2.0,
        size_y=3.0,
        transform=Transform3D(
            position=(
                subject_position[0] + 2.0,
                subject_position[1],
                subject_position[2] + 0.5
            ),
            rotation=(0, -45, 0)
        ),
        shadow_soft_size=1.0
    )

    return [overhead_config, front_config, left_config, right_config]


def create_studio_low_key(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 2000.0
) -> List[LightConfig]:
    """
    Create low-key studio lighting configuration.

    Dark, dramatic, selective lighting for mood:
    - Single narrow key
    - Minimal fill
    - Strong contrast

    Args:
        subject_position: Center position for subject
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for low-key lighting
    """
    # Narrow key light
    key_config = position_key_light(
        LightConfig(
            name="key_narrow",
            light_type="spot",
            intensity=intensity,
            spot_size=0.262,  # 15 degrees - narrow
            spot_blend=0.1,
            shadow_soft_size=0.1
        ),
        subject_position,
        angle=30.0,
        elevation=45.0,
        distance=0.8
    )

    # Minimal fill (optional)
    fill_config = LightConfig(
        name="fill_minimal",
        light_type="area",
        intensity=100.0,
        shape="RECTANGLE",
        size=1.0,
        size_y=1.0,
        transform=Transform3D(
            position=(
                subject_position[0] - 1.5,
                subject_position[1] - 1.0,
                subject_position[2] + 0.3
            ),
            rotation=(-20, 30, 0)
        ),
        shadow_soft_size=0.5
    )

    return [key_config, fill_config]


def create_light_rig(
    preset_name: str,
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity_scale: float = 1.0
) -> List[LightConfig]:
    """
    Create lighting rig from preset name.

    Maps preset names to their creator functions for easy access.

    Args:
        preset_name: Name of preset (three_point_soft, three_point_hard,
                     product_hero, studio_high_key, studio_low_key)
        subject_position: Center position for lighting rig
        intensity_scale: Multiplier for all light intensities

    Returns:
        List of LightConfig objects for the rig

    Raises:
        ValueError: If preset name not recognized
    """
    preset_map = {
        "three_point_soft": create_three_point_soft,
        "three_point_hard": create_three_point_hard,
        "product_hero": create_product_hero,
        "studio_high_key": create_studio_high_key,
        "studio_low_key": create_studio_low_key,
    }

    if preset_name not in preset_map:
        raise ValueError(
            f"Unknown lighting rig preset: {preset_name}. "
            f"Available: {list(preset_map.keys())}"
        )

    creator = preset_map[preset_name]
    configs = creator(subject_position)

    # Apply intensity scale
    if intensity_scale != 1.0:
        scaled_configs = []
        for config in configs:
            scaled = LightConfig(
                name=config.name,
                light_type=config.light_type,
                intensity=config.intensity * intensity_scale,
                color=config.color,
                transform=config.transform,
                shape=config.shape,
                size=config.size,
                size_y=config.size_y,
                spread=config.spread,
                spot_size=config.spot_size,
                spot_blend=config.spot_blend,
                shadow_soft_size=config.shadow_soft_size,
                use_shadow=config.use_shadow,
                use_temperature=config.use_temperature,
                temperature=config.temperature
            )
            scaled_configs.append(scaled)
        return scaled_configs

    return configs


def list_light_rig_presets() -> List[str]:
    """
    List available light rig preset names.

    Returns:
        Sorted list of preset names
    """
    return sorted([
        "three_point_soft",
        "three_point_hard",
        "product_hero",
        "studio_high_key",
        "studio_low_key",
    ])
