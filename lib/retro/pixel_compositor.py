"""
Pixel Art Compositor Integration

Integrates pixel art conversion with Blender's compositor system
for real-time preview and rendering.
"""

from __future__ import annotations
from typing import Any, Dict, Optional, Tuple, List
import os

try:
    import bpy
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    bpy = None  # type: ignore

from lib.retro.pixel_types import PixelationConfig, PixelStyle
from lib.retro.pixelator import pixelate, downscale_image, pixelate_block
from lib.retro.quantizer import quantize_colors


def create_pixelator_nodes(
    node_tree: Any,
    config: PixelationConfig,
    input_node_name: str = "Render Layers",
    output_name: str = "Pixel Art Output"
) -> Dict[str, Any]:
    """
    Create Blender compositor nodes for pixelation.

    Creates a node setup that applies pixelation effects
    in the Blender compositor.

    Args:
        node_tree: Blender compositor node tree
        config: Pixelation configuration
        input_node_name: Name of input node to connect from
        output_name: Name for output node

    Returns:
        Dictionary of created nodes
    """
    if not HAS_BLENDER:
        raise ImportError("Blender is required for compositor integration")

    nodes = node_tree.nodes
    links = node_tree.links

    created_nodes: Dict[str, Any] = {}

    # Find input node
    input_node = nodes.get(input_node_name)
    if input_node is None:
        # Create render layers if not found
        input_node = nodes.new("CompositorNodeRLayers")
        input_node.name = input_node_name
    created_nodes["input"] = input_node

    # Create scale node for downscaling
    scale_node = nodes.new("CompositorNodeScale")
    scale_node.name = "Pixel Downscale"
    scale_node.space = "RENDER_SIZE"

    # Calculate scale factor
    if config.target_resolution[0] > 0 and config.target_resolution[1] > 0:
        # Use target resolution
        scale_node.inputs[0].default_value = 100  # Will be overridden
        scale_node.inputs[1].default_value = 100
        scale_node.frame_method = "CROP" if config.aspect_ratio_mode == "crop" else "FIT"
    created_nodes["scale"] = scale_node

    # Create pixelation using translate trick
    # This creates chunky pixels by scaling down and back up
    if config.style.pixel_size > 1:
        # Scale down
        pixel_down_node = nodes.new("CompositorNodeScale")
        pixel_down_node.name = "Pixel Block Down"
        pixel_down_node.space = "ABSOLUTE"
        pixel_down_node.inputs[0].default_value = 1.0 / config.style.pixel_size
        pixel_down_node.inputs[1].default_value = 1.0 / config.style.pixel_size
        pixel_down_node.interpolation = "Nearest"
        created_nodes["pixel_down"] = pixel_down_node

        # Scale back up
        pixel_up_node = nodes.new("CompositorNodeScale")
        pixel_up_node.name = "Pixel Block Up"
        pixel_up_node.space = "ABSOLUTE"
        pixel_up_node.inputs[0].default_value = config.style.pixel_size
        pixel_up_node.inputs[1].default_value = config.style.pixel_size
        pixel_up_node.interpolation = "Nearest"
        created_nodes["pixel_up"] = pixel_up_node

    # Create posterize effect using color ramp
    if config.style.posterize_levels > 0:
        posterize_node = nodes.new("CompositorNodePosterize")
        posterize_node.name = "Posterize"
        posterize_node.steps = config.style.posterize_levels
        created_nodes["posterize"] = posterize_node

    # Create output node
    output_node = nodes.new("CompositorNodeComposite")
    output_node.name = output_name
    created_nodes["output"] = output_node

    # Connect nodes
    current_output = input_node.outputs[0]  # Image output

    # Connect through scale
    if "scale" in created_nodes:
        links.new(current_output, created_nodes["scale"].inputs[0])
        current_output = created_nodes["scale"].outputs[0]

    # Connect through pixelation
    if "pixel_down" in created_nodes:
        links.new(current_output, created_nodes["pixel_down"].inputs[0])
        current_output = created_nodes["pixel_down"].outputs[0]

    if "pixel_up" in created_nodes:
        links.new(current_output, created_nodes["pixel_up"].inputs[0])
        current_output = created_nodes["pixel_up"].outputs[0]

    # Connect through posterize
    if "posterize" in created_nodes:
        links.new(current_output, created_nodes["posterize"].inputs[0])
        current_output = created_nodes["posterize"].outputs[0]

    # Connect to output
    links.new(current_output, created_nodes["output"].inputs[0])

    return created_nodes


