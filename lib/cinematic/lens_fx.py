"""
Lens FX Module - Post-Process Lens Effects via Compositor

Extends lenses.py with additional post-process effects via
Blender compositor nodes (Glare, LensDistortion, CurveRGB).

Compositor Pipeline Order:
1. Geometric distortions (chromatic aberration, lens distortion)
2. Luminance effects (glare, bloom)
3. Color grading
4. Film effects (grain, vignette)

Usage:
    from lib.cinematic.lens_fx import apply_lens_fx, setup_bloom, remove_lens_fx
    from lib.cinematic.types import LensFXConfig

    # Apply from config
    config = LensFXConfig(
        enabled=True,
        bloom_intensity=0.3,
        vignette_intensity=0.2
    )
    apply_lens_fx(config)

    # Apply preset
    apply_lens_fx_preset("cinematic")

    # Remove all effects
    remove_lens_fx()
"""

from __future__ import annotations
from typing import Dict, Any, Tuple, Optional, List

from .types import LensFXConfig
from .enums import LensFXType

# Blender availability check
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    BLENDER_AVAILABLE = False

# Node name constants
NODE_BLOOM = "LensFX_Bloom"
NODE_FLARE = "LensFX_Flare"
NODE_VIGNETTE_MASK = "LensFX_VignetteMask"
NODE_VIGNETTE_MIX = "LensFX_VignetteMix"
NODE_CHROMATIC = "LensFX_Chromatic"
NODE_GRAIN = "LensFX_Grain"
NODE_GRAIN_MIX = "LensFX_GrainMix"


def _setup_compositor() -> bool:
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


def _get_current_output_node(tree: Any) -> Any:
    """
    Get the node currently connected to Composite input.

    Returns Render Layers if no effects applied, or the last effect node.
    """
    composite = tree.nodes.get('Composite')
    if not composite:
        return None

    # Get the node connected to Composite's Image input
    for link in tree.links:
        if link.to_node == composite and link.to_socket.name == 'Image':
            return link.from_node

    # Default to Render Layers
    return tree.nodes.get('Render Layers')


