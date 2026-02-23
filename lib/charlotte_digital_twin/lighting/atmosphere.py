"""
Atmospheric Effects

Creates atmospheric effects for realistic outdoor scenes:
- Distance haze
- Volumetric fog
- Morning mist
- Pollution/haze layers
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Tuple
import math

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


class FogType(Enum):
    """Types of atmospheric fog."""
    DISTANCE_HAZE = "distance_haze"
    VOLUMETRIC_FOG = "volumetric_fog"
    GROUND_MIST = "ground_mist"
    POLLUTION = "pollution"
    CLOUD_LAYER = "cloud_layer"


@dataclass
class AtmosphereConfig:
    """Configuration for atmospheric effects."""
    # Distance haze
    haze_density: float = 0.0005  # Exponential falloff
    haze_start_distance: float = 100.0  # Meters before haze starts
    haze_color: Tuple[float, float, float] = (0.7, 0.75, 0.85)

    # Volumetric fog
    fog_density: float = 0.0
    fog_height: float = 50.0  # Maximum height
    fog_anisotropy: float = 0.0  # Light scattering direction

    # Ground mist
    mist_density: float = 0.0
    mist_height: float = 5.0  # Only near ground
    mist_falloff: float = 0.5

    # General
    sun_influence: float = 0.5  # How much sun affects fog color


# Preset configurations
ATMOSPHERE_PRESETS = {
    "clear": AtmosphereConfig(
        haze_density=0.0002,
        haze_start_distance=200.0,
        fog_density=0.0,
    ),
    "light_haze": AtmosphereConfig(
        haze_density=0.0005,
        haze_start_distance=100.0,
        fog_density=0.0,
    ),
    "hazy": AtmosphereConfig(
        haze_density=0.001,
        haze_start_distance=50.0,
        fog_density=0.0001,
    ),
    "foggy": AtmosphereConfig(
        haze_density=0.002,
        haze_start_distance=20.0,
        fog_density=0.001,
    ),
    "morning_mist": AtmosphereConfig(
        haze_density=0.0003,
        haze_start_distance=80.0,
        mist_density=0.002,
        mist_height=3.0,
    ),
    "polluted": AtmosphereConfig(
        haze_density=0.0015,
        haze_start_distance=30.0,
        haze_color=(0.75, 0.72, 0.7),
        fog_density=0.0005,
    ),
}


class AtmosphericEffects:
    """
    Creates atmospheric effects in the scene.

    Uses Blender's volumetric shader system for fog and haze.
    """

    def __init__(self):
        """Initialize atmospheric effects."""
        self._volume_obj = None

    def add_distance_haze(
        self,
        density: float = 0.0005,
        start_distance: float = 100.0,
        color: Tuple[float, float, float] = (0.7, 0.75, 0.85),
    ) -> bool:
        """
        Add simple distance-based haze.

        This uses world volumetrics for a subtle distance fade.

        Args:
            density: Haze density (lower = more subtle)
            start_distance: Distance before haze starts (meters)
            color: Haze color (typically slight blue/purple)

        Returns:
            True if successful
        """
        if not BLENDER_AVAILABLE:
            return False

        world = bpy.context.scene.world
        if not world or not world.use_nodes:
            return False

        nodes = world.node_tree.nodes
        links = world.node_tree.links

        # Add volume output
        # Find output node
        output_node = None
        for node in nodes:
            if node.type == "OUTPUT_WORLD":
                output_node = node
                break

        if not output_node:
            output_node = nodes.new("ShaderNodeOutputWorld")

        # Check if volume socket exists
        if "Volume" not in output_node.inputs:
            print("[Atmosphere] Volume output not available in this Blender version")
            return False

        # Create volume scatter for haze
        scatter = nodes.new("ShaderNodeVolumeScatter")
        scatter.location = (-400, -300)
        scatter.inputs["Density"].default_value = density
        scatter.inputs["Color"].default_value = (*color, 1.0)
        scatter.inputs["Anisotropy"].default_value = 0.0

        # Link to volume output
        links.new(scatter.outputs["Volume"], output_node.inputs["Volume"])

        return True

    def add_volumetric_fog(
        self,
        density: float = 0.001,
        height: float = 50.0,
        anisotropy: float = 0.0,
    ) -> bool:
        """
        Add volumetric fog with height falloff.

        Args:
            density: Fog density
            height: Maximum height of fog layer
            anisotropy: Light scattering direction (-1 to 1)

        Returns:
            True if successful
        """
        if not BLENDER_AVAILABLE:
            return False

        world = bpy.context.scene.world
        if not world or not world.use_nodes:
            return False

        nodes = world.node_tree.nodes
        links = world.node_tree.links

        # Find output node
        output_node = None
        for node in nodes:
            if node.type == "OUTPUT_WORLD":
                output_node = node
                break

        if not output_node:
            return False

        # Create coordinate and math nodes for height-based density
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-800, -300)

        separate = nodes.new("ShaderNodeSeparateXYZ")
        separate.location = (-600, -300)
        links.new(tex_coord.outputs["Generated"], separate.inputs["Vector"])

        # Height falloff (Z > height = no fog)
        greater = nodes.new("ShaderNodeMath")
        greater.operation = "LESS_THAN"
        greater.location = (-400, -400)
        greater.inputs[1].default_value = height / 100.0  # Normalized height
        links.new(separate.outputs["Z"], greater.inputs[0])

        # Multiply with density
        mult = nodes.new("ShaderNodeMath")
        mult.operation = "MULTIPLY"
        mult.location = (-200, -400)
        mult.inputs[1].default_value = density
        links.new(greater.outputs[0], mult.inputs[0])

        # Volume scatter
        scatter = nodes.new("ShaderNodeVolumeScatter")
        scatter.location = (-200, -300)
        scatter.inputs["Color"].default_value = (0.9, 0.92, 0.95, 1.0)
        scatter.inputs["Anisotropy"].default_value = anisotropy
        links.new(mult.outputs[0], scatter.inputs["Density"])

        # Link to volume output
        if "Volume" in output_node.inputs:
            links.new(scatter.outputs["Volume"], output_node.inputs["Volume"])

        return True

    def add_ground_mist(
        self,
        density: float = 0.002,
        height: float = 3.0,
    ) -> bool:
        """
        Add low-lying ground mist.

        Args:
            density: Mist density
            height: Height of mist layer

        Returns:
            True if successful
        """
        if not BLENDER_AVAILABLE:
            return False

        # Create a large cube for the mist volume
        if "Ground_Mist" in bpy.data.objects:
            mist_obj = bpy.data.objects["Ground_Mist"]
        else:
            bpy.ops.mesh.primitive_cube_add(size=1000)
            mist_obj = bpy.context.active_object
            mist_obj.name = "Ground_Mist"

        # Create volume material
        if "Mist_Material" in bpy.data.materials:
            mat = bpy.data.materials["Mist_Material"]
        else:
            mat = bpy.data.materials.new("Mist_Material")
            mat.use_nodes = True

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            nodes.clear()

            # Geometry for position
            geo = nodes.new("ShaderNodeNewGeometry")
            geo.location = (-600, 0)

            separate = nodes.new("ShaderNodeSeparateXYZ")
            separate.location = (-400, 0)
            links.new(geo.outputs["Position"], separate.inputs["Vector"])

            # Height falloff
            divide = nodes.new("ShaderNodeMath")
            divide.operation = "DIVIDE"
            divide.location = (-200, 100)
            divide.inputs[1].default_value = height
            links.new(separate.outputs["Z"], divide.inputs[0])

            # Clamp to 0-1
            clamp = nodes.new("ShaderNodeMath")
            clamp.operation = "CLAMP"
            clamp.location = (-200, -50)
            clamp.inputs[0].default_value = 0
            clamp.inputs[1].default_value = 0
            clamp.inputs[2].default_value = 1
            links.new(divide.outputs[0], clamp.inputs[0])

            # Invert (high Z = low density)
            invert = nodes.new("ShaderNodeMath")
            invert.operation = "SUBTRACT"
            invert.location = (0, 0)
            invert.inputs[0].default_value = 1.0
            links.new(clamp.outputs[0], invert.inputs[1])

            # Multiply by density
            density_mult = nodes.new("ShaderNodeMath")
            density_mult.operation = "MULTIPLY"
            density_mult.location = (100, 0)
            density_mult.inputs[1].default_value = density
            links.new(invert.outputs[0], density_mult.inputs[0])

            # Volume scatter
            scatter = nodes.new("ShaderNodeVolumeScatter")
            scatter.location = (300, 0)
            scatter.inputs["Color"].default_value = (0.95, 0.97, 1.0, 1.0)
            links.new(density_mult.outputs[0], scatter.inputs["Density"])

            # Output
            output = nodes.new("ShaderNodeOutputMaterial")
            output.location = (500, 0)
            links.new(scatter.outputs["Volume"], output.inputs["Volume"])

        mist_obj.data.materials.append(mat)

        # Position at ground level
        mist_obj.location = (0, 0, height / 2)

        return True

    def apply_preset(self, preset_name: str) -> bool:
        """
        Apply an atmospheric preset.

        Args:
            preset_name: Name of preset ("clear", "hazy", "foggy", etc.)

        Returns:
            True if successful
        """
        config = ATMOSPHERE_PRESETS.get(preset_name)
        if not config:
            print(f"[Atmosphere] Unknown preset: {preset_name}")
            return False

        success = True

        if config.haze_density > 0:
            success = success and self.add_distance_haze(
                config.haze_density,
                config.haze_start_distance,
                config.haze_color,
            )

        if config.fog_density > 0:
            success = success and self.add_volumetric_fog(
                config.fog_density,
                config.fog_height,
            )

        if config.mist_density > 0:
            success = success and self.add_ground_mist(
                config.mist_density,
                config.mist_height,
            )

        return success


def add_distance_haze(
    density: float = 0.0005,
    start_distance: float = 100.0,
    color: Tuple[float, float, float] = (0.7, 0.75, 0.85),
) -> bool:
    """Convenience function to add distance haze."""
    effects = AtmosphericEffects()
    return effects.add_distance_haze(density, start_distance, color)


def add_volumetric_fog(
    density: float = 0.001,
    height: float = 50.0,
) -> bool:
    """Convenience function to add volumetric fog."""
    effects = AtmosphericEffects()
    return effects.add_volumetric_fog(density, height)


__all__ = [
    "FogType",
    "AtmosphereConfig",
    "ATMOSPHERE_PRESETS",
    "AtmosphericEffects",
    "add_distance_haze",
    "add_volumetric_fog",
]
