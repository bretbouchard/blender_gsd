"""
Example Artifact - Demonstrates the full pipeline system.

This is a reference implementation showing:
- Stage-based pipeline
- Mask generation and storage
- Debug visualization support
- Deterministic geometry generation
"""

import bpy
from lib.nodekit import NodeKit
from lib.pipeline import Pipeline
from lib.masks import height_mask_geo


def build_artifact(task: dict, collection: bpy.types.Collection):
    """
    Build an artifact from a task definition.

    Args:
        task: Task dict with parameters, debug settings, outputs
        collection: Blender collection to place objects in

    Returns:
        Dict with 'root_objects' list
    """
    params = task["parameters"]
    debug = task.get("debug", {})

    # --- Base object ---
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.active_object
    obj.name = "Artifact"
    obj.scale = params.get("size", [0.25, 0.25, 0.08])
    bpy.ops.object.transform_apply(scale=True)

    collection.objects.link(obj)
    bpy.context.scene.collection.objects.unlink(obj)

    # --- Geometry Nodes system ---
    mod = obj.modifiers.new("System", "NODES")
    tree = bpy.data.node_groups.new("ArtifactSystem", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    gi = nk.group_input(0, 0)
    go = nk.group_output(1400, 0)

    # Create interface sockets
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    # Initialize context
    ctx = {
        "params": params,
        "debug": debug,
        "nk": nk,
        "tree": tree,
        "masks": {},
        "attributes": [],
        "norm": {},
    }

    # --- Stage definitions ---

    def stage_normalize(geo, ctx):
        """Stage 0: Normalize parameters."""
        p = ctx["params"]
        ctx["norm"] = {
            "z_min": -p.get("size", [0, 0, 0.08])[2],
            "z_max": p.get("size", [0, 0, 0.08])[2],
            "detail": float(p.get("detail_amount", 0.0)),
        }
        return geo, ctx

    def stage_primary(geo, ctx):
        """Stage 1: Primary structure (pass-through for this example)."""
        return geo, ctx

    def stage_secondary(geo, ctx):
        """Stage 2: Secondary operations - create height mask."""
        nk = ctx["nk"]
        mask = height_mask_geo(
            nk,
            x=200,
            y=-200,
            z_min=ctx["norm"]["z_min"],
            z_max=ctx["norm"]["z_max"],
            invert=False,
        )
        ctx["masks"]["mask_height"] = mask
        return geo, ctx

    def stage_detail(geo, ctx):
        """Stage 3: Detail pass (placeholder for surface effects)."""
        # This would apply noise, displacement, etc. gated by masks
        return geo, ctx

    def stage_output(geo, ctx):
        """Stage 4: Output prep - store debug attributes."""
        nk = ctx["nk"]

        if ctx["debug"].get("enabled"):
            for name, mask in ctx["masks"].items():
                store = nk.n(
                    "GeometryNodeStoreNamedAttribute",
                    f"Store_{name}",
                    x=900,
                    y=-200,
                )
                store.data_type = "FLOAT"
                store.domain = "POINT"
                nk.set(store.inputs["Name"], name)

                nk.link(geo, store.inputs["Geometry"])
                nk.link(mask, store.inputs["Value"])
                geo = store.outputs["Geometry"]

        return geo, ctx

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

    return {"root_objects": [obj]}