def setup_pixelator_pass(
    node_tree: Any,
    config: PixelationConfig,
    pass_name: str = "PixelArt"
) -> str:
    """
    Set up pixelation as a separate render pass.

    Creates a file output node that saves pixelated version
    alongside the main render.

    Args:
        node_tree: Blender compositor node tree
        config: Pixelation configuration
        pass_name: Name for the output pass

    Returns:
        Path pattern for the output files
    """
    if not HAS_BLENDER:
        raise ImportError("Blender is required for compositor integration")

    nodes = node_tree.nodes
    links = node_tree.links

    # Create pixelation nodes
    pixel_nodes = create_pixelator_nodes(
        node_tree,
        config,
        input_node_name="Render Layers",
        output_name=f"{pass_name}_Composite"
    )

    # Create file output node
    file_output = nodes.new("CompositorNodeOutputFile")
    file_output.name = f"{pass_name}_Output"
    file_output.format.file_format = "PNG"
    file_output.format.color_mode = "RGBA"
    file_output.format.color_depth = "8"
    file_output.base_path = "//render/pixel/"
    file_output.file_slots[0].path = f"{pass_name}_"

    # Connect pixelated output to file output
    # Find the last processing node before composite output
    last_node = pixel_nodes.get("posterize") or \
                pixel_nodes.get("pixel_up") or \
                pixel_nodes.get("scale") or \
                pixel_nodes["input"]

    links.new(last_node.outputs[0], file_output.inputs[0])

    return f"//render/pixel/{pass_name}_"


