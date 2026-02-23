"""
Blender Compositor Integration

Create Blender compositor node trees from configuration.

Part of Phase 12.1: Compositor (REQ-COMP-05)
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
import math

from .compositor_types import (
    CompositeConfig,
    CompLayer,
    ColorCorrection,
    Transform2D,
    BlendMode,
    LayerSource,
    OutputFormat,
)


def create_composite_nodes(
    config: CompositeConfig,
    scene: Optional[Any] = None,
) -> Optional[Any]:
    """
    Create Blender compositor nodes from configuration.

    Args:
        config: CompositeConfig with layers and settings
        scene: Blender scene (uses bpy.context.scene if None)

    Returns:
        The node tree or None if failed
    """
    try:
        import bpy
    except ImportError:
        print("Blender compositor requires bpy module")
        return None

    # Get scene
    if scene is None:
        scene = bpy.context.scene

    # Enable compositing
    scene.use_nodes = True
    tree = scene.node_tree

    # Clear existing nodes
    for node in tree.nodes:
        tree.nodes.remove(node)

    # Create render layers node
    render_layers = tree.nodes.new("CompositorNodeRLayers")
    render_layers.location = (-400, 0)

    # Create composite output
    composite = tree.nodes.new("CompositorNodeComposite")
    composite.location = (800, 0)

    # Track last node for chaining
    last_node = render_layers
    last_y = 0

    # Create layer nodes
    for i, layer in enumerate(config.get_enabled_layers()):
        layer_node = create_layer_node(tree, layer, render_layers)
        if layer_node:
            layer_node.location = (i * 200, last_y)
            # Connect to composite
            tree.links.new(layer_node.outputs[0], composite.inputs[0])
            last_node = layer_node
            last_y -= 200

    # If no layers, connect render layers directly
    if not config.layers:
        tree.links.new(render_layers.outputs[0], composite.inputs[0])

    # Create output node
    if config.output_path:
        file_output = tree.nodes.new("CompositorNodeOutputFile")
        file_output.base_path = config.output_path
        file_output.format.file_format = _get_blender_format(config.output_format)
        file_output.location = (800, -300)
        tree.links.new(last_node.outputs[0], file_output.inputs[0])

    return tree


def create_layer_node(
    tree: Any,
    layer: CompLayer,
    render_layers: Any,
) -> Optional[Any]:
    """
    Create a compositor node for a layer.

    Returns the final node in the layer's chain.
    """
    try:
        import bpy
    except ImportError:
        return None

    # Create source node based on layer type
    source_node = None

    if layer.source_type == LayerSource.RENDER_PASS:
        # Try to connect to render pass output
        pass_name = layer.source.lower()
        if pass_name in render_layers.outputs:
            source_node = render_layers
        else:
            # Create separate render layers for different passes
            source_node = tree.nodes.new("CompositorNodeRLayers")
            # Would need to configure for specific pass

    elif layer.source_type == LayerSource.IMAGE_SEQUENCE:
        source_node = tree.nodes.new("CompositorNodeImage")
        # Load image sequence
        try:
            import bpy
            img = bpy.data.images.load(layer.source, check_existing=True)
            source_node.image = img
        except:
            pass

    elif layer.source_type == LayerSource.SOLID:
        source_node = tree.nodes.new("CompositorNodeMixRGB")
        source_node.blend_type = 'MIX'
        # Set solid color (would need to create input)

    elif layer.source_type == LayerSource.GRADIENT:
        # Would need to create gradient texture
        source_node = tree.nodes.new("CompositorNodeMixRGB")

    if not source_node:
        return None

    # Apply transform if non-default
    if _transform_non_default(layer.transform):
        transform_node = create_transform_node(tree, layer.transform)
        # Connect source -> transform
        if source_node.outputs:
            tree.links.new(source_node.outputs[0], transform_node.inputs[0])
        source_node = transform_node

    # Apply color correction if non-default
    if _color_correction_non_default(layer.color_correction):
        cc_node = create_color_correction_node(tree, layer.color_correction)
        # Connect source -> cc
        if source_node.outputs:
            tree.links.new(source_node.outputs[0], cc_node.inputs[0])
        source_node = cc_node

    # Apply blend mode and opacity
    if layer.blend_mode != BlendMode.NORMAL or layer.opacity < 1.0:
        blend_node = create_blend_node(tree, layer.blend_mode, layer.opacity)
        # This would need the base layer input too
        if source_node.outputs:
            tree.links.new(source_node.outputs[0], blend_node.inputs[1])
        source_node = blend_node

    return source_node


def create_transform_node(tree: Any, transform: Transform2D) -> Any:
    """Create a transform node for position/rotation/scale."""
    transform_node = tree.nodes.new("CompositorNodeTransform")
    transform_node.location_x = transform.position[0]
    transform_node.location_y = transform.position[1]
    transform_node.rotation = math.degrees(transform.rotation)
    transform_node.scale_x = transform.scale[0]
    transform_node.scale_y = transform.scale[1]
    return transform_node


def create_color_correction_node(tree: Any, cc: ColorCorrection) -> Any:
    """
    Create a color correction node group.

    Blender's color balance node offers lift/gamma/gain or offset/power/slope.
    """
    # Use Color Balance node with LGG mode
    cb_node = tree.nodes.new("CompositorNodeColorBalance")
    cb_node.correction_method = 'LIFT_GAMMA_GAIN'

    # Set lift, gamma, gain
    cb_node.lift = cc.lift
    cb_node.gamma = (cc.gamma, cc.gamma, cc.gamma)
    cb_node.gain = cc.gain

    # For additional controls, would need to chain more nodes:
    # - Brightness/Contrast node
    # - Hue/Saturation node
    # - Curve node for custom curves

    if cc.contrast != 1.0:
        bc_node = tree.nodes.new("CompositorNodeBrightContrast")
        bc_node.contrast = (cc.contrast - 1.0) * 10  # Scale to Blender's range
        tree.links.new(cb_node.outputs[0], bc_node.inputs[0])
        cb_node = bc_node

    if cc.saturation != 1.0:
        hs_node = tree.nodes.new("CompositorNodeHueSat")
        hs_node.saturation = cc.saturation
        tree.links.new(cb_node.outputs[0], hs_node.inputs[0])
        cb_node = hs_node

    return cb_node


def create_blend_node(tree: Any, mode: BlendMode, opacity: float) -> Any:
    """Create a blend/alpha over node."""
    mix_node = tree.nodes.new("CompositorNodeMixRGB")

    # Map blend modes to Blender's mix types
    blend_map = {
        BlendMode.NORMAL: 'MIX',
        BlendMode.ADD: 'ADD',
        BlendMode.MULTIPLY: 'MULTIPLY',
        BlendMode.SCREEN: 'SCREEN',
        BlendMode.OVERLAY: 'OVERLAY',
        BlendMode.DARKEN: 'DARKEN',
        BlendMode.LIGHTEN: 'LIGHTEN',
        BlendMode.COLOR_DODGE: 'DODGE',
        BlendMode.COLOR_BURN: 'BURN',
        BlendMode.HARD_LIGHT: 'HARD_LIGHT',
        BlendMode.SOFT_LIGHT: 'SOFT_LIGHT',
        BlendMode.DIFFERENCE: 'DIFFERENCE',
    }

    mix_node.blend_type = blend_map.get(mode, 'MIX')
    mix_node.use_alpha = True

    # Opacity would be controlled via the Fac input
    # mix_node.inputs[0].default_value = opacity

    return mix_node


def setup_render_passes(scene: Any, passes: List[str]) -> None:
    """
    Enable required render passes in the scene.

    Args:
        scene: Blender scene
        passes: List of pass names to enable
    """
    try:
        import bpy
    except ImportError:
        return

    view_layer = scene.view_layers.active

    pass_map = {
        "combined": lambda vl: setattr(vl, "use_pass_combined", True),
        "z": lambda vl: setattr(vl, "use_pass_z", True),
        "mist": lambda vl: setattr(vl, "use_pass_mist", True),
        "normal": lambda vl: setattr(vl, "use_pass_normal", True),
        "position": lambda vl: setattr(vl, "use_pass_position", True),
        "vector": lambda vl: setattr(vl, "use_pass_vector", True),
        "uv": lambda vl: setattr(vl, "use_pass_uv", True),
        "denoising": lambda vl: setattr(vl, "use_pass_denoising_normal", True),
        "object_index": lambda vl: setattr(vl, "use_pass_object_index", True),
        "material_index": lambda vl: setattr(vl, "use_pass_material_index", True),
        "diffuse_direct": lambda vl: setattr(vl, "use_pass_diffuse_direct", True),
        "diffuse_indirect": lambda vl: setattr(vl, "use_pass_diffuse_indirect", True),
        "diffuse_color": lambda vl: setattr(vl, "use_pass_diffuse_color", True),
        "glossy_direct": lambda vl: setattr(vl, "use_pass_glossy_direct", True),
        "glossy_indirect": lambda vl: setattr(vl, "use_pass_glossy_indirect", True),
        "glossy_color": lambda vl: setattr(vl, "use_pass_glossy_color", True),
        "transmission_direct": lambda vl: setattr(vl, "use_pass_transmission_direct", True),
        "transmission_indirect": lambda vl: setattr(vl, "use_pass_transmission_indirect", True),
        "transmission_color": lambda vl: setattr(vl, "use_pass_transmission_color", True),
        "emission": lambda vl: setattr(vl, "use_pass_emit", True),
        "environment": lambda vl: setattr(vl, "use_pass_environment", True),
        "shadow": lambda vl: setattr(vl, "use_pass_shadow", True),
        "ambient_occlusion": lambda vl: setattr(vl, "use_pass_ambient_occlusion", True),
        "cryptomatte_object": lambda vl: setattr(vl, "use_pass_cryptomatte_object", True),
        "cryptomatte_material": lambda vl: setattr(vl, "use_pass_cryptomatte_material", True),
        "cryptomatte_asset": lambda vl: setattr(vl, "use_pass_cryptomatte_asset", True),
    }

    for pass_name in passes:
        pass_lower = pass_name.lower().replace(" ", "_")
        if pass_lower in pass_map:
            pass_map[pass_lower](view_layer)


def _get_blender_format(format: OutputFormat) -> str:
    """Convert OutputFormat to Blender file format string."""
    format_map = {
        OutputFormat.PNG: 'PNG',
        OutputFormat.JPEG: 'JPEG',
        OutputFormat.EXR: 'OPEN_EXR',
        OutputFormat.TIFF: 'TIFF',
        OutputFormat.WEBM: 'WEBM',
        OutputFormat.MP4: 'FFMPEG',
        OutputFormat.PRORES: 'FFMPEG',
    }
    return format_map.get(format, 'PNG')


def _transform_non_default(transform: Transform2D) -> bool:
    """Check if transform has non-default values."""
    return (
        transform.position != (0.0, 0.0) or
        transform.rotation != 0.0 or
        transform.scale != (1.0, 1.0)
    )


def _color_correction_non_default(cc: ColorCorrection) -> bool:
    """Check if color correction has non-default values."""
    return (
        cc.exposure != 0.0 or
        cc.contrast != 1.0 or
        cc.saturation != 1.0 or
        cc.gamma != 1.0 or
        cc.lift != (0.0, 0.0, 0.0) or
        cc.gain != (1.0, 1.0, 1.0) or
        cc.offset != (0.0, 0.0, 0.0) or
        cc.hue_shift != 0.0 or
        cc.temperature != 0.0 or
        cc.tint != 0.0
    )


# ==================== Convenience Functions ====================

def create_basic_composite(scene: Optional[Any] = None) -> Any:
    """Create a basic composite setup with render layers -> composite."""
    try:
        import bpy
    except ImportError:
        return None

    if scene is None:
        scene = bpy.context.scene

    scene.use_nodes = True
    tree = scene.node_tree

    # Clear existing
    for node in tree.nodes:
        tree.nodes.remove(node)

    # Create nodes
    rl = tree.nodes.new("CompositorNodeRLayers")
    comp = tree.nodes.new("CompositorNodeComposite")

    rl.location = (-300, 0)
    comp.location = (300, 0)

    tree.links.new(rl.outputs[0], comp.inputs[0])

    return tree


def add_color_correction_to_composite(
    tree: Any,
    cc: ColorCorrection,
    insert_before_output: bool = True,
) -> Any:
    """Add color correction to an existing composite tree."""
    cc_node = create_color_correction_node(tree, cc)
    cc_node.location = (0, 0)

    if insert_before_output:
        # Find composite output and insert before it
        for node in tree.nodes:
            if node.type == 'COMPOSITE':
                # Find connected node
                for link in tree.links:
                    if link.to_node == node:
                        # Insert cc_node between
                        from_node = link.from_node
                        from_socket = link.from_socket
                        to_socket = link.to_socket
                        tree.links.remove(link)
                        tree.links.new(from_socket, cc_node.inputs[0])
                        tree.links.new(cc_node.outputs[0], to_socket)
                        break
                break

    return cc_node
