"""
Neve Knob Geometry Nodes Generator v3

Full implementation with:
- Cap and skirt cylinders
- REAL ridge geometry via Set Position displacement
- Pointer line (cube geometry)
- Material with position-based pointer mask

Two skirt styles:
- INTEGRATED (0): Flat bottom, seamless transition
- SEPARATE (1): Independent rotating ring (gap between cap and skirt)
"""

import bpy
import sys
import pathlib
import math

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit


def build_artifact(task: dict, collection: bpy.types.Collection):
    """
    Build a Neve-style knob using pure Geometry Nodes.
    """
    params = task["parameters"]

    # Extract parameters with defaults
    cap_height = params.get("cap_height", 0.020)
    cap_diameter = params.get("cap_diameter", 0.018)
    skirt_height = params.get("skirt_height", 0.008)
    skirt_diameter = params.get("skirt_diameter", 0.020)
    skirt_style = params.get("skirt_style", 0)  # 0=integrated, 1=separate
    ridge_count = params.get("ridge_count", 0)
    ridge_depth = params.get("ridge_depth", 0.001)
    pointer_length = params.get("pointer_length", 0.012)
    pointer_width_rad = params.get("pointer_width", 0.08)
    segments = params.get("segments", 64)

    # Create empty mesh object
    mesh = bpy.data.meshes.new("NeveKnobMesh")
    obj = bpy.data.objects.new("NeveKnob", mesh)
    collection.objects.link(obj)

    # Geometry Nodes modifier
    mod = obj.modifiers.new("KnobGeometry", "NODES")
    tree = bpy.data.node_groups.new("NeveKnobGeoTree", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    # Interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    gi = nk.group_input(0, 0)
    go = nk.group_output(3000, 0)

    # === LAYOUT CONSTANTS ===
    X = 200
    Y_CAP = 300
    Y_SKIRT = -100

    # === 1. CAP CYLINDER ===
    cap_cyl = nk.n("GeometryNodeMeshCylinder", "CapCylinder", X, Y_CAP)
    cap_cyl.inputs["Vertices"].default_value = segments
    cap_cyl.inputs["Radius"].default_value = cap_diameter / 2
    cap_cyl.inputs["Depth"].default_value = cap_height
    X += 200

    cap_transform = nk.n("GeometryNodeTransform", "CapTransform", X, Y_CAP)
    nk.link(cap_cyl.outputs["Mesh"], cap_transform.inputs["Geometry"])
    cap_transform.inputs["Translation"].default_value = (0, 0, skirt_height + cap_height/2)
    X += 200

    # === 2. SKIRT CYLINDER ===
    X = 200
    skirt_cyl = nk.n("GeometryNodeMeshCylinder", "SkirtCylinder", X, Y_SKIRT)
    skirt_cyl.inputs["Vertices"].default_value = segments
    skirt_cyl.inputs["Radius"].default_value = skirt_diameter / 2
    skirt_cyl.inputs["Depth"].default_value = skirt_height
    X += 200

    # For SEPARATE style, add a small gap
    gap_z = 0.002 if skirt_style == 1 else 0.0

    skirt_transform = nk.n("GeometryNodeTransform", "SkirtTransform", X, Y_SKIRT)
    nk.link(skirt_cyl.outputs["Mesh"], skirt_transform.inputs["Geometry"])
    skirt_transform.inputs["Translation"].default_value = (0, 0, skirt_height/2 + gap_z)
    X += 200

    # === 3. JOIN CAP + SKIRT ===
    join1 = nk.n("GeometryNodeJoinGeometry", "JoinCapSkirt", X, 100)
    nk.link(cap_transform.outputs["Geometry"], join1.inputs["Geometry"])
    nk.link(skirt_transform.outputs["Geometry"], join1.inputs["Geometry"])
    X += 200

    # === 4. SUBDIVIDE FOR SMOOTH RIDGES ===
    subd = nk.n("GeometryNodeSubdivisionSurface", "Subdivide", X, 100)
    subd.inputs["Level"].default_value = 3  # Higher for smoother ridges
    nk.link(join1.outputs["Geometry"], subd.inputs["Mesh"])
    X += 200

    # === 5. ADD RIDGES (if ridge_count > 0) ===
    # We'll build the ridge displacement math
    if ridge_count > 0:
        # Get position
        pos = nk.n("GeometryNodeInputPosition", "GetPosition", X, 350)
        sep = nk.n("ShaderNodeSeparateXYZ", "SepPosition", X + 100, 350)
        nk.link(pos.outputs["Position"], sep.inputs["Vector"])

        # Calculate angle: atan2(x, y)
        angle = nk.n("ShaderNodeMath", "Angle", X + 200, 350)
        angle.operation = "ARCTAN2"
        nk.link(sep.outputs["X"], angle.inputs[0])
        nk.link(sep.outputs["Y"], angle.inputs[1])

        # Normalize: (angle + pi) / (2*pi) -> [0, 1]
        add_pi = nk.n("ShaderNodeMath", "AddPi", X + 300, 350)
        add_pi.operation = "ADD"
        nk.link(angle.outputs["Value"], add_pi.inputs[0])
        add_pi.inputs[1].default_value = math.pi

        div_2pi = nk.n("ShaderNodeMath", "Div2Pi", X + 400, 350)
        div_2pi.operation = "DIVIDE"
        nk.link(add_pi.outputs["Value"], div_2pi.inputs[0])
        div_2pi.inputs[1].default_value = 2 * math.pi

        # Multiply by ridge count
        freq = nk.n("ShaderNodeMath", "Freq", X + 500, 350)
        freq.operation = "MULTIPLY"
        nk.link(div_2pi.outputs["Value"], freq.inputs[0])
        freq.inputs[1].default_value = float(ridge_count)

        # Sawtooth: fract()
        sawtooth = nk.n("ShaderNodeMath", "Sawtooth", X + 600, 350)
        sawtooth.operation = "FRACT"
        nk.link(freq.outputs["Value"], sawtooth.inputs[0])

        # Remap sawtooth to [-1, 1] for centered displacement
        # sawtooth * 2 - 1
        mult2 = nk.n("ShaderNodeMath", "Mult2", X + 700, 350)
        mult2.operation = "MULTIPLY"
        nk.link(sawtooth.outputs["Value"], mult2.inputs[0])
        mult2.inputs[1].default_value = 2.0

        sub1 = nk.n("ShaderNodeMath", "Sub1", X + 800, 350)
        sub1.operation = "SUBTRACT"
        nk.link(mult2.outputs["Value"], sub1.inputs[0])
        sub1.inputs[1].default_value = 1.0

        # Scale by ridge depth
        depth_scale = nk.n("ShaderNodeMath", "DepthScale", X + 900, 350)
        depth_scale.operation = "MULTIPLY"
        nk.link(sub1.outputs["Value"], depth_scale.inputs[0])
        depth_scale.inputs[1].default_value = ridge_depth

        # Get normal for displacement direction
        normal = nk.n("GeometryNodeInputNormal", "GetNormal", X + 900, 200)

        # Scale normal by displacement
        scale_disp = nk.n("ShaderNodeVectorMath", "ScaleDisplacement", X + 1000, 200)
        scale_disp.operation = "SCALE"
        nk.link(normal.outputs["Normal"], scale_disp.inputs["Vector"])
        nk.link(depth_scale.outputs["Value"], scale_disp.inputs["Scale"])

        # Set position with displacement
        set_pos = nk.n("GeometryNodeSetPosition", "SetRidgeDisplacement", X + 1200, 100)
        nk.link(subd.outputs["Mesh"], set_pos.inputs["Geometry"])
        nk.link(scale_disp.outputs["Vector"], set_pos.inputs["Offset"])

        ridge_geo = set_pos.outputs["Geometry"]
        X += 1300
    else:
        ridge_geo = subd.outputs["Mesh"]

    # === 6. SET SHADE SMOOTH ===
    smooth = nk.n("GeometryNodeSetShadeSmooth", "Smooth", X, 100)
    smooth.inputs["Shade Smooth"].default_value = True
    nk.link(ridge_geo, smooth.inputs["Geometry"])
    X += 200

    # === 7. POINTER CUBE ===
    pointer_x = 200
    pointer_y = 500
    pointer_cube = nk.n("GeometryNodeMeshCube", "PointerCube", pointer_x, pointer_y)
    # Size: thin width, pointer_length, very thin height
    pointer_width_linear = (cap_diameter / 2) * pointer_width_rad  # Approximate linear width
    pointer_cube.inputs["Size"].default_value = (pointer_width_linear, pointer_length, 0.0005)
    pointer_cube.inputs["Vertices X"].default_value = 1
    pointer_cube.inputs["Vertices Y"].default_value = 1
    pointer_cube.inputs["Vertices Z"].default_value = 1

    pointer_transform = nk.n("GeometryNodeTransform", "PointerTransform", pointer_x + 200, pointer_y)
    nk.link(pointer_cube.outputs["Mesh"], pointer_transform.inputs["Geometry"])
    # Position: on top of cap, pointing to 12 o'clock (-Y direction)
    pointer_z = skirt_height + cap_height + 0.00025
    pointer_y_pos = -pointer_length / 2
    pointer_transform.inputs["Translation"].default_value = (0, pointer_y_pos, pointer_z)

    # === 8. JOIN ALL ===
    join_all = nk.n("GeometryNodeJoinGeometry", "JoinAll", X, 100)
    nk.link(smooth.outputs["Geometry"], join_all.inputs["Geometry"])
    nk.link(pointer_transform.outputs["Geometry"], join_all.inputs["Geometry"])
    X += 200

    # === 9. MERGE VERTICES ===
    merge = nk.n("GeometryNodeMergeByDistance", "Merge", X, 100)
    nk.link(join_all.outputs["Geometry"], merge.inputs["Geometry"])
    X += 200

    # === 10. SET MATERIAL ===
    mat = _create_material(params)
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", X, 100)
    set_mat.inputs["Material"].default_value = mat
    nk.link(merge.outputs["Geometry"], set_mat.inputs["Geometry"])
    X += 200

    # OUTPUT
    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    return {"root_objects": [obj]}


def _create_material(params: dict) -> bpy.types.Material:
    """Create knob material with position-based pointer mask."""
    mat = bpy.data.materials.new("NeveKnobMaterial")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    nk = NodeKit(nt)

    base_color = params.get("base_color", [0.5, 0.5, 0.5])
    pointer_color = params.get("pointer_color", [1.0, 1.0, 1.0])
    pointer_width = params.get("pointer_width", 0.08)
    metallic = params.get("metallic", 0.0)
    roughness = params.get("roughness", 0.3)
    clearcoat = params.get("clearcoat", 0.0)

    X = -900
    STEP = 100

    # Position-based pointer mask
    geo = nk.n("ShaderNodeNewGeometry", "Geometry", X, 0)
    sep = nk.n("ShaderNodeSeparateXYZ", "SepPosition", X + STEP, 0)
    nk.link(geo.outputs["Position"], sep.inputs["Vector"])

    # Negate Y for 12 o'clock direction
    neg_y = nk.n("ShaderNodeMath", "NegateY", X + 2*STEP, 0)
    neg_y.operation = "MULTIPLY"
    nk.link(sep.outputs["Y"], neg_y.inputs[0])
    neg_y.inputs[1].default_value = -1.0

    # Angle: atan2(x, -y)
    angle = nk.n("ShaderNodeMath", "Angle", X + 3*STEP, 0)
    angle.operation = "ARCTAN2"
    nk.link(sep.outputs["X"], angle.inputs[0])
    nk.link(neg_y.outputs["Value"], angle.inputs[1])

    # Absolute value
    abs_angle = nk.n("ShaderNodeMath", "AbsAngle", X + 4*STEP, 0)
    abs_angle.operation = "ABSOLUTE"
    nk.link(angle.outputs["Value"], abs_angle.inputs[0])

    # Wedge mask: |angle| < pointer_width
    wedge = nk.n("ShaderNodeMath", "WedgeMask", X + 5*STEP, 0)
    wedge.operation = "LESS_THAN"
    nk.link(abs_angle.outputs["Value"], wedge.inputs[0])
    wedge.inputs[1].default_value = pointer_width

    # Mix colors
    mix = nk.n("ShaderNodeMix", "ColorMix", X + 6*STEP, 0)
    mix.data_type = "RGBA"
    nk.link(wedge.outputs["Value"], mix.inputs["Factor"])
    mix.inputs[6].default_value = (*base_color, 1.0)  # A = base color
    mix.inputs[7].default_value = (*pointer_color, 1.0)  # B = pointer color

    # Principled BSDF
    bsdf = nk.n("ShaderNodeBsdfPrincipled", "BSDF", X + 8*STEP, 0)
    nk.link(mix.outputs[2], bsdf.inputs["Base Color"])  # Output 2 is Result for Mix RGB
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness

    if clearcoat > 0:
        bsdf.inputs["Coat Weight"].default_value = clearcoat
        bsdf.inputs["Coat Roughness"].default_value = 0.05

    # Output
    out = nk.n("ShaderNodeOutputMaterial", "Output", X + 10*STEP, 0)
    nk.link(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat
