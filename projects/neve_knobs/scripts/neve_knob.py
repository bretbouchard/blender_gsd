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
    Create a procedural material for the knob with pointer line and ridge bump.

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

    # Extract parameters with defaults
    base_color = params.get("base_color", [0.5, 0.5, 0.5])
    pointer_color = params.get("pointer_color", [1.0, 1.0, 1.0])
    metallic = params.get("metallic", 0.0)
    roughness = params.get("roughness", 0.3)
    clearcoat = params.get("clearcoat", 0.0)
    ridge_count = params.get("ridge_count", 0)
    ridge_depth = params.get("ridge_depth", 0.001)
    pointer_width = params.get("pointer_width", 0.08)

    # === POINTER MASK (Position-based wedge) ===
    pointer_mask = _create_pointer_mask(nk, pointer_width)

    # === COLOR BLENDING ===
    # Mix base color with pointer color based on mask
    base_rgba = (base_color[0], base_color[1], base_color[2], 1.0)
    pointer_rgba = (pointer_color[0], pointer_color[1], pointer_color[2], 1.0)

    color_mix = nk.n("ShaderNodeMix", "PointerColorMix", 200, 0)
    color_mix.data_type = "RGBA"
    nk.link(pointer_mask, color_mix.inputs["Factor"])
    nk.set(color_mix.inputs["A"], base_rgba)
    nk.set(color_mix.inputs["B"], pointer_rgba)

    final_color = color_mix.outputs[0]

    # === NORMAL/BUMP FOR RIDGES ===
    normal_input = None
    if ridge_count > 0:
        normal_input = _create_ridge_bump(nk, ridge_count, ridge_depth)

    # === PRINCIPLED BSDF ===
    bsdf = nk.n("ShaderNodeBsdfPrincipled", "PrincipledBSDF", 500, 0)

    # Core PBR properties
    nk.link(final_color, bsdf.inputs["Base Color"])
    nk.set(bsdf.inputs["Metallic"], metallic)
    nk.set(bsdf.inputs["Roughness"], roughness)

    # Clearcoat for glossy finish
    if clearcoat > 0:
        nk.set(bsdf.inputs["Coat Weight"], clearcoat)
        nk.set(bsdf.inputs["Coat Roughness"], 0.05)

    # Connect normal if we have ridges
    if normal_input:
        nk.link(normal_input, bsdf.inputs["Normal"])

    # Output
    out = nk.n("ShaderNodeOutputMaterial", "Output", 700, 0)
    nk.link(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat


def _create_pointer_mask(nk: NodeKit, pointer_width: float):
    """
    Create a radial wedge mask for the pointer line.

    Uses position-based masking to create a white indicator line
    that points toward the -Y direction (12 o'clock in front view).

    Args:
        nk: NodeKit instance
        pointer_width: Angular half-width in radians

    Returns:
        Socket containing mask value (0.0 to 1.0)
    """
    X_OFFSET = -500
    Y_OFFSET = 0
    X_STEP = 80

    # Get surface position
    geo = nk.n("ShaderNodeNewGeometry", "Geometry", X_OFFSET, Y_OFFSET)

    # Separate XYZ components
    sep = nk.n("ShaderNodeSeparateXYZ", "SepPosition", X_OFFSET + X_STEP, Y_OFFSET)
    nk.link(geo.outputs["Position"], sep.inputs["Vector"])

    # Negate Y so pointer points "up" in front view
    neg_y = nk.n("ShaderNodeMath", "NegateY", X_OFFSET + 2*X_STEP, Y_OFFSET)
    neg_y.operation = "MULTIPLY"
    nk.set(neg_y.inputs[1], -1.0)
    nk.link(sep.outputs["Y"], neg_y.inputs[0])

    # Calculate angle: atan2(x, -y)
    arctan2 = nk.n("ShaderNodeMath", "PointerAngle", X_OFFSET + 3*X_STEP, Y_OFFSET)
    arctan2.operation = "ARCTAN2"
    nk.link(sep.outputs["X"], arctan2.inputs[0])
    nk.link(neg_y.outputs["Value"], arctan2.inputs[1])

    # Absolute value of angle
    abs_angle = nk.n("ShaderNodeMath", "AbsAngle", X_OFFSET + 4*X_STEP, Y_OFFSET)
    abs_angle.operation = "ABSOLUTE"
    nk.link(arctan2.outputs["Value"], abs_angle.inputs[0])

    # Create wedge mask: mask = 1 where |angle| < pointer_width
    wedge = nk.n("ShaderNodeMath", "WedgeMask", X_OFFSET + 5*X_STEP, Y_OFFSET)
    wedge.operation = "LESS_THAN"
    nk.set(wedge.inputs[1], pointer_width)
    nk.link(abs_angle.outputs["Value"], wedge.inputs[0])

    return wedge.outputs["Value"]


def _create_ridge_bump(nk: NodeKit, ridge_count: int, ridge_depth: float):
    """
    Create procedural bump mapping for grip ridges.

    Creates a sawtooth pattern around the circumference using
    angular position around the Z axis.

    Args:
        nk: NodeKit instance
        ridge_count: Number of ridges around circumference
        ridge_depth: Bump strength/depth

    Returns:
        Socket containing normal vector for BSDF connection
    """
    X_OFFSET = -500
    Y_OFFSET = 200
    X_STEP = 80

    # Get surface position
    geo = nk.n("ShaderNodeNewGeometry", "GeometryRidges", X_OFFSET, Y_OFFSET)

    # Separate XYZ
    sep = nk.n("ShaderNodeSeparateXYZ", "SepRidges", X_OFFSET + X_STEP, Y_OFFSET)
    nk.link(geo.outputs["Position"], sep.inputs["Vector"])

    # Calculate angle around Z axis: atan2(x, y)
    arctan2 = nk.n("ShaderNodeMath", "RidgeAngle", X_OFFSET + 2*X_STEP, Y_OFFSET)
    arctan2.operation = "ARCTAN2"
    nk.link(sep.outputs["X"], arctan2.inputs[0])
    nk.link(sep.outputs["Y"], arctan2.inputs[1])

    # Shift from [-pi, pi] to [0, 2pi]
    add_pi = nk.n("ShaderNodeMath", "AddPi", X_OFFSET + 3*X_STEP, Y_OFFSET)
    add_pi.operation = "ADD"
    nk.set(add_pi.inputs[1], 3.14159)
    nk.link(arctan2.outputs["Value"], add_pi.inputs[0])

    # Normalize to [0, 1]: divide by 2pi
    div_2pi = nk.n("ShaderNodeMath", "Div2Pi", X_OFFSET + 4*X_STEP, Y_OFFSET)
    div_2pi.operation = "DIVIDE"
    nk.set(div_2pi.inputs[1], 6.28318)
    nk.link(add_pi.outputs["Value"], div_2pi.inputs[0])

    # Multiply by ridge count
    ridge_freq = nk.n("ShaderNodeMath", "RidgeFreq", X_OFFSET + 5*X_STEP, Y_OFFSET)
    ridge_freq.operation = "MULTIPLY"
    nk.set(ridge_freq.inputs[1], float(ridge_count))
    nk.link(div_2pi.outputs["Value"], ridge_freq.inputs[0])

    # Create sawtooth: fractional part
    sawtooth = nk.n("ShaderNodeMath", "Sawtooth", X_OFFSET + 6*X_STEP, Y_OFFSET)
    sawtooth.operation = "FRACT"
    nk.link(ridge_freq.outputs["Value"], sawtooth.inputs[0])

    # Bump node
    bump = nk.n("ShaderNodeBump", "RidgeBump", X_OFFSET + 7*X_STEP, Y_OFFSET)
    nk.set(bump.inputs["Strength"], ridge_depth * 10)  # Scale up for visibility
    nk.set(bump.inputs["Distance"], 0.01)
    nk.link(sawtooth.outputs["Value"], bump.inputs["Height"])

    return bump.outputs["Normal"]
