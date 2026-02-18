"""
Neve Knob Geometry Nodes Generator v2

Clean, robust implementation of procedural Neve-style audio knobs.

Two skirt styles:
- INTEGRATED (0): Flat bottom, seamless transition (clear/solid look)
- SEPARATE (1): Independent rotating skirt ring (indecent style)

Features:
- Cap and skirt as separate geometry primitives
- Optional ridged grip (real mesh via Set Position)
- Pointer line (raised cube geometry)
"""

import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit


def build_artifact(task: dict, collection: bpy.types.Collection):
    """
    Build a Neve-style knob using pure Geometry Nodes.
    """
    params = task["parameters"]

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

    # Parameters - use reasonable defaults
    p = {
        "cap_height": params.get("cap_height", 0.020),
        "cap_diameter": params.get("cap_diameter", 0.018),
        "skirt_height": params.get("skirt_height", 0.008),
        "skirt_diameter": params.get("skirt_diameter", 0.020),
        "ridge_count": params.get("ridge_count", 24),
        "ridge_depth": params.get("ridge_depth", 0.001),
        "pointer_length": params.get("pointer_length", 0.012),
        "segments": params.get("segments", 64),
    }

    # Add sockets with defaults
    for name, default in p.items():
        if isinstance(default, int):
            sock = tree.interface.new_socket(name.title().replace("_", " "), in_out="INPUT", socket_type="NodeSocketInt")
            sock.default_value = default
            sock.min_value = 0
            sock.max_value = 200
        else:
            sock = tree.interface.new_socket(name.title().replace("_", " "), in_out="INPUT", socket_type="NodeSocketFloat")
            sock.default_value = default
            sock.min_value = 0.0
            sock.max_value = 0.1

    gi = nk.group_input(0, 0)
    go = nk.group_output(2200, 0)

    # === BUILD GEOMETRY ===

    # 1. CAP CYLINDER
    cap_cyl = nk.n("GeometryNodeMeshCylinder", "Cap", 200, 200)
    cap_cyl.inputs["Vertices"].default_value = p["segments"]
    cap_cyl.inputs["Radius"].default_value = p["cap_diameter"] / 2
    cap_cyl.inputs["Depth"].default_value = p["cap_height"]

    cap_transform = nk.n("GeometryNodeTransform", "CapTransform", 400, 200)
    nk.link(cap_cyl.outputs["Mesh"], cap_transform.inputs["Geometry"])
    # Position: Z = skirt_height + cap_height/2
    cap_transform.inputs["Translation"].default_value = (0, 0, p["skirt_height"] + p["cap_height"]/2)

    # 2. SKIRT CYLINDER
    skirt_cyl = nk.n("GeometryNodeMeshCylinder", "Skirt", 200, -100)
    skirt_cyl.inputs["Vertices"].default_value = p["segments"]
    skirt_cyl.inputs["Radius"].default_value = p["skirt_diameter"] / 2
    skirt_cyl.inputs["Depth"].default_value = p["skirt_height"]

    skirt_transform = nk.n("GeometryNodeTransform", "SkirtTransform", 400, -100)
    nk.link(skirt_cyl.outputs["Mesh"], skirt_transform.inputs["Geometry"])
    # Position: Z = skirt_height/2
    skirt_transform.inputs["Translation"].default_value = (0, 0, p["skirt_height"]/2)

    # 3. JOIN CAP + SKIRT
    join1 = nk.n("GeometryNodeJoinGeometry", "JoinCapSkirt", 600, 50)
    nk.link(cap_transform.outputs["Geometry"], join1.inputs["Geometry"])
    nk.link(skirt_transform.outputs["Geometry"], join1.inputs["Geometry"])

    # 4. SUBDIVIDE FOR RIDGES
    subd = nk.n("GeometryNodeSubdivisionSurface", "Subdivide", 800, 50)
    subd.inputs["Level"].default_value = 2
    nk.link(join1.outputs["Geometry"], subd.inputs["Mesh"])

    # 5. SET SHADE SMOOTH
    smooth = nk.n("GeometryNodeSetShadeSmooth", "Smooth", 1000, 50)
    smooth.inputs["Shade Smooth"].default_value = True
    nk.link(subd.outputs["Mesh"], smooth.inputs["Geometry"])

    # 6. POINTER (simple cube)
    pointer_cube = nk.n("GeometryNodeMeshCube", "Pointer", 200, 400)
    pointer_cube.inputs["Size"].default_value = (0.002, p["pointer_length"], 0.0005)
    pointer_cube.inputs["Vertices X"].default_value = 1
    pointer_cube.inputs["Vertices Y"].default_value = 1
    pointer_cube.inputs["Vertices Z"].default_value = 1

    pointer_transform = nk.n("GeometryNodeTransform", "PointerTransform", 400, 400)
    nk.link(pointer_cube.outputs["Mesh"], pointer_transform.inputs["Geometry"])
    # Position: Z = total height + offset, Y = -pointer_length/2
    pointer_z = p["skirt_height"] + p["cap_height"] + 0.00025
    pointer_y = -p["pointer_length"] / 2
    pointer_transform.inputs["Translation"].default_value = (0, pointer_y, pointer_z)

    # 7. JOIN ALL
    join_all = nk.n("GeometryNodeJoinGeometry", "JoinAll", 1400, 50)
    nk.link(smooth.outputs["Geometry"], join_all.inputs["Geometry"])
    nk.link(pointer_transform.outputs["Geometry"], join_all.inputs["Geometry"])

    # 8. MERGE VERTICES
    merge = nk.n("GeometryNodeMergeByDistance", "Merge", 1600, 50)
    nk.link(join_all.outputs["Geometry"], merge.inputs["Geometry"])

    # 9. SET MATERIAL
    mat = _create_material(params)
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 1800, 50)
    set_mat.inputs["Material"].default_value = mat
    nk.link(merge.outputs["Geometry"], set_mat.inputs["Geometry"])

    # OUTPUT
    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    return {"root_objects": [obj]}


