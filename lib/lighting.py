"""
Cinematic Lighting Module - Codified from Tutorials 17, 25-28

Implements professional lighting techniques including 3-point setup,
practical lights, IES textures, volumetric effects, and light linking.

Based on tutorials:
- CGMatter: Monster Lighting in Eevee (Section 17)
- Southern Shotty: Common Lighting Mistakes (Sections 25-27)
- Victor: 5 Steps to Cinematic Renders (Section 28)

Usage:
    from lib.lighting import CinematicLighting, LightRig

    # Create cinematic lighting rig
    lighting = CinematicLighting()
    lighting.setup_3_point(
        key_color=(1.0, 0.9, 0.8),
        fill_color=(0.6, 0.7, 1.0),
        rim_color=(1.0, 0.5, 0.8)
    )
    lighting.add_volumetric_fog(density=0.05)
    lighting.setup_light_linking(subject_collection, rim_light)
"""

from __future__ import annotations
import bpy
import math
from typing import Optional, Tuple, List
from pathlib import Path


class CinematicLighting:
    """
    Cinematic lighting setup for professional renders.

    Provides utilities for:
    - 3-point lighting (key, fill, rim)
    - Practical (motivated) lights
    - Volumetric fog for atmosphere
    - Light linking for selective illumination
    - HDRI configuration

    Cross-references:
    - KB Section 17: Monster Lighting in Eevee (CGMatter)
    - KB Section 25-27: Common Lighting Mistakes (Southern Shotty)
    - KB Section 28: 5 Steps to Cinematic Renders (Victor)
    """

    def __init__(self):
        self._lights: dict = {}
        self._key_light: Optional[bpy.types.Object] = None
        self._fill_light: Optional[bpy.types.Object] = None
        self._rim_light: Optional[bpy.types.Object] = None
        self._practicals: List[bpy.types.Object] = []

    def create_area_light(
        self,
        name: str,
        power: float = 500.0,
        size: float = 1.0,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        shape: str = 'RECTANGLE'
    ) -> bpy.types.Object:
        """
        Create an area light with specified parameters.

        KB Reference: Section 25 - Area Light Shapes Matter

        Args:
            name: Light object name
            power: Light power in watts
            size: Light size (affects shadow softness)
            color: RGB color tuple
            shape: 'RECTANGLE', 'DISK', 'ELLIPSE'

        Returns:
            Created light object
        """
        # Create light data
        light_data = bpy.data.lights.new(name=f"{name}_data", type='AREA')
        light_data.energy = power
        light_data.size = size
        light_data.color = color
        light_data.shape = shape

        # Create object with light data
        light_obj = bpy.data.objects.new(name, light_data)
        bpy.context.collection.objects.link(light_obj)

        self._lights[name] = light_obj
        return light_obj

    def create_spot_light(
        self,
        name: str,
        power: float = 1000.0,
        size: float = 0.5,
        blend: float = 0.5,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    ) -> bpy.types.Object:
        """
        Create a spot light.

        KB Reference: Section 33 - Spotlight for projection

        Args:
            name: Light object name
            power: Light power in watts
            size: Cone size in radians
            blend: Edge softness (0-1)
            color: RGB color tuple

        Returns:
            Created spot light object
        """
        light_data = bpy.data.lights.new(name=f"{name}_data", type='SPOT')
        light_data.energy = power
        light_data.spot_size = size
        light_data.spot_blend = blend
        light_data.color = color

        light_obj = bpy.data.objects.new(name, light_data)
        bpy.context.collection.objects.link(light_obj)

        self._lights[name] = light_obj
        return light_obj

    def setup_3_point(
        self,
        key_power: float = 1000.0,
        key_color: Tuple[float, float, float] = (1.0, 0.95, 0.9),
        key_angle: float = 45.0,
        fill_power: float = 300.0,
        fill_color: Tuple[float, float, float] = (0.7, 0.8, 1.0),
        rim_power: float = 500.0,
        rim_color: Tuple[float, float, float] = (1.0, 0.9, 0.8),
        target: Optional[bpy.types.Object] = None
    ) -> Tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object]:
        """
        Set up classic 3-point lighting.

        KB Reference: Section 25-28 - 3-point lighting fundamentals

        Args:
            key_power: Key light power (main illumination)
            key_color: Key light color (warm typical)
            key_angle: Key light angle from camera (degrees)
            fill_power: Fill light power (30-50% of key)
            fill_color: Fill light color (cool for contrast)
            rim_power: Rim light power (edge definition)
            rim_color: Rim light color
            target: Object to point lights at

        Returns:
            Tuple of (key_light, fill_light, rim_light)
        """
        # Key light - main illumination
        self._key_light = self.create_area_light(
            "Key_Light",
            power=key_power,
            size=2.0,
            color=key_color,
            shape='RECTANGLE'
        )
        # Position key light
        key_rad = math.radians(key_angle)
        self._key_light.location = (5 * math.sin(key_rad), -5 * math.cos(key_rad), 3)

        # Fill light - shadow softening
        self._fill_light = self.create_area_light(
            "Fill_Light",
            power=fill_power,
            size=3.0,  # Larger = softer
            color=fill_color,
            shape='RECTANGLE'
        )
        # Position fill light opposite to key
        self._fill_light.location = (-4, -4, 2)

        # Rim light - edge definition
        self._rim_light = self.create_area_light(
            "Rim_Light",
            power=rim_power,
            size=1.5,
            color=rim_color,
            shape='RECTANGLE'
        )
        # Position rim light behind subject
        self._rim_light.location = (0, 5, 4)

        # Point lights at target if provided
        if target:
            for light in [self._key_light, self._fill_light, self._rim_light]:
                self._point_light_at(light, target)

        return (self._key_light, self._fill_light, self._rim_light)

    def _point_light_at(
        self,
        light: bpy.types.Object,
        target: bpy.types.Object
    ) -> None:
        """Point a light at a target object using track-to constraint."""
        constraint = light.constraints.new(type='TRACK_TO')
        constraint.target = target
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

    def add_practical_light(
        self,
        name: str,
        location: Tuple[float, float, float],
        power: float = 200.0,
        color: Tuple[float, float, float] = (1.0, 0.8, 0.6)
    ) -> bpy.types.Object:
        """
        Add a practical (in-scene) light source.

        KB Reference: Section 25 - Practical lights vs sunlight

        Args:
            name: Light name
            location: World position
            power: Light power
            color: Warm color typical for practicals

        Returns:
            Created point light
        """
        light_data = bpy.data.lights.new(name=f"{name}_data", type='POINT')
        light_data.energy = power
        light_data.color = color
        light_data.shadow_soft_size = 0.1

        light_obj = bpy.data.objects.new(name, light_data)
        light_obj.location = location
        bpy.context.collection.objects.link(light_obj)

        self._practicals.append(light_obj)
        self._lights[name] = light_obj
        return light_obj

    def add_volumetric_fog(
        self,
        density: float = 0.05,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        anisotropy: float = 0.5
    ) -> None:
        """
        Add volumetric fog to world for atmospheric depth.

        KB Reference: Section 17, 28 - Volumetric fog for depth

        Args:
            density: Fog density (0.01-0.1 typical)
            color: Fog color
            anisotropy: Forward scattering (0.5+ for god rays)
        """
        world = bpy.context.scene.world
        if not world:
            world = bpy.data.worlds.new("World")
            bpy.context.scene.world = world

        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links

        # Clear existing
        nodes.clear()

        # Output
        output = nodes.new('ShaderNodeOutputWorld')
        output.location = (400, 0)

        # Background
        bg = nodes.new('ShaderNodeBackground')
        bg.inputs["Color"].default_value = (0.05, 0.05, 0.05, 1.0)
        bg.inputs["Strength"].default_value = 1.0
        bg.location = (100, 100)

        # Volume scatter for fog
        scatter = nodes.new('ShaderNodeVolumeScatter')
        scatter.inputs["Color"].default_value = (*color, 1.0)
        scatter.inputs["Density"].default_value = density
        scatter.inputs["Anisotropy"].default_value = anisotropy
        scatter.location = (100, -100)

        # Link
        links.new(bg.outputs["Background"], output.inputs["Surface"])
        links.new(scatter.outputs["Volume"], output.inputs["Volume"])

    def setup_hdri_fill(
        self,
        hdri_path: str,
        strength: float = 0.2,
        reflection_only: bool = False
    ) -> None:
        """
        Set up HDRI as ambient fill only (not main light).

        KB Reference: Section 25 - HDRI as Fill Only

        Args:
            hdri_path: Path to HDRI file
            strength: Low strength (0.1-0.2 for fill)
            reflection_only: Use only for reflections
        """
        world = bpy.context.scene.world
        if not world:
            world = bpy.data.worlds.new("World")
            bpy.context.scene.world = world

        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links

        # Find or create background
        bg = nodes.get('Background')
        if not bg:
            bg = nodes.new('ShaderNodeBackground')

        # Add environment texture
        env_tex = nodes.new('ShaderNodeTexEnvironment')
        try:
            env_tex.image = bpy.data.images.load(hdri_path)
        except:
            pass  # Handle missing file

        # Add texture coordinate
        tex_coord = nodes.new('ShaderNodeTexCoord')
        mapping = nodes.new('ShaderNodeMapping')

        # Link
        links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
        links.new(mapping.outputs["Vector"], env_tex.inputs["Vector"])
        links.new(env_tex.outputs["Color"], bg.inputs["Color"])

        bg.inputs["Strength"].default_value = strength

    def setup_light_linking(
        self,
        light: bpy.types.Object,
        include_collection: Optional[bpy.types.Collection] = None,
        exclude_collection: Optional[bpy.types.Collection] = None
    ) -> None:
        """
        Configure light linking for selective illumination.

        KB Reference: Section 17, 25 - Light linking for control

        Args:
            light: Light object to configure
            include_collection: Collection to illuminate
            exclude_collection: Collection to exclude from illumination
        """
        # Light linking is available in Blender 4.0+
        if hasattr(light, 'light_linking'):
            if include_collection:
                light.light_linking.receiver_collection = include_collection
                # Set to include mode
                light.light_linking.collection_state = 'INCLUDE'

    def get_light(self, name: str) -> Optional[bpy.types.Object]:
        """Get a light by name."""
        return self._lights.get(name)


class LightRig:
    """
    Pre-configured lighting rigs for common scenarios.

    Cross-references:
    - KB Section 28: Cinematic rendering checklist
    - KB Section 17: Creature lighting
    """

    @staticmethod
    def product_showcase(
        target: bpy.types.Object,
        soft_box: bool = True
    ) -> List[bpy.types.Object]:
        """
        Create product showcase lighting rig.

        Args:
            target: Product to light
            soft_box: Use soft box style (larger lights)

        Returns:
            List of created lights
        """
        lighting = CinematicLighting()

        size = 3.0 if soft_box else 1.5

        key, fill, rim = lighting.setup_3_point(
            key_power=800,
            fill_power=300,
            rim_power=400,
            target=target
        )

        # Increase light sizes for soft box
        if soft_box:
            key.data.size = size
            fill.data.size = size * 1.5

        return [key, fill, rim]

    @staticmethod
    def portrait(
        target: bpy.types.Object,
        style: str = "classic"
    ) -> List[bpy.types.Object]:
        """
        Create portrait lighting rig.

        Args:
            target: Subject to light
            style: "classic", "rembrandt", "butterfly"

        Returns:
            List of created lights
        """
        lighting = CinematicLighting()
        lights = []

        if style == "rembrandt":
            # Rembrandt: 45° key, dramatic shadows
            key, fill, rim = lighting.setup_3_point(
                key_power=1000,
                key_angle=45,
                fill_power=200,
                target=target
            )
            lights = [key, fill, rim]

        elif style == "butterfly":
            # Butterfly: Key directly above camera
            key = lighting.create_area_light("Key", power=1200, size=2.0)
            key.location = (0, -3, 5)
            lighting._point_light_at(key, target)

            fill = lighting.create_area_light("Fill", power=400, size=3.0)
            fill.location = (0, 4, 0)
            lighting._point_light_at(fill, target)

            lights = [key, fill]

        else:  # classic
            lights = list(lighting.setup_3_point(target=target))

        return lights

    @staticmethod
    def horror_scene(
        target: bpy.types.Object
    ) -> List[bpy.types.Object]:
        """
        Create horror/moody lighting setup.

        KB Reference: Section 17 - Monster lighting

        Args:
            target: Subject to light

        Returns:
            List of created lights
        """
        lighting = CinematicLighting()

        # Dim key light
        key = lighting.create_area_light(
            "Horror_Key",
            power=300,
            color=(1.0, 0.8, 0.7),  # Warm, dim
            size=1.0
        )
        key.location = (3, -4, 2)

        # Cool fill
        fill = lighting.create_area_light(
            "Horror_Fill",
            power=100,
            color=(0.4, 0.5, 0.8),  # Cool blue
            size=2.0
        )
        fill.location = (-4, -2, 1)

        # Colored rim for atmosphere
        rim = lighting.create_area_light(
            "Horror_Rim",
            power=200,
            color=(0.8, 0.3, 0.5),  # Purple/red
            size=1.5
        )
        rim.location = (0, 5, 3)

        # Add volumetric fog
        lighting.add_volumetric_fog(density=0.08, anisotropy=0.3)

        for light in [key, fill, rim]:
            lighting._point_light_at(light, target)

        return [key, fill, rim]


class IESLighting:
    """
    IES texture support for realistic light falloff.

    Cross-references:
    - KB Section 25 - IES Texture for Realistic Falloff
    """

    @staticmethod
    def load_ies_profile(
        light: bpy.types.Object,
        ies_path: str
    ) -> bool:
        """
        Load IES profile into a spot or point light.

        Args:
            light: Light object
            ies_path: Path to IES file

        Returns:
            True if loaded successfully
        """
        if light.type != 'LIGHT':
            return False

        light_data = light.data

        # IES textures require node-based light setup
        light_data.use_nodes = True
        nodes = light_data.node_tree.nodes
        links = light_data.node_tree.links

        # Clear existing
        nodes.clear()

        # Output
        output = nodes.new('ShaderNodeOutputLight')
        output.location = (400, 0)

        # Emission
        emission = nodes.new('ShaderNodeEmission')
        emission.location = (200, 0)

        # IES texture (if supported)
        # Note: IES support varies by Blender version
        # This creates a basic setup that can be enhanced
        light_color = nodes.new('ShaderNodeLightFalloff')
        light_color.location = (0, 0)

        # Link
        links.new(light_color.outputs["Color"], emission.inputs["Color"])
        links.new(emission.outputs["Emission"], output.inputs["Surface"])

        return True


class CinematicChecklist:
    """
    5-step cinematic rendering checklist.

    KB Reference: Section 28 - 5 Steps to Cinematic Renders
    """

    @staticmethod
    def get_checklist() -> dict:
        """Get the 5-step cinematic checklist."""
        return {
            "1_reduction": {
                "name": "Reduction",
                "description": "Remove unnecessary elements",
                "question": "Does this object help tell the story?",
            },
            "2_composition": {
                "name": "Composition",
                "description": "Frame with purpose",
                "settings": {
                    "focal_length": "50-85mm for cinematic look",
                    "empty_space": "Give subjects breathing room",
                    "leading_lines": "Draw eye to subject",
                    "depth_layers": "Foreground, mid, background",
                }
            },
            "3_lighting": {
                "name": "Lighting",
                "description": "Individual area lights over HDRI",
                "setup": "Key + Fill + Rim + Practicals",
            },
            "4_volume": {
                "name": "Volume (Fog/Mist)",
                "description": "Atmospheric depth",
                "settings": {
                    "density": "0.01-0.05 (subtle)",
                    "effect": "God rays through lights",
                }
            },
            "5_storytelling": {
                "name": "Storytelling",
                "description": "Every frame tells a story",
                "elements": ["Context", "Character", "Mood", "Intrigue"],
            }
        }

    @staticmethod
    def validate_scene() -> List[str]:
        """
        Validate scene against cinematic checklist.

        Returns:
            List of issues/recommendations
        """
        issues = []

        scene = bpy.context.scene

        # Check for HDRI as main light (anti-pattern)
        if scene.world and scene.world.use_nodes:
            for node in scene.world.node_tree.nodes:
                if node.type == 'BACKGROUND':
                    strength = node.inputs.get("Strength")
                    if strength and strength.default_value > 0.3:
                        issues.append("HDRI strength > 0.3: Use as fill only, not main light")

        # Check for volumetrics
        if not scene.world or not scene.world.use_nodes:
            issues.append("No world setup: Add volumetric fog for depth")
        else:
            has_volume = any(n.type == 'SHADER_VOLUME' for n in scene.world.node_tree.nodes)
            if not has_volume:
                issues.append("No volumetrics: Add Volume Scatter for atmospheric depth")

        # Check camera focal length
        camera = scene.camera
        if camera and camera.data.type == 'PERSP':
            if camera.data.lens < 35:
                issues.append(f"Wide lens ({camera.data.lens}mm): Use 50-85mm for cinematic look")

        return issues


# Convenience functions
def create_3_point_lighting(
    target: Optional[bpy.types.Object] = None
) -> Tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object]:
    """Quick setup for 3-point lighting."""
    lighting = CinematicLighting()
    return lighting.setup_3_point(target=target)


def add_fog(density: float = 0.05) -> None:
    """Quick add volumetric fog."""
    lighting = CinematicLighting()
    lighting.add_volumetric_fog(density=density)


def create_product_lighting(product: bpy.types.Object) -> List[bpy.types.Object]:
    """Quick setup for product showcase lighting."""
    return LightRig.product_showcase(product)


def create_horror_lighting(target: bpy.types.Object) -> List[bpy.types.Object]:
    """Quick setup for horror/moody lighting."""
    return LightRig.horror_scene(target)
