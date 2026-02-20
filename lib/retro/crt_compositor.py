"""
CRT Compositor Integration Module

Provides Blender compositor node setup for CRT effects.
Enables real-time CRT simulation in Blender's compositor.

Example Usage:
    from lib.retro.crt_compositor import setup_crt_compositing
    from lib.retro.crt_types import CRTConfig

    config = CRTConfig.for_preset("crt_arcade")
    setup_crt_compositing(scene.node_tree, config)
"""

from typing import Dict, Any, List, Optional, Tuple

from lib.retro.crt_types import (
    CRTConfig,
    ScanlineConfig,
    PhosphorConfig,
    CurvatureConfig,
)


# Node group name constant
CRT_NODE_GROUP_NAME = "CRT_Effects"


# =============================================================================
# Node Creation Functions
# =============================================================================

def create_crt_node_group(config: CRTConfig) -> Dict[str, Any]:
    """
    Create Blender compositor node group configuration for CRT effects.

    Returns a dictionary with node setup parameters that can be
    used to create the actual nodes in Blender.

    Args:
        config: CRT configuration

    Returns:
        Dictionary with node group configuration
    """
    nodes = []

    # 1. Color adjustments (brightness, contrast, saturation, gamma)
    if config.brightness != 1.0 or config.contrast != 1.0:
        nodes.append({
            "type": "CompositorNodeBrightContrast",
            "name": "CRT_BrightContrast",
            "inputs": {
                "bright": (config.brightness - 1.0) * 100,  # Blender uses -100 to 100
                "contrast": (config.contrast - 1.0) * 100,
            }
        })

    # 2. Gamma correction
    if config.gamma != 2.2:
        nodes.append({
            "type": "CompositorNodeGamma",
            "name": "CRT_Gamma",
            "inputs": {
                "gamma": config.gamma,
            }
        })

    # 3. Curvature (using lens distortion)
    if config.curvature.enabled and config.curvature.amount > 0:
        nodes.append({
            "type": "CompositorNodeLensdist",
            "name": "CRT_Curvature",
            "inputs": {
                "dispersion": config.curvature.amount * 0.1,
            },
            "use_dispersion": True,
        })

    # 4. Chromatic aberration (using separate RGB and transform)
    if config.chromatic_aberration > 0:
        nodes.append({
            "type": "CompositorNodeChromaMatte",
            "name": "CRT_Chromatic",
            "inputs": {
                "threshold": config.chromatic_aberration * 100,
            }
        })

    # 5. Scanlines (using curve or math nodes)
    if config.scanlines.enabled:
        nodes.extend(create_scanline_node_config(config.scanlines))

    # 6. Phosphor mask (using RGB curves)
    if config.phosphor.enabled:
        nodes.extend(create_phosphor_node_config(config.phosphor))

    # 7. Bloom (using blur and mix)
    if config.bloom > 0:
        nodes.extend([
            {
                "type": "CompositorNodeBrightness",
                "name": "CRT_Bloom_Threshold",
                "inputs": {
                    "bright": 2.0,
                }
            },
            {
                "type": "CompositorNodeBlur",
                "name": "CRT_Bloom_Blur",
                "filter_type": "GAUSSIAN",
                "size_x": int(10 * config.bloom),
                "size_y": int(10 * config.bloom),
            },
            {
                "type": "CompositorNodeMixRGB",
                "name": "CRT_Bloom_Mix",
                "blend_type": "ADD",
                "inputs": {
                    "fac": config.bloom,
                }
            }
        ])

    # 8. Vignette (using ellipse mask)
    if config.curvature.vignette_amount > 0:
        nodes.extend([
            {
                "type": "CompositorNodeEllipseMask",
                "name": "CRT_Vignette_Mask",
                "mask_type": "MULTIPLY",
                "inputs": {
                    "x": 0.5,
                    "y": 0.5,
                    "width": 1.0 - config.curvature.vignette_amount * 0.5,
                    "height": 1.0 - config.curvature.vignette_amount * 0.5,
                    "rotation": 0,
                }
            },
            {
                "type": "CompositorNodeMixRGB",
                "name": "CRT_Vignette_Mix",
                "blend_type": "MULTIPLY",
            }
        ])

    # 9. Noise (using noise texture if available)
    if config.noise > 0:
        nodes.append({
            "type": "CompositorNodeNoise",
            "name": "CRT_Noise",
            "inputs": {
                "scale": 100,
            },
            "noise_intensity": config.noise,
        })

    return {
        "name": CRT_NODE_GROUP_NAME,
        "nodes": nodes,
        "config": config.to_dict(),
    }