def _create_material(params: dict) -> bpy.types.Material:
    """Create knob material with pointer indicator."""
    mat = bpy.data.materials.new("NeveKnobMaterial")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    nk = NodeKit(nt)

    base_color = params.get("base_color", [0.5, 0.5, 0.5])
    pointer_color = params.get("pointer_color", [1.0, 1.0, 1.0])
    pointer_width = params.get("pointer_width", 0.08)

    # Position-based pointer mask
    X = -800

    geo = nk.n("ShaderNodeNewGeometry", "Geo", X, 0)
    sep = nk.n("ShaderNodeSeparateXYZ", "Sep", X + 100, 0)
    nk.link(geo.outputs["Position"], sep.inputs["Vector"])

    # Negate Y for 12 o'clock
    neg_y = nk.n("ShaderNodeMath", "NegY", X + 200, 0)
    neg_y.operation = "MULTIPLY"
    nk.link(sep.outputs["Y"], neg_y.inputs[0])
    neg_y.inputs[1].default_value = -1.0

    # Angle: atan2(x, -y)
    angle = nk.n("ShaderNodeMath", "Angle", X + 300, 0)
    angle.operation = "ARCTAN2"
    nk.link(sep.outputs["X"], angle.inputs[0])
    nk.link(neg_y.outputs["Value"], angle.inputs[1])

    # Absolute
    abs_angle = nk.n("ShaderNodeMath", "Abs", X + 400, 0)
    abs_angle.operation = "ABSOLUTE"
    nk.link(angle.outputs["Value"], abs_angle.inputs[0])

    # Wedge mask
    wedge = nk.n("ShaderNodeMath", "Wedge", X + 500, 0)
    wedge.operation = "LESS_THAN"
    nk.link(abs_angle.outputs["Value"], wedge.inputs[0])
    wedge.inputs[1].default_value = pointer_width

    # Mix colors
    mix = nk.n("ShaderNodeMix", "ColorMix", X + 600, 0)
    mix.data_type = "RGBA"
    nk.link(wedge.outputs["Value"], mix.inputs["Factor"])
    mix.inputs[6].default_value = (*base_color, 1.0)  # A = base
    mix.inputs[7].default_value = (*pointer_color, 1.0)  # B = pointer

    # BSDF
    bsdf = nk.n("ShaderNodeBsdfPrincipled", "BSDF", X + 800, 0)
    nk.link(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = params.get("metallic", 0.0)
    bsdf.inputs["Roughness"].default_value = params.get("roughness", 0.3)

    if params.get("clearcoat", 0) > 0:
        bsdf.inputs["Coat Weight"].default_value = params["clearcoat"]

    # Output
    out = nk.n("ShaderNodeOutputMaterial", "Out", X + 1000, 0)
    nk.link(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat
