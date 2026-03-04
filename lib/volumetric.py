"""
Volumetric Effects Module - Codified from Tutorials 29, 33

Implements volumetric projector effects, god rays, and fog systems.
Based on Default Cube tutorials: https://youtu.be/A-RQIFYnS2U, https://youtu.be/F8pqNeVam54

Usage:
    from lib.volumetric import VolumetricProjector, WorldFog, GodRays

    # Create projector effect
    projector = VolumetricProjector(scene)
    projector.setup_video_projection("path/to/video.mp4", spotlight)
    projector.set_aspect_ratio(1920, 1080)

    # Add world fog
    fog = WorldFog(scene)
    fog.set_density(0.1)
    fog.set_anisotropy(0.5)
"""

from __future__ import annotations
import bpy
from typing import Optional
from pathlib import Path


class WorldFog:
    """
    Global volumetric fog using world volume scatter.

    Cross-references:
    - KB Section 25: Volumetric Lighting (Southern Shotty)
    - KB Section 28: Volume step for cinematic renders
    - KB Section 29, 33: Volumetric Projector Effect
    """

    def __init__(self, scene: Optional[bpy.types.Scene] = None):
        self.scene = scene or bpy.context.scene
        self._setup_world_volume()

    def _setup_world_volume(self) -> None:
        """Ensure world has volume output."""
        world = self.scene.world
        if not world:
            world = bpy.data.worlds.new("VolumetricWorld")
            self.scene.world = world

        world.use_nodes = True

        # Check for existing volume output
        output = world.node_tree.nodes.get("Volume Output")
        if not output:
            # Try to find output node
            for node in world.node_tree.nodes:
                if node.type == 'OUTPUT_WORLD':
                    output = node
                    break

        if not output:
            output = world.node_tree.nodes.new("ShaderNodeOutputWorld")
            output.name = "Volume Output"

    def set_density(self, density: float) -> "WorldFog":
        """
        Set fog density.

        Args:
            density: 0.01 = subtle haze, 0.05 = visible fog, 0.1 = strong god rays, 0.5+ = dense fog
        """
        world = self.scene.world
        node_tree = world.node_tree

        # Find or create volume scatter
        scatter = None
        for node in node_tree.nodes:
            if node.type == 'SHADER_VOLUME':
                if hasattr(node, 'node_tree') and 'scatter' in node.node_tree.name.lower():
                    scatter = node
                    break

        if not scatter:
            scatter = node_tree.nodes.new("ShaderNodeVolumeScatter")
            scatter.name = "Volume Scatter"

        scatter.inputs['Density'].default_value = density
        return self

    def set_anisotropy(self, anisotropy: float) -> "WorldFog":
        """
        Set light scattering direction.

        Args:
            anisotropy: -1 = backward scatter, 0 = isotropic, 0.5+ = forward scatter (god rays)
        """
        world = self.scene.world
        node_tree = world.node_tree

        for node in node_tree.nodes:
            if node.type == 'SHADER_VOLUME':
                if 'Anisotropy' in node.inputs:
                    node.inputs['Anisotropy'].default_value = anisotropy
        return self

    def set_color(self, color: tuple) -> "WorldFog":
        """Set fog color (default white)."""
        world = self.scene.world
        node_tree = world.node_tree

        for node in node_tree.nodes:
            if node.type == 'SHADER_VOLUME':
                node.inputs['Color'].default_value = (*color, 1.0) if len(color) == 3 else color
        return self


