"""
Button Geometry Builders

Geometry Nodes builders for procedural button generation.

Builders:
- build_button_base(): Base button body
- build_button_cap(): Removable cap
- build_button_illumination(): LED elements
- build_button(): Complete button assembly
"""

from __future__ import annotations
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from lib.nodekit import NodeKit

from .buttons import (
    ButtonConfig,
    ButtonCapConfig,
    IlluminationConfig,
    ButtonShape,
    ButtonSurface,
    TexturePattern,
    IlluminationType,
    CapShape,
)


def build_button_base(
    nk: "NodeKit",
    config: ButtonConfig,
    x: float = 0,
    y: float = 0
) -> Any:
    """
    Build base button body geometry.

    Args:
        nk: NodeKit instance
        config: Button configuration
        x, y: Node positions

    Returns:
        Geometry output socket
    """
    # Determine dimensions based on shape
    width = config.width
    length = config.length if config.shape == ButtonShape.RECTANGULAR else config.width
    height = config.depth_unpressed - (config.travel if config.pressed else 0)

    if config.shape == ButtonShape.ROUND:
        # Round button - use cylinder
        cyl = nk.n("GeometryNodeMeshCylinder", "ButtonBase", x, y)
        cyl.inputs["Vertices"].default_value = 32
        cyl.inputs["Radius"].default_value = width / 2
        cyl.inputs["Depth"].default_value = height

        # Transform to position
        transform = nk.n("GeometryNodeTransform", "ButtonTransform", x + 200, y)
        nk.link(cyl.outputs["Mesh"], transform.inputs["Geometry"])
        transform.inputs["Translation"].default_value = (0, 0, height / 2)

        base_geo = transform.outputs["Geometry"]

    else:
        # Square/rectangular button - use cube
        # Blender 5.x: Size is a vector, Vertices are named
        cube = nk.n("GeometryNodeMeshCube", "ButtonBase", x, y)
        cube.inputs["Size"].default_value = (width, length, height)
        cube.inputs["Vertices X"].default_value = 2
        cube.inputs["Vertices Y"].default_value = 2
        cube.inputs["Vertices Z"].default_value = 2

        # Transform to position
        transform = nk.n("GeometryNodeTransform", "ButtonTransform", x + 200, y)
        nk.link(cube.outputs["Mesh"], transform.inputs["Geometry"])
        transform.inputs["Translation"].default_value = (0, 0, height / 2)

        base_geo = transform.outputs["Geometry"]

    # Apply surface modification
    if config.surface == ButtonSurface.DOMED:
        base_geo = _build_dome_surface(nk, base_geo, config, x + 400, y)
    elif config.surface == ButtonSurface.CONCAVE:
        base_geo = _build_concave_surface(nk, base_geo, config, x + 400, y)
    elif config.texture_pattern != TexturePattern.NONE:
        base_geo = _build_textured_surface(nk, base_geo, config, x + 400, y)

    return base_geo


