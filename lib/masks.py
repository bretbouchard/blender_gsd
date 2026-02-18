"""
Masks - Reusable mask generation for Geometry Nodes.

Masking is a first-class concept. Every system must support masks.
Masks are stored as named attributes for debugging and visualization.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .nodekit import NodeKit


def height_mask_geo(
    nk: "NodeKit",
    *,
    x: float = 0,
    y: float = 0,
    z_min: float = 0.0,
    z_max: float = 1.0,
    invert: bool = False
):
    """
    Geometry Nodes height mask: Position -> Separate XYZ -> Z -> Map Range.

    Output: float mask 0..1

    Args:
        nk: NodeKit instance
        x: Starting X position in node editor
        y: Starting Y position in node editor
        z_min: Minimum Z value (maps to 0)
        z_max: Maximum Z value (maps to 1)
        invert: If True, swap the mask values

    Returns:
        Output socket (float) containing the mask value
    """
    pos = nk.n("GeometryNodeInputPosition", "Position", x, y)
    sep = nk.n("ShaderNodeSeparateXYZ", "SepXYZ", x + 180, y)
    mr = nk.n("ShaderNodeMapRange", "MapRange", x + 360, y)
    mr.clamp = True

    nk.link(pos.outputs["Position"], sep.inputs["Vector"])
    nk.link(sep.outputs["Z"], mr.inputs["Value"])
    nk.set(mr.inputs["From Min"], z_min)
    nk.set(mr.inputs["From Max"], z_max)
    nk.set(mr.inputs["To Min"], 0.0)
    nk.set(mr.inputs["To Max"], 1.0)

    out = mr.outputs["Result"]

    if invert:
        inv = nk.n("ShaderNodeMath", "Invert", x + 540, y)
        inv.operation = "SUBTRACT"
        nk.set(inv.inputs[0], 1.0)
        nk.link(out, inv.inputs[1])
        out = inv.outputs["Value"]

    return out


def curvature_mask_geo(
    nk: "NodeKit",
    *,
    x: float = 0,
    y: float = 0,
    radius: float = 0.1,
    invert: bool = False
):
    """
    Geometry Nodes curvature mask based on point normals.

    Detects edges and corners based on normal variation.

    Args:
        nk: NodeKit instance
        x: Starting X position
        y: Starting Y position
        radius: Sampling radius for curvature detection
        invert: If True, invert the mask

    Returns:
        Output socket (float) containing the curvature mask
    """
    # This is a placeholder - real implementation would use
    # Geometry Proximity or Edge Angle nodes
    # For now, return a constant 1.0 mask
    val = nk.n("GeometryNodeInputConstant", "Const", x, y)
    val.data_type = "FLOAT"
    # Note: Constant node setup varies by Blender version
    return val.outputs.get("Value", val.outputs.get("Float"))


def combine_masks(
    nk: "NodeKit",
    mask_a,
    mask_b,
    *,
    x: float = 0,
    y: float = 0,
    operation: str = "MULTIPLY"
):
    """
    Combine two masks with a math operation.

    Args:
        nk: NodeKit instance
        mask_a: First mask socket
        mask_b: Second mask socket
        x: X position for math node
        y: Y position for math node
        operation: Math operation (MULTIPLY, ADD, SUBTRACT, etc.)

    Returns:
        Output socket (float) with combined mask
    """
    math = nk.n("ShaderNodeMath", f"Combine_{operation}", x, y)
    math.operation = operation
    math.use_clamp = True

    nk.link(mask_a, math.inputs[0])
    nk.link(mask_b, math.inputs[1])

    return math.outputs["Value"]