def create_scanline_node_config(config: ScanlineConfig) -> List[Dict[str, Any]]:
    """
    Create node configuration for scanline effect.

    Args:
        config: Scanline configuration

    Returns:
        List of node configuration dictionaries
    """
    nodes = []

    # Scanlines are tricky in compositor - use wave texture
    nodes.append({
        "type": "CompositorNodeTexture",
        "name": "CRT_Scanlines_Texture",
        "texture_type": "BLEND",
        "inputs": {},
    })

    # Math node to create stripe pattern
    nodes.append({
        "type": "CompositorNodeMath",
        "name": "CRT_Scanlines_Math",
        "operation": "MULTIPLY",
        "inputs": {
            "Value": config.intensity,
        }
    })

    # Mix to blend with image
    nodes.append({
        "type": "CompositorNodeMixRGB",
        "name": "CRT_Scanlines_Mix",
        "blend_type": "MULTIPLY",
        "inputs": {
            "fac": 1.0 if config.enabled else 0.0,
        }
    })

    return nodes


def create_phosphor_node_config(config: PhosphorConfig) -> List[Dict[str, Any]]:
    """
    Create node configuration for phosphor mask effect.

    Args:
        config: Phosphor configuration

    Returns:
        List of node configuration dictionaries
    """
    nodes = []

    # Phosphor pattern using separate RGB curves
    if config.pattern in ("rgb", "aperture_grille"):
        # Red channel - emphasize
        nodes.append({
            "type": "CompositorNodeCurveRGB",
            "name": "CRT_Phosphor_RGB",
            "inputs": {},
        })
    elif config.pattern == "bgr":
        # Reversed pattern
        nodes.append({
            "type": "CompositorNodeCurveRGB",
            "name": "CRT_Phosphor_BGR",
            "inputs": {},
        })

    # Mix with intensity
    nodes.append({
        "type": "CompositorNodeMixRGB",
        "name": "CRT_Phosphor_Mix",
        "blend_type": "MIX",
        "inputs": {
            "fac": config.intensity,
        }
    })

    return nodes


# =============================================================================
# Full Pipeline Setup
# =============================================================================

def setup_crt_compositing(node_tree: Any, config: CRTConfig) -> List[str]:
    """
    Set up full CRT compositing pipeline in Blender.

    Creates all necessary nodes and connections for CRT effects
    in the provided node tree.

    Args:
        node_tree: Blender compositor node tree
        config: CRT configuration

    Returns:
        List of created node names
    """
    # Get node configuration
    node_config = create_crt_node_group(config)

    created_nodes = []

    # This would create actual Blender nodes
    # For now, return the configuration for manual setup
    for node_def in node_config["nodes"]:
        created_nodes.append(node_def["name"])

    return created_nodes


def create_curvature_node(node_tree: Any, config: CurvatureConfig) -> Any:
    """
    Create curvature compositor node.

    Args:
        node_tree: Blender compositor node tree
        config: Curvature configuration

    Returns:
        Created node (or None if not in Blender)
    """
    if not config.enabled:
        return None

    # Return configuration dict for actual implementation
    return {
        "type": "lens_distortion",
        "amount": config.amount,
        "vignette": config.vignette_amount,
    }


def create_scanline_node(node_tree: Any, config: ScanlineConfig) -> Any:
    """
    Create scanline compositor node.

    Args:
        node_tree: Blender compositor node tree
        config: Scanline configuration

    Returns:
        Created node (or None if not in Blender)
    """
    if not config.enabled:
        return None

    return {
        "type": "scanlines",
        "intensity": config.intensity,
        "spacing": config.spacing,
        "thickness": config.thickness,
    }


# =============================================================================
# Node Group Templates
# =============================================================================