def _build_dome_surface(
    nk: "NodeKit",
    geo_input: Any,
    config: ButtonConfig,
    x: float,
    y: float
) -> Any:
    """Add domed surface to button using set position."""
    # Get position
    pos = nk.n("GeometryNodeInputPosition", "Pos", x, y + 100)

    # Separate Z
    sep_z = nk.n("ShaderNodeSeparateXYZ", "SepZ", x + 100, y + 100)
    nk.link(pos.outputs["Position"], sep_z.inputs["Vector"])

    # Calculate dome factor based on height
    # Higher Z = pushed toward center
    height = config.depth_unpressed

    # Normalize Z position
    math_div = nk.n("ShaderNodeMath", "NormZ", x + 200, y + 100)
    math_div.operation = "DIVIDE"
    math_div.inputs[1].default_value = height
    nk.link(sep_z.outputs["Z"], math_div.inputs[0])

    # Scale factor: 1 at bottom, smaller at top
    math_sub = nk.n("ShaderNodeMath", "ScaleFactor", x + 300, y + 100)
    math_sub.operation = "SUBTRACT"
    math_sub.inputs[1].default_value = 0.7  # Dome intensity
    nk.link(math_div.outputs["Value"], math_sub.inputs[0])

    math_max = nk.n("ShaderNodeMath", "ClampScale", x + 400, y + 100)
    math_max.operation = "MAXIMUM"
    math_max.inputs[1].default_value = 0.0
    nk.link(math_sub.outputs["Value"], math_max.inputs[0])

    # Apply to X and Y
    sep_xy = nk.n("ShaderNodeSeparateXYZ", "SepXY", x, y)
    nk.link(pos.outputs["Position"], sep_xy.inputs["Vector"])

    # Scale X
    scale_x = nk.n("ShaderNodeMath", "ScaleX", x + 200, y - 50)
    scale_x.operation = "MULTIPLY"
    nk.link(sep_xy.outputs["X"], scale_x.inputs[0])
    nk.link(math_max.outputs["Value"], scale_x.inputs[1])

    # Scale Y
    scale_y = nk.n("ShaderNodeMath", "ScaleY", x + 200, y - 100)
    scale_y.operation = "MULTIPLY"
    nk.link(sep_xy.outputs["Y"], scale_y.inputs[0])
    nk.link(math_max.outputs["Value"], scale_y.inputs[1])

    # Combine new position
    combine = nk.n("ShaderNodeCombineXYZ", "CombinePos", x + 400, y - 50)
    nk.link(scale_x.outputs["Value"], combine.inputs["X"])
    nk.link(scale_y.outputs["Value"], combine.inputs["Y"])
    nk.link(sep_z.outputs["Z"], combine.inputs["Z"])

    # Set position
    set_pos = nk.n("GeometryNodeSetPosition", "SetDome", x + 600, y)
    nk.link(geo_input, set_pos.inputs["Geometry"])
    nk.link(combine.outputs["Vector"], set_pos.inputs["Position"])

    return set_pos.outputs["Geometry"]


def _build_concave_surface(
    nk: "NodeKit",
    geo_input: Any,
    config: ButtonConfig,
    x: float,
    y: float
) -> Any:
    """Add concave (recessed) surface to button."""
    # Get position
    pos = nk.n("GeometryNodeInputPosition", "Pos", x, y + 100)

    # Separate XYZ
    sep = nk.n("ShaderNodeSeparateXYZ", "SepXYZ", x + 100, y + 100)
    nk.link(pos.outputs["Position"], sep.inputs["Vector"])

    # Calculate distance from center in XY
    x_sq = nk.n("ShaderNodeMath", "XSq", x + 200, y + 150)
    x_sq.operation = "MULTIPLY"
    nk.link(sep.outputs["X"], x_sq.inputs[0])
    nk.link(sep.outputs["X"], x_sq.inputs[1])

    y_sq = nk.n("ShaderNodeMath", "YSq", x + 200, y + 100)
    y_sq.operation = "MULTIPLY"
    nk.link(sep.outputs["Y"], y_sq.inputs[0])
    nk.link(sep.outputs["Y"], y_sq.inputs[1])

    add_sq = nk.n("ShaderNodeMath", "AddSq", x + 300, y + 125)
    add_sq.operation = "ADD"
    nk.link(x_sq.outputs["Value"], add_sq.inputs[0])
    nk.link(y_sq.outputs["Value"], add_sq.inputs[1])

    dist = nk.n("ShaderNodeMath", "SqrtDist", x + 400, y + 125)
    dist.operation = "SQRT"
    nk.link(add_sq.outputs["Value"], dist.inputs[0])

    # Normalize by radius
    radius = config.width / 2
    norm_dist = nk.n("ShaderNodeMath", "NormDist", x + 500, y + 125)
    norm_dist.operation = "DIVIDE"
    norm_dist.inputs[1].default_value = radius
    nk.link(dist.outputs["Value"], norm_dist.inputs[0])

    # Concave factor: push down at center
    concave = nk.n("ShaderNodeMath", "Concave", x + 600, y + 125)
    concave.operation = "MULTIPLY"
    concave.inputs[1].default_value = -0.001  # Concave depth
    nk.link(norm_dist.outputs["Value"], concave.inputs[0])

    # Invert (center goes down)
    invert = nk.n("ShaderNodeMath", "Invert", x + 700, y + 125)
    invert.operation = "SUBTRACT"
    invert.inputs[0].default_value = 1.0
    nk.link(concave.outputs["Value"], invert.inputs[1])

    # Add to Z
    new_z = nk.n("ShaderNodeMath", "NewZ", x + 800, y + 100)
    new_z.operation = "ADD"
    nk.link(sep.outputs["Z"], new_z.inputs[0])
    nk.link(invert.outputs["Value"], new_z.inputs[1])

    # Combine
    combine = nk.n("ShaderNodeCombineXYZ", "CombinePos", x + 900, y + 100)
    nk.link(sep.outputs["X"], combine.inputs["X"])
    nk.link(sep.outputs["Y"], combine.inputs["Y"])
    nk.link(new_z.outputs["Value"], combine.inputs["Z"])

    # Set position
    set_pos = nk.n("GeometryNodeSetPosition", "SetConcave", x + 1100, y)
    nk.link(geo_input, set_pos.inputs["Geometry"])
    nk.link(combine.outputs["Vector"], set_pos.inputs["Position"])

    return set_pos.outputs["Geometry"]


