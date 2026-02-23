"""
Studio Equipment Module

Provides equipment simulation and presets for professional photoshoots.
Includes light modifiers, stands, reflectors, and studio gear.

Equipment Types:
- Light modifiers (softboxes, umbrellas, grids, snoots)
- Stands and booms
- Reflectors and flags
- Diffusers and scrims
- Backdrop supports
- Props and accessories

Usage:
    from lib.cinematic.equipment import (
        EquipmentType,
        EquipmentConfig,
        LightModifier,
        create_softbox,
        create_umbrella,
        get_equipment_preset,
    )

    # Create a softbox modifier
    softbox = create_softbox("medium", "octagonal")

    # Get equipment preset for portrait session
    equipment = get_equipment_preset("portrait_studio")
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .types import Transform3D


class EquipmentType(Enum):
    """Types of studio equipment."""
    # Light Modifiers
    SOFTBOX = "softbox"
    UMBRELLA = "umbrella"
    BEAUTY_DISH = "beauty_dish"
    GRID = "grid"
    SNOOT = "snoot"
    BARN_DOORS = "barn_doors"
    GELS = "gels"
    DIFFUSER = "diffuser"

    # Support Equipment
    LIGHT_STAND = "light_stand"
    BOOM_ARM = "boom_arm"
    C_STAND = "c_stand"
    TRUSS = "truss"
    OVERHEAD_RIG = "overhead_rig"

    # Reflectors and Flags
    REFLECTOR = "reflector"
    FLAG = "flag"
    SCRIM = "scrim"
    V_FLAT = "v_flat"

    # Backdrop Equipment
    BACKDROP_STAND = "backdrop_stand"
    PAPER_ROLL = "paper_roll"
    MUSLIN = "muslin"
    SEAMLESS = "seamless"

    # Props and Accessories
    APPLE_BOX = "apple_box"
    SAND_BAG = "sand_bag"
    CLAMP = "clamp"
    Gaffer_TAPE = "gaffer_tape"

    # Camera Support
    TRIPOD = "tripod"
    DOLLY = "dolly"
    JIB = "jib"
    SLIDER = "slider"


class ModifierShape(Enum):
    """Shapes for light modifiers."""
    RECTANGULAR = "rectangular"
    SQUARE = "square"
    OCTAGONAL = "octagonal"
    HEXAGONAL = "hexagonal"
    CIRCULAR = "circular"
    STRIP = "strip"
    PARABOLIC = "parabolic"


class ReflectorType(Enum):
    """Types of reflectors."""
    WHITE = "white"
    SILVER = "silver"
    GOLD = "gold"
    BLACK = "black"  # Negative fill
    MIXED = "mixed"  # Multi-surface


@dataclass
class EquipmentConfig:
    """Configuration for a piece of equipment."""
    name: str
    equipment_type: EquipmentType
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    dimensions: Tuple[float, float, float] = (1.0, 1.0, 1.0)  # width, height, depth
    weight: float = 1.0  # kg
    color: Optional[str] = None
    material: Optional[str] = None
    transform: Transform3D = field(default_factory=lambda: Transform3D())
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "equipment_type": self.equipment_type.value,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "dimensions": self.dimensions,
            "weight": self.weight,
            "color": self.color,
            "material": self.material,
            "transform": {
                "position": self.transform.position,
                "rotation": self.transform.rotation,
                "scale": self.transform.scale,
            },
            "properties": self.properties,
        }


@dataclass
class LightModifier:
    """Light modifier configuration."""
    name: str
    modifier_type: EquipmentType
    shape: ModifierShape
    size: Tuple[float, float]  # width, height (or diameter, depth)
    inner_color: str = "white"
    outer_color: str = "black"
    diffusion_factor: float = 0.8  # 0.0 = no diffusion, 1.0 = max diffusion
    throw_distance: float = 1.5  # Optimal distance from subject (meters)
    spill_control: float = 0.5  # 0.0 = no control, 1.0 = tight control
    properties: Dict[str, Any] = field(default_factory=dict)

    def get_effective_area(self) -> float:
        """Calculate effective light-emitting area in square meters."""
        if self.shape in (ModifierShape.RECTANGULAR, ModifierShape.STRIP):
            return self.size[0] * self.size[1]
        elif self.shape == ModifierShape.SQUARE:
            return self.size[0] * self.size[0]
        elif self.shape in (ModifierShape.OCTAGONAL, ModifierShape.HEXAGONAL, ModifierShape.CIRCULAR):
            # Approximate octagon/hexagon as circle for area
            radius = self.size[0] / 2
            return 3.14159 * radius * radius
        elif self.shape == ModifierShape.PARABOLIC:
            # Parabolic dish - approximate
            radius = self.size[0] / 2
            return 3.14159 * radius * radius * 0.7
        return self.size[0] * self.size[1]


# =============================================================================
# SOFTBOX PRESETS
# =============================================================================

def create_softbox(
    size_name: str = "medium",
    shape: str = "rectangular"
) -> LightModifier:
    """
    Create a softbox configuration.

    Args:
        size_name: Size preset (small, medium, large, xlarge)
        shape: Shape type (rectangular, square, octagonal, strip)

    Returns:
        LightModifier configuration
    """
    size_presets = {
        "small": (0.4, 0.6),     # 40x60cm
        "medium": (0.6, 0.9),    # 60x90cm
        "large": (0.9, 1.2),     # 90x120cm
        "xlarge": (1.2, 1.8),    # 120x180cm
    }

    shape_enum = ModifierShape.RECTANGULAR
    if shape == "square":
        shape_enum = ModifierShape.SQUARE
        size_presets = {
            "small": (0.5, 0.5),
            "medium": (0.8, 0.8),
            "large": (1.2, 1.2),
            "xlarge": (1.5, 1.5),
        }
    elif shape in ("octagonal", "octa"):
        shape_enum = ModifierShape.OCTAGONAL
        size_presets = {
            "small": (0.6, 0.3),   # diameter, depth
            "medium": (1.0, 0.4),
            "large": (1.5, 0.5),
            "xlarge": (2.0, 0.6),
        }
    elif shape == "strip":
        shape_enum = ModifierShape.STRIP
        size_presets = {
            "small": (0.3, 1.0),
            "medium": (0.3, 1.5),
            "large": (0.4, 2.0),
            "xlarge": (0.5, 2.5),
        }

    size = size_presets.get(size_name, size_presets["medium"])

    return LightModifier(
        name=f"{size_name}_{shape}_softbox",
        modifier_type=EquipmentType.SOFTBOX,
        shape=shape_enum,
        size=size,
        diffusion_factor=0.85,
        throw_distance=1.5,
        spill_control=0.7,
    )


def create_strip_softbox(length: float = 1.5, width: float = 0.3) -> LightModifier:
    """Create a strip softbox (long, narrow modifier)."""
    return LightModifier(
        name="strip_softbox",
        modifier_type=EquipmentType.SOFTBOX,
        shape=ModifierShape.STRIP,
        size=(width, length),
        diffusion_factor=0.8,
        throw_distance=1.2,
        spill_control=0.6,
    )


# =============================================================================
# UMBRELLA PRESETS
# =============================================================================

def create_umbrella(
    size_name: str = "medium",
    umbrella_type: str = "translucent"
) -> LightModifier:
    """
    Create an umbrella configuration.

    Args:
        size_name: Size preset (small, medium, large, xlarge)
        umbrella_type: Type (translucent, silver, white, deep)

    Returns:
        LightModifier configuration
    """
    size_presets = {
        "small": (0.8, 0.4),    # diameter, depth
        "medium": (1.0, 0.5),
        "large": (1.3, 0.6),
        "xlarge": (1.7, 0.7),
    }

    size = size_presets.get(size_name, size_presets["medium"])

    properties = {}
    if umbrella_type == "translucent":
        properties["shoot_through"] = True
        properties["reflective"] = False
    elif umbrella_type in ("silver", "white"):
        properties["shoot_through"] = False
        properties["reflective"] = True
        properties["surface"] = umbrella_type
    elif umbrella_type == "deep":
        size = (size[0], size[1] * 1.5)  # Deeper parabolic
        properties["parabolic"] = True

    return LightModifier(
        name=f"{size_name}_{umbrella_type}_umbrella",
        modifier_type=EquipmentType.UMBRELLA,
        shape=ModifierShape.PARABOLIC,
        size=size,
        inner_color=umbrella_type if umbrella_type in ("silver", "white") else "white",
        diffusion_factor=0.7 if umbrella_type == "translucent" else 0.5,
        throw_distance=1.8,
        spill_control=0.4,
        properties=properties,
    )


# =============================================================================
# BEAUTY DISH PRESETS
# =============================================================================

def create_beauty_dish(size_name: str = "medium") -> LightModifier:
    """
    Create a beauty dish configuration.

    Args:
        size_name: Size preset (small, medium, large)

    Returns:
        LightModifier configuration
    """
    size_presets = {
        "small": (0.4, 0.2),   # 40cm diameter
        "medium": (0.56, 0.25),  # 56cm (22")
        "large": (0.7, 0.3),   # 70cm
    }

    size = size_presets.get(size_name, size_presets["medium"])

    return LightModifier(
        name=f"{size_name}_beauty_dish",
        modifier_type=EquipmentType.BEAUTY_DISH,
        shape=ModifierShape.PARABOLIC,
        size=size,
        inner_color="white",
        diffusion_factor=0.3,  # Harder light
        throw_distance=1.2,
        spill_control=0.8,
        properties={
            "center_deflector": True,
            "sock_available": True,  # Optional diffusion sock
        },
    )


# =============================================================================
# GRIDS AND SNOOTS
# =============================================================================

def create_grid(
    grid_type: str = "honeycomb",
    degrees: int = 40
) -> LightModifier:
    """
    Create a light grid (honeycomb) configuration.

    Args:
        grid_type: Type (honeycomb, egg_crate)
        degrees: Beam angle (10, 20, 30, 40 degrees)

    Returns:
        LightModifier configuration
    """
    return LightModifier(
        name=f"{degrees}deg_{grid_type}_grid",
        modifier_type=EquipmentType.GRID,
        shape=ModifierShape.SQUARE,
        size=(0.4, 0.4),  # Typical grid size
        diffusion_factor=0.1,
        throw_distance=2.0,
        spill_control=1.0 - (degrees / 60),  # Tighter = more control
        properties={
            "beam_angle": degrees,
            "grid_type": grid_type,
        },
    )


def create_snoot(
    length: float = 0.3,
    opening_diameter: float = 0.05
) -> LightModifier:
    """
    Create a snoot configuration for focused light.

    Args:
        length: Length of snoot (meters)
        opening_diameter: Diameter of opening (meters)

    Returns:
        LightModifier configuration
    """
    return LightModifier(
        name="snoot",
        modifier_type=EquipmentType.SNOOT,
        shape=ModifierShape.CIRCULAR,
        size=(opening_diameter, length),
        diffusion_factor=0.0,  # No diffusion - hard light
        throw_distance=2.5,
        spill_control=1.0,
        properties={
            "beam_angle": 10,  # Very narrow
        },
    )


def create_barn_doors(
    size: Tuple[float, float] = (0.3, 0.3)
) -> LightModifier:
    """Create barn doors configuration."""
    return LightModifier(
        name="barn_doors",
        modifier_type=EquipmentType.BARN_DOORS,
        shape=ModifierShape.RECTANGULAR,
        size=size,
        diffusion_factor=0.0,
        throw_distance=1.5,
        spill_control=0.9,
        properties={
            "four_way": True,
            "adjustable": True,
        },
    )


# =============================================================================
# REFLECTORS AND FLAGS
# =============================================================================

@dataclass
class ReflectorConfig:
    """Configuration for a reflector."""
    name: str
    reflector_type: ReflectorType
    size: Tuple[float, float]  # width, height
    foldable: bool = True
    surfaces: List[str] = field(default_factory=list)

    def get_reflectance(self) -> float:
        """Get reflectance factor (0.0 to 1.0)."""
        reflectance_map = {
            ReflectorType.WHITE: 0.8,
            ReflectorType.SILVER: 0.95,
            ReflectorType.GOLD: 0.85,
            ReflectorType.BLACK: 0.0,  # Negative fill
            ReflectorType.MIXED: 0.8,
        }
        return reflectance_map.get(self.reflector_type, 0.5)


def create_reflector(
    size_name: str = "medium",
    surface: str = "white"
) -> ReflectorConfig:
    """
    Create a reflector configuration.

    Args:
        size_name: Size preset (small, medium, large, xlarge)
        surface: Surface type (white, silver, gold, black)

    Returns:
        ReflectorConfig
    """
    size_presets = {
        "small": (0.6, 0.9),    # 60x90cm
        "medium": (1.0, 1.5),   # 100x150cm
        "large": (1.2, 1.8),    # 120x180cm
        "xlarge": (1.5, 2.0),   # 150x200cm
    }

    size = size_presets.get(size_name, size_presets["medium"])
    reflector_type = ReflectorType(surface.lower())

    return ReflectorConfig(
        name=f"{size_name}_{surface}_reflector",
        reflector_type=reflector_type,
        size=size,
        foldable=True,
        surfaces=[surface],
    )


def create_5in1_reflector(size_name: str = "medium") -> ReflectorConfig:
    """Create a 5-in-1 multi-surface reflector."""
    size_presets = {
        "small": (0.6, 0.9),
        "medium": (1.0, 1.5),
        "large": (1.2, 1.8),
        "xlarge": (1.5, 2.0),
    }

    size = size_presets.get(size_name, size_presets["medium"])

    return ReflectorConfig(
        name=f"{size_name}_5in1_reflector",
        reflector_type=ReflectorType.MIXED,
        size=size,
        foldable=True,
        surfaces=["white", "silver", "gold", "black", "translucent"],
    )


def create_flag(size_name: str = "medium") -> EquipmentConfig:
    """Create a flag (light blocker) configuration."""
    size_presets = {
        "small": (0.3, 0.45),   # 12x18"
        "medium": (0.45, 0.6),  # 18x24"
        "large": (0.6, 0.9),    # 24x36"
        "xlarge": (1.0, 1.5),   # Large flag
    }

    size = size_presets.get(size_name, size_presets["medium"])

    return EquipmentConfig(
        name=f"{size_name}_flag",
        equipment_type=EquipmentType.FLAG,
        dimensions=(size[0], size[1], 0.02),
        color="black",
        material="velour",
        properties={
            "absorptive": True,
            "frames_available": True,
        },
    )


def create_v_flat(size: str = "4x8") -> EquipmentConfig:
    """Create a V-flat configuration."""
    size_presets = {
        "4x4": (1.2, 1.2, 0.02),
        "4x8": (1.2, 2.4, 0.02),
        "8x8": (2.4, 2.4, 0.02),
    }

    dims = size_presets.get(size, size_presets["4x8"])

    return EquipmentConfig(
        name=f"{size}_vflat",
        equipment_type=EquipmentType.V_FLAT,
        dimensions=dims,
        color="white/black",  # Reversible
        material="foam_core",
        properties={
            "reversible": True,
            "folding": True,
        },
    )


# =============================================================================
# DIFFUSERS AND SCRIMS
# =============================================================================

def create_diffuser(
    size_name: str = "medium",
    density: str = "half"
) -> EquipmentConfig:
    """
    Create a diffuser configuration.

    Args:
        size_name: Size preset
        density: Diffusion density (quarter, half, full)

    Returns:
        EquipmentConfig
    """
    size_presets = {
        "small": (0.6, 0.6, 0.01),
        "medium": (1.0, 1.0, 0.01),
        "large": (1.5, 1.5, 0.01),
        "xlarge": (2.0, 2.0, 0.01),
    }

    dims = size_presets.get(size_name, size_presets["medium"])

    density_map = {
        "quarter": 0.25,
        "half": 0.5,
        "full": 1.0,
    }

    return EquipmentConfig(
        name=f"{size_name}_{density}_diffuser",
        equipment_type=EquipmentType.DIFFUSER,
        dimensions=dims,
        material="silk",
        properties={
            "density": density,
            "light_reduction": density_map.get(density, 0.5),
        },
    )


def create_scrim(
    size: Tuple[float, float] = (2.0, 2.0),
    frame: bool = True
) -> EquipmentConfig:
    """Create a scrim (large diffuser on frame)."""
    return EquipmentConfig(
        name="scrim",
        equipment_type=EquipmentType.SCRIM,
        dimensions=(size[0], size[1], 0.02),
        material="silk",
        properties={
            "frame": frame,
            "frame_material": "aluminum" if frame else None,
        },
    )


# =============================================================================
# STANDS AND SUPPORT
# =============================================================================

@dataclass
class StandConfig:
    """Configuration for a light stand."""
    name: str
    stand_type: EquipmentType
    min_height: float  # meters
    max_height: float  # meters
    footprint: float  # diameter in meters
    max_load: float  # kg
    weight: float  # kg
    sections: int = 3
    air_cushioned: bool = False
    material: str = "aluminum"

    def get_stability_rating(self) -> float:
        """Calculate stability rating (0.0 to 1.0)."""
        # Heavier, wider base = more stable
        base_factor = min(1.0, self.footprint / 1.5)
        weight_factor = min(1.0, self.weight / 5.0)
        return (base_factor + weight_factor) / 2


def create_light_stand(stand_type: str = "standard") -> StandConfig:
    """
    Create a light stand configuration.

    Args:
        stand_type: Type (mini, standard, heavy_duty, c_stand)

    Returns:
        StandConfig
    """
    presets = {
        "mini": StandConfig(
            name="mini_stand",
            stand_type=EquipmentType.LIGHT_STAND,
            min_height=0.4,
            max_height=1.2,
            footprint=0.5,
            max_load=2.0,
            weight=0.8,
            sections=2,
        ),
        "standard": StandConfig(
            name="standard_stand",
            stand_type=EquipmentType.LIGHT_STAND,
            min_height=0.8,
            max_height=2.8,
            footprint=0.8,
            max_load=5.0,
            weight=2.5,
            sections=3,
            air_cushioned=True,
        ),
        "heavy_duty": StandConfig(
            name="heavy_duty_stand",
            stand_type=EquipmentType.LIGHT_STAND,
            min_height=1.0,
            max_height=3.5,
            footprint=1.2,
            max_load=15.0,
            weight=6.0,
            sections=4,
            air_cushioned=True,
            material="steel",
        ),
        "c_stand": StandConfig(
            name="c_stand",
            stand_type=EquipmentType.C_STAND,
            min_height=0.6,
            max_height=3.0,
            footprint=0.9,
            max_load=10.0,
            weight=7.0,
            sections=3,
            material="steel",
        ),
    }

    return presets.get(stand_type, presets["standard"])


def create_boom_arm(length: float = 2.0) -> StandConfig:
    """Create a boom arm configuration."""
    return StandConfig(
        name="boom_arm",
        stand_type=EquipmentType.BOOM_ARM,
        min_height=0.0,
        max_height=length,
        footprint=0.0,  # No footprint - attaches to stand
        max_load=3.0,
        weight=2.0,
        sections=2,
    )


# =============================================================================
# EQUIPMENT PRESETS
# =============================================================================

def get_equipment_preset(preset_name: str) -> Dict[str, Any]:
    """
    Get a complete equipment preset for a photoshoot type.

    Args:
        preset_name: Name of preset (portrait_studio, product_table, etc.)

    Returns:
        Dictionary with equipment list
    """
    presets = {
        "portrait_studio": {
            "name": "Portrait Studio Setup",
            "description": "Basic portrait studio equipment",
            "modifiers": [
                create_softbox("large", "octagonal"),
                create_softbox("medium", "rectangular"),
                create_reflector("large", "white"),
            ],
            "stands": [
                create_light_stand("standard"),
                create_light_stand("standard"),
                create_boom_arm(),
            ],
            "accessories": [
                create_flag("medium"),
                create_5in1_reflector("large"),
            ],
        },
        "product_table": {
            "name": "Product Photography Setup",
            "description": "Equipment for product photography",
            "modifiers": [
                create_softbox("large", "rectangular"),
                create_strip_softbox(1.5),
                create_strip_softbox(1.5),
                create_diffuser("large"),
            ],
            "stands": [
                create_light_stand("standard"),
                create_light_stand("standard"),
                create_light_stand("standard"),
            ],
            "accessories": [
                create_reflector("small", "white"),
                create_reflector("small", "white"),
                create_flag("small"),
            ],
        },
        "beauty_setup": {
            "name": "Beauty Photography Setup",
            "description": "Equipment for beauty/fashion photography",
            "modifiers": [
                create_beauty_dish("medium"),
                create_softbox("medium", "rectangular"),
                create_reflector("medium", "silver"),
            ],
            "stands": [
                create_light_stand("heavy_duty"),
                create_light_stand("standard"),
                create_c_stand("c_stand"),
            ],
            "accessories": [
                create_5in1_reflector("medium"),
                create_flag("medium"),
            ],
        },
        "food_photography": {
            "name": "Food Photography Setup",
            "description": "Equipment for food photography",
            "modifiers": [
                create_softbox("large", "rectangular"),
                create_diffuser("medium"),
                create_reflector("medium", "white"),
            ],
            "stands": [
                create_light_stand("standard"),
                create_boom_arm(),
            ],
            "accessories": [
                create_flag("small"),
                create_v_flat("4x4"),
            ],
        },
        "automotive_studio": {
            "name": "Automotive Photography Setup",
            "description": "Large-scale lighting for vehicles",
            "modifiers": [
                create_strip_softbox(2.5),
                create_strip_softbox(2.5),
                create_strip_softbox(2.5),
                create_strip_softbox(2.5),
            ],
            "stands": [
                create_light_stand("heavy_duty"),
                create_light_stand("heavy_duty"),
                create_light_stand("heavy_duty"),
                create_light_stand("heavy_duty"),
            ],
            "accessories": [
                create_scrim((4.0, 4.0)),
                create_scrim((4.0, 4.0)),
            ],
        },
        "jewelry_table": {
            "name": "Jewelry Photography Setup",
            "description": "Macro jewelry lighting setup",
            "modifiers": [
                create_softbox("small", "rectangular"),
                create_diffuser("small"),
            ],
            "stands": [
                create_light_stand("mini"),
                create_light_stand("mini"),
            ],
            "accessories": [
                create_reflector("small", "white"),
            ],
        },
        "outdoor_portrait": {
            "name": "Outdoor Portrait Setup",
            "description": "Portable equipment for outdoor portraits",
            "modifiers": [
                create_softbox("medium", "octagonal"),
            ],
            "stands": [
                create_light_stand("standard"),
            ],
            "accessories": [
                create_5in1_reflector("large"),
                create_diffuser("large"),
                create_flag("medium"),
            ],
        },
    }

    if preset_name not in presets:
        available = list(presets.keys())
        raise ValueError(f"Unknown preset: {preset_name}. Available: {available}")

    return presets[preset_name]


def list_equipment_presets() -> List[str]:
    """List available equipment preset names."""
    return [
        "portrait_studio",
        "product_table",
        "beauty_setup",
        "food_photography",
        "automotive_studio",
        "jewelry_table",
        "outdoor_portrait",
    ]


def get_all_modifiers() -> List[LightModifier]:
    """Get a list of all available light modifier presets."""
    return [
        # Softboxes
        create_softbox("small", "rectangular"),
        create_softbox("medium", "rectangular"),
        create_softbox("large", "rectangular"),
        create_softbox("medium", "octagonal"),
        create_softbox("large", "octagonal"),
        create_strip_softbox(),
        # Umbrellas
        create_umbrella("medium", "translucent"),
        create_umbrella("medium", "silver"),
        create_umbrella("large", "deep"),
        # Beauty dishes
        create_beauty_dish("medium"),
        create_beauty_dish("large"),
        # Focusing
        create_grid("honeycomb", 40),
        create_grid("honeycomb", 20),
        create_snoot(),
        create_barn_doors(),
    ]
