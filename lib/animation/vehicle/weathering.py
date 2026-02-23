"""
Weathering System - Dirt, Rust, Scratches, and Wear

Applies procedural weathering effects to vehicles for realism.
From showroom-new to wasteland-worn.

Usage:
    from lib.animation.vehicle.weathering import (
        WeatheringConfig, WeatheringSystem, apply_weathering
    )

    # Apply moderate wear
    config = WeatheringConfig(
        dirt_level=0.4,
        sun_fade=0.15,
        scratches=8,
        rust_spots=3
    )

    system = WeatheringSystem()
    system.apply_weathering(vehicle, config)

    # Or use presets
    apply_weathering(vehicle, preset="daily_driver")
"""

import bpy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from math import pi, sin, cos, sqrt
from mathutils import Vector, Color
from enum import Enum
import random


class DirtPattern(Enum):
    UNIFORM = "uniform"
    REALISTIC = "realistic"     # Aerodynamic flow patterns
    OFFROAD = "offroad"         # Heavy wheel well spray
    URBAN = "urban"             # Road dust
    MUD = "mud"                 # Splattered mud


class RustSeverity(Enum):
    NONE = "none"
    SURFACE = "surface"         # Light surface rust
    SPOT = "spot"               # Spot rust
    HEAVY = "heavy"             # Heavy rust patches
    CANCER = "cancer"           # Rust perforation


@dataclass
class WeatheringConfig:
    """Configuration for vehicle weathering."""

    # === AGE & USE ===
    age_years: float = 5.0
    mileage_km: float = 80000.0

    # === DIRT ===
    dirt_level: float = 0.3            # 0-1 overall dirtiness
    dirt_pattern: DirtPattern = DirtPattern.REALISTIC
    mud_splatter: bool = False
    mud_intensity: float = 0.5
    dust_coating: float = 0.2

    # === PAINT ===
    sun_fade: float = 0.1              # 0-1 UV fading
    clear_coat_wear: float = 0.1       # 0-1 clear coat degradation
    oxidation: float = 0.0             # Paint oxidation

    # === SCRATCHES & CHIPS ===
    scratches: int = 5                 # Number of scratches
    scratch_depth: float = 0.3         # 0-1 depth intensity
    paint_chips: int = 10              # Number of chips
    door_dings: int = 2                # Number of door dings

    # === RUST ===
    rust_spots: int = 0
    rust_severity: RustSeverity = RustSeverity.NONE
    rust_on_scratches: bool = True     # Rust develops on deep scratches

    # === WEAR PATTERNS ===
    bumper_scuffs: bool = True
    wheel_well_grime: bool = True
    exhaust_staining: bool = True
    brake_dust: bool = True
    headlight_haze: float = 0.0        # 0-1 headlight clouding

    # === INTERIOR ===
    interior_wear: float = 0.2
    seat_wear: float = 0.3
    steering_wheel_wear: float = 0.2

    # === WEATHERING ZONES ===
    # Higher values = more weathering in that zone
    hood_factor: float = 1.0
    roof_factor: float = 0.8
    sides_factor: float = 0.7
    rear_factor: float = 0.6
    lower_factor: float = 1.5          # Lower panels get more dirt


# === WEATHERING PRESETS ===