def bake_pixelation(
    render_path: str,
    config: PixelationConfig,
    output_path: str,
    use_alpha: bool = True
) -> str:
    """
    Apply pixelation to a rendered image.

    Post-processes a rendered image to create pixel art version.

    Args:
        render_path: Path to source render
        config: Pixelation configuration
        output_path: Path for pixelated output
        use_alpha: Whether to preserve alpha channel

    Returns:
        Path to the pixelated output file
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError("PIL/Pillow is required for image processing")

    # Load the rendered image
    source_image = Image.open(render_path)

    # Preserve alpha if needed
    if use_alpha and source_image.mode == "RGBA":
        alpha = source_image.split()[3]
        # Process RGB only
        rgb_image = source_image.convert("RGB")
        result = pixelate(rgb_image, config)

        if result.image:
            # Restore alpha
            result_image = result.image.convert("RGBA")
            result_image.putalpha(alpha.resize(result_image.size))
            result_image.save(output_path)
        else:
            source_image.save(output_path)
    else:
        result = pixelate(source_image, config)
        if result.image:
            result.image.save(output_path)
        else:
            source_image.save(output_path)

    return output_path


def create_scale_node(
    node_tree: Any,
    scale: float,
    filter_type: str = "nearest"
) -> Any:
    """
    Create a scale node for down/upscaling.

    Args:
        node_tree: Blender compositor node tree
        scale: Scale factor (e.g., 0.5 for half size)
        filter_type: Interpolation type (nearest, bilinear, bicubic)

    Returns:
        Created scale node
    """
    if not HAS_BLENDER:
        raise ImportError("Blender is required for compositor integration")

    nodes = node_tree.nodes

    scale_node = nodes.new("CompositorNodeScale")
    scale_node.name = f"Scale_{scale}"

    if scale < 1:
        scale_node.space = "RELATIVE"
        scale_node.inputs[0].default_value = scale
        scale_node.inputs[1].default_value = scale
    else:
        scale_node.space = "ABSOLUTE"
        scale_node.inputs[0].default_value = scale
        scale_node.inputs[1].default_value = scale

    # Set interpolation
    interp_map = {
        "nearest": "Nearest",
        "bilinear": "Bilinear",
        "bicubic": "Bicubic",
    }
    scale_node.interpolation = interp_map.get(filter_type, "Nearest")

    return scale_node


def create_posterize_node(
    node_tree: Any,
    levels: int
) -> Any:
    """
    Create a posterize node.

    Args:
        node_tree: Blender compositor node tree
        levels: Number of color levels

    Returns:
        Created posterize node
    """
    if not HAS_BLENDER:
        raise ImportError("Blender is required for compositor integration")

    nodes = node_tree.nodes

    posterize_node = nodes.new("CompositorNodePosterize")
    posterize_node.name = f"Posterize_{levels}"
    posterize_node.steps = levels

    return posterize_node


def create_color_ramp_quantize(
    node_tree: Any,
    colors: List[Tuple[float, float, float, float]]
) -> Any:
    """
    Create a color ramp for palette quantization.

    Args:
        node_tree: Blender compositor node tree
        colors: List of RGBA color tuples (0-1 range)

    Returns:
        Created color ramp node
    """
    if not HAS_BLENDER:
        raise ImportError("Blender is required for compositor integration")

    nodes = node_tree.nodes

    ramp_node = nodes.new("CompositorNodeValToRGB")
    ramp_node.name = "Palette_Ramp"

    # Clear existing stops
    ramp_node.color_ramp.elements.clear()

    # Add color stops
    for i, color in enumerate(colors):
        position = i / (len(colors) - 1) if len(colors) > 1 else 0.5
        element = ramp_node.color_ramp.elements.new(position)
        element.color = color

    return ramp_node


def setup_pixel_preview(
    node_tree: Any,
    config: PixelationConfig
) -> Dict[str, Any]:
    """
    Set up a pixel art preview in the viewport.

    Creates nodes for real-time pixel art preview while working.

    Args:
        node_tree: Blender compositor node tree
        config: Pixelation configuration

    Returns:
        Dictionary of created nodes
    """
    if not HAS_BLENDER:
        raise ImportError("Blender is required for compositor integration")

    nodes = node_tree.nodes
    links = node_tree.links

    created_nodes: Dict[str, Any] = {}

    # Enable backdrop for preview
    node_tree.use_backdrop = True

    # Get or create render layers
    render_layers = nodes.get("Render Layers")
    if render_layers is None:
        render_layers = nodes.new("CompositorNodeRLayers")
    created_nodes["input"] = render_layers

    # Create viewer node for preview
    viewer = nodes.new("CompositorNodeViewer")
    viewer.name = "Pixel Preview Viewer"
    created_nodes["viewer"] = viewer

    # Create pixelation nodes
    pixel_nodes = create_pixelator_nodes(
        node_tree,
        config,
        input_node_name="Render Layers",
        output_name="Pixel_Preview_Output"
    )
    created_nodes.update(pixel_nodes)

    # Also connect to viewer
    last_node = pixel_nodes.get("posterize") or \
                pixel_nodes.get("pixel_up") or \
                pixel_nodes.get("scale") or \
                render_layers

    links.new(last_node.outputs[0], viewer.inputs[0])

    return created_nodes


def apply_pixel_style_to_scene(
    scene: Any,
    config: PixelationConfig
) -> None:
    """
    Apply pixel art settings to a Blender scene.

    Configures render settings to match pixel art requirements.

    Args:
        scene: Blender scene object
        config: Pixelation configuration
    """
    if not HAS_BLENDER:
        raise ImportError("Blender is required")

    # Set resolution
    if config.target_resolution[0] > 0 and config.target_resolution[1] > 0:
        scene.render.resolution_x = config.target_resolution[0]
        scene.render.resolution_y = config.target_resolution[1]
        scene.render.pixel_aspect_x = 1.0
        scene.render.pixel_aspect_y = 1.0

    # Set to use nearest filtering for preview
    if config.scaling_filter == "nearest":
        # Disable anti-aliasing
        if hasattr(scene.render, "use_antialiasing"):
            scene.render.use_antialiasing = False

    # Enable compositor
    scene.use_nodes = True


def get_pixel_node_group(
    config: PixelationConfig,
    name: str = "PixelArt"
) -> Any:
    """
    Create a reusable node group for pixel art.

    Creates a node group that can be reused across different
    compositor setups.

    Args:
        config: Pixelation configuration
        name: Name for the node group

    Returns:
        Created node group
    """
    if not HAS_BLENDER:
        raise ImportError("Blender is required for compositor integration")

    # Check if group already exists
    existing = bpy.data.node_groups.get(name)
    if existing:
        bpy.data.node_groups.remove(existing)

    # Create new node group
    node_group = bpy.data.node_groups.new(name, "CompositorNodeTree")

    # Create input/output sockets
    node_group.inputs.new("NodeSocketColor", "Image")
    node_group.outputs.new("NodeSocketColor", "Image")

    # Add nodes to group
    nodes = create_pixelator_nodes(node_group, config)

    # Create group input/output nodes
    group_input = node_group.nodes.new("NodeGroupInput")
    group_output = node_group.nodes.new("NodeGroupOutput")

    # Connect input
    node_group.links.new(group_input.outputs[0], nodes["scale"].inputs[0])

    # Connect output
    node_group.links.new(nodes["output"].outputs[0], group_output.inputs[0])

    return node_group
