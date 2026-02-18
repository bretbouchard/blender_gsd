"""
Debug Materials - Mask visualization for Geometry Nodes.

Enables inspection of any named attribute as emission (white on black).

Usage:
    mat = ensure_mask_debug_material(attribute_name="mask_height")
    obj.data.materials.append(mat)
"""

from __future__ import annotations
import bpy


def ensure_mask_debug_material(
    name: str = "DEBUG_Mask",
    attribute_name: str = "mask_height",
    remap: bool = True,
) -> bpy.types.Material:
    """
    Create or update a material that visualizes a named float attribute.

    White = 1.0, Black = 0.0

    Args:
        name: Material name
        attribute_name: Named attribute to visualize
        remap: Apply Map Range node for clamping

    Returns:
        The debug material
    """
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)

    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    # Nodes
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)

    emit = nt.nodes.new("ShaderNodeEmission")
    emit.location = (400, 0)

    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.location = (0, 0)
    attr.attribute_name = attribute_name

    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])

    if remap:
        mapr = nt.nodes.new("ShaderNodeMapRange")
        mapr.location = (200, 0)
        mapr.clamp = True
        mapr.inputs["From Min"].default_value = 0.0
        mapr.inputs["From Max"].default_value = 1.0
        mapr.inputs["To Min"].default_value = 0.0
        mapr.inputs["To Max"].default_value = 1.0

        nt.links.new(attr.outputs["Fac"], mapr.inputs["Value"])
        nt.links.new(mapr.outputs["Result"], emit.inputs["Strength"])
        nt.links.new(mapr.outputs["Result"], emit.inputs["Color"])
    else:
        nt.links.new(attr.outputs["Fac"], emit.inputs["Strength"])
        nt.links.new(attr.outputs["Fac"], emit.inputs["Color"])

    return mat


def apply_mask_debug(
    obj: bpy.types.Object,
    *,
    attribute: str,
    material_name: str = "DEBUG_Mask"
) -> None:
    """
    Apply a mask debug material to an object.

    Args:
        obj: Blender object with geometry
        attribute: Named attribute to visualize
        material_name: Material name (will be created/updated)
    """
    mat = ensure_mask_debug_material(
        name=material_name,
        attribute_name=attribute,
    )

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
