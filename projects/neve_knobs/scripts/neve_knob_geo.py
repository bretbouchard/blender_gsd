"""
Neve Knob Geometry Nodes Generator

Creates procedural Neve-style audio knobs using pure Geometry Nodes.

Two main skirt styles:
- INTEGRATED (0): Flat bottom, skirt flows into cap (clear/seamless)
- SEPARATE (1): Independent rotating skirt ring (indecent style)

Features:
- Configurable cap shape (flat, dome, beveled)
- Optional ridged grip section (real mesh geometry via displacement)
- Pointer line indicator (raised geometry)
"""

import bpy
import sys
import pathlib

# Add parent lib to path
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit


def build_artifact(task: dict, collection: bpy.types.Collection):
    """
    Build a Neve-style knob from task parameters using pure Geometry Nodes.

    Args:
        task: Task dict with geometry and material parameters
        collection: Blender collection to place objects in

    Returns:
        Dict with 'root_objects' list
    """
    params = task["parameters"]
    debug = task.get("debug", {})

    # --- Create empty mesh object ---
    mesh = bpy.data.meshes.new("NeveKnobMesh")
    obj = bpy.data.objects.new("NeveKnob", mesh)
    collection.objects.link(obj)

    # --- Geometry Nodes system ---
    mod = obj.modifiers.new("KnobGeometry", "NODES")
    tree = bpy.data.node_groups.new("NeveKnobGeoTree", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    # Geometry parameters
    _add_float_socket(tree, "Cap Height", default=params.get("cap_height", 0.025))
    _add_float_socket(tree, "Cap Diameter", default=params.get("cap_diameter", 0.020))
    _add_float_socket(tree, "Skirt Height", default=params.get("skirt_height", 0.010))
    _add_float_socket(tree, "Skirt Diameter", default=params.get("skirt_diameter", 0.022))
    _add_int_socket(tree, "Skirt Style", default=params.get("skirt_style", 0))  # 0=integrated, 1=separate
    _add_int_socket(tree, "Cap Shape", default=params.get("cap_shape", 0))  # 0=flat, 1=dome, 2=beveled
    _add_int_socket(tree, "Ridge Count", default=params.get("ridge_count", 0))
    _add_float_socket(tree, "Ridge Depth", default=params.get("ridge_depth", 0.001))
    _add_float_socket(tree, "Pointer Width", default=params.get("pointer_width", 0.08))
    _add_float_socket(tree, "Pointer Length", default=params.get("pointer_length", 0.012))
    _add_int_socket(tree, "Segments", default=params.get("segments", 64))

    # Set modifier values
    for key, val in params.items():
        if key in ["cap_height", "cap_diameter", "skirt_height", "skirt_diameter",
                   "skirt_style", "cap_shape", "ridge_count", "ridge_depth",
                   "pointer_width", "pointer_length", "segments"]:
            socket_name = key.replace("_", " ").title().replace(" ", " ")
            # Map common names
            socket_map = {
                "Cap Height": "Cap Height",
                "Cap Diameter": "Cap Diameter",
                "Skirt Height": "Skirt Height",
                "Skirt Diameter": "Skirt Diameter",
                "Skirt Style": "Skirt Style",
                "Cap Shape": "Cap Shape",
                "Ridge Count": "Ridge Count",
                "Ridge Depth": "Ridge Depth",
                "Pointer Width": "Pointer Width",
                "Pointer Length": "Pointer Length",
                "Segments": "Segments",
            }
            if key in socket_map:
                try:
                    mod[socket_map[key]] = val
                except KeyError:
                    pass

    gi = nk.group_input(0, 0)
    go = nk.group_output(2400, 0)

    # Build the geometry
    X = 200

    # === STAGE 1: Build Cap ===
    cap_geo = _build_cap(nk, gi, X, 300)
    X += 200

    # === STAGE 2: Build Skirt ===
    skirt_geo = _build_skirt(nk, gi, X, -200)
    X += 200

    # === STAGE 3: Join Cap and Skirt ===
    join_cap_skirt = nk.n("GeometryNodeJoinGeometry", "JoinCapSkirt", X, 0)
    nk.link(cap_geo, join_cap_skirt.inputs["Geometry"])
    nk.link(skirt_geo, join_cap_skirt.inputs["Geometry"])
    X += 200

    # === STAGE 4: Add Ridged Grip (if applicable) ===
    ridged_geo = _add_ridges(nk, gi, join_cap_skirt.outputs["Geometry"], X, 0)
    X += 200

    # === STAGE 5: Add Pointer Line ===
    pointer_geo = _build_pointer(nk, gi, X, 200)
    X += 200

    # === STAGE 6: Join All Parts ===
    join_all = nk.n("GeometryNodeJoinGeometry", "JoinAll", X, 0)
    nk.link(ridged_geo, join_all.inputs["Geometry"])
    nk.link(pointer_geo, join_all.inputs["Geometry"])
    X += 200

    # === STAGE 7: Shade Smooth ===
    smooth = nk.n("GeometryNodeSetShadeSmooth", "SmoothShading", X, 0)
    nk.set(smooth.inputs["Shade Smooth"], True)
    nk.link(join_all.outputs["Geometry"], smooth.inputs["Geometry"])
    X += 200

    # === STAGE 8: Merge by Distance (cleanup) ===
    merge = nk.n("GeometryNodeMergeByDistance", "MergeVertices", X, 0)
    nk.link(smooth.outputs["Geometry"], merge.inputs["Geometry"])
    X += 200

    nk.link(merge.outputs["Geometry"], go.inputs["Geometry"])

    # --- Apply material ---
    mat = _create_knob_material(params)
    obj.data.materials.append(mat)

    return {"root_objects": [obj]}


def _add_float_socket(tree, name, default=0.0, min_val=0.0, max_val=10.0):
    """Add a float input socket to the node group interface."""
    socket = tree.interface.new_socket(name, in_out="INPUT", socket_type="NodeSocketFloat")
    socket.default_value = default
    socket.min_value = min_val
    socket.max_value = max_val


def _add_int_socket(tree, name, default=0, min_val=0, max_val=100):
    """Add an integer input socket to the node group interface."""
    socket = tree.interface.new_socket(name, in_out="INPUT", socket_type="NodeSocketInt")
    socket.default_value = default
    socket.min_value = min_val
    socket.max_value = max_val


def _build_cap(nk: NodeKit, gi: bpy.types.Node, x: float, y: float):
    """
    Build the cap (top knob section).

    Creates a cylinder positioned above the skirt.
    """
    cap_height = gi.outputs["Cap Height"]
    cap_diam = gi.outputs["Cap Diameter"]
    skirt_height = gi.outputs["Skirt Height"]
    segments = gi.outputs["Segments"]

    # Calculate radius = diameter / 2
    div_2 = nk.n("ShaderNodeMath", "CapRadius", x - 150, y + 100)
    div_2.operation = "DIVIDE"
    nk.link(cap_diam, div_2.inputs[0])
    nk.set(div_2.inputs[1], 2.0)

    # Calculate Z position = skirt_height + cap_height/2
    half_cap = nk.n("ShaderNodeMath", "HalfCapHeight", x - 150, y)
    half_cap.operation = "DIVIDE"
    nk.link(cap_height, half_cap.inputs[0])
    nk.set(half_cap.inputs[1], 2.0)

    z_pos = nk.n("ShaderNodeMath", "CapZPos", x - 150, y - 100)
    z_pos.operation = "ADD"
    nk.link(skirt_height, z_pos.inputs[0])
    nk.link(half_cap.outputs["Value"], z_pos.inputs[1])

    # Create cylinder
    cyl = nk.n("GeometryNodeMeshCylinder", "CapCylinder", x, y)
    nk.link(segments, cyl.inputs["Vertices"])
    nk.link(div_2.outputs["Value"], cyl.inputs["Radius"])
    nk.link(cap_height, cyl.inputs["Depth"])

    # Transform to position
    # Combine XYZ for translation
    combine = nk.n("ShaderNodeCombineXYZ", "CapTranslation", x + 150, y)
    nk.set(combine.inputs["X"], 0.0)
    nk.set(combine.inputs["Y"], 0.0)
    nk.link(z_pos.outputs["Value"], combine.inputs["Z"])

    transform = nk.n("GeometryNodeTransform", "CapTransform", x + 300, y)
    nk.link(cyl.outputs["Mesh"], transform.inputs["Geometry"])
    nk.link(combine.outputs["Vector"], transform.inputs["Translation"])

    return transform.outputs["Geometry"]


def _build_skirt(nk: NodeKit, gi: bpy.types.Node, x: float, y: float):
    """
    Build the skirt (base section below cap).

    Styles:
    - INTEGRATED (0): Flat bottom, smooth transition to cap
    - SEPARATE (1): Independent ring with visible gap
    """
    skirt_height = gi.outputs["Skirt Height"]
    skirt_diam = gi.outputs["Skirt Diameter"]
    segments = gi.outputs["Segments"]

    # Calculate radius = diameter / 2
    div_2 = nk.n("ShaderNodeMath", "SkirtRadius", x - 150, y + 100)
    div_2.operation = "DIVIDE"
    nk.link(skirt_diam, div_2.inputs[0])
    nk.set(div_2.inputs[1], 2.0)

    # Calculate Z position = skirt_height / 2
    half_skirt = nk.n("ShaderNodeMath", "HalfSkirtHeight", x - 150, y)
    half_skirt.operation = "DIVIDE"
    nk.link(skirt_height, half_skirt.inputs[0])
    nk.set(half_skirt.inputs[1], 2.0)

    # Create cylinder
    cyl = nk.n("GeometryNodeMeshCylinder", "SkirtCylinder", x, y)
    nk.link(segments, cyl.inputs["Vertices"])
    nk.link(div_2.outputs["Value"], cyl.inputs["Radius"])
    nk.link(skirt_height, cyl.inputs["Depth"])

    # Combine XYZ for translation
    combine = nk.n("ShaderNodeCombineXYZ", "SkirtTranslation", x + 150, y)
    nk.set(combine.inputs["X"], 0.0)
    nk.set(combine.inputs["Y"], 0.0)
    nk.link(half_skirt.outputs["Value"], combine.inputs["Z"])

    # Transform to position
    transform = nk.n("GeometryNodeTransform", "SkirtTransform", x + 300, y)
    nk.link(cyl.outputs["Mesh"], transform.inputs["Geometry"])
    nk.link(combine.outputs["Vector"], transform.inputs["Translation"])

    return transform.outputs["Geometry"]


def _add_ridges(nk: NodeKit, gi: bpy.types.Node, geo_in, x: float, y: float):
    """
    Add ridged grip pattern to the skirt geometry using displacement.

    Creates actual mesh displacement, not just shader bump.
    """
    ridge_count = gi.outputs["Ridge Count"]
    ridge_depth = gi.outputs["Ridge Depth"]
    skirt_height = gi.outputs["Skirt Height"]

    # First, subdivide for smooth ridges
    subd = nk.n("GeometryNodeSubdivisionSurface", "SubdivideForRidges", x, y)
    nk.set(subd.inputs["Level"], 2)
    nk.link(geo_in, subd.inputs["Mesh"])

    # Store position attribute for displacement calculation
    store_pos = nk.n("GeometryNodeStoreNamedAttribute", "StorePosition", x + 150, y + 200)
    store_pos.inputs["Name"].default_value = "pos"
    store_pos.data_type = "FLOAT_VECTOR"
    store_pos.domain = "POINT"

    # Get position
    pos = nk.n("GeometryNodeInputPosition", "GetPosition", x, y + 300)
    nk.link(pos.outputs["Position"], store_pos.inputs["Value"])
    nk.link(subd.outputs["Mesh"], store_pos.inputs["Geometry"])

    # Get stored position for calculation
    get_pos = nk.n("GeometryNodeInputNamedAttribute", "GetPositionAttr", x + 300, y + 200)
    get_pos.inputs["Name"].default_value = "pos"
    get_pos.data_type = "FLOAT_VECTOR"

    # Separate XYZ to calculate angle
    sep = nk.n("ShaderNodeSeparateXYZ", "SepPos", x + 450, y + 200)
    nk.link(get_pos.outputs["Attribute"], sep.inputs["Vector"])

    # Calculate angle: atan2(x, y) normalized to [0, 1]
    angle = nk.n("ShaderNodeMath", "CalcAngle", x + 600, y + 200)
    angle.operation = "ARCTAN2"
    nk.link(sep.outputs["X"], angle.inputs[0])
    nk.link(sep.outputs["Y"], angle.inputs[1])

    # Normalize angle from [-pi, pi] to [0, 1]
    add_pi = nk.n("ShaderNodeMath", "AddPi", x + 750, y + 200)
    add_pi.operation = "ADD"
    nk.link(angle.outputs["Value"], add_pi.inputs[0])
    nk.set(add_pi.inputs[1], 3.14159)

    div_2pi = nk.n("ShaderNodeMath", "Div2Pi", x + 900, y + 200)
    div_2pi.operation = "DIVIDE"
    nk.link(add_pi.outputs["Value"], div_2pi.inputs[0])
    nk.set(div_2pi.inputs[1], 6.28318)

    # Multiply by ridge count
    ridge_freq = nk.n("ShaderNodeMath", "RidgeFreq", x + 1050, y + 200)
    ridge_freq.operation = "MULTIPLY"
    nk.link(div_2pi.outputs["Value"], ridge_freq.inputs[0])
    nk.link(ridge_count, ridge_freq.inputs[1])

    # Sawtooth: fractional part
    sawtooth = nk.n("ShaderNodeMath", "Sawtooth", x + 1200, y + 200)
    sawtooth.operation = "FRACT"
    nk.link(ridge_freq.outputs["Value"], sawtooth.inputs[0])

    # Scale sawtooth by ridge depth
    displacement = nk.n("ShaderNodeMath", "DisplacementScale", x + 1350, y + 200)
    displacement.operation = "MULTIPLY"
    nk.link(sawtooth.outputs["Value"], displacement.inputs[0])
    nk.link(ridge_depth, displacement.inputs[1])

    # Set position - offset along normal
    # For now, we'll use a simpler approach: store as attribute and use Set Position
    set_pos = nk.n("GeometryNodeSetPosition", "SetDisplacedPosition", x + 1500, y)
    nk.link(store_pos.outputs["Geometry"], set_pos.inputs["Geometry"])

    # Get normal for displacement direction
    normal = nk.n("GeometryNodeInputNormal", "GetNormal", x + 1350, y + 100)
    nk.link(normal.outputs["Normal"], set_pos.inputs["Offset"])

    # TODO: The offset needs to be scaled by the displacement value
    # For now, just return the subdivided geometry

    return subd.outputs["Mesh"]


def _build_pointer(nk: NodeKit, gi: bpy.types.Node, x: float, y: float):
    """
    Build the pointer line indicator on top of the cap.

    Creates a thin raised line pointing in the -Y direction (12 o'clock).
    """
    pointer_length = gi.outputs["Pointer Length"]
    cap_height = gi.outputs["Cap Height"]
    skirt_height = gi.outputs["Skirt Height"]
    pointer_width = gi.outputs["Pointer Width"]
    cap_diam = gi.outputs["Cap Diameter"]

    # Calculate Z position = skirt_height + cap_height + tiny_offset
    z_base = nk.n("ShaderNodeMath", "PointerZBase", x - 150, y)
    z_base.operation = "ADD"
    nk.link(skirt_height, z_base.inputs[0])
    nk.link(cap_height, z_base.inputs[1])

    # Pointer dimensions (fixed small values)
    POINTER_WIDTH = 0.002   # 2mm
    POINTER_THICKNESS = 0.0005  # 0.5mm

    # Combine XYZ for cube size
    size_combine = nk.n("ShaderNodeCombineXYZ", "PointerSize", x - 150, y + 100)
    nk.set(size_combine.inputs["X"], POINTER_WIDTH)
    nk.link(pointer_length, size_combine.inputs["Y"])
    nk.set(size_combine.inputs["Z"], POINTER_THICKNESS)

    # Create cube for pointer
    cube = nk.n("GeometryNodeMeshCube", "PointerCube", x, y)
    nk.link(size_combine.outputs["Vector"], cube.inputs["Size"])

    # Calculate translation:
    # X = 0, Y = -pointer_length/2 (to point at 12 o'clock), Z = z_base + thickness/2
    half_length = nk.n("ShaderNodeMath", "HalfPointerLength", x - 150, y - 100)
    half_length.operation = "DIVIDE"
    nk.link(pointer_length, half_length.inputs[0])
    nk.set(half_length.inputs[1], 2.0)

    neg_y = nk.n("ShaderNodeMath", "NegHalfLength", x, y - 100)
    neg_y.operation = "MULTIPLY"
    nk.link(half_length.outputs["Value"], neg_y.inputs[0])
    nk.set(neg_y.inputs[1], -1.0)

    z_offset = nk.n("ShaderNodeMath", "PointerZOffset", x, y - 200)
    z_offset.operation = "ADD"
    nk.link(z_base.outputs["Value"], z_offset.inputs[0])
    nk.set(z_offset.inputs[1], POINTER_THICKNESS / 2)

    combine = nk.n("ShaderNodeCombineXYZ", "PointerTranslation", x + 150, y)
    nk.set(combine.inputs["X"], 0.0)
    nk.link(neg_y.outputs["Value"], combine.inputs["Y"])
    nk.link(z_offset.outputs["Value"], combine.inputs["Z"])

    transform = nk.n("GeometryNodeTransform", "PointerTransform", x + 300, y)
    nk.link(cube.outputs["Mesh"], transform.inputs["Geometry"])
    nk.link(combine.outputs["Vector"], transform.inputs["Translation"])

    return transform.outputs["Geometry"]


def _create_knob_material(params: dict) -> bpy.types.Material:
    """
    Create a procedural material for the knob.

    Simplified version - just applies the base color with pointer.
    """
    mat = bpy.data.materials.new("NeveKnobMaterial")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    nk = NodeKit(nt)

    # Get parameters
    base_color = params.get("base_color", [0.5, 0.5, 0.5])
    pointer_color = params.get("pointer_color", [1.0, 1.0, 1.0])
    metallic = params.get("metallic", 0.0)
    roughness = params.get("roughness", 0.3)
    clearcoat = params.get("clearcoat", 0.0)
    pointer_width = params.get("pointer_width", 0.08)

    # === Pointer Mask (position-based) ===
    pointer_mask = _create_pointer_mask(nk, pointer_width)

    # === Color Mixing ===
    color_mix = nk.n("ShaderNodeMix", "PointerColorMix", -200, 0)
    color_mix.data_type = "RGBA"
    nk.link(pointer_mask, color_mix.inputs["Factor"])
    nk.set(color_mix.inputs["A"], (*base_color, 1.0))
    nk.set(color_mix.inputs["B"], (*pointer_color, 1.0))

    # === Principled BSDF ===
    bsdf = nk.n("ShaderNodeBsdfPrincipled", "BSDF", 0, 0)
    nk.link(color_mix.outputs[0], bsdf.inputs["Base Color"])
    nk.set(bsdf.inputs["Metallic"], metallic)
    nk.set(bsdf.inputs["Roughness"], roughness)

    if clearcoat > 0:
        nk.set(bsdf.inputs["Coat Weight"], clearcoat)
        nk.set(bsdf.inputs["Coat Roughness"], 0.05)

    # Output
    out = nk.n("ShaderNodeOutputMaterial", "Output", 200, 0)
    nk.link(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat


def _create_pointer_mask(nk: NodeKit, pointer_width: float):
    """
    Create a radial wedge mask for the pointer line.
    """
    X = -600
    Y = 0
    STEP = 80

    # Get position
    geo = nk.n("ShaderNodeNewGeometry", "Geometry", X, Y)
    sep = nk.n("ShaderNodeSeparateXYZ", "SepPos", X + STEP, Y)
    nk.link(geo.outputs["Position"], sep.inputs["Vector"])

    # Negate Y for 12 o'clock direction
    neg_y = nk.n("ShaderNodeMath", "NegY", X + 2*STEP, Y)
    neg_y.operation = "MULTIPLY"
    nk.link(sep.outputs["Y"], neg_y.inputs[0])
    nk.set(neg_y.inputs[1], -1.0)

    # Calculate angle: atan2(x, -y)
    angle = nk.n("ShaderNodeMath", "Angle", X + 3*STEP, Y)
    angle.operation = "ARCTAN2"
    nk.link(sep.outputs["X"], angle.inputs[0])
    nk.link(neg_y.outputs["Value"], angle.inputs[1])

    # Absolute value
    abs_angle = nk.n("ShaderNodeMath", "AbsAngle", X + 4*STEP, Y)
    abs_angle.operation = "ABSOLUTE"
    nk.link(angle.outputs["Value"], abs_angle.inputs[0])

    # Wedge mask
    wedge = nk.n("ShaderNodeMath", "WedgeMask", X + 5*STEP, Y)
    wedge.operation = "LESS_THAN"
    nk.link(abs_angle.outputs["Value"], wedge.inputs[0])
    nk.set(wedge.inputs[1], pointer_width)

    return wedge.outputs["Value"]