def apply_lens_fx(config: LensFXConfig) -> bool:
    """
    Apply all enabled effects from config via compositor.

    Pipeline order:
    1. Chromatic aberration (geometric)
    2. Bloom (luminance)
    3. Flare (luminance)
    4. Vignette (film effect)
    5. Film grain (film effect)

    Args:
        config: LensFXConfig with effect settings

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    if not config.enabled:
        return True

    try:
        if not _setup_compositor():
            return False

        scene = bpy.context.scene
        tree = scene.node_tree

        # Get render layers and composite nodes
        render_layers = tree.nodes.get('Render Layers')
        composite = tree.nodes.get('Composite')

        if not render_layers or not composite:
            return False

        # Track the current output node (start with Render Layers)
        current_output = render_layers

        # Remove existing lens FX nodes first
        _remove_lens_fx_nodes(tree, reconnect=False)

        # 1. Chromatic aberration (geometric distortion)
        if config.chromatic_aberration > 0:
            ca_node = tree.nodes.new('CompositorNodeLensdist')
            ca_node.name = NODE_CHROMATIC
            ca_node.use_fit = False
            ca_node.use_jitter = False
            ca_node.use_projector = False
            ca_node.dispersion = config.chromatic_aberration * 100  # Scale for visibility

            tree.links.new(current_output.outputs['Image'], ca_node.inputs['Image'])
            current_output = ca_node

        # 2. Bloom (luminance effect via Glare node)
        if config.bloom_intensity > 0:
            bloom_node = tree.nodes.new('CompositorNodeGlare')
            bloom_node.name = NODE_BLOOM
            bloom_node.glare_type = 'FOG_GLOW'
            bloom_node.quality = 'MEDIUM'
            # Map intensity (0-1) to threshold (1.0-0.1, lower = more bloom)
            bloom_node.threshold = max(0.1, 1.0 - config.bloom_intensity)
            bloom_node.size = 6  # Glow size

            tree.links.new(current_output.outputs['Image'], bloom_node.inputs['Image'])
            current_output = bloom_node

        # 3. Lens flare (luminance effect)
        if config.flare_intensity > 0:
            flare_node = tree.nodes.new('CompositorNodeGlare')
            flare_node.name = NODE_FLARE
            flare_node.glare_type = 'GHOSTS'
            flare_node.quality = 'MEDIUM'
            flare_node.streaks = config.flare_ghost_count
            flare_node.threshold = max(0.5, 1.0 - config.flare_intensity)

            tree.links.new(current_output.outputs['Image'], flare_node.inputs['Image'])
            current_output = flare_node

        # 4. Vignette (film effect)
        if config.vignette_intensity > 0:
            # Create elliptical mask
            mask = tree.nodes.new('CompositorNodeEllipseMask')
            mask.name = NODE_VIGNETTE_MASK
            mask.mask_type = 'ELLIPSE'
            mask.x = 0.5
            mask.y = 0.5
            mask.width = config.vignette_radius
            mask.height = config.vignette_radius
            mask.rotation = 0.0

            # Create invert node for mask
            invert = tree.nodes.new('CompositorNodeInvert')
            invert.name = f"{NODE_VIGNETTE_MASK}_Invert"
            invert.invert_rgb = False

            # Create mix node
            mix = tree.nodes.new('CompositorNodeMixRGB')
            mix.name = NODE_VIGNETTE_MIX
            mix.blend_type = 'MULTIPLY'
            mix.inputs['Fac'].default_value = config.vignette_intensity

            # Connect mask -> invert -> mix[0]
            tree.links.new(mask.outputs['Mask'], invert.inputs['Color'])
            tree.links.new(invert.outputs['Color'], mix.inputs[0])

            # Connect current -> mix[1]
            tree.links.new(current_output.outputs['Image'], mix.inputs[1])

            current_output = mix

        # 5. Film grain (film effect)
        if config.film_grain > 0:
            # Create noise texture for grain
            grain = tree.nodes.new('CompositorNodeNoise')
            grain.name = NODE_GRAIN
            grain.scale = 200.0  # Fine grain
            grain.detail = 1.0
            grain.distortion = 0.0

            # Mix grain with image
            grain_mix = tree.nodes.new('CompositorNodeMixRGB')
            grain_mix.name = NODE_GRAIN_MIX
            grain_mix.blend_type = 'OVERLAY'
            grain_mix.inputs['Fac'].default_value = config.film_grain

            # Connect noise -> mix[2]
            tree.links.new(grain.outputs['Color'], grain_mix.inputs[2])

            # Connect current -> mix[1]
            tree.links.new(current_output.outputs['Image'], grain_mix.inputs[1])

            current_output = grain_mix

        # Connect final output to composite
        tree.links.new(current_output.outputs['Image'], composite.inputs['Image'])

        return True

    except Exception:
        return False


def setup_bloom(intensity: float, threshold: float) -> bool:
    """
    Set up bloom effect via glare compositor node.

    Creates a fog glow effect for bright areas.

    Args:
        intensity: Bloom intensity (0-1), maps to threshold adjustment
        threshold: Brightness threshold for bloom cutoff

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not _setup_compositor():
            return False

        scene = bpy.context.scene
        tree = scene.node_tree

        render_layers = tree.nodes.get('Render Layers')
        composite = tree.nodes.get('Composite')

        if not render_layers or not composite:
            return False

        # Remove existing bloom node if any
        existing = tree.nodes.get(NODE_BLOOM)
        if existing:
            tree.nodes.remove(existing)

        # Create bloom node
        bloom_node = tree.nodes.new('CompositorNodeGlare')
        bloom_node.name = NODE_BLOOM
        bloom_node.glare_type = 'FOG_GLOW'
        bloom_node.quality = 'MEDIUM'
        bloom_node.threshold = threshold if threshold > 0 else max(0.1, 1.0 - intensity)
        bloom_node.size = 6

        # Get current connection
        current_output = _get_current_output_node(tree)

        # Disconnect composite and insert bloom
        for link in list(tree.links):
            if link.to_node == composite and link.to_socket.name == 'Image':
                tree.links.remove(link)

        tree.links.new(current_output.outputs['Image'], bloom_node.inputs['Image'])
        tree.links.new(bloom_node.outputs['Image'], composite.inputs['Image'])

        return True

    except Exception:
        return False


