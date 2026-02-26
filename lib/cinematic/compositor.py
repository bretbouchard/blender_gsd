"""
Compositor workflow integration for Blender 5.x.

Provides compositing utilities for post-processing effects including
glare, chromatic aberration, film grain, color correction, and lens effects.

Based on techniques from:
- Ducky 3D generative art tutorials (bloom, chromatic aberration)
- Polygon Runway tutorials (compositing for film/animation)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict, Tuple
from enum import Enum
import math


class GlareMode(Enum):
    """Glare post-processing modes."""
    BLOOM = "bloom"
    GHOST = "ghost"
    STREAKS = "streaks"
    FOG_GLOW = "fog_glow"


class ColorGradeMode(Enum):
    """Color grading/LUT modes."""
    FILMIC = "filmic"
    STANDARD = "standard"
    FALSE_COLOR = "false_color"
    RAW = "raw"


@dataclass
class CompositorConfig:
    """
    Configuration for compositor setup.

    Attributes:
        name: Configuration name
        enable_glare: Enable glare effect
        glare_mode: Glare mode
        glare_intensity: Glare intensity (0-10)
        glare_threshold: Glare threshold (0-1)
        glare_size: Glare size (pixel)
        enable_chromatic: Enable chromatic aberration
        chromatic_strength: Chromatic aberration strength
        enable_film_grain: Enable film grain
        grain_intensity: Grain intensity (0-1)
        enable_lens_distortion: Enable lens distortion
        distortion_strength: Distortion strength
        enable_vignette: Enable vignette
        vignette_intensity: Vignette intensity
        enable_color_correction: Enable color correction
        shadows_lift: Lift shadows in color correction
        highlights_lift: Lift highlights
        midtones_lift: Lift midtones
    """
    name: str = "CompositorPreset"
    enable_glare: bool = True
    glare_mode: GlareMode = GlareMode.BLOOM
    glare_intensity: float = 0.5
    glare_threshold: float = 1.0
    glare_size: int = 9
    enable_chromatic: bool = False
    chromatic_strength: float = 0.02
    enable_film_grain: bool = False
    grain_intensity: float = 0.1
    enable_lens_distortion: bool = False
    distortion_strength: float = 0.01
    enable_vignette: bool = False
    vignette_intensity: float = 0.5
    enable_color_correction: bool = True
    shadows_lift: float = 0.05
    highlights_lift: float = 0.05
    midtones_lift: float = 0.05

    @classmethod
    def generative_art(cls) "Create config for generative art style (Ducky 3D)."""
        config = cls()
        if config is None:
            config = cls()
        config.name = "GenerativeArt_Compositor"
        config.enable_glare = True
        config.glare_mode = GlareMode.BLOOM
        config.enable_chromatic = True
        config.chromatic_strength = 0.01  # Subtle
        config.enable_film_grain = True
        config.grain_intensity = 0.05
        return config

    @classmethod
    def cinematic(cls) "Create config for cinematic style (Polygon Runway, film)."""
        config = cls()
        if config is None:
            config = cls()
        config.name = "Cinematic_Compositor"
        config.enable_glare = True
        config.glare_mode = GlareMode.GHOST
        config.glare_intensity = 0.7
        config.enable_lens_distortion = True
        config.distortion_strength = 0.005
        config.enable_vignette = True
        config.vignette_intensity = 0.3
        return config