WEATHERING_PRESETS = {
    "showroom": WeatheringConfig(
        age_years=0.0,
        mileage_km=0.0,
        dirt_level=0.0,
        scratches=0,
        paint_chips=0,
        sun_fade=0.0,
        clear_coat_wear=0.0
    ),

    "new": WeatheringConfig(
        age_years=1.0,
        mileage_km=15000.0,
        dirt_level=0.05,
        dust_coating=0.05,
        scratches=1,
        paint_chips=2,
        sun_fade=0.02
    ),

    "daily_driver": WeatheringConfig(
        age_years=5.0,
        mileage_km=80000.0,
        dirt_level=0.25,
        dust_coating=0.15,
        scratches=5,
        scratch_depth=0.3,
        paint_chips=10,
        door_dings=3,
        sun_fade=0.1,
        clear_coat_wear=0.1,
        bumper_scuffs=True,
        wheel_well_grime=True
    ),

    "worn": WeatheringConfig(
        age_years=12.0,
        mileage_km=200000.0,
        dirt_level=0.4,
        dust_coating=0.3,
        scratches=15,
        scratch_depth=0.5,
        paint_chips=25,
        door_dings=8,
        sun_fade=0.25,
        clear_coat_wear=0.4,
        oxidation=0.1,
        rust_spots=3,
        rust_severity=RustSeverity.SPOT,
        headlight_haze=0.3
    ),

    "beater": WeatheringConfig(
        age_years=20.0,
        mileage_km=350000.0,
        dirt_level=0.6,
        mud_splatter=True,
        scratches=30,
        scratch_depth=0.7,
        paint_chips=50,
        door_dings=15,
        sun_fade=0.4,
        clear_coat_wear=0.6,
        oxidation=0.3,
        rust_spots=15,
        rust_severity=RustSeverity.HEAVY,
        rust_on_scratches=True,
        headlight_haze=0.6,
        bumper_scuffs=True,
        wheel_well_grime=True
    ),

    "wasteland": WeatheringConfig(
        age_years=30.0,
        mileage_km=500000.0,
        dirt_level=0.8,
        mud_splatter=True,
        mud_intensity=0.8,
        dirt_pattern=DirtPattern.OFFROAD,
        scratches=50,
        scratch_depth=0.9,
        paint_chips=100,
        door_dings=25,
        sun_fade=0.5,
        clear_coat_wear=0.9,
        oxidation=0.5,
        rust_spots=40,
        rust_severity=RustSeverity.CANCER,
        rust_on_scratches=True,
        headlight_haze=0.8,
        bumper_scuffs=True,
        wheel_well_grime=True,
        brake_dust=True
    ),

    "hero": WeatheringConfig(
        age_years=2.0,
        mileage_km=30000.0,
        dirt_level=0.1,
        scratches=2,
        paint_chips=3,
        sun_fade=0.03,
        clear_coat_wear=0.05
    ),

    "racing": WeatheringConfig(
        age_years=3.0,
        mileage_km=50000.0,
        dirt_level=0.2,
        dirt_pattern=DirtPattern.REALISTIC,
        scratches=10,
        scratch_depth=0.4,
        paint_chips=15,
        brake_dust=True,
        wheel_well_grime=True,
        sun_fade=0.05
    ),
}