def _build_textured_surface(
    nk: "NodeKit",
    geo_input: Any,
    config: ButtonConfig,
    x: float,
    y: float
) -> Any:
    """Add texture pattern to button surface (simplified)."""
    # For now, just return input - full texture implementation would use noise/displacement
    return geo_input


def build_button_cap(
    nk: "NodeKit",
    cap_config: ButtonCapConfig,
    base_width: float,
    base_length: float,
    x: float = 0,
    y: float = 0
) -> Any:
    """
    Build removable button cap geometry.

    Args:
        nk: NodeKit instance
        cap_config: Cap configuration
        base_width: Width of base button
        base_length: Length of base button
        x, y: Node positions

    Returns:
        Geometry output socket
    """
    if not cap_config.enabled:
        return None

    # Cap is slightly smaller than base
    cap_width = base_width - 0.001
    cap_length = base_length - 0.001

    if cap_config.shape == CapShape.ROUND:
        cyl = nk.n("GeometryNodeMeshCylinder", "Cap", x, y)
        cyl.inputs["Vertices"].default_value = 32
        cyl.inputs["Radius"].default_value = cap_width / 2
        cyl.inputs["Depth"].default_value = cap_config.height

        transform = nk.n("GeometryNodeTransform", "CapTransform", x + 200, y)
        nk.link(cyl.outputs["Mesh"], transform.inputs["Geometry"])

        # Position cap on top of base
        base_height = 0.005  # Approximate base height
        z_offset = base_height + cap_config.height / 2 - cap_config.inset
        transform.inputs["Translation"].default_value = (0, 0, z_offset)

        return transform.outputs["Geometry"]

    else:
        # Square/rectangular cap - Blender 5.x style
        cube = nk.n("GeometryNodeMeshCube", "Cap", x, y)
        cube.inputs["Size"].default_value = (cap_width, cap_length, cap_config.height)
        cube.inputs["Vertices X"].default_value = 2
        cube.inputs["Vertices Y"].default_value = 2
        cube.inputs["Vertices Z"].default_value = 2

        transform = nk.n("GeometryNodeTransform", "CapTransform", x + 200, y)
        nk.link(cube.outputs["Mesh"], transform.inputs["Geometry"])

        base_height = 0.005
        z_offset = base_height + cap_config.height / 2 - cap_config.inset
        transform.inputs["Translation"].default_value = (0, 0, z_offset)

        return transform.outputs["Geometry"]


def build_button_illumination(
    nk: "NodeKit",
    illum_config: IlluminationConfig,
    button_width: float,
    button_length: float,
    active: bool = False,
    x: float = 0,
    y: float = 0
) -> Any:
    """
    Build LED illumination geometry.

    Args:
        nk: NodeKit instance
        illum_config: Illumination configuration
        button_width: Button width
        button_length: Button length
        active: Whether button is active state
        x, y: Node positions

    Returns:
        Geometry output socket (or None if disabled)
    """
    if not illum_config.enabled:
        return None

    # Determine color based on state
    if active:
        color = illum_config.color_active
    else:
        color = illum_config.color_on

    if illum_config.type == IlluminationType.RING:
        return _build_led_ring(nk, illum_config, button_width, x, y)
    elif illum_config.type == IlluminationType.SPOT:
        return _build_led_spot(nk, illum_config, button_width, x, y)
    else:
        # BACKLIT or other - simple spot
        return _build_led_spot(nk, illum_config, button_width, x, y)