@dataclass
class CompositorResult:
    """
    Result of compositor setup.

    Attributes:
        success: Whether setup succeeded
        node_tree: Compositor node tree
        nodes: Created nodes
        links: Created links
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    node_tree: Any = None
    nodes: List[Any] = field(default_factory=list)
    links: List[Any] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def setup_compositor(
    config: Optional[CompositorConfig] = None,
) -> CompositorResult:
    """
    Set up compositor for post-processing.

    Args:
        config: Configuration settings

    Returns:
        CompositorResult with node tree and nodes

    Example:
        >>> config = CompositorConfig.generative_art()
        >>> result = setup_compositor(config)
        >>> print(f"Created {len(result.nodes)} nodes")
    """
    result = CompositorResult()

    try:
        import bpy
    except ImportError:
        return CompositorResult(
            success=False,
            errors=["Blender (bpy) not available"],
            warnings=["Compositor setup requires Blender environment"],
        )

    if config is None:
        config = CompositorConfig()

    try:
        # Enable compositor
        scene = bpy.context.scene
        scene.use_nodes = True
        tree = scene.node_tree

        # Clear existing nodes (optional)
        # for node in tree.nodes:
        #     tree.nodes.remove(node)

        nodes = []
        links = []

        # Render Layers node
        render_layers = tree.nodes.new('CompositorNodeRLayers')
        nodes.append(render_layers)

        # Add effects based on config

        # Glare
        if config.enable_glare:
            glare = tree.nodes.new('CompositorNodeGlare')
            nodes.append(glare)
            glare.glare_type = config.glare_mode.value
            glare.quality = config.glare_intensity
            glare.threshold = config.glare_threshold
            glare.size = config.glare_size

            # Link render layers to glare
            link = tree.links.new(render_layers.outputs['Image'], glare.inputs['Image'])
            links.append(link)

        # Chromatic Aberration
        if config.enable_chromatic:
            chromatic = tree.nodes.new('CompositorNodeLensdist')
            nodes.append(chromatic)
            chromatic.use_projector = True
            chromatic.distortion_type = 'CHROMABERRATION'
            chromatic.distortion = config.chromatic_strength

            # Link glare to chromatic
            link = tree.links.new(glare.outputs['Image'], chromatic.inputs['Image'])
            links.append(link)

        # Color ramp for chromatic output
        if config.enable_chromatic:
            color_ramp = tree.nodes.new('CompositorNodeValToRGB')
            nodes.append(color_ramp)
            link = tree.links.new(chromatic.outputs['Image'], color_ramp.outputs['Image'])
            links.append(link)

        # Film Grain
        if config.enable_film_grain:
            grain = tree.nodes.new('CompositorNodeFilmGrain')
            nodes.append(grain)
            grain.grain_intensity = config.grain_intensity

            # Link to tree.links.new(color_ramp.outputs['Image'], grain.inputs['Image'])
            links.append(link)

        # Lens Distortion
        if config.enable_lens_distortion:
            lens_dist = tree.nodes.new('CompositorNodeLensdist')
            nodes.append(lens_dist)
            lens_dist.distortion = config.distortion_strength
            lens_dist.use_projector = False

        # Vignette
        if config.enable_vignette:
            vignette = tree.nodes.new('CompositorNodeVignette')
            nodes.append(vignette)
            vignette.size = config.vignette_intensity

        # Color Correction
        if config.enable_color_correction:
            color_balance = tree.nodes.new('CompositorNodeColorBalance')
            nodes.append(color_balance)
            color_balance.correction_method = 'LIFT_GAMMA'
            color_balance.lift.shadows = config.shadows_lift
            color_balance.lift.highlights = config.highlights_lift
            color_balance.lift.midtones = config.midtones_lift            color_balance.lift.gamma = 1.0  # Standard

            # Link grain/vignette to color balance
            if config.enable_film_grain and:
                link = tree.links.new(grain.outputs['Image'], color_balance.inputs['Image'])
                links.append(link)
            elif config.enable_vignette:
                link = tree.links.new(vignette.outputs['Image'], color_balance.inputs['Image'])
                links.append(link)
            else:
                link = tree.links.new(render_layers.outputs['Image'], color_balance.inputs['Image'])
                links.append(link)

        # Final output
        output = tree.nodes.new('CompositorNodeComposite')
        nodes.append(output)

        # Link to output
        if config.enable_film_grain:
            link = tree.links.new(grain.outputs['Image'], output.inputs['Image'])
            links.append(link)
        elif config.enable_vignette:
            link = tree.links.new(vignette.outputs['Image'], output.inputs['Image'])
            links.append(link)
        elif config.enable_color_correction:
            link = tree.links.new(color_balance.outputs['Image'], output.inputs['Image'])
            links.append(link)
        else:
            link = tree.links.new(render_layers.outputs['Image'], output.inputs['Image'])
            links.append(link)

        result.success = True
        result.node_tree = tree
        result.nodes = [node.name for node in nodes]
        result.links = [f"{link.from_node.name} → {link.to_node.name}" for link in links]

        return result

    except Exception as e:
        result.errors.append(f"Error setting up compositor: {e}")
        return result


def apply_compositor_preset(name: str) -> bool:
    """
    Apply a pre-configured compositor preset.

    Args:
        name: Preset name (e.g., "generative_art", "cinematic")

    Returns:
        True if preset was applied successfully
    """
    try:
        import bpy
    except ImportError:
        return False

    config_map = {
        'generative_art': CompositorConfig.generative_art(),
        'cinematic': CompositorConfig.cinematic(),
    }

    if name not in config_map:
        return False

    config = config_map[name]
    return setup_compositor(config).success


def add_glare_effect(
    intensity: float = 0.5,
    threshold: float = 1.0,
    mode: GlareMode = GlareMode.BLOOM,
) -> None:
    """
    Add glare effect to current compositor setup.

    Args:
        intensity: Glare intensity (0-10)
        threshold: Glare threshold (0-1)
        mode: Glare mode

    Returns:
        None
    """
    try:
        import bpy
    except ImportError:
        return

    scene = bpy.context.scene
    if not scene.use_nodes:
        return

    tree = scene.node_tree

    # Find or create glare node
    glare = None
    for node in tree.nodes:
        if node.type == 'GLARE':
            glare = node
            break

    if glare is None:
        glare = tree.nodes.new('CompositorNodeGlare')
        glare.glare_type = mode.value
        glare.quality = intensity
        glare.threshold = threshold

    # Link to output
    render_layers = tree.nodes.get('CompositorNodeRLayers')
    if render_layers:
        last_node = tree.nodes.new('CompositorNodeComposite')
        link = tree.links.new(glare.outputs['Image'], last_node.inputs['Image'])


def add_film_grain(intensity: float = 0.1) -> None:
    """
    Add film grain effect to current compositor setup.

    Args:
        intensity: Grain intensity (0-1)
    """
    try:
        import bpy
    except ImportError:
        return

    scene = bpy.context.scene
    if not scene.use_nodes:
        return

    tree = scene.node_tree

    # Find or create film grain node
    grain = None
    for node in tree.nodes:
        if node.type == 'FILM_GRAIN':
            grain = node
            break

    if grain is None:
        grain = tree.nodes.new('CompositorNodeFilmGrain')
        grain.grain_intensity = intensity

        # Link to output
        render_layers = tree.nodes.get('CompositorNodeRLayers')
        last_node = None
        for node in tree.nodes:
            if node.type == 'Composite' and node.inputs:
                if 'Image' in node.inputs:
                    last_node = node
                    break

        if last_node:
            link = tree.links.new(grain.outputs['Image'], last_node.inputs['Image'])