def setup_flare(intensity: float, ghost_count: int) -> bool:
    """
    Set up lens flare via glare node with ghosts type.

    Args:
        intensity: Flare intensity (0-1)
        ghost_count: Number of flare ghost elements

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not _setup_compositor():
            return False

        scene = bpy.context.scene
        tree = scene.node_tree

        render_layers = tree.nodes.get('Render Layers')
        composite = tree.nodes.get('Composite')

        if not render_layers or not composite:
            return False

        # Remove existing flare node if any
        existing = tree.nodes.get(NODE_FLARE)
        if existing:
            tree.nodes.remove(existing)

        # Create flare node
        flare_node = tree.nodes.new('CompositorNodeGlare')
        flare_node.name = NODE_FLARE
        flare_node.glare_type = 'GHOSTS'
        flare_node.quality = 'MEDIUM'
        flare_node.streaks = ghost_count if 1 <= ghost_count <= 16 else 4
        flare_node.threshold = max(0.5, 1.0 - intensity)

        # Get current connection
        current_output = _get_current_output_node(tree)

        # Disconnect composite and insert flare
        for link in list(tree.links):
            if link.to_node == composite and link.to_socket.name == 'Image':
                tree.links.remove(link)

        tree.links.new(current_output.outputs['Image'], flare_node.inputs['Image'])
        tree.links.new(flare_node.outputs['Image'], composite.inputs['Image'])

        return True

    except Exception:
        return False


def setup_vignette(intensity: float, radius: float) -> bool:
    """
    Set up vignette via elliptical mask + multiply mix node.

    Creates darker edges around the frame.

    Args:
        intensity: Vignette darkness (0-1)
        radius: Vignette radius/size (0-1, larger = less visible)

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not _setup_compositor():
            return False

        scene = bpy.context.scene
        tree = scene.node_tree

        render_layers = tree.nodes.get('Render Layers')
        composite = tree.nodes.get('Composite')

        if not render_layers or not composite:
            return False

        # Remove existing vignette nodes if any
        for name in [NODE_VIGNETTE_MASK, NODE_VIGNETTE_MIX, f"{NODE_VIGNETTE_MASK}_Invert"]:
            existing = tree.nodes.get(name)
            if existing:
                tree.nodes.remove(existing)

        # Create elliptical mask
        mask = tree.nodes.new('CompositorNodeEllipseMask')
        mask.name = NODE_VIGNETTE_MASK
        mask.mask_type = 'ELLIPSE'
        mask.x = 0.5
        mask.y = 0.5
        mask.width = radius if radius > 0 else 0.8
        mask.height = radius if radius > 0 else 0.8
        mask.rotation = 0.0

        # Create invert node
        invert = tree.nodes.new('CompositorNodeInvert')
        invert.name = f"{NODE_VIGNETTE_MASK}_Invert"
        invert.invert_rgb = False

        # Create mix node
        mix = tree.nodes.new('CompositorNodeMixRGB')
        mix.name = NODE_VIGNETTE_MIX
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Fac'].default_value = intensity if intensity > 0 else 0.3

        # Connect mask -> invert -> mix[0]
        tree.links.new(mask.outputs['Mask'], invert.inputs['Color'])
        tree.links.new(invert.outputs['Color'], mix.inputs[0])

        # Get current connection
        current_output = _get_current_output_node(tree)

        # Disconnect composite and insert vignette
        for link in list(tree.links):
            if link.to_node == composite and link.to_socket.name == 'Image':
                tree.links.remove(link)

        tree.links.new(current_output.outputs['Image'], mix.inputs[1])
        tree.links.new(mix.outputs['Image'], composite.inputs['Image'])

        return True

    except Exception:
        return False


def setup_chromatic_aberration(strength: float) -> bool:
    """
    Set up chromatic aberration via lens distortion node.

    Creates RGB color fringing at edges.

    Args:
        strength: CA strength/amount (typically 0.001-0.01)

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not _setup_compositor():
            return False

        scene = bpy.context.scene
        tree = scene.node_tree

        render_layers = tree.nodes.get('Render Layers')
        composite = tree.nodes.get('Composite')

        if not render_layers or not composite:
            return False

        # Remove existing CA node if any
        existing = tree.nodes.get(NODE_CHROMATIC)
        if existing:
            tree.nodes.remove(existing)

        # Create lens distortion node
        ca_node = tree.nodes.new('CompositorNodeLensdist')
        ca_node.name = NODE_CHROMATIC
        ca_node.use_fit = False
        ca_node.use_jitter = False
        ca_node.use_projector = False
        ca_node.dispersion = strength * 100 if strength > 0 else 0.5

        # Get current connection
        current_output = _get_current_output_node(tree)

        # Disconnect composite and insert CA
        for link in list(tree.links):
            if link.to_node == composite and link.to_socket.name == 'Image':
                tree.links.remove(link)

        tree.links.new(current_output.outputs['Image'], ca_node.inputs['Image'])
        tree.links.new(ca_node.outputs['Image'], composite.inputs['Image'])

        return True

    except Exception:
        return False


def setup_film_grain(intensity: float) -> bool:
    """
    Set up film grain via noise texture + overlay mix.

    Adds subtle texture to the image.

    Args:
        intensity: Grain visibility (0-1)

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        if not _setup_compositor():
            return False

        scene = bpy.context.scene
        tree = scene.node_tree

        render_layers = tree.nodes.get('Render Layers')
        composite = tree.nodes.get('Composite')

        if not render_layers or not composite:
            return False

        # Remove existing grain nodes if any
        for name in [NODE_GRAIN, NODE_GRAIN_MIX]:
            existing = tree.nodes.get(name)
            if existing:
                tree.nodes.remove(existing)

        # Create noise node
        grain = tree.nodes.new('CompositorNodeNoise')
        grain.name = NODE_GRAIN
        grain.scale = 200.0
        grain.detail = 1.0
        grain.distortion = 0.0

        # Create mix node
        mix = tree.nodes.new('CompositorNodeMixRGB')
        mix.name = NODE_GRAIN_MIX
        mix.blend_type = 'OVERLAY'
        mix.inputs['Fac'].default_value = intensity if intensity > 0 else 0.1

        # Connect noise -> mix[2]
        tree.links.new(grain.outputs['Color'], mix.inputs[2])

        # Get current connection
        current_output = _get_current_output_node(tree)

        # Disconnect composite and insert grain
        for link in list(tree.links):
            if link.to_node == composite and link.to_socket.name == 'Image':
                tree.links.remove(link)

        tree.links.new(current_output.outputs['Image'], mix.inputs[1])
        tree.links.new(mix.outputs['Image'], composite.inputs['Image'])

        return True

    except Exception:
        return False