def _build_led_ring(
    nk: "NodeKit",
    illum_config: IlluminationConfig,
    button_width: float,
    x: float,
    y: float
) -> Any:
    """Build LED ring around button using a thin cylinder."""
    # Use cylinder as LED ring (torus not available in Blender 5.x GN)
    # Create outer cylinder
    outer_radius = button_width / 2 + illum_config.ring_width
    inner_radius = button_width / 2

    # Create outer cylinder
    outer = nk.n("GeometryNodeMeshCylinder", "OuterRing", x, y)
    outer.inputs["Vertices"].default_value = 32
    outer.inputs["Radius"].default_value = outer_radius
    outer.inputs["Depth"].default_value = 0.001

    # Create inner cylinder for boolean
    inner = nk.n("GeometryNodeMeshCylinder", "InnerRing", x + 100, y)
    inner.inputs["Vertices"].default_value = 32
    inner.inputs["Radius"].default_value = inner_radius
    inner.inputs["Depth"].default_value = 0.002

    # Boolean difference (Blender 5.x uses index-based for boolean node)
    bool_diff = nk.n("GeometryNodeMeshBoolean", "RingBool", x + 200, y)
    # Operation is index 0 in Blender 5.x - but we need to use enum
    # Actually use named access for operation enum
    bool_diff.operation = 'DIFFERENCE'
    nk.link(outer.outputs["Mesh"], bool_diff.inputs[0])  # Mesh A (index-based)
    nk.link(inner.outputs["Mesh"], bool_diff.inputs[1])  # Mesh B (index-based)

    # Position at top of button
    transform = nk.n("GeometryNodeTransform", "RingTransform", x + 400, y)
    nk.link(bool_diff.outputs[0], transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (0, 0, 0.003)

    return transform.outputs["Geometry"]


def _build_led_spot(
    nk: "NodeKit",
    illum_config: IlluminationConfig,
    button_width: float,
    x: float,
    y: float
) -> Any:
    """Build single LED spot on button."""
    # Small cylinder representing LED
    led = nk.n("GeometryNodeMeshCylinder", "LED", x, y)
    led.inputs["Vertices"].default_value = 16
    led.inputs["Radius"].default_value = button_width / 8
    led.inputs["Depth"].default_value = 0.001

    # Position at top center of button
    transform = nk.n("GeometryNodeTransform", "LEDTransform", x + 200, y)
    nk.link(led.outputs["Mesh"], transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (0, 0, 0.006)

    return transform.outputs["Geometry"]


def build_button(
    nk: "NodeKit",
    config: ButtonConfig,
    x: float = 0,
    y: float = 0
) -> Any:
    """
    Build complete button assembly.

    Args:
        nk: NodeKit instance
        config: Button configuration
        x, y: Starting node positions

    Returns:
        Geometry output socket
    """
    geometries = []

    # 1. Build base button
    base_geo = build_button_base(nk, config, x, y)
    if base_geo:
        geometries.append(base_geo)

    # 2. Build cap if enabled
    base_length = config.length if config.shape == ButtonShape.RECTANGULAR else config.width
    cap_geo = build_button_cap(
        nk,
        config.cap,
        config.width,
        base_length,
        x + 600,
        y
    )
    if cap_geo:
        geometries.append(cap_geo)

    # 3. Build illumination if enabled
    illum_geo = build_button_illumination(
        nk,
        config.illumination,
        config.width,
        base_length,
        config.active,
        x + 600,
        y - 200
    )
    if illum_geo:
        geometries.append(illum_geo)

    # 4. Join all geometries
    if not geometries:
        return None

    if len(geometries) == 1:
        return geometries[0]

    # Join multiple geometries
    current_geo = geometries[0]
    join_x = x + 900

    for i, geo in enumerate(geometries[1:], 1):
        join = nk.n("GeometryNodeJoinGeometry", f"Join{i}", join_x, y - i * 50)
        nk.link(current_geo, join.inputs["Geometry"])
        nk.link(geo, join.inputs["Geometry"])
        current_geo = join.outputs["Geometry"]
        join_x += 100

    return current_geo


def create_button_material(
    config: ButtonConfig,
    color_override: tuple = None
) -> dict:
    """
    Create material parameters for button.

    Args:
        config: Button configuration
        color_override: Optional color override

    Returns:
        Material parameter dictionary
    """
    color = color_override if color_override else config.color

    return {
        "base_color": list(color),
        "metallic": config.metallic,
        "roughness": config.roughness,
        "subsurface": 0.0,
        "subsurface_color": [0.0, 0.0, 0.0, 1.0],
    }
