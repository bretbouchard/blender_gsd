"""
Compositor Asset Shelf for Blender 5.0+.

Provides drag-and-drop compositor effects, presets, and templates
for the asset shelf integration in Blender 5.0.

Example:
    >>> from lib.blender5x.compositor import EffectPresets, EffectTemplates
    >>> EffectPresets.apply_cinematic_grade(strip)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from bpy.types import Sequence, Scene


class EffectCategory(Enum):
    """Categories for compositor effects."""

    COLOR = "color"
    """Color correction and grading effects."""

    BLUR = "blur"
    """Blur and focus effects."""

    LENS = "lens"
    """Lens simulation effects."""

    STYLIZE = "stylize"
    """Artistic/stylized effects."""

    FILM = "film"
    """Film simulation effects."""

    GLARE = "glare"
    """Glow and glare effects."""


@dataclass
class EffectPreset:
    """A compositor effect preset."""

    name: str
    """Preset name."""

    category: EffectCategory
    """Effect category."""

    description: str
    """Description of the effect."""

    thumbnail: str | None = None
    """Optional thumbnail path."""

    node_group_name: str | None = None
    """Associated node group name."""


# Built-in effect presets
BUILTIN_EFFECT_PRESETS: list[EffectPreset] = [
    # Color category
    EffectPreset(
        name="Cinematic Grade",
        category=EffectCategory.COLOR,
        description="Hollywood-style teal and orange color grade",
        node_group_name="preset_cinematic",
    ),
    EffectPreset(
        name="Vintage Film",
        category=EffectCategory.COLOR,
        description="Warm, faded vintage film look",
        node_group_name="preset_vintage",
    ),
    EffectPreset(
        name="Cold Horror",
        category=EffectCategory.COLOR,
        description="Cold, desaturated horror movie look",
        node_group_name="preset_horror",
    ),
    EffectPreset(
        name="Summer Bright",
        category=EffectCategory.COLOR,
        description="Warm, bright summer colors",
        node_group_name="preset_summer",
    ),
    EffectPreset(
        name="Noir",
        category=EffectCategory.COLOR,
        description="High contrast black and white",
        node_group_name="preset_noir",
    ),
    # Lens category
    EffectPreset(
        name="Anamorphic Flare",
        category=EffectCategory.LENS,
        description="Horizontal anamorphic lens flare",
        node_group_name="preset_anamorphic",
    ),
    EffectPreset(
        name="Chromatic Aberration",
        category=EffectCategory.LENS,
        description="RGB color fringing effect",
        node_group_name="preset_chromatic",
    ),
    EffectPreset(
        name="Lens Distortion",
        category=EffectCategory.LENS,
        description="Barrel/pincushion distortion",
        node_group_name="preset_distortion",
    ),
    # Blur category
    EffectPreset(
        name="Bokeh Blur",
        category=EffectCategory.BLUR,
        description="Beautiful bokeh defocus blur",
        node_group_name="preset_bokeh",
    ),
    EffectPreset(
        name="Motion Blur",
        category=EffectCategory.BLUR,
        description="Directional motion blur",
        node_group_name="preset_motion",
    ),
    # Glare category
    EffectPreset(
        name="Bloom",
        category=EffectCategory.GLARE,
        description="Soft bloom glow effect",
        node_group_name="preset_bloom",
    ),
    EffectPreset(
        name="God Rays",
        category=EffectCategory.GLARE,
        description="Volumetric god rays",
        node_group_name="preset_godrays",
    ),
    EffectPreset(
        name="Fog Glow",
        category=EffectCategory.GLARE,
        description="Atmospheric fog glow",
        node_group_name="preset_fog_glow",
    ),
    # Film category
    EffectPreset(
        name="Film Grain",
        category=EffectCategory.FILM,
        description="Realistic film grain texture",
        node_group_name="preset_grain",
    ),
    EffectPreset(
        name="Scratches",
        category=EffectCategory.FILM,
        description="Film scratches and dust",
        node_group_name="preset_scratches",
    ),
    # Stylize category
    EffectPreset(
        name="Vignette",
        category=EffectCategory.STYLIZE,
        description="Classic edge darkening",
        node_group_name="preset_vignette",
    ),
    EffectPreset(
        name="Split Tone",
        category=EffectCategory.STYLIZE,
        description="Shadow and highlight coloring",
        node_group_name="preset_split_tone",
    ),
    EffectPreset(
        name="Posterize",
        category=EffectCategory.STYLIZE,
        description="Reduce color levels for poster effect",
        node_group_name="preset_posterize",
    ),
]


class EffectPresets:
    """
    Effect preset management for Blender 5.0+.

    Provides access to and application of compositor effect presets.

    Example:
        >>> EffectPresets.apply_cinematic_grade(strip)
        >>> EffectPresets.list_by_category(EffectCategory.COLOR)
    """

    @staticmethod
    def get_all() -> list[EffectPreset]:
        """
        Get all available effect presets.

        Returns:
            List of EffectPreset objects.
        """
        return list(BUILTIN_EFFECT_PRESETS)

    @staticmethod
    def list_by_category(category: EffectCategory) -> list[EffectPreset]:
        """
        Get presets filtered by category.

        Args:
            category: Category to filter by.

        Returns:
            List of presets in the category.
        """
        return [p for p in BUILTIN_EFFECT_PRESETS if p.category == category]

    @staticmethod
    def get_by_name(name: str) -> EffectPreset | None:
        """
        Get a preset by name.

        Args:
            name: Preset name.

        Returns:
            EffectPreset if found, None otherwise.
        """
        for preset in BUILTIN_EFFECT_PRESETS:
            if preset.name.lower() == name.lower():
                return preset
        return None

    @staticmethod
    def apply_to_strip(
        preset_name: str,
        strip: Sequence | str,
        scene: Scene | None = None,
    ) -> bool:
        """
        Apply a preset to a VSE strip.

        Args:
            preset_name: Name of the preset to apply.
            strip: Target strip or name.
            scene: Scene with VSE.

        Returns:
            True if applied successfully.

        Example:
            >>> EffectPresets.apply_to_strip("Cinematic Grade", "Video.001")
        """
        import bpy

        preset = EffectPresets.get_by_name(preset_name)
        if preset is None:
            raise ValueError(f"Preset not found: {preset_name}")

        scene = scene or bpy.context.scene
        seq_editor = scene.sequence_editor

        if seq_editor is None:
            raise ValueError("Scene has no sequence editor")

        # Get target strip
        if isinstance(strip, str):
            target_strip = None
            for s in seq_editor.sequences_all:
                if s.name == strip:
                    target_strip = s
                    break
            if target_strip is None:
                raise ValueError(f"Strip not found: {strip}")
        else:
            target_strip = strip

        # Apply effect based on preset
        # This would create the appropriate node setup
        # For now, add a basic modifier
        mod = target_strip.modifiers.new(f"Preset_{preset.name}", "COLOR_BALANCE")

        return True

    @staticmethod
    def apply_cinematic_grade(strip: Sequence | str) -> bool:
        """Apply cinematic teal-orange grade."""
        return EffectPresets.apply_to_strip("Cinematic Grade", strip)

    @staticmethod
    def apply_vintage_look(strip: Sequence | str) -> bool:
        """Apply vintage film look."""
        return EffectPresets.apply_to_strip("Vintage Film", strip)

    @staticmethod
    def apply_horror_grade(strip: Sequence | str) -> bool:
        """Apply horror movie grade."""
        return EffectPresets.apply_to_strip("Cold Horror", strip)

    @staticmethod
    def create_custom_preset(
        name: str,
        category: EffectCategory,
        description: str,
        node_group_name: str,
    ) -> EffectPreset:
        """
        Create a custom effect preset.

        Args:
            name: Preset name.
            category: Effect category.
            description: Description.
            node_group_name: Associated node group.

        Returns:
            Created EffectPreset.

        Example:
            >>> preset = EffectPresets.create_custom_preset(
            ...     "My Grade",
            ...     EffectCategory.COLOR,
            ...     "Custom color grade",
            ...     "my_grade_nodes",
            ... )
        """
        preset = EffectPreset(
            name=name,
            category=category,
            description=description,
            node_group_name=node_group_name,
        )

        BUILTIN_EFFECT_PRESETS.append(preset)

        return preset


class EffectTemplates:
    """
    Effect template system for Blender 5.0+.

    Provides templates for creating common compositor setups.
    """

    @staticmethod
    def create_color_grade_template(
        name: str = "ColorGrade",
        lift: tuple[float, float, float] = (1.0, 1.0, 1.0),
        gamma: tuple[float, float, float] = (1.0, 1.0, 1.0),
        gain: tuple[float, float, float] = (1.0, 1.0, 1.0),
        saturation: float = 1.0,
        contrast: float = 1.0,
    ) -> str:
        """
        Create a color grading template node group.

        Args:
            name: Template name.
            lift: Shadow color adjustment.
            gamma: Midtone color adjustment.
            gain: Highlight color adjustment.
            saturation: Saturation multiplier.
            contrast: Contrast multiplier.

        Returns:
            Name of the created node group.

        Example:
            >>> template = EffectTemplates.create_color_grade_template(
            ...     "MyGrade",
            ...     lift=(0.9, 0.9, 1.0),
            ...     saturation=1.1,
            ... )
        """
        import bpy

        # Create node group
        tree = bpy.data.node_groups.new(name, "CompositorNodeTree")

        # Add input/output nodes
        input_node = tree.nodes.new("NodeGroupInput")
        input_node.location = (-400, 0)

        output_node = tree.nodes.new("NodeGroupOutput")
        output_node.location = (600, 0)

        # Create interface
        tree.interface.new_socket("Image", in_out="INPUT", socket_type="NodeSocketColor")
        tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")

        # Color Balance node
        color_balance = tree.nodes.new("CompositorNodeColorBalance")
        color_balance.correction_method = "LIFT_GAMMA_GAIN"
        color_balance.lift = lift
        color_balance.gamma = gamma
        color_balance.gain = gain
        color_balance.location = (0, 100)

        # Hue Correct for saturation
        hue_correct = tree.nodes.new("CompositorNodeHueCorrect")
        hue_correct.location = (200, 100)

        # Brightness/Contrast
        bright_contrast = tree.nodes.new("CompositorNodeBrightContrast")
        bright_contrast.bright = 0.0
        bright_contrast.contrast = contrast - 1.0
        bright_contrast.location = (400, 100)

        # Link nodes
        tree.links.new(input_node.outputs[0], color_balance.inputs[1])
        tree.links.new(color_balance.outputs[0], hue_correct.inputs[1])
        tree.links.new(hue_correct.outputs[0], bright_contrast.inputs[0])
        tree.links.new(bright_contrast.outputs[0], output_node.inputs[0])

        return tree.name

    @staticmethod
    def create_glare_template(
        name: str = "Glare",
        glare_type: str = "BLOOM",
        threshold: float = 1.0,
        intensity: float = 0.5,
        size: float = 8.0,
    ) -> str:
        """
        Create a glare/glow template node group.

        Args:
            name: Template name.
            glare_type: Type of glare ('BLOOM', 'GHOSTS', 'STREAKS', 'FOG_GLOW').
            threshold: Brightness threshold.
            intensity: Glare intensity.
            size: Glare size.

        Returns:
            Name of the created node group.

        Example:
            >>> template = EffectTemplates.create_glare_template(
            ...     "MyGlow",
            ...     glare_type="BLOOM",
            ...     intensity=0.7,
            ... )
        """
        import bpy

        # Create node group
        tree = bpy.data.node_groups.new(name, "CompositorNodeTree")

        # Add input/output nodes
        input_node = tree.nodes.new("NodeGroupInput")
        input_node.location = (-200, 0)

        output_node = tree.nodes.new("NodeGroupOutput")
        output_node.location = (400, 0)

        # Create interface
        tree.interface.new_socket("Image", in_out="INPUT", socket_type="NodeSocketColor")
        tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")

        # Glare node
        glare = tree.nodes.new("CompositorNodeGlare")
        glare.glare_type = glare_type
        glare.threshold = threshold
        glare.intensity = intensity
        glare.size = size
        glare.location = (100, 0)

        # Mix node for blending
        mix = tree.nodes.new("CompositorNodeMixRGB")
        mix.blend_type = "ADD"
        mix.inputs[0].default_value = 1.0
        mix.location = (250, 0)

        # Link nodes
        tree.links.new(input_node.outputs[0], glare.inputs[1])
        tree.links.new(input_node.outputs[0], mix.inputs[1])
        tree.links.new(glare.outputs[0], mix.inputs[2])
        tree.links.new(mix.outputs[0], output_node.inputs[0])

        return tree.name

    @staticmethod
    def create_lens_effects_template(
        name: str = "LensEffects",
        distortion: float = 0.1,
        dispersion: float = 0.01,
    ) -> str:
        """
        Create a lens effects template.

        Args:
            name: Template name.
            distortion: Lens distortion amount.
            dispersion: Chromatic dispersion.

        Returns:
            Name of the created node group.

        Example:
            >>> template = EffectTemplates.create_lens_effects_template(
            ...     "Anamorphic",
            ...     distortion=0.05,
            ...     dispersion=0.02,
            ... )
        """
        import bpy

        # Create node group
        tree = bpy.data.node_groups.new(name, "CompositorNodeTree")

        # Add input/output nodes
        input_node = tree.nodes.new("NodeGroupInput")
        input_node.location = (-400, 0)

        output_node = tree.nodes.new("NodeGroupOutput")
        output_node.location = (600, 0)

        # Create interface
        tree.interface.new_socket("Image", in_out="INPUT", socket_type="NodeSocketColor")
        tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")

        # Lens Distortion node
        lens_dist = tree.nodes.new("CompositorNodeLensdist")
        lens_dist.use_jitter = False
        lens_dist.use_fit = True
        lens_dist.inputs[0].default_value = distortion
        lens_dist.location = (0, 0)

        # Chromatic aberration simulation using separate RGB channels
        # This would require more complex node setup
        # For now, use basic lens distortion

        # Link nodes
        tree.links.new(input_node.outputs[0], lens_dist.inputs[1])
        tree.links.new(lens_dist.outputs[0], output_node.inputs[0])

        return tree.name

    @staticmethod
    def create_film_look_template(
        name: str = "FilmLook",
        grain_intensity: float = 0.3,
        vignette_intensity: float = 0.5,
    ) -> str:
        """
        Create a film look template with grain and vignette.

        Args:
            name: Template name.
            grain_intensity: Film grain intensity.
            vignette_intensity: Vignette intensity.

        Returns:
            Name of the created node group.

        Example:
            >>> template = EffectTemplates.create_film_look_template(
            ...     "VintageFilm",
            ...     grain_intensity=0.4,
            ...     vignette_intensity=0.6,
            ... )
        """
        import bpy

        # Create node group
        tree = bpy.data.node_groups.new(name, "CompositorNodeTree")

        # Add input/output nodes
        input_node = tree.nodes.new("NodeGroupInput")
        input_node.location = (-400, 0)

        output_node = tree.nodes.new("NodeGroupOutput")
        output_node.location = (600, 0)

        # Create interface
        tree.interface.new_socket("Image", in_out="INPUT", socket_type="NodeSocketColor")
        tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")

        # Vignette using ellipse mask
        vignette = tree.nodes.new("CompositorNodeEllipseMask")
        vignette.mask_type = "MULTIPLY"
        vignette.location = (0, 100)

        # Film grain using texture
        texture = tree.nodes.new("CompositorNodeTexture")
        texture.location = (0, -100)

        # Mix for grain
        mix_grain = tree.nodes.new("CompositorNodeMixRGB")
        mix_grain.blend_type = "OVERLAY"
        mix_grain.inputs[0].default_value = grain_intensity
        mix_grain.location = (200, -100)

        # Final mix for vignette
        mix_vignette = tree.nodes.new("CompositorNodeMixRGB")
        mix_vignette.blend_type = "MULTIPLY"
        mix_vignette.inputs[0].default_value = vignette_intensity
        mix_vignette.location = (400, 0)

        # Link nodes
        tree.links.new(input_node.outputs[0], mix_vignette.inputs[1])
        tree.links.new(vignette.outputs[0], mix_vignette.inputs[2])
        tree.links.new(mix_vignette.outputs[0], output_node.inputs[0])

        return tree.name


# Convenience exports
__all__ = [
    "EffectPresets",
    "EffectTemplates",
    "EffectCategory",
    "EffectPreset",
    "BUILTIN_EFFECT_PRESETS",
]