class WeatheringSystem:
    """
    Applies procedural weathering to vehicles.

    Uses a combination of:
    - Vertex color layers for dirt maps
    - Material node mixing
    - Decal projection for scratches
    """

    def __init__(self):
        self.vertex_color_layers: Dict[str, str] = {}

    def apply_weathering(
        self,
        vehicle: bpy.types.Object,
        config: WeatheringConfig,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Apply weathering effects to a vehicle.

        Args:
            vehicle: The vehicle object
            config: Weathering configuration
            seed: Random seed for reproducibility

        Returns:
            Dictionary with applied effects
        """
        random.seed(seed)
        result = {
            'dirt': False,
            'scratches': 0,
            'rust': 0,
            'wear': False
        }

        # Get or create vertex color layer for dirt
        dirt_layer = self._get_or_create_vertex_color(vehicle, "DirtMask")

        # Apply dirt
        if config.dirt_level > 0:
            self._apply_dirt(vehicle, config, dirt_layer)
            result['dirt'] = True

        # Apply scratches
        if config.scratches > 0:
            result['scratches'] = self._apply_scratches(vehicle, config)

        # Apply rust
        if config.rust_spots > 0:
            result['rust'] = self._apply_rust(vehicle, config)

        # Apply paint chips
        if config.paint_chips > 0:
            self._apply_paint_chips(vehicle, config)

        # Apply sun fade to materials
        if config.sun_fade > 0:
            self._apply_sun_fade(vehicle, config)

        # Apply clear coat wear
        if config.clear_coat_wear > 0:
            self._apply_clear_coat_wear(vehicle, config)

        # Apply wheel well grime
        if config.wheel_well_grime:
            self._apply_wheel_well_grime(vehicle, config)

        # Apply headlight haze
        if config.headlight_haze > 0:
            self._apply_headlight_haze(vehicle, config)

        # Store config on object
        vehicle["weathering_config"] = {
            'dirt_level': config.dirt_level,
            'sun_fade': config.sun_fade,
            'scratches': config.scratches,
            'rust_spots': config.rust_spots
        }

        return result

    def _get_or_create_vertex_color(
        self,
        obj: bpy.types.Object,
        layer_name: str
    ):
        """Get or create a vertex color layer."""
        if obj.type != 'MESH':
            return None

        mesh = obj.data

        # Check if layer exists
        if layer_name in mesh.color_attributes:
            return mesh.color_attributes[layer_name]

        # Create new layer
        layer = mesh.color_attributes.new(name=layer_name, type='BYTE_COLOR', domain='CORNER')
        return layer

    def _apply_dirt(
        self,
        vehicle: bpy.types.Object,
        config: WeatheringConfig,
        layer
    ) -> None:
        """Apply dirt accumulation based on pattern."""
        if not layer or vehicle.type != 'MESH':
            return

        mesh = vehicle.data
        level = config.dirt_level

        # Get bounding box for height-based distribution
        bbox = vehicle.bound_box
        min_z = min(v[2] for v in bbox)
        max_z = max(v[2] for v in bbox)
        height_range = max_z - min_z

        # Apply dirt based on pattern
        for i, loop in enumerate(mesh.loops):
            vert = mesh.vertices[loop.vertex_index]
            normal = vert.normal
            pos = vert.co

            # Base dirt from config
            dirt = level

            # Height-based: more dirt on lower surfaces
            height_factor = 1.0 - (pos.z - min_z) / height_range
            dirt *= (0.5 + height_factor * config.lower_factor * 0.5)

            # Pattern-based adjustments
            if config.dirt_pattern == DirtPattern.REALISTIC:
                # Aerodynamic: less dirt on leading surfaces
                if normal.x > 0.5:  # Front-facing
                    dirt *= 0.6

            elif config.dirt_pattern == DirtPattern.OFFROAD:
                # Heavy on wheel wells and lower
                if pos.z < min_z + height_range * 0.3:
                    dirt *= 1.8
                if normal.z < -0.3:  # Underneath
                    dirt *= 2.0

            elif config.dirt_pattern == DirtPattern.MUD:
                # Splattered pattern
                if random.random() > 0.7:
                    dirt = min(1.0, dirt * random.uniform(1.5, 3.0))

            # Add some randomness
            dirt *= random.uniform(0.8, 1.2)
            dirt = max(0, min(1, dirt))

            # Set vertex color (grayscale dirt)
            layer.data[i].color = (dirt, dirt, dirt, 1.0)

    def _apply_scratches(
        self,
        vehicle: bpy.types.Object,
        config: WeatheringConfig
    ) -> int:
        """Apply procedural scratches."""
        count = config.scratches
        applied = 0

        # Create a scratch material if needed
        scratch_mat = self._get_or_create_scratch_material(config.scratch_depth)

        # For a proper implementation, we'd use grease pencil or curves
        # For now, store scratch data for later application
        scratches = []

        for i in range(count):
            # Random scratch parameters
            scratch = {
                'position': Vector((
                    random.uniform(-1.5, 1.5),
                    random.uniform(-0.8, 0.8),
                    random.uniform(0.3, 1.2)
                )),
                'length': random.uniform(0.1, 0.5),
                'angle': random.uniform(-30, 30) if random.random() > 0.3 else random.uniform(-5, 5),
                'depth': config.scratch_depth * random.uniform(0.5, 1.0)
            }
            scratches.append(scratch)
            applied += 1

        # Store scratches for later
        vehicle["scratches"] = scratches

        return applied

    def _apply_rust(
        self,
        vehicle: bpy.types.Object,
        config: WeatheringConfig
    ) -> int:
        """Apply rust spots."""
        count = config.rust_spots
        applied = 0

        rust_mat = self._get_or_create_rust_material(config.rust_severity)

        # Create rust vertex color layer
        rust_layer = self._get_or_create_vertex_color(vehicle, "RustMask")

        if rust_layer and vehicle.type == 'MESH':
            mesh = vehicle.data

            # Generate rust spot centers
            rust_spots = []
            for i in range(count):
                spot = {
                    'center': Vector((
                        random.uniform(-1.5, 1.5),
                        random.uniform(-0.8, 0.8),
                        random.uniform(0.2, 1.0)
                    )),
                    'radius': random.uniform(0.05, 0.15),
                    'intensity': random.uniform(0.5, 1.0)
                }
                rust_spots.append(spot)

            # Apply rust to vertices near spots
            for i, loop in enumerate(mesh.loops):
                vert = mesh.vertices[loop.vertex_index]
                pos = vert.co

                rust_value = 0.0
                for spot in rust_spots:
                    dist = (pos - spot['center']).length
                    if dist < spot['radius']:
                        rust_value = max(rust_value, spot['intensity'] * (1 - dist / spot['radius']))

                rust_layer.data[i].color = (rust_value, rust_value * 0.6, rust_value * 0.3, 1.0)
                applied += 1

        vehicle["rust_spots"] = count
        return count

    def _apply_paint_chips(
        self,
        vehicle: bpy.types.Object,
        config: WeatheringConfig
    ) -> None:
        """Apply paint chips (small spots where paint is missing)."""
        chips_layer = self._get_or_create_vertex_color(vehicle, "ChipsMask")

        if not chips_layer or vehicle.type != 'MESH':
            return

        mesh = vehicle.data

        # Generate chip positions
        chips = []
        for i in range(config.paint_chips):
            chip = {
                'position': Vector((
                    random.uniform(-2, 2),
                    random.uniform(-1, 1),
                    random.uniform(0.2, 1.4)
                )),
                'radius': random.uniform(0.005, 0.02)
            }
            chips.append(chip)

        # Apply to vertices
        for i, loop in enumerate(mesh.loops):
            vert = mesh.vertices[loop.vertex_index]
            pos = vert.co

            chip_value = 0.0
            for chip in chips:
                dist = (pos - chip['position']).length
                if dist < chip['radius']:
                    chip_value = 1.0

            # Blend with existing
            existing = chips_layer.data[i].color
            chips_layer.data[i].color = (
                max(existing[0], chip_value),
                max(existing[1], chip_value),
                max(existing[2], chip_value),
                1.0
            )

    def _apply_sun_fade(
        self,
        vehicle: bpy.types.Object,
        config: WeatheringConfig
    ) -> None:
        """Apply sun fading to materials."""
        fade_amount = config.sun_fade

        for slot in vehicle.material_slots:
            if slot.material and slot.material.use_nodes:
                # Find the base color and desaturate/darken
                for node in slot.material.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        base_color = node.inputs.get("Base Color")
                        if base_color:
                            color = base_color.default_value[:3]
                            # Desaturate and slightly darken
                            gray = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
                            faded = tuple(
                                c * (1 - fade_amount) + gray * fade_amount
                                for c in color
                            )
                            base_color.default_value = (*faded, 1.0)

    def _apply_clear_coat_wear(
        self,
        vehicle: bpy.types.Object,
        config: WeatheringConfig
    ) -> None:
        """Apply clear coat degradation."""
        wear = config.clear_coat_wear

        for slot in vehicle.material_slots:
            if slot.material and slot.material.use_nodes:
                for node in slot.material.node_tree.nodes:
                    if node.type == 'BSDF_PRINCIPLED':
                        # Increase roughness where clear coat is worn
                        roughness = node.inputs.get("Roughness")
                        if roughness:
                            roughness.default_value = min(1.0, roughness.default_value + wear * 0.3)

                        # Reduce clearcoat
                        clearcoat = node.inputs.get("Clearcoat")
                        if clearcoat:
                            clearcoat.default_value = max(0, clearcoat.default_value - wear)

    def _apply_wheel_well_grime(
        self,
        vehicle: bpy.types.Object,
        config: WeatheringConfig
    ) -> None:
        """Apply grime to wheel well areas."""
        grime_layer = self._get_or_create_vertex_color(vehicle, "GrimeMask")

        if not grime_layer or vehicle.type != 'MESH':
            return

        mesh = vehicle.data
        bbox = vehicle.bound_box
        min_z = min(v[2] for v in bbox)

        for i, loop in enumerate(mesh.loops):
            vert = mesh.vertices[loop.vertex_index]
            pos = vert.co

            # Wheel wells are lower and on sides
            grime = 0.0
            if pos.z < min_z + 0.3 and abs(pos.y) > 0.3:
                grime = config.dirt_level * 1.5

            grime_layer.data[i].color = (grime, grime * 0.8, grime * 0.5, 1.0)

    def _apply_headlight_haze(
        self,
        vehicle: bpy.types.Object,
        config: WeatheringConfig
    ) -> None:
        """Apply headlight clouding/haze."""
        haze = config.headlight_haze

        # Find headlight materials
        for slot in vehicle.material_slots:
            if slot.material and 'headlight' in slot.material.name.lower():
                if slot.material.use_nodes:
                    for node in slot.material.node_tree.nodes:
                        if node.type == 'BSDF_PRINCIPLED':
                            # Increase roughness for haze
                            roughness = node.inputs.get("Roughness")
                            if roughness:
                                roughness.default_value = min(0.8, roughness.default_value + haze * 0.6)

                            # Reduce transmission
                            transmission = node.inputs.get("Transmission")
                            if transmission:
                                transmission.default_value = max(0, transmission.default_value - haze * 0.5)

    def _get_or_create_scratch_material(self, depth: float) -> bpy.types.Material:
        """Create a scratch material."""
        name = f"vehicle_scratch_{depth:.2f}"

        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        # Create scratch appearance (exposed primer/metal)
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Gray primer color
            bsdf.inputs["Base Color"].default_value = (0.4, 0.4, 0.42, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.3
            bsdf.inputs["Roughness"].default_value = 0.7

        return mat

    def _get_or_create_rust_material(self, severity: RustSeverity) -> bpy.types.Material:
        """Create a rust material."""
        name = f"vehicle_rust_{severity.value}"

        if name in bpy.data.materials:
            return bpy.data.materials[name]

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if severity == RustSeverity.SURFACE:
                color = (0.6, 0.45, 0.35, 1.0)
            elif severity == RustSeverity.SPOT:
                color = (0.55, 0.35, 0.25, 1.0)
            elif severity == RustSeverity.HEAVY:
                color = (0.45, 0.25, 0.15, 1.0)
            else:  # CANCER
                color = (0.35, 0.18, 0.1, 1.0)

            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Metallic"].default_value = 0.1
            bsdf.inputs["Roughness"].default_value = 0.9

        return mat

    def generate_dirt_texture(
        self,
        vehicle: bpy.types.Object,
        resolution: int = 1024
    ) -> bpy.types.Image:
        """Generate a baked dirt texture for the vehicle."""
        name = f"{vehicle.name}_dirt_texture"

        if name in bpy.data.images:
            return bpy.data.images[name]

        # Create image
        image = bpy.data.images.new(name, resolution, resolution, alpha=True)

        # Generate procedural dirt pattern
        pixels = []
        for y in range(resolution):
            for x in range(resolution):
                # Simple procedural noise
                nx, ny = x / resolution, y / resolution

                # Perlin-like noise (simplified)
                noise = random.uniform(0.3, 0.7)

                # Add streaks (dirt runs downward)
                streak = sin(nx * 20 + random.uniform(-0.5, 0.5)) * 0.1

                dirt = noise + streak
                dirt = max(0, min(1, dirt))

                pixels.extend([dirt, dirt, dirt * 0.8, 1.0])

        image.pixels = pixels
        image.pack()

        return image


# === CONVENIENCE FUNCTIONS ===

def apply_weathering(
    vehicle: bpy.types.Object,
    preset: str = "daily_driver",
    custom_config: Optional[WeatheringConfig] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Convenience function to apply weathering.

    Args:
        vehicle: The vehicle object
        preset: Weathering preset name
        custom_config: Override with custom config
        seed: Random seed

    Returns:
        Dictionary with applied effects
    """
    config = custom_config or WEATHERING_PRESETS.get(preset, WEATHERING_PRESETS["daily_driver"])
    system = WeatheringSystem()
    return system.apply_weathering(vehicle, config, seed)


def get_weathering_preset(preset_name: str) -> WeatheringConfig:
    """Get a weathering preset by name."""
    return WEATHERING_PRESETS.get(preset_name, WEATHERING_PRESETS["daily_driver"])


def list_weathering_presets() -> List[str]:
    """List available weathering presets."""
    return list(WEATHERING_PRESETS.keys())