def _remove_lens_fx_nodes(tree: Any, reconnect: bool = True) -> int:
    """
    Remove all lens FX nodes from the compositor tree.

    Args:
        tree: Compositor node tree
        reconnect: If True, reconnect Render Layers directly to Composite

    Returns:
        Number of nodes removed
    """
    lens_node_names = [
        NODE_BLOOM, NODE_FLARE, NODE_VIGNETTE_MASK,
        f"{NODE_VIGNETTE_MASK}_Invert", NODE_VIGNETTE_MIX,
        NODE_CHROMATIC, NODE_GRAIN, NODE_GRAIN_MIX
    ]

    removed = 0
    for name in lens_node_names:
        node = tree.nodes.get(name)
        if node:
            tree.nodes.remove(node)
            removed += 1

    if reconnect:
        # Reconnect Render Layers directly to Composite
        render_layers = tree.nodes.get('Render Layers')
        composite = tree.nodes.get('Composite')

        if render_layers and composite:
            # Remove existing links to composite
            for link in list(tree.links):
                if link.to_node == composite and link.to_socket.name == 'Image':
                    tree.links.remove(link)

            # Create direct connection
            tree.links.new(render_layers.outputs['Image'], composite.inputs['Image'])

    return removed


def remove_lens_fx() -> bool:
    """
    Remove all lens FX nodes from compositor.

    Restores direct connection from Render Layers to Composite.

    Returns:
        True if successful
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
        _remove_lens_fx_nodes(tree, reconnect=True)

        return True

    except Exception:
        return False


def apply_lens_fx_preset(preset_name: str) -> bool:
    """
    Apply lens FX preset by name.

    Args:
        preset_name: Name of preset from lens_fx_presets.yaml

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        from .preset_loader import get_lens_fx_preset

        preset = get_lens_fx_preset(preset_name)

        config = LensFXConfig(
            enabled=preset.get("enabled", True),
            bloom_intensity=preset.get("bloom_intensity", 0.0),
            bloom_threshold=preset.get("bloom_threshold", 0.8),
            flare_intensity=preset.get("flare_intensity", 0.0),
            flare_ghost_count=preset.get("flare_ghost_count", 4),
            vignette_intensity=preset.get("vignette_intensity", 0.0),
            vignette_radius=preset.get("vignette_radius", 0.8),
            chromatic_aberration=preset.get("chromatic_aberration", 0.0),
            film_grain=preset.get("film_grain", 0.0),
        )

        return apply_lens_fx(config)

    except Exception:
        return False


def get_active_effects() -> List[str]:
    """
    Return list of currently active lens effect names.

    Returns:
        List of effect type names (bloom, flare, vignette, etc.)
    """
    if not BLENDER_AVAILABLE:
        return []

    active = []

    try:
        if not hasattr(bpy, "context") or bpy.context.scene is None:
            return []

        scene = bpy.context.scene
        if not scene.use_nodes or scene.node_tree is None:
            return []

        tree = scene.node_tree

        # Check for each effect node
        if tree.nodes.get(NODE_BLOOM):
            active.append("bloom")
        if tree.nodes.get(NODE_FLARE):
            active.append("flare")
        if tree.nodes.get(NODE_VIGNETTE_MASK):
            active.append("vignette")
        if tree.nodes.get(NODE_CHROMATIC):
            active.append("chromatic_aberration")
        if tree.nodes.get(NODE_GRAIN):
            active.append("film_grain")

    except Exception:
        pass

    return active