class VolumetricProjector:
    """
    Video projection through volumetric fog creating god rays.

    Cross-references:
    - KB Section 29, 33: Volumetric Projector Effect (Default Cube)
    - KB Section 25: HDRI as fill only
    - lib/nodekit.py: For node tree building
    """

    def __init__(self, scene: Optional[bpy.types.Scene] = None):
        self.scene = scene or bpy.context.scene
        self.spotlight: Optional[bpy.types.Object] = None
        self.video_texture: Optional[bpy.types.Image] = None

    def create_spotlight(self, name: str = "ProjectorLight") -> bpy.types.Object:
        """
        Create a spotlight for video projection.

        Returns:
            The spotlight object
        """
        bpy.ops.object.light_add(type='SPOT')
        self.spotlight = bpy.context.active_object
        self.spotlight.name = name

        # Set reasonable defaults
        light = self.spotlight.data
        light.energy = 1000  # Power in watts
        light.shadow_soft_size = 0.1

        return self.spotlight

    def load_video_texture(self, video_path: str | Path) -> bpy.types.Image:
        """
        Load video file as texture.

        Args:
            video_path: Path to video file

        Returns:
            The image/texture object
        """
        path = str(video_path)

        # Check if already loaded
        for img in bpy.data.images:
            if img.filepath == path:
                self.video_texture = img
                return img

        # Load new video
        self.video_texture = bpy.data.images.load(path, check_existing=True)
        self.video_texture.source = 'MOVIE'

        # Enable auto-refresh for animation
        # Note: This is set in the Image User when used in nodes

        return self.video_texture

    def setup_video_projection(
        self,
        video_path: str | Path,
        spotlight: Optional[bpy.types.Object] = None
    ) -> bpy.types.NodeTree:
        """
        Set up video texture on spotlight for projection through fog.

        Args:
            video_path: Path to video file
            spotlight: Spotlight to use (creates one if None)

        Returns:
            The spotlight's node tree
        """
        if spotlight:
            self.spotlight = spotlight
        elif not self.spotlight:
            self.create_spotlight()

        # Load video
        self.load_video_texture(video_path)

        # Setup spotlight nodes
        light = self.spotlight.data
        light.use_nodes = True
        node_tree = light.node_tree

        # Clear existing
        node_tree.nodes.clear()

        # Create emission with video texture
        emission = node_tree.nodes.new("ShaderNodeEmission")
        tex_image = node_tree.nodes.new("ShaderNodeTexImage")
        output = node_tree.nodes.new("ShaderNodeOutputLight")

        # Configure texture node
        tex_image.image = self.video_texture
        tex_image.label = "Video Projection"

        # Enable auto-refresh for animation
        tex_image.image_user.use_auto_refresh = True
        tex_image.image_user.use_cyclic = True

        # Fix color space (KB Section 33)
        # Video files expect sRGB display, Blender uses linear
        # AGX base gives correct appearance
        self.video_texture.colorspace_settings.name = 'AgX Base sRGB'

        # Link nodes
        node_tree.links.new(tex_image.outputs['Color'], emission.inputs['Color'])
        node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

        return node_tree

    def set_aspect_ratio(self, width: int, height: int) -> "VolumetricProjector":
        """
        Fix stretched video by setting correct aspect ratio.

        Args:
            width: Video width in pixels
            height: Video height in pixels

        KB Reference: Section 33 - Aspect Ratio Fix with Object Scale
        """
        if not self.spotlight:
            raise RuntimeError("Create spotlight first")

        aspect = width / height

        # Apply to spotlight scale
        self.spotlight.scale.x = aspect
        self.spotlight.scale.y = 1.0
        self.spotlight.scale.z = 1.0

        return self

    def set_power(self, watts: float) -> "VolumetricProjector":
        """Set spotlight power (500-2000W typical for projection)."""
        if self.spotlight:
            self.spotlight.data.energy = watts
        return self


class GodRays:
    """
    Simplified god ray creation combining fog and light placement.

    Cross-references:
    - KB Section 25: Volumetric lighting placement
    - KB Section 28: Volume step for cinematic renders
    - KB Section 33: Complete god ray setup
    """

    @staticmethod
    def create_from_spotlight(
        spotlight: bpy.types.Object,
        density: float = 0.1,
        anisotropy: float = 0.5
    ) -> WorldFog:
        """
        Create god rays from a spotlight.

        Args:
            spotlight: The spotlight creating the rays
            density: Fog density (0.05-0.1 for visible rays)
            anisotropy: Forward scatter amount (0.5+ for rays)

        Returns:
            WorldFog instance for further configuration
        """
        fog = WorldFog(spotlight.scene)
        fog.set_density(density)
        fog.set_anisotropy(anisotropy)
        return fog

    @staticmethod
    def optimal_light_placement() -> dict:
        """
        Get guidelines for light placement to maximize god rays.

        KB Reference: Section 25 - Light placement for volumetric
        """
        return {
            "front_of_camera": "Visible rays in frame",
            "behind_objects": "Silhouette glow effect",
            "side_angle": "Dramatic diagonal beams",
            "density_range": "0.01-0.1 (subtle to strong)",
            "anisotropy_range": "0.0-0.8 (isotropic to forward)"
        }


# Convenience functions
def create_fog_scene(density: float = 0.05, anisotropy: float = 0.5) -> WorldFog:
    """Quick setup for foggy scene."""
    fog = WorldFog()
    fog.set_density(density)
    fog.set_anisotropy(anisotropy)
    return fog


def create_projector_effect(
    video_path: str | Path,
    resolution: tuple[int, int] = (1920, 1080)
) -> tuple[VolumetricProjector, WorldFog]:
    """
    Complete projector effect setup.

    Args:
        video_path: Path to video file
        resolution: Video resolution (width, height)

    Returns:
        Tuple of (projector, fog) for further configuration
    """
    projector = VolumetricProjector()
    projector.create_spotlight()
    projector.setup_video_projection(video_path)
    projector.set_aspect_ratio(*resolution)

    fog = WorldFog()
    fog.set_density(0.1)
    fog.set_anisotropy(0.5)

    return projector, fog
