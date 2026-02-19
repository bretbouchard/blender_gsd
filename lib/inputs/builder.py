"""
Input Builder

Builds Blender objects from input configurations and presets.
This is the main entry point for creating input controls.

Usage:
    from lib.inputs import build_input

    # Build from preset
    obj = build_input(preset="knob_neve_1073", collection=my_collection)

    # Build with overrides
    obj = build_input(
        preset="knob_neve_1073",
        overrides={"zones.a.width_top_mm": 16},
        collection=my_collection
    )

    # Build from config
    config = InputConfig(...)
    obj = build_from_config(config, collection=my_collection)
"""

from __future__ import annotations
import bpy
from typing import Dict, Any, Optional
from pathlib import Path

import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit
from lib.inputs.input_types import InputConfig
from lib.inputs.input_presets import get_preset, InputPreset
from lib.inputs.zone_geometry import ZoneBuilder


def build_input(
    preset: str,
    collection: bpy.types.Collection,
    overrides: Optional[Dict[str, Any]] = None,
    object_name: Optional[str] = None,
) -> bpy.types.Object:
    """
    Build an input from a preset.

    Args:
        preset: Preset ID (e.g., "knob_neve_1073")
        collection: Blender collection to place object in
        overrides: Optional parameter overrides (dot-notation paths)
        object_name: Optional object name (default: preset name)

    Returns:
        Created Blender object

    Example overrides:
        {
            "zones.a.width_top_mm": 16,
            "material.base_color": [1.0, 0.0, 0.0],
        }
    """
    # Load preset
    preset_obj = get_preset(preset)
    config = preset_obj.config

    # Apply overrides
    if overrides:
        config = _apply_overrides(config, overrides)

    # Set object name
    if object_name is None:
        object_name = preset_obj.name

    return build_from_config(config, collection, object_name)


def build_from_config(
    config: InputConfig,
    collection: bpy.types.Collection,
    object_name: str = "Input",
) -> bpy.types.Object:
    """
    Build an input from a configuration.

    Args:
        config: Complete input configuration
        collection: Blender collection to place object in
        object_name: Object name

    Returns:
        Created Blender object
    """
    # Create mesh object
    mesh = bpy.data.meshes.new(f"{object_name}_Mesh")
    obj = bpy.data.objects.new(object_name, mesh)
    collection.objects.link(obj)

    # Create Geometry Nodes modifier
    mod = obj.modifiers.new("InputGeometry", "NODES")
    tree = bpy.data.node_groups.new(f"{object_name}_GeoTree", "GeometryNodeTree")
    mod.node_group = tree

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    nk = NodeKit(tree).clear()

    gi = nk.group_input(0, 0)
    go = nk.group_output(2000, 0)

    # Build geometry
    builder = ZoneBuilder(tree)
    geo = builder.build_input(config, x=200, y=0)

    if geo is None:
        # Fallback: create a simple cylinder
        cyl = nk.n("GeometryNodeMeshCylinder", "FallbackCylinder", 200, 0)
        cyl.inputs["Vertices"].default_value = 32
        cyl.inputs["Radius"].default_value = config.total_width_m / 2
        cyl.inputs["Depth"].default_value = config.total_height_m

        transform = nk.n("GeometryNodeTransform", "FallbackTransform", 400, 0)
        nk.link(cyl.outputs["Mesh"], transform.inputs["Geometry"])
        transform.inputs["Translation"].default_value = (0, 0, config.total_height_m / 2)

        geo = transform.outputs["Geometry"]

    # Merge vertices
    merge = nk.n("GeometryNodeMergeByDistance", "MergeVertices", 1600, 0)
    nk.link(geo, merge.inputs["Geometry"])

    # Set material
    mat = _create_material(config)
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 1800, 0)
    set_mat.inputs["Material"].default_value = mat
    nk.link(merge.outputs["Geometry"], set_mat.inputs["Geometry"])

    # Output
    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    return obj


def _apply_overrides(config: InputConfig, overrides: Dict[str, Any]) -> InputConfig:
    """
    Apply overrides to a configuration using dot-notation paths.

    Args:
        config: Base configuration
        overrides: Override dictionary with dot-notation paths

    Returns:
        New configuration with overrides applied

    Example:
        config = _apply_overrides(config, {
            "zones.a.width_top_mm": 16,
            "material.base_color": [1, 0, 0],
        })
    """
    # Convert config to dict
    config_dict = config.to_dict()

    # Apply each override
    for path, value in overrides.items():
        _set_nested(config_dict, path, value)

    # Convert back to config
    return InputConfig.from_dict(config_dict)


def _set_nested(d: Dict, path: str, value: Any):
    """Set a nested dictionary value using dot-notation path."""
    keys = path.split(".")
    current = d

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value


def _create_material(config: InputConfig) -> bpy.types.Material:
    """Create a material from input configuration."""
    mat = bpy.data.materials.new(f"InputMaterial_{config.name}")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    nk = NodeKit(nt)

    X = -800
    STEP = 100

    # Principled BSDF
    bsdf = nk.n("ShaderNodeBsdfPrincipled", "BSDF", X, 0)
    bsdf.inputs["Base Color"].default_value = (*config.base_color, 1.0)
    bsdf.inputs["Metallic"].default_value = config.metallic
    bsdf.inputs["Roughness"].default_value = config.roughness

    # Output
    out = nk.n("ShaderNodeOutputMaterial", "Output", X + 2*STEP, 0)
    nk.link(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat
