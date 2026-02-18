"""
Neve Knob Generator - Geometry Nodes + Shader Nodes

Creates procedural Neve-style audio knobs with:
- Configurable cap and skirt dimensions
- Optional ridged grip section
- Pointer line indicator
- Material system (glossy/metallic)
"""

import bpy
import sys
import pathlib

# Add parent lib to path
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit
from lib.pipeline import Pipeline
from lib.masks import height_mask_geo


def build_artifact(task: dict, collection: bpy.types.Collection):
    """
    Build a Neve-style knob from task parameters.

    Args:
        task: Task dict with geometry and material parameters
        collection: Blender collection to place objects in

    Returns:
        Dict with 'root_objects' list
    """
    params = task["parameters"]
    debug = task.get("debug", {})

    # --- Base mesh: Cylinder for knob ---
    bpy.ops.mesh.primitive_cylinder_add(
        radius=params.get("cap_diameter", 0.02) / 2,
        depth=params.get("cap_height", 0.025),
        location=(0, 0, params.get("cap_height", 0.025) / 2)
    )
    obj = bpy.context.active_object
    obj.name = "NeveKnob"

    # Move to collection
    try:
        bpy.context.scene.collection.objects.unlink(obj)
    except RuntimeError:
        pass
    collection.objects.link(obj)

    # --- Geometry Nodes system ---
    mod = obj.modifiers.new("KnobSystem", "NODES")
    tree = bpy.data.node_groups.new("NeveKnobSystem", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    gi = nk.group_input(0, 0)
    go = nk.group_output(1600, 0)

    # Create interface sockets
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    # Add parameter inputs
    tree.interface.new_socket("Cap Height", in_out="INPUT", socket_type="NodeSocketFloat")
    tree.interface.new_socket("Cap Diameter", in_out="INPUT", socket_type="NodeSocketFloat")
    tree.interface.new_socket("Skirt Height", in_out="INPUT", socket_type="NodeSocketFloat")
    tree.interface.new_socket("Skirt Diameter", in_out="INPUT", socket_type="NodeSocketFloat")
    tree.interface.new_socket("Ridge Count", in_out="INPUT", socket_type="NodeSocketInt")
    tree.interface.new_socket("Ridge Depth", in_out="INPUT", socket_type="NodeSocketFloat")
    tree.interface.new_socket("Pointer Width", in_out="INPUT", socket_type="NodeSocketFloat")

    # Set default values on modifier
    mod["Cap Height"] = params.get("cap_height", 0.025)
    mod["Cap Diameter"] = params.get("cap_diameter", 0.020)
    mod["Skirt Height"] = params.get("skirt_height", 0.010)
    mod["Skirt Diameter"] = params.get("skirt_diameter", 0.022)
    mod["Ridge Count"] = params.get("ridge_count", 0)
    mod["Ridge Depth"] = params.get("ridge_depth", 0.001)
    mod["Pointer Width"] = params.get("pointer_width", 0.002)

    # Initialize context
    ctx = {
        "params": params,
        "debug": debug,
        "nk": nk,
        "tree": tree,
        "masks": {},
        "norm": {},
    }

    # --- Stage definitions ---

    def stage_normalize(geo, ctx):
        """Stage 0: Normalize parameters to usable values."""
        p = ctx["params"]
        ctx["norm"] = {
            "cap_radius": p.get("cap_diameter", 0.02) / 2,
            "skirt_radius": p.get("skirt_diameter", 0.022) / 2,
            "total_height": p.get("cap_height", 0.025) + p.get("skirt_height", 0.010),
            "ridge_count": max(0, int(p.get("ridge_count", 0))),
        }
        return geo, ctx

    def stage_primary(geo, ctx):
        """Stage 1: Primary structure - base cylinder is already created."""
        # The base cylinder was created before the modifier
        # This stage could add the skirt geometry
        nk = ctx["nk"]
        p = ctx["params"]

        # Add a Transform node to position geometry
        transform = nk.n("GeometryNodeTransform", "BaseTransform", 200, 0)

        # Move geometry up so base is at Z=0
        nk.link(geo, transform.inputs["Geometry"])
        nk.set(transform.inputs["Translation"], (0, 0, p.get("skirt_height", 0.010)))

        return transform.outputs["Geometry"], ctx

    def stage_secondary(geo, ctx):
        """Stage 2: Add skirt geometry."""
        nk = ctx["nk"]
        p = ctx["params"]
        norm = ctx["norm"]

        # Create skirt cylinder
        skirt_cyl = nk.n("GeometryNodeMeshCylinder", "SkirtCylinder", 400, -200)
        nk.set(skirt_cyl.inputs["Radius"], norm["skirt_radius"])
        nk.set(skirt_cyl.inputs["Depth"], p.get("skirt_height", 0.010))

        # Position skirt at base
        skirt_transform = nk.n("GeometryNodeTransform", "SkirtTransform", 600, -200)
        nk.link(skirt_cyl.outputs["Mesh"], skirt_transform.inputs["Geometry"])
        nk.set(skirt_transform.inputs["Translation"], (0, 0, p.get("skirt_height", 0.010) / 2))

        # Join cap and skirt
        join = nk.n("GeometryNodeJoinGeometry", "JoinCapSkirt", 800, 0)
        nk.link(geo, join.inputs["Geometry"])
        nk.link(skirt_transform.outputs["Geometry"], join.inputs["Geometry"])

        # Create height mask for later use
        z_min = 0
        z_max = norm["total_height"]
        mask = height_mask_geo(nk, x=400, y=-400, z_min=z_min, z_max=z_max, invert=False)
        ctx["masks"]["mask_height"] = mask

        return join.outputs["Geometry"], ctx

    def stage_detail(geo, ctx):
        """Stage 3: Add ridges if ridge_count > 0."""
        nk = ctx["nk"]
        p = ctx["params"]

        ridge_count = int(p.get("ridge_count", 0))
        if ridge_count <= 0:
            return geo, ctx

        # Add subdivision surface for smoother ridges
        subd = nk.n("GeometryNodeSubdivisionSurface", "SubdivideForRidges", 900, 0)
        nk.set(subd.inputs["Level"], 2)
        nk.link(geo, subd.inputs["Mesh"])

        # TODO: Add actual ridge displacement via shader bump or displacement
        # For now, we just subdivide

        return subd.outputs["Mesh"], ctx

    def stage_output(geo, ctx):
        """Stage 4: Output prep - store debug attributes, finalize."""
        nk = ctx["nk"]

        if ctx["debug"].get("enabled"):
            for name, mask in ctx["masks"].items():
                store = nk.n(
                    "GeometryNodeStoreNamedAttribute",
                    f"Store_{name}",
                    x=1100,
                    y=-400,
                )
                store.data_type = "FLOAT"
                store.domain = "POINT"
                nk.set(store.inputs["Name"], name)

                nk.link(geo, store.inputs["Geometry"])
                nk.link(mask, store.inputs["Value"])
                geo = store.outputs["Geometry"]

        # Final transform to center the knob
        final_transform = nk.n("GeometryNodeTransform", "FinalTransform", 1300, 0)
        nk.link(geo, final_transform.inputs["Geometry"])

        return final_transform.outputs["Geometry"], ctx

    # --- Run pipeline ---
    pipe = (
        Pipeline()
        .add("normalize", stage_normalize)
        .add("primary", stage_primary)
        .add("secondary", stage_secondary)
        .add("detail", stage_detail)
        .add("output", stage_output)
    )

    geo, ctx = pipe.run(gi.outputs["Geometry"], ctx)
    nk.link(geo, go.inputs["Geometry"])

    # --- Apply material ---
    mat = create_knob_material(params)
    obj.data.materials.append(mat)

    return {"root_objects": [obj]}


def create_knob_material(params: dict) -> bpy.types.Material:
    """
    Create a procedural material for the knob.

    Args:
        params: Material parameters (base_color, metallic, roughness, etc.)

    Returns:
        Blender material with shader nodes
    """
    mat = bpy.data.materials.new("NeveKnobMaterial")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    nk = NodeKit(nt)

    # Node positions
    x = 0

    # Output
    out = nk.n("ShaderNodeOutputMaterial", "Output", 800, 0)

    # Principled BSDF
    bsdf = nk.n("ShaderNodeBsdfPrincipled", "PrincipledBSDF", 400, 0)

    # Set material properties
    base_color = params.get("base_color", [0.5, 0.5, 0.5])
    nk.set(bsdf.inputs["Base Color"], (base_color[0], base_color[1], base_color[2], 1.0))
    nk.set(bsdf.inputs["Metallic"], params.get("metallic", 0.0))
    nk.set(bsdf.inputs["Roughness"], params.get("roughness", 0.3))

    # Coat (clearcoat in Blender 5.0 terminology) for glossy knobs
    if params.get("clearcoat", 0) > 0:
        nk.set(bsdf.inputs["Coat Weight"], params.get("clearcoat", 0.5))
        nk.set(bsdf.inputs["Coat Roughness"], 0.1)

    # Link to output
    nk.link(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # TODO: Add pointer line via mix shader based on UV or position

    return mat
