"""
Lens System Module

Provides lens imperfections via compositor nodes.
Follows correct pipeline order: geometric -> luminance -> color -> film

Compositor Pipeline Order:
1. Geometric distortions (chromatic aberration, lens distortion)
2. Luminance effects (glare, bloom)
3. Color grading
4. Film effects (grain, vignette)

Usage:
    from lib.cinematic.lenses import apply_lens_imperfections, get_bokeh_blade_count
    from lib.cinematic.types import ImperfectionConfig

    config = ImperfectionConfig(
        vignette=0.3,
        chromatic_aberration=0.002,
        flare_enabled=True
    )
    apply_lens_imperfections(config)

    # Get bokeh blade count for camera
    blades = get_bokeh_blade_count("hexagonal")  # Returns 6
"""

from __future__ import annotations
from typing import Optional, Any, Dict
from pathlib import Path

from .types import ImperfectionConfig
from .preset_loader import get_imperfection_preset

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False


def setup_compositor_for_lens() -> bool:
    """
    Enable compositor and ensure basic nodes exist.

    Returns:
        True on success, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene
        scene.use_nodes = True

        tree = scene.node_tree
        if tree is None:
            return False

        # Check for Render Layers node
        render_layers = tree.nodes.get('Render Layers')
        if not render_layers:
            render_layers = tree.nodes.new('CompositorNodeRLayers')
            render_layers.name = 'Render Layers'

        # Check for Composite node
        composite = tree.nodes.get('Composite')
        if not composite:
            composite = tree.nodes.new('CompositorNodeComposite')
            composite.name = 'Composite'

        return True

    except Exception:
        return False


def apply_lens_imperfections(config: ImperfectionConfig) -> bool:
    """
    Apply lens imperfections via compositor nodes.

    Pipeline order:
    1. Chromatic aberration (geometric)
    2. Flare/glare (luminance)
    3. Vignette (film effect)

    Args:
        config: ImperfectionConfig with effect parameters

    Returns:
        True on success, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not setup_compositor_for_lens():
            return False

        scene = bpy.context.scene
        tree = scene.node_tree

        # Get render layers and composite nodes
        render_layers = tree.nodes.get('Render Layers')
        composite = tree.nodes.get('Composite')

        if not render_layers or not composite:
            return False

        # Track the current output node
        current_output = render_layers

        # 1. Chromatic aberration (if > 0)
        if config.chromatic_aberration > 0:
            ca_node = tree.nodes.new('CompositorNodeLensdist')
            ca_node.name = 'Lens_CA'
            ca_node.use_fit = False
            ca_node.use_jitter = False
            ca_node.use_projector = False
            # Dispersion is the chromatic aberration amount
            ca_node.dispersion = config.chromatic_aberration * 100  # Scale for visibility

            # Connect: current -> CA
            tree.links.new(current_output.outputs['Image'], ca_node.inputs['Image'])
            current_output = ca_node

        # 2. Flare (if enabled)
        if config.flare_enabled and config.flare_intensity > 0:
            glare_node = tree.nodes.new('CompositorNodeGlare')
            glare_node.name = 'Lens_Flare'
            glare_node.glare_type = 'FOG_GLOW'
            # Intensity 0-1 maps to threshold (lower = more bloom)
            glare_node.threshold = max(0.1, 1.0 - config.flare_intensity)

            # Connect: current -> Glare
            tree.links.new(current_output.outputs['Image'], glare_node.inputs['Image'])
            current_output = glare_node

        # 3. Vignette (if > 0)
        if config.vignette > 0:
            # Create vignette using mask + mix
            mask = tree.nodes.new('CompositorNodeEllipseMask')
            mask.name = 'Vignette_Mask'
            mask.mask_type = 'ELLIPSE'
            # Position in center
            mask.x = 0.5
            mask.y = 0.5
            # Size based on vignette intensity
            mask.width = 1.0 + config.vignette
            mask.height = 1.0 + config.vignette
            # Rotation
            mask.rotation = 0.0

            # Invert the mask (vignette darkens edges)
            invert = tree.nodes.new('CompositorNodeInvert')
            invert.name = 'Vignette_Invert'
            invert.invert_rgb = False

            # Mix node for vignette
            mix = tree.nodes.new('CompositorNodeMixRGB')
            mix.name = 'Vignette_Mix'
            mix.blend_type = 'MULTIPLY'

            # Connect: current -> Mix[1], Mask -> Invert -> Mix[0]
            tree.links.new(current_output.outputs['Image'], mix.inputs[1])
            tree.links.new(mask.outputs['Mask'], invert.inputs['Color'])
            tree.links.new(invert.outputs['Color'], mix.inputs[0])

            # Set mix factor
            mix.inputs['Fac'].default_value = config.vignette

            current_output = mix

        # Connect final output to composite
        tree.links.new(current_output.outputs['Image'], composite.inputs['Image'])

        return True

    except Exception:
        return False


def get_bokeh_blade_count(shape: str) -> int:
    """
    Get aperture blade count for bokeh shape.

    Args:
        shape: Shape name ("circular", "hexagonal", "octagonal", "rounded")

    Returns:
        Number of aperture blades (0 = circular aperture)
    """
    shape_map = {
        "circular": 0,   # Circular aperture (no polygonal shape)
        "hexagonal": 6,   # 6-sided
        "octagonal": 8,   # 8-sided
        "rounded": 9,     # Rounded octagon (9 blades for smoother circle)
    }
    return shape_map.get(shape.lower(), 0)


def clear_lens_effects() -> bool:
    """
    Remove all lens-related compositor nodes.

    Keeps only Render Layers and Composite nodes.

    Returns:
        True on success, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return False

        scene = bpy.context.scene
        if not scene.use_nodes or scene.node_tree is None:
            return True  # Nothing to clear

        tree = scene.node_tree

        # Nodes to remove (lens-related)
        lens_node_names = [
            'Lens_CA', 'Lens_Flare', 'Vignette_Mask',
            'Vignette_Invert', 'Vignette_Mix'
        ]

        # Remove lens nodes
        for name in lens_node_names:
            node = tree.nodes.get(name)
            if node:
                tree.nodes.remove(node)

        # Reconnect Render Layers directly to Composite
        render_layers = tree.nodes.get('Render Layers')
        composite = tree.nodes.get('Composite')

        if render_layers and composite:
            # Remove existing links to composite
            for link in tree.links:
                if link.to_node == composite:
                    tree.links.remove(link)

            # Create direct connection
            tree.links.new(render_layers.outputs['Image'], composite.inputs['Image'])

        return True

    except Exception:
        return False


def apply_imperfection_preset(preset_name: str) -> bool:
    """
    Apply lens imperfection preset by name.

    Args:
        preset_name: Name of preset from imperfection_presets.yaml

    Returns:
        True on success, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        preset = get_imperfection_preset(preset_name)

        config = ImperfectionConfig(
            name=preset_name,
            flare_enabled=preset.get("flare_enabled", False),
            flare_intensity=preset.get("flare_intensity", 0.0),
            flare_streaks=preset.get("flare_streaks", 8),
            vignette=preset.get("vignette", 0.0),
            chromatic_aberration=preset.get("chromatic_aberration", 0.0),
            bokeh_shape=preset.get("bokeh_shape", "circular"),
            bokeh_swirl=preset.get("bokeh_swirl", 0.0),
        )

        return apply_lens_imperfections(config)

    except Exception:
        return False


def apply_bokeh_to_camera(camera_name: str, shape: str) -> bool:
    """
    Apply bokeh shape to camera via aperture blade count.

    Args:
        camera_name: Name of camera object
        shape: Bokeh shape ("circular", "hexagonal", "octagonal", "rounded")

    Returns:
        True on success, False if failed
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if camera_name not in bpy.data.objects:
            return False

        camera = bpy.data.objects[camera_name]
        if camera.data is None or not hasattr(camera.data, "dof"):
            return False

        blade_count = get_bokeh_blade_count(shape)
        camera.data.dof.aperture_blades = blade_count

        return True

    except Exception:
        return False