CRT_NODE_TEMPLATES = {
    "scanlines": {
        "inputs": ["Image"],
        "outputs": ["Image"],
        "description": "CRT scanline effect",
    },
    "phosphor": {
        "inputs": ["Image"],
        "outputs": ["Image"],
        "description": "Phosphor mask effect",
    },
    "curvature": {
        "inputs": ["Image"],
        "outputs": ["Image"],
        "description": "Screen curvature effect",
    },
    "bloom": {
        "inputs": ["Image"],
        "outputs": ["Image"],
        "description": "Bloom/glow effect",
    },
    "vignette": {
        "inputs": ["Image"],
        "outputs": ["Image"],
        "description": "Vignette edge darkening",
    },
    "chromatic": {
        "inputs": ["Image"],
        "outputs": ["Image"],
        "description": "Chromatic aberration",
    },
    "full_crt": {
        "inputs": ["Image"],
        "outputs": ["Image"],
        "description": "Complete CRT effects pipeline",
    },
}


# =============================================================================
# Utility Functions
# =============================================================================

def get_crt_node_group_name(preset: str = "") -> str:
    """
    Get node group name for a CRT preset.

    Args:
        preset: Preset name (optional)

    Returns:
        Node group name
    """
    if preset:
        return f"CRT_Effects_{preset}"
    return CRT_NODE_GROUP_NAME


def list_crt_node_templates() -> List[str]:
    """
    List available CRT node templates.

    Returns:
        List of template names
    """
    return list(CRT_NODE_TEMPLATES.keys())


def get_node_template_description(name: str) -> str:
    """
    Get description for a node template.

    Args:
        name: Template name

    Returns:
        Description string
    """
    template = CRT_NODE_TEMPLATES.get(name, {})
    return template.get("description", "Unknown template")


def create_preset_nodes(preset_name: str) -> Dict[str, Any]:
    """
    Create node configuration for a preset.

    Args:
        preset_name: Name of the CRT preset

    Returns:
        Node configuration dictionary
    """
    from lib.retro.crt_types import get_preset

    try:
        config = get_preset(preset_name)
    except KeyError:
        config = CRTConfig()

    return create_crt_node_group(config)


def export_node_setup_python(config: CRTConfig) -> str:
    """
    Export node setup as Python code.

    Generates Python code that can be run in Blender
    to create the CRT effect nodes.

    Args:
        config: CRT configuration

    Returns:
        Python code string
    """
    node_config = create_crt_node_group(config)

    code_lines = [
        "# CRT Effects Node Setup",
        "# Generated from CRTConfig",
        "",
        "import bpy",
        "",
        "# Get compositor node tree",
        "scene = bpy.context.scene",
        "scene.use_nodes = True",
        "tree = scene.node_tree",
        "",
        "# Clear existing nodes",
        "for node in tree.nodes:",
        "    tree.nodes.remove(node)",
        "",
        "# Create render layers node",
        "rl_node = tree.nodes.new('CompositorNodeRLayers')",
        "rl_node.location = (0, 0)",
        "",
        "# Create output node",
        "output_node = tree.nodes.new('CompositorNodeComposite')",
        "output_node.location = (1500, 0)",
        "",
        "# Track last node for linking",
        "last_node = rl_node",
        "last_output = 'Image'",
        "",
    ]

    x_offset = 300
    y_offset = 0

    for node_def in node_config["nodes"]:
        node_type = node_def.get("type", "")
        node_name = node_def.get("name", f"CRT_{node_type}")

        code_lines.extend([
            f"# Create {node_name}",
            f"node = tree.nodes.new('{node_type}')",
            f"node.name = '{node_name}'",
            f"node.location = ({x_offset}, {y_offset})",
        ])

        # Add input values
        for input_name, input_value in node_def.get("inputs", {}).items():
            if isinstance(input_value, float):
                code_lines.append(f"node.inputs['{input_name}'].default_value = {input_value}")
            elif isinstance(input_value, int):
                code_lines.append(f"node.inputs['{input_name}'].default_value = {input_value}")
            else:
                code_lines.append(f"node.inputs['{input_name}'].default_value = {repr(input_value)}")

        # Link from previous node
        code_lines.extend([
            f"tree.links.new(last_node.outputs[last_output], node.inputs['Image'])",
            "last_node = node",
            "last_output = 'Image'",
            "",
        ])

        x_offset += 200

    # Final link to output
    code_lines.extend([
        "# Link to output",
        "tree.links.new(last_node.outputs[last_output], output_node.inputs['Image'])",
        "",
        "print('CRT effects nodes created successfully')",
    ])

    return "\n".join(code_lines)
