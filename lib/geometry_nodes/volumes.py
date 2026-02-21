"""
Volumes - Volumetric rendering utilities.

Based on CGMatter tutorials for volumetric effects. Provides utilities
for creating and configuring volumetric materials like fog, smoke,
clouds, and god rays.

Usage:
    # Create fog material
    fog = VolumetricTools.create_fog_material(density=0.5)

    # Create smoke material
    smoke = VolumetricTools.create_smoke_material(density=10.0)

    # Create god rays material
    rays = VolumetricTools.create_god_rays_material(density=0.3, anisotropy=0.7)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import bpy
from mathutils import Color, Vector

if TYPE_CHECKING:
    from bpy.types import Material, Node, NodeTree, Object

    from .node_builder import NodeTreeBuilder


class VolumetricTools:
    """
    Volumetric rendering utilities.

    Provides tools for creating and configuring volume materials
    for effects like fog, smoke, clouds, and light shafts.

    All methods work with Blender's Principled Volume BSDF shader.
    """

    # Density presets for common effects
    DENSITY_PRESETS = {
        "thin_fog": 0.1,
        "fog": 0.3,
        "thick_fog": 1.0,
        "mist": 0.05,
        "clouds": 10.0,
        "cumulus": 5.0,
        "smoke": 50.0,
        "heavy_smoke": 100.0,
        "steam": 20.0,
        "dust": 2.0,
    }

    # Anisotropy presets
    ANISOTROPY_PRESETS = {
        "isotropic": 0.0,  # Even scattering
        "forward": 0.5,  # Light passes through
        "strong_forward": 0.8,  # Strong forward scattering
        "backward": -0.3,  # Light reflects back
        "god_rays": 0.7,  # Good for light shafts
    }

    @staticmethod
    def create_fog_material(
        density: float = 0.5,
        anisotropy: float = 0.0,
        color: tuple[float, float, float] = (0.9, 0.9, 0.95),
        absorption_strength: float = 0.0,
        material_name: str = "FogMaterial",
    ) -> Optional[Material]:
        """
        Create a fog volume material.

        Creates a Principled Volume material configured for fog effects.
        Uses relatively low density for atmospheric haze.

        Args:
            density: Volume density (default 0.5).
                    - 0.1: Thin fog, distant objects visible
                    - 0.5: Medium fog
                    - 1.0+: Thick fog, nearby objects obscured
            anisotropy: Scattering anisotropy (-1 to 1, default 0.0).
                       - 0: Isotropic (even scattering)
                       - Positive: Forward scattering (light passes through)
                       - Negative: Backward scattering (light reflects)
            color: Fog color (default light blue-white).
            absorption_strength: Absorption multiplier (default 0.0).
            material_name: Name for the material.

        Returns:
            Created Material, or None if creation failed.

        Example:
            >>> fog = VolumetricTools.create_fog_material(
            ...     density=0.3,
            ...     anisotropy=0.2,
            ...     color=(0.95, 0.95, 1.0)
            ... )
        """
        if not hasattr(bpy, "data"):
            return None

        if material_name in bpy.data.materials:
            return bpy.data.materials[material_name]

        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create output node
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (600, 0)

        # Create Principled Volume BSDF
        volume = nodes.new("ShaderNodeVolumePrincipled")
        volume.location = (300, 0)

        # Configure volume parameters
        volume.inputs["Density"].default_value = density
        volume.inputs["Anisotropy"].default_value = anisotropy
        volume.inputs["Color"].default_value = (*color, 1.0)
        volume.inputs["Absorption Strength"].default_value = absorption_strength

        # Connect nodes
        links.new(volume.outputs["Volume"], output.inputs["Volume"])

        return material

    @staticmethod
    def create_smoke_material(
        density: float = 10.0,
        color: tuple[float, float, float] = (0.2, 0.2, 0.2),
        anisotropy: float = 0.3,
        blackbody_intensity: float = 0.0,
        blackbody_tint: tuple[float, float, float] = (1.0, 0.5, 0.1),
        material_name: str = "SmokeMaterial",
    ) -> Optional[Material]:
        """
        Create a smoke volume material.

        Creates a Principled Volume material configured for smoke
        and fire effects with higher density and optional emission.

        Args:
            density: Volume density (default 10.0).
                    - 10-50: Visible smoke
                    - 50-100: Thick smoke
                    - 100+: Heavy smoke, dense clouds
            color: Smoke color (default dark gray).
            anisotropy: Scattering anisotropy (default 0.3).
            blackbody_intensity: Emission intensity for fire glow (default 0.0).
            blackbody_tint: Color tint for emission (default orange).
            material_name: Name for the material.

        Returns:
            Created Material, or None.

        Example:
            >>> # Create smoke with fire emission
            >>> smoke = VolumetricTools.create_smoke_material(
            ...     density=30.0,
            ...     blackbody_intensity=0.5
            ... )
        """
        if not hasattr(bpy, "data"):
            return None

        if material_name in bpy.data.materials:
            return bpy.data.materials[material_name]

        material = bpy.data.materials.new(name=material_name)
        material.use_nodes = True

        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()

        # Output
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (800, 0)

        # Principled Volume
        volume = nodes.new("ShaderNodeVolumePrincipled")
        volume.location = (400, 0)
        volume.inputs["Density"].default_value = density
        volume.inputs["Color"].default_value = (*color, 1.0)
        volume.inputs["Anisotropy"].default_value = anisotropy

        # Blackbody emission for fire
        if blackbody_intensity > 0:
            # Add emission through the temperature input
            volume.inputs["Blackbody Intensity"].default_value = blackbody_intensity
            volume.inputs["Blackbody Tint"].default_value = (*blackbody_tint, 1.0)

        links.new(volume.outputs["Volume"], output.inputs["Volume"])

        return material

    @staticmethod
    def create_god_rays_material(
        density: float = 0.3,
        anisotropy: float = 0.7,
        color: tuple[float, float, float] = (1.0, 0.98, 0.9),
        material_name: str = "GodRaysMaterial",
    ) -> Optional[Material]:
        """
        Create god rays / light shaft material.

        Creates a volume material optimized for visible light beams
        with strong forward scattering.

        Args:
            density: Volume density (default 0.3, keep low for visibility).
            anisotropy: Forward scattering (default 0.7).
                       Higher values create more defined shafts.
            color: Light color (default warm white).
            material_name: Name for the material.

        Returns:
            Created Material, or None.

        Example:
            >>> rays = VolumetricTools.create_god_rays_material(
            ...     density=0.2,
            ...     anisotropy=0.8
            ... )
        """
        return VolumetricTools.create_fog_material(
            density=density,
            anisotropy=anisotropy,
            color=color,
            material_name=material_name,
        )

    @staticmethod
    def create_cloud_material(
        density: float = 5.0,
        anisotropy: float = 0.2,
        color: tuple[float, float, float] = (1.0, 1.0, 1.0),
        material_name: str = "CloudMaterial",
    ) -> Optional[Material]:
        """
        Create a cloud volume material.

        Args:
            density: Volume density (default 5.0).
            anisotropy: Scattering anisotropy (default 0.2).
            color: Cloud color (default white).
            material_name: Name for the material.

        Returns:
            Created Material, or None.
        """
        return VolumetricTools.create_fog_material(
            density=density,
            anisotropy=anisotropy,
            color=color,
            material_name=material_name,
        )

    @staticmethod
    def create_dust_material(
        density: float = 2.0,
        color: tuple[float, float, float] = (0.9, 0.85, 0.7),
        anisotropy: float = 0.1,
        material_name: str = "DustMaterial",
    ) -> Optional[Material]:
        """
        Create atmospheric dust material.

        Args:
            density: Volume density (default 2.0).
            color: Dust color (default warm beige).
            anisotropy: Scattering anisotropy (default 0.1).
            material_name: Name for the material.

        Returns:
            Created Material, or None.
        """
        return VolumetricTools.create_fog_material(
            density=density,
            anisotropy=anisotropy,
            color=color,
            material_name=material_name,
        )

    @staticmethod
    def add_noise_to_density(
        material: Material,
        scale: float = 1.0,
        detail: float = 3.0,
        distortion: float = 0.0,
        multiply_factor: float = 1.0,
    ) -> Optional[NodeTree]:
        """
        Add noise texture to volume density.

        Modifies an existing volume material to use noise-based
        density variation for more natural appearance.

        Args:
            material: Material to modify.
            scale: Noise scale (default 1.0).
            detail: Noise detail level (default 3.0).
            distortion: Noise distortion (default 0.0).
            multiply_factor: Factor to multiply density by noise.

        Returns:
            Modified node tree, or None.
        """
        if material is None or not material.use_nodes:
            return None

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Find Principled Volume node
        volume_node = None
        for node in nodes:
            if node.type == "ShaderNodeVolumePrincipled":
                volume_node = node
                break

        if volume_node is None:
            return None

        # Add position input
        position = nodes.new("ShaderNodeTexCoord")
        position.location = (-600, 0)

        # Add noise texture
        noise = nodes.new("ShaderNodeTexNoise")
        noise.location = (-400, 0)
        noise.inputs["Scale"].default_value = scale
        noise.inputs["Detail"].default_value = detail
        noise.inputs["Distortion"].default_value = distortion

        # Add math node to multiply
        multiply = nodes.new("ShaderNodeMath")
        multiply.location = (-200, 0)
        multiply.operation = "MULTIPLY"
        multiply.inputs[1].default_value = multiply_factor

        # Store original density value
        original_density = volume_node.inputs["Density"].default_value

        # Create value node for base density
        density_value = nodes.new("ShaderNodeValue")
        density_value.location = (-400, -100)
        density_value.outputs[0].default_value = original_density

        # Connect nodes
        links.new(position.outputs["Generated"], noise.inputs["Vector"])
        links.new(noise.outputs["Fac"], multiply.inputs[0])
        links.new(density_value.outputs[0], multiply.inputs[1])
        links.new(multiply.outputs[0], volume_node.inputs["Density"])

        return material.node_tree

    @staticmethod
    def add_color_ramp(
        material: Material,
        positions: list[tuple[float, tuple[float, float, float, float]]],
        color_input: str = "noise",
        scale: float = 1.0,
    ) -> Optional[NodeTree]:
        """
        Add color ramp to volume for gradient coloring.

        Args:
            material: Material to modify.
            positions: List of (position, color) tuples for ramp stops.
                      Position is 0-1, color is RGBA.
            color_input: Input for color ramp ("noise", "position", "density").
            scale: Scale for noise input.

        Returns:
            Modified node tree, or None.
        """
        if material is None or not material.use_nodes:
            return None

        nodes = material.node_tree.nodes
        links = material.node_tree.links

        # Find volume node
        volume_node = None
        for node in nodes:
            if node.type == "ShaderNodeVolumePrincipled":
                volume_node = node
                break

        if volume_node is None:
            return None

        # Create input based on type
        if color_input == "noise":
            position = nodes.new("ShaderNodeTexCoord")
            position.location = (-800, 0)

            noise = nodes.new("ShaderNodeTexNoise")
            noise.location = (-600, 0)
            noise.inputs["Scale"].default_value = scale

            links.new(position.outputs["Generated"], noise.inputs["Vector"])
            input_output = noise.outputs["Fac"]
        elif color_input == "position":
            position = nodes.new("ShaderNodeTexCoord")
            position.location = (-600, 0)
            separate = nodes.new("ShaderNodeSeparateXYZ")
            separate.location = (-400, 0)
            links.new(position.outputs["Generated"], separate.inputs["Vector"])
            input_output = separate.outputs["Z"]
        else:
            return None

        # Create color ramp
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.location = (-200, 0)

        # Configure color ramp stops
        # Note: Color ramp configuration requires Blender API
        color_ramp = ramp.color_ramp
        color_ramp.elements.clear()

        for pos, color in positions:
            element = color_ramp.elements.new(pos)
            element.color = color

        # Connect
        links.new(input_output, ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], volume_node.inputs["Color"])

        return material.node_tree

    @staticmethod
    def configure_volume_object(
        obj: Object,
        material: Material,
        volume_collection: Optional[str] = None,
    ) -> None:
        """
        Configure an object for volume rendering.

        Sets up an object to use volume material properly.

        Args:
            obj: Object to configure.
            material: Volume material to assign.
            volume_collection: Optional collection for volume objects.
        """
        if obj is None or material is None:
            return

        # Assign material
        if obj.data is not None and hasattr(obj.data, "materials"):
            if len(obj.data.materials) == 0:
                obj.data.materials.append(material)
            else:
                obj.data.materials[0] = material

        # Move to collection if specified
        if volume_collection and hasattr(bpy, "data"):
            if volume_collection in bpy.data.collections:
                collection = bpy.data.collections[volume_collection]
                # Unlink from current collections
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                # Link to volume collection
                collection.objects.link(obj)

    @staticmethod
    def create_volume_cube(
        size: float = 10.0,
        material: Optional[Material] = None,
        location: tuple[float, float, float] = (0, 0, 0),
        name: str = "VolumeCube",
    ) -> Optional[Object]:
        """
        Create a cube for volume rendering.

        Args:
            size: Cube size.
            material: Volume material to assign.
            location: World position.
            name: Object name.

        Returns:
            Created Object, or None.
        """
        if not hasattr(bpy, "data"):
            return None

        # Create mesh data
        mesh = bpy.data.meshes.new(f"{name}_mesh")

        # Create cube vertices and faces
        half = size / 2
        vertices = [
            (-half, -half, -half),
            (half, -half, -half),
            (half, half, -half),
            (-half, half, -half),
            (-half, -half, half),
            (half, -half, half),
            (half, half, half),
            (-half, half, half),
        ]
        faces = [
            (0, 1, 2, 3),
            (4, 5, 6, 7),
            (0, 1, 5, 4),
            (2, 3, 7, 6),
            (0, 3, 7, 4),
            (1, 2, 6, 5),
        ]
        mesh.from_pydata(vertices, [], faces)
        mesh.update()

        # Create object
        obj = bpy.data.objects.new(name, mesh)
        obj.location = location

        # Link to scene
        bpy.context.collection.objects.link(obj)

        # Assign material
        if material:
            obj.data.materials.append(material)

        return obj


class VolumePreset:
    """Pre-configured volume setups for common effects."""

    @staticmethod
    def morning_fog() -> Optional[Material]:
        """Create morning fog preset."""
        return VolumetricTools.create_fog_material(
            density=0.15,
            anisotropy=0.2,
            color=(0.95, 0.97, 1.0),
            material_name="MorningFog",
        )

    @staticmethod
    def campfire_smoke() -> Optional[Material]:
        """Create campfire smoke preset."""
        return VolumetricTools.create_smoke_material(
            density=25.0,
            color=(0.3, 0.3, 0.3),
            blackbody_intensity=0.3,
            material_name="CampfireSmoke",
        )

    @staticmethod
    def underwater_dust() -> Optional[Material]:
        """Create underwater dust particles preset."""
        return VolumetricTools.create_dust_material(
            density=3.0,
            color=(0.6, 0.8, 0.9),
            anisotropy=0.4,
            material_name="UnderwaterDust",
        )

    @staticmethod
    def cathedral_rays() -> Optional[Material]:
        """Create cathedral god rays preset."""
        return VolumetricTools.create_god_rays_material(
            density=0.25,
            anisotropy=0.8,
            color=(1.0, 0.95, 0.85),
            material_name="CathedralRays",
        )

    @staticmethod
    def fluffy_clouds() -> Optional[Material]:
        """Create fluffy cumulus clouds preset."""
        material = VolumetricTools.create_cloud_material(
            density=3.0,
            anisotropy=0.3,
            color=(1.0, 1.0, 1.0),
            material_name="FluffyClouds",
        )
        if material:
            VolumetricTools.add_noise_to_density(
                material,
                scale=0.5,
                detail=5.0,
                multiply_factor=2.0,
            )
        return material

    @staticmethod
    def toxic_fog() -> Optional[Material]:
        """Create toxic/green fog preset."""
        return VolumetricTools.create_fog_material(
            density=0.8,
            anisotropy=0.0,
            color=(0.6, 0.9, 0.5),
            absorption_strength=0.5,
            material_name="ToxicFog",
        )


# Convenience functions
def create_quick_fog(density: float = 0.5) -> Optional[Material]:
    """Quick fog creation."""
    return VolumetricTools.create_fog_material(density=density)


def create_quick_smoke(density: float = 10.0) -> Optional[Material]:
    """Quick smoke creation."""
    return VolumetricTools.create_smoke_material(density=density)


def create_quick_cloud() -> Optional[Material]:
    """Quick cloud creation with noise."""
    return VolumePreset.fluffy_clouds()
