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
        preset_name: Name of preset (see list_light_rig_presets() for options)
        subject_position: Center position for lighting rig
        intensity_scale: Multiplier for all light intensities

    Returns:
        List of LightConfig objects for the rig

    Raises:
        ValueError: If preset name not recognized
    """
    preset_map = {
        # Studio/General
        "three_point_soft": create_three_point_soft,
        "three_point_hard": create_three_point_hard,
        "product_hero": create_product_hero,
        "studio_high_key": create_studio_high_key,
        "studio_low_key": create_studio_low_key,
        # Portrait Patterns
        "portrait_rembrandt": create_portrait_rembrandt,
        "portrait_loop": create_portrait_loop,
        "portrait_butterfly": create_portrait_butterfly,
        "portrait_split": create_portrait_split,
        "portrait_broad": create_portrait_broad,
        "portrait_short": create_portrait_short,
        "portrait_clamshell": create_portrait_clamshell,
        "portrait_high_key": create_portrait_high_key,
        "portrait_low_key": create_portrait_low_key,
        "portrait_rim": create_portrait_rim,
        "portrait_flat": create_portrait_flat,
        "portrait_dramatic": create_portrait_dramatic,
        # Product Categories
        "product_electronics": create_product_electronics,
        "product_cosmetics": create_product_cosmetics,
        "product_food": create_product_food,
        "product_jewelry": create_product_jewelry,
        "product_fashion": create_product_fashion,
        "product_automotive": create_product_automotive,
        "product_furniture": create_product_furniture,
        "product_industrial": create_product_industrial,
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


# =============================================================================
# PORTRAIT LIGHTING PATTERNS (12 Classic Patterns)
# =============================================================================

def create_portrait_rembrandt(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1000.0
) -> List[LightConfig]:
    """
    Create Rembrandt lighting configuration.

    Classic portrait lighting characterized by a triangle of light on the
    shadow side of the face. Named after the Dutch painter.

    Key features:
    - Key light at 45 degrees, elevated 45 degrees
    - Small triangle of light on shadow cheek
    - Dramatic but flattering

    Args:
        subject_position: Position of subject's face (x, y, z)
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for Rembrandt lighting
    """
    # Key light - creates the triangle
    key_config = position_key_light(
        LightConfig(
            name="rembrandt_key",
            light_type="area",
            intensity=intensity,
            shape="RECTANGLE",
            size=1.5,
            size_y=1.0,
            shadow_soft_size=0.3
        ),
        subject_position,
        angle=45.0,
        elevation=45.0,
        distance=1.2
    )

    # Minimal fill - preserves shadows
    fill_config = position_fill_light(
        LightConfig(
            name="rembrandt_fill",
            light_type="area",
            intensity=intensity * 0.2,
            shape="RECTANGLE",
            size=2.0,
            size_y=2.0,
            shadow_soft_size=0.8
        ),
        key_config,
        ratio=0.2
    )

    # Hair light for separation
    hair_config = LightConfig(
        name="rembrandt_hair",
        light_type="spot",
        intensity=intensity * 0.4,
        spot_size=0.349,  # 20 degrees
        spot_blend=0.3,
        transform=Transform3D(
            position=(
                subject_position[0] - 0.5,
                subject_position[1] - 1.0,
                subject_position[2] + 1.5
            ),
            rotation=(-60, 0, -150)
        ),
        shadow_soft_size=0.2
    )

    return [key_config, fill_config, hair_config]


def create_portrait_loop(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1000.0
) -> List[LightConfig]:
    """
    Create Loop lighting configuration.

    A slight variation of Rembrandt with a small shadow of the nose
    that "loops" down towards the corner of the mouth.

    Key features:
    - Key light slightly lower and more frontal than Rembrandt
    - Small shadow loop from nose
    - Flattering, less dramatic than Rembrandt

    Args:
        subject_position: Position of subject's face (x, y, z)
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for Loop lighting
    """
    # Key light - more frontal than Rembrandt
    key_config = position_key_light(
        LightConfig(
            name="loop_key",
            light_type="area",
            intensity=intensity,
            shape="RECTANGLE",
            size=1.5,
            size_y=1.0,
            shadow_soft_size=0.4
        ),
        subject_position,
        angle=30.0,
        elevation=30.0,
        distance=1.3
    )

    # Fill light
    fill_config = position_fill_light(
        LightConfig(
            name="loop_fill",
            light_type="area",
            intensity=intensity * 0.3,
            shape="RECTANGLE",
            size=2.5,
            size_y=2.0,
            shadow_soft_size=0.6
        ),
        key_config,
        ratio=0.3
    )

    return [key_config, fill_config]


def create_portrait_butterfly(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1200.0
) -> List[LightConfig]:
    """
    Create Butterfly (Paramount) lighting configuration.

    Classic glamour lighting with the key light directly in front and
    above, creating a butterfly-shaped shadow under the nose.

    Key features:
    - Key light directly above camera
    - Butterfly shadow under nose
    - Glamorous, beauty lighting

    Args:
        subject_position: Position of subject's face (x, y, z)
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for Butterfly lighting
    """
    # Key light - directly above and in front
    key_config = LightConfig(
        name="butterfly_key",
        light_type="area",
        intensity=intensity,
        shape="RECTANGLE",
        size=2.0,
        size_y=1.5,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 1.0,
                subject_position[2] + 1.2
            ),
            rotation=(-45, 0, 0)
        ),
        shadow_soft_size=0.5
    )

    # Fill from below (reflector simulation)
    fill_config = LightConfig(
        name="butterfly_fill",
        light_type="area",
        intensity=intensity * 0.25,
        shape="RECTANGLE",
        size=2.0,
        size_y=1.5,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 0.8,
                subject_position[2] - 0.3
            ),
            rotation=(45, 0, 0)
        ),
        shadow_soft_size=0.8
    )

    # Hair light
    hair_config = LightConfig(
        name="butterfly_hair",
        light_type="spot",
        intensity=intensity * 0.3,
        spot_size=0.436,  # 25 degrees
        spot_blend=0.2,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 0.8,
                subject_position[2] + 1.8
            ),
            rotation=(-70, 0, 0)
        ),
        shadow_soft_size=0.3
    )

    return [key_config, fill_config, hair_config]


def create_portrait_split(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1000.0
) -> List[LightConfig]:
    """
    Create Split lighting configuration.

    Dramatic lighting that splits the face in half - one side lit,
    one side in shadow. Very moody and artistic.

    Key features:
    - Key light at 90 degrees (side)
    - Half the face in shadow
    - Dramatic, artistic effect

    Args:
        subject_position: Position of subject's face (x, y, z)
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for Split lighting
    """
    # Key light - directly from side
    key_config = position_key_light(
        LightConfig(
            name="split_key",
            light_type="area",
            intensity=intensity,
            shape="RECTANGLE",
            size=1.0,
            size_y=1.5,
            shadow_soft_size=0.2
        ),
        subject_position,
        angle=90.0,
        elevation=0.0,
        distance=1.0
    )

    # No fill - pure split
    return [key_config]


def create_portrait_broad(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1000.0
) -> List[LightConfig]:
    """
    Create Broad lighting configuration.

    Lighting where the key illuminates the side of the face turned
    towards the camera. Makes faces appear wider.

    Key features:
    - Key lights the broad side (towards camera)
    - Fill on the far side
    - Makes face appear wider

    Args:
        subject_position: Position of subject's face (x, y, z)
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for Broad lighting
    """
    # Key light - on camera side
    key_config = position_key_light(
        LightConfig(
            name="broad_key",
            light_type="area",
            intensity=intensity,
            shape="RECTANGLE",
            size=1.5,
            size_y=1.0,
            shadow_soft_size=0.4
        ),
        subject_position,
        angle=-45.0,  # Camera left (broad side)
        elevation=35.0,
        distance=1.3
    )

    # Fill on short side
    fill_config = position_fill_light(
        LightConfig(
            name="broad_fill",
            light_type="area",
            intensity=intensity * 0.35,
            shape="RECTANGLE",
            size=2.0,
            size_y=1.5,
            shadow_soft_size=0.6
        ),
        key_config,
        ratio=0.35
    )

    return [key_config, fill_config]


def create_portrait_short(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1000.0
) -> List[LightConfig]:
    """
    Create Short lighting configuration.

    Lighting where the key illuminates the side of the face turned
    away from the camera. More slimming and dimensional.

    Key features:
    - Key lights the short side (away from camera)
    - Shadow towards camera
    - Slimming effect, more depth

    Args:
        subject_position: Position of subject's face (x, y, z)
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for Short lighting
    """
    # Key light - on far side
    key_config = position_key_light(
        LightConfig(
            name="short_key",
            light_type="area",
            intensity=intensity,
            shape="RECTANGLE",
            size=1.5,
            size_y=1.0,
            shadow_soft_size=0.4
        ),
        subject_position,
        angle=45.0,  # Camera right (short side)
        elevation=35.0,
        distance=1.3
    )

    # Fill on broad side (towards camera)
    fill_config = position_fill_light(
        LightConfig(
            name="short_fill",
            light_type="area",
            intensity=intensity * 0.25,
            shape="RECTANGLE",
            size=2.5,
            size_y=2.0,
            shadow_soft_size=0.7
        ),
        key_config,
        ratio=0.25
    )

    return [key_config, fill_config]


def create_portrait_clamshell(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1000.0
) -> List[LightConfig]:
    """
    Create Clamshell lighting configuration.

    Beauty lighting with two lights - one above, one below -
    creating even, shadowless illumination. Perfect for beauty
    and fashion photography.

    Key features:
    - Key light above camera
    - Fill/reflector below camera
    - Even, flattering beauty light

    Args:
        subject_position: Position of subject's face (x, y, z)
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for Clamshell lighting
    """
    # Top light - softbox above
    top_config = LightConfig(
        name="clamshell_top",
        light_type="area",
        intensity=intensity,
        shape="RECTANGLE",
        size=2.0,
        size_y=1.5,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 0.8,
                subject_position[2] + 0.8
            ),
            rotation=(-35, 0, 0)
        ),
        shadow_soft_size=0.6
    )

    # Bottom fill - reflector simulation
    bottom_config = LightConfig(
        name="clamshell_bottom",
        light_type="area",
        intensity=intensity * 0.5,
        shape="RECTANGLE",
        size=2.0,
        size_y=1.5,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 0.6,
                subject_position[2] - 0.2
            ),
            rotation=(40, 0, 0)
        ),
        shadow_soft_size=0.8
    )

    return [top_config, bottom_config]


def create_portrait_high_key(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 800.0
) -> List[LightConfig]:
    """
    Create High Key portrait lighting configuration.

    Bright, cheerful lighting with minimal shadows. Uses multiple
    lights for even illumination.

    Key features:
    - Multiple overlapping lights
    - Minimal shadows
    - Bright, clean, cheerful look

    Args:
        subject_position: Position of subject's face (x, y, z)
        intensity: Base intensity in watts

    Returns:
        List of LightConfig objects for High Key lighting
    """
    # Main front light
    front_config = LightConfig(
        name="highkey_front",
        light_type="area",
        intensity=intensity,
        shape="RECTANGLE",
        size=3.0,
        size_y=2.5,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 1.5,
                subject_position[2] + 0.5
            ),
            rotation=(-20, 0, 0)
        ),
        shadow_soft_size=0.8
    )

    # Side lights for wrap
    left_config = LightConfig(
        name="highkey_left",
        light_type="area",
        intensity=intensity * 0.6,
        shape="RECTANGLE",
        size=2.0,
        size_y=2.0,
        transform=Transform3D(
            position=(
                subject_position[0] - 1.2,
                subject_position[1] - 0.5,
                subject_position[2] + 0.3
            ),
            rotation=(0, 45, 0)
        ),
        shadow_soft_size=0.7
    )

    right_config = LightConfig(
        name="highkey_right",
        light_type="area",
        intensity=intensity * 0.6,
        shape="RECTANGLE",
        size=2.0,
        size_y=2.0,
        transform=Transform3D(
            position=(
                subject_position[0] + 1.2,
                subject_position[1] - 0.5,
                subject_position[2] + 0.3
            ),
            rotation=(0, -45, 0)
        ),
        shadow_soft_size=0.7
    )

    # Top fill
    top_config = LightConfig(
        name="highkey_top",
        light_type="area",
        intensity=intensity * 0.5,
        shape="RECTANGLE",
        size=3.0,
        size_y=3.0,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1],
                subject_position[2] + 2.0
            ),
            rotation=(-90, 0, 0)
        ),
        shadow_soft_size=1.0
    )

    return [front_config, left_config, right_config, top_config]


def create_portrait_low_key(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1500.0
) -> List[LightConfig]:
    """
    Create Low Key portrait lighting configuration.

    Dark, dramatic lighting with selective illumination. Creates
    mood and mystery.

    Key features:
    - Single key light
    - Dark shadows
    - Dramatic, moody

    Args:
        subject_position: Position of subject's face (x, y, z)
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for Low Key lighting
    """
    # Single harsh key
    key_config = position_key_light(
        LightConfig(
            name="lowkey_key",
            light_type="spot",
            intensity=intensity,
            spot_size=0.349,  # 20 degrees
            spot_blend=0.1,
            shadow_soft_size=0.1
        ),
        subject_position,
        angle=60.0,
        elevation=40.0,
        distance=1.0
    )

    return [key_config]


def create_portrait_rim(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1200.0
) -> List[LightConfig]:
    """
    Create Rim (Kicker) lighting configuration.

    Lighting that creates a bright edge/rim around the subject,
    separating them from the background.

    Key features:
    - Key from behind/beside subject
    - Bright edge/rim effect
    - Separation from background

    Args:
        subject_position: Position of subject's face (x, y, z)
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for Rim lighting
    """
    # Front fill - minimal
    fill_config = LightConfig(
        name="rim_fill",
        light_type="area",
        intensity=intensity * 0.15,
        shape="RECTANGLE",
        size=2.0,
        size_y=1.5,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 1.5,
                subject_position[2] + 0.3
            ),
            rotation=(-15, 0, 0)
        ),
        shadow_soft_size=0.6
    )

    # Left rim
    left_rim = position_back_light(
        LightConfig(
            name="rim_left",
            light_type="area",
            intensity=intensity,
            shape="RECTANGLE",
            size=0.5,
            size_y=1.5,
            shadow_soft_size=0.2
        ),
        subject_position,
        elevation=10.0
    )

    # Right rim
    right_rim = LightConfig(
        name="rim_right",
        light_type="area",
        intensity=intensity,
        shape="RECTANGLE",
        size=0.5,
        size_y=1.5,
        transform=Transform3D(
            position=(
                subject_position[0] + 1.2,
                subject_position[1] + 0.3,
                subject_position[2] + 0.2
            ),
            rotation=(-10, -70, 0)
        ),
        shadow_soft_size=0.2
    )

    return [fill_config, left_rim, right_rim]


def create_portrait_flat(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1000.0
) -> List[LightConfig]:
    """
    Create Flat lighting configuration.

    Even, shadowless lighting from directly in front. Simple and
    straightforward, often used for ID photos.

    Key features:
    - Light directly from camera direction
    - Minimal shadows
    - Simple, even illumination

    Args:
        subject_position: Position of subject's face (x, y, z)
        intensity: Light intensity in watts

    Returns:
        List of LightConfig objects for Flat lighting
    """
    # Front light - on-camera flash simulation
    front_config = LightConfig(
        name="flat_front",
        light_type="area",
        intensity=intensity,
        shape="RECTANGLE",
        size=2.5,
        size_y=2.0,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 1.5,
                subject_position[2] + 0.5
            ),
            rotation=(-15, 0, 0)
        ),
        shadow_soft_size=0.5
    )

    # Fill from sides for evenness
    left_fill = LightConfig(
        name="flat_left",
        light_type="area",
        intensity=intensity * 0.3,
        shape="RECTANGLE",
        size=1.5,
        size_y=1.5,
        transform=Transform3D(
            position=(
                subject_position[0] - 1.0,
                subject_position[1] - 0.8,
                subject_position[2] + 0.3
            ),
            rotation=(0, 30, 0)
        ),
        shadow_soft_size=0.7
    )

    right_fill = LightConfig(
        name="flat_right",
        light_type="area",
        intensity=intensity * 0.3,
        shape="RECTANGLE",
        size=1.5,
        size_y=1.5,
        transform=Transform3D(
            position=(
                subject_position[0] + 1.0,
                subject_position[1] - 0.8,
                subject_position[2] + 0.3
            ),
            rotation=(0, -30, 0)
        ),
        shadow_soft_size=0.7
    )

    return [front_config, left_fill, right_fill]


def create_portrait_dramatic(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 2000.0
) -> List[LightConfig]:
    """
    Create Dramatic lighting configuration.

    High contrast, theatrical lighting for artistic portraits.
    Uses hard light with minimal fill.

    Key features:
    - Hard, directional key
    - Deep shadows
    - Theatrical, cinematic feel

    Args:
        subject_position: Position of subject's face (x, y, z)
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for Dramatic lighting
    """
    # Hard key light
    key_config = position_key_light(
        LightConfig(
            name="dramatic_key",
            light_type="spot",
            intensity=intensity,
            spot_size=0.262,  # 15 degrees - hard
            spot_blend=0.05,
            shadow_soft_size=0.05
        ),
        subject_position,
        angle=55.0,
        elevation=50.0,
        distance=1.2
    )

    # Very minimal fill
    fill_config = LightConfig(
        name="dramatic_fill",
        light_type="area",
        intensity=intensity * 0.08,
        shape="RECTANGLE",
        size=1.0,
        size_y=1.0,
        transform=Transform3D(
            position=(
                subject_position[0] - 1.5,
                subject_position[1] - 0.5,
                subject_position[2] + 0.2
            ),
            rotation=(-10, 20, 0)
        ),
        shadow_soft_size=0.5
    )

    # Accent rim
    rim_config = position_back_light(
        LightConfig(
            name="dramatic_rim",
            light_type="spot",
            intensity=intensity * 0.5,
            spot_size=0.174,  # 10 degrees
            spot_blend=0.1,
            shadow_soft_size=0.1
        ),
        subject_position,
        elevation=30.0
    )

    return [key_config, fill_config, rim_config]


# =============================================================================
# PRODUCT PHOTOGRAPHY PRESETS (8 Categories)
# =============================================================================

def create_product_electronics(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1500.0
) -> List[LightConfig]:
    """
    Create electronics product lighting configuration.

    Clean, modern lighting for tech products with reflective surfaces.
    Emphasizes design details and screen quality.

    Key features:
    - Soft overhead key
    - Gradient fill cards for reflections
    - Screen accent lighting

    Args:
        subject_position: Center position for product
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for electronics lighting
    """
    # Overhead softbox
    overhead = LightConfig(
        name="electronics_overhead",
        light_type="area",
        intensity=intensity,
        shape="RECTANGLE",
        size=2.5,
        size_y=2.0,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1],
                subject_position[2] + 2.5
            ),
            rotation=(-90, 0, 0)
        ),
        shadow_soft_size=0.7
    )

    # Front gradient fill
    front = LightConfig(
        name="electronics_front",
        light_type="area",
        intensity=intensity * 0.5,
        shape="RECTANGLE",
        size=2.0,
        size_y=1.5,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 2.0,
                subject_position[2] + 0.8
            ),
            rotation=(-25, 0, 0)
        ),
        shadow_soft_size=0.6
    )

    # Side accent for edge definition
    side = LightConfig(
        name="electronics_side",
        light_type="area",
        intensity=intensity * 0.4,
        shape="RECTANGLE",
        size=0.5,
        size_y=1.5,
        transform=Transform3D(
            position=(
                subject_position[0] - 1.5,
                subject_position[1] - 0.5,
                subject_position[2] + 0.5
            ),
            rotation=(0, 60, 0)
        ),
        shadow_soft_size=0.3
    )

    # Back rim for product edge
    back_rim = LightConfig(
        name="electronics_rim",
        light_type="area",
        intensity=intensity * 0.6,
        shape="RECTANGLE",
        size=0.3,
        size_y=1.2,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] + 1.5,
                subject_position[2] + 0.8
            ),
            rotation=(-30, 180, 0)
        ),
        shadow_soft_size=0.2
    )

    return [overhead, front, side, back_rim]


def create_product_cosmetics(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1200.0
) -> List[LightConfig]:
    """
    Create cosmetics product lighting configuration.

    Soft, glamorous lighting for beauty products. Emphasizes
    texture, gloss, and premium feel.

    Key features:
    - Very soft key light
    - Gradient reflections
    - Premium, luxurious feel

    Args:
        subject_position: Center position for product
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for cosmetics lighting
    """
    # Large soft key
    key = LightConfig(
        name="cosmetics_key",
        light_type="area",
        intensity=intensity,
        shape="RECTANGLE",
        size=3.0,
        size_y=2.5,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 2.0,
                subject_position[2] + 1.5
            ),
            rotation=(-40, 0, 0)
        ),
        shadow_soft_size=1.0
    )

    # Top fill for gradient
    top_fill = LightConfig(
        name="cosmetics_top",
        light_type="area",
        intensity=intensity * 0.6,
        shape="RECTANGLE",
        size=2.5,
        size_y=2.5,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1],
                subject_position[2] + 2.0
            ),
            rotation=(-90, 0, 0)
        ),
        shadow_soft_size=0.9
    )

    # Side cards for reflections
    left_card = LightConfig(
        name="cosmetics_left",
        light_type="area",
        intensity=intensity * 0.3,
        shape="RECTANGLE",
        size=1.0,
        size_y=2.0,
        transform=Transform3D(
            position=(
                subject_position[0] - 1.2,
                subject_position[1] - 0.3,
                subject_position[2] + 0.5
            ),
            rotation=(0, 45, 0)
        ),
        shadow_soft_size=0.7
    )

    right_card = LightConfig(
        name="cosmetics_right",
        light_type="area",
        intensity=intensity * 0.3,
        shape="RECTANGLE",
        size=1.0,
        size_y=2.0,
        transform=Transform3D(
            position=(
                subject_position[0] + 1.2,
                subject_position[1] - 0.3,
                subject_position[2] + 0.5
            ),
            rotation=(0, -45, 0)
        ),
        shadow_soft_size=0.7
    )

    return [key, top_fill, left_card, right_card]


def create_product_food(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1500.0
) -> List[LightConfig]:
    """
    Create food photography lighting configuration.

    Appetizing lighting that enhances food appeal. Uses warm tones
    and soft shadows for natural, fresh look.

    Key features:
    - Warm-toned key light
    - Soft fill for texture
    - Appetizing, fresh appearance

    Args:
        subject_position: Center position for food
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for food lighting
    """
    # Main key with warm tone
    key = position_key_light(
        LightConfig(
            name="food_key",
            light_type="area",
            intensity=intensity,
            shape="RECTANGLE",
            size=2.0,
            size_y=1.5,
            shadow_soft_size=0.6,
            use_temperature=True,
            temperature=4500  # Warm daylight
        ),
        subject_position,
        angle=50.0,
        elevation=45.0,
        distance=1.5
    )

    # Soft fill
    fill = position_fill_light(
        LightConfig(
            name="food_fill",
            light_type="area",
            intensity=intensity * 0.4,
            shape="RECTANGLE",
            size=3.0,
            size_y=2.0,
            shadow_soft_size=0.8,
            use_temperature=True,
            temperature=5000
        ),
        key,
        ratio=0.4
    )

    # Back light for steam/texture
    back = position_back_light(
        LightConfig(
            name="food_back",
            light_type="area",
            intensity=intensity * 0.5,
            shape="RECTANGLE",
            size=1.5,
            size_y=1.0,
            shadow_soft_size=0.5,
            use_temperature=True,
            temperature=4800
        ),
        subject_position,
        elevation=30.0
    )

    return [key, fill, back]


def create_product_jewelry(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 800.0
) -> List[LightConfig]:
    """
    Create jewelry product lighting configuration.

    Precise lighting for gemstones and precious metals. Uses
    multiple accent lights to create sparkle and brilliance.

    Key features:
    - Multiple small accent lights
    - Creates sparkle in gems
    - Precious metal reflections

    Args:
        subject_position: Center position for jewelry
        intensity: Base intensity in watts

    Returns:
        List of LightConfig objects for jewelry lighting
    """
    # Soft overhead fill
    overhead = LightConfig(
        name="jewelry_overhead",
        light_type="area",
        intensity=intensity,
        shape="RECTANGLE",
        size=1.5,
        size_y=1.5,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1],
                subject_position[2] + 1.5
            ),
            rotation=(-90, 0, 0)
        ),
        shadow_soft_size=0.5
    )

    # Front light tent simulation
    front = LightConfig(
        name="jewelry_front",
        light_type="area",
        intensity=intensity * 0.7,
        shape="RECTANGLE",
        size=1.0,
        size_y=1.0,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 1.0,
                subject_position[2] + 0.5
            ),
            rotation=(-30, 0, 0)
        ),
        shadow_soft_size=0.4
    )

    # Sparkle lights (small spots)
    sparkle_left = LightConfig(
        name="jewelry_sparkle_left",
        light_type="spot",
        intensity=intensity * 1.2,
        spot_size=0.087,  # 5 degrees - very narrow
        spot_blend=0.0,
        transform=Transform3D(
            position=(
                subject_position[0] - 0.6,
                subject_position[1] - 0.3,
                subject_position[2] + 1.0
            ),
            rotation=(-60, 0, 30)
        ),
        shadow_soft_size=0.0
    )

    sparkle_right = LightConfig(
        name="jewelry_sparkle_right",
        light_type="spot",
        intensity=intensity * 1.2,
        spot_size=0.087,
        spot_blend=0.0,
        transform=Transform3D(
            position=(
                subject_position[0] + 0.6,
                subject_position[1] - 0.3,
                subject_position[2] + 1.0
            ),
            rotation=(-60, 0, -30)
        ),
        shadow_soft_size=0.0
    )

    return [overhead, front, sparkle_left, sparkle_right]


def create_product_fashion(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 1500.0
) -> List[LightConfig]:
    """
    Create fashion product lighting configuration.

    Editorial-style lighting for clothing and accessories.
    Balances product detail with artistic presentation.

    Key features:
    - Editorial-style key
    - Texture emphasis
    - Artistic shadows

    Args:
        subject_position: Center position for product
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for fashion lighting
    """
    # Dramatic key
    key = position_key_light(
        LightConfig(
            name="fashion_key",
            light_type="area",
            intensity=intensity,
            shape="RECTANGLE",
            size=2.0,
            size_y=2.5,
            shadow_soft_size=0.4
        ),
        subject_position,
        angle=35.0,
        elevation=40.0,
        distance=1.8
    )

    # Soft fill
    fill = position_fill_light(
        LightConfig(
            name="fashion_fill",
            light_type="area",
            intensity=intensity * 0.35,
            shape="RECTANGLE",
            size=3.0,
            size_y=2.5,
            shadow_soft_size=0.6
        ),
        key,
        ratio=0.35
    )

    # Edge separation
    edge = position_back_light(
        LightConfig(
            name="fashion_edge",
            light_type="area",
            intensity=intensity * 0.5,
            shape="RECTANGLE",
            size=0.8,
            size_y=2.0,
            shadow_soft_size=0.3
        ),
        subject_position,
        elevation=20.0
    )

    return [key, fill, edge]


def create_product_automotive(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 3000.0
) -> List[LightConfig]:
    """
    Create automotive product lighting configuration.

    Dramatic lighting for car photography. Emphasizes curves,
    reflections, and metallic surfaces.

    Key features:
    - Long strip lights for reflections
    - Dramatic gradients
    - Emphasizes body curves

    Args:
        subject_position: Center position for vehicle
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for automotive lighting
    """
    # Main strip light
    main_strip = LightConfig(
        name="auto_main_strip",
        light_type="area",
        intensity=intensity,
        shape="RECTANGLE",
        size=0.5,
        size_y=8.0,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] - 4.0,
                subject_position[2] + 2.0
            ),
            rotation=(-30, 0, 0)
        ),
        shadow_soft_size=0.3
    )

    # Side accent strip
    side_strip = LightConfig(
        name="auto_side_strip",
        light_type="area",
        intensity=intensity * 0.7,
        shape="RECTANGLE",
        size=0.3,
        size_y=6.0,
        transform=Transform3D(
            position=(
                subject_position[0] - 3.0,
                subject_position[1],
                subject_position[2] + 1.5
            ),
            rotation=(0, 50, 0)
        ),
        shadow_soft_size=0.2
    )

    # Back rim for separation
    back_rim = LightConfig(
        name="auto_back_rim",
        light_type="area",
        intensity=intensity * 0.8,
        shape="RECTANGLE",
        size=0.5,
        size_y=6.0,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1] + 4.0,
                subject_position[2] + 1.0
            ),
            rotation=(-20, 180, 0)
        ),
        shadow_soft_size=0.3
    )

    # Ground fill
    ground_fill = LightConfig(
        name="auto_ground",
        light_type="area",
        intensity=intensity * 0.3,
        shape="RECTANGLE",
        size=10.0,
        size_y=10.0,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1],
                subject_position[2] - 0.5
            ),
            rotation=(90, 0, 0)
        ),
        shadow_soft_size=1.0
    )

    return [main_strip, side_strip, back_rim, ground_fill]


def create_product_furniture(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 2000.0
) -> List[LightConfig]:
    """
    Create furniture product lighting configuration.

    Natural lighting for furniture and home goods. Shows scale,
    material quality, and design features.

    Key features:
    - Natural-looking key
    - Material texture emphasis
    - Scale-appropriate shadows

    Args:
        subject_position: Center position for furniture
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for furniture lighting
    """
    # Large soft key (window simulation)
    key = LightConfig(
        name="furniture_key",
        light_type="area",
        intensity=intensity,
        shape="RECTANGLE",
        size=4.0,
        size_y=5.0,
        transform=Transform3D(
            position=(
                subject_position[0] - 2.0,
                subject_position[1] - 3.0,
                subject_position[2] + 2.0
            ),
            rotation=(-35, 30, 0)
        ),
        shadow_soft_size=0.7
    )

    # Fill for interior shadows
    fill = LightConfig(
        name="furniture_fill",
        light_type="area",
        intensity=intensity * 0.4,
        shape="RECTANGLE",
        size=3.0,
        size_y=4.0,
        transform=Transform3D(
            position=(
                subject_position[0] + 2.0,
                subject_position[1] - 2.0,
                subject_position[2] + 1.5
            ),
            rotation=(-25, -20, 0)
        ),
        shadow_soft_size=0.8
    )

    # Top fill
    top = LightConfig(
        name="furniture_top",
        light_type="area",
        intensity=intensity * 0.3,
        shape="RECTANGLE",
        size=5.0,
        size_y=5.0,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1],
                subject_position[2] + 4.0
            ),
            rotation=(-90, 0, 0)
        ),
        shadow_soft_size=0.9
    )

    return [key, fill, top]


def create_product_industrial(
    subject_position: Tuple[float, float, float] = (0, 0, 0),
    intensity: float = 2500.0
) -> List[LightConfig]:
    """
    Create industrial product lighting configuration.

    Technical lighting for machinery and industrial products.
    Emphasizes functionality, durability, and precision.

    Key features:
    - Clear, even illumination
    - Technical detail visibility
    - Professional appearance

    Args:
        subject_position: Center position for product
        intensity: Key light intensity in watts

    Returns:
        List of LightConfig objects for industrial lighting
    """
    # Main key
    key = position_key_light(
        LightConfig(
            name="industrial_key",
            light_type="area",
            intensity=intensity,
            shape="RECTANGLE",
            size=3.0,
            size_y=2.5,
            shadow_soft_size=0.5
        ),
        subject_position,
        angle=40.0,
        elevation=35.0,
        distance=2.5
    )

    # Balanced fill
    fill = position_fill_light(
        LightConfig(
            name="industrial_fill",
            light_type="area",
            intensity=intensity * 0.5,
            shape="RECTANGLE",
            size=3.0,
            size_y=2.5,
            shadow_soft_size=0.6
        ),
        key,
        ratio=0.5
    )

    # Top fill for details
    top = LightConfig(
        name="industrial_top",
        light_type="area",
        intensity=intensity * 0.4,
        shape="RECTANGLE",
        size=3.0,
        size_y=3.0,
        transform=Transform3D(
            position=(
                subject_position[0],
                subject_position[1],
                subject_position[2] + 3.0
            ),
            rotation=(-90, 0, 0)
        ),
        shadow_soft_size=0.6
    )

    # Accent for texture
    accent = position_back_light(
        LightConfig(
            name="industrial_accent",
            light_type="area",
            intensity=intensity * 0.3,
            shape="RECTANGLE",
            size=1.5,
            size_y=2.0,
            shadow_soft_size=0.4
        ),
        subject_position,
        elevation=25.0
    )

    return [key, fill, top, accent]


def list_light_rig_presets() -> List[str]:
    """
    List available light rig preset names.

    Returns:
        Sorted list of preset names
    """
    return sorted([
        # Studio/General
        "three_point_soft",
        "three_point_hard",
        "product_hero",
        "studio_high_key",
        "studio_low_key",
        # Portrait Patterns
        "portrait_rembrandt",
        "portrait_loop",
        "portrait_butterfly",
        "portrait_split",
        "portrait_broad",
        "portrait_short",
        "portrait_clamshell",
        "portrait_high_key",
        "portrait_low_key",
        "portrait_rim",
        "portrait_flat",
        "portrait_dramatic",
        # Product Categories
        "product_electronics",
        "product_cosmetics",
        "product_food",
        "product_jewelry",
        "product_fashion",
        "product_automotive",
        "product_furniture",
        "product_industrial",
    ])
