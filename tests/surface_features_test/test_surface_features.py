"""
Surface Features Test Script

Generates test renders for all surface feature types:
- Knurling (straight, diamond, helical)
- Ribbing
- Grooves (single, multi, spiral)
- Indicators (line, dot, pointer)
- Collet and cap

Run with: blender --background --python test_surface_features.py
"""

import bpy
import sys
import math
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit
from lib.control_system.surface_features import (
    KnurlingConfig, RibbingConfig, GrooveConfig,
    IndicatorConfig, ColletConfig, CapConfig,
    KnurlPattern, IndicatorType, GroovePattern
)
from lib.control_system.surface_geo import (
    build_knurling, build_ribbing, build_grooves,
    build_indicator, build_collet, build_cap
)


def clear_scene():
    """Clear all objects from scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Remove all materials
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)

    # Remove all node groups
    for ng in bpy.data.node_groups:
        bpy.data.node_groups.remove(ng)


def setup_scene():
    """Setup render scene with lighting."""
    scene = bpy.context.scene

    # Render settings
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = True

    # World background
    world = bpy.data.worlds.get("World")
    if world:
        world.use_nodes = True
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs[0].default_value = (0.1, 0.1, 0.12, 1.0)  # Dark gray

    # Camera
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    cam_obj.location = (0.15, -0.25, 0.2)
    cam_obj.rotation_euler = (math.radians(60), 0, math.radians(30))

    # Key light
    key = bpy.data.objects.new("KeyLight", bpy.data.lights.new("KeyLight", 'AREA'))
    key.location = (0.3, -0.3, 0.4)
    key.data.energy = 500
    key.data.size = 0.2
    key.data.color = (1.0, 0.98, 0.95)
    bpy.context.collection.objects.link(key)

    # Fill light
    fill = bpy.data.objects.new("FillLight", bpy.data.lights.new("FillLight", 'AREA'))
    fill.location = (-0.2, -0.2, 0.3)
    fill.data.energy = 200
    fill.data.size = 0.15
    fill.data.color = (0.95, 0.95, 1.0)
    bpy.context.collection.objects.link(fill)

    # Rim light
    rim = bpy.data.objects.new("RimLight", bpy.data.lights.new("RimLight", 'AREA'))
    rim.location = (0, 0.2, 0.15)
    rim.data.energy = 300
    rim.data.size = 0.1
    rim.data.color = (1.0, 1.0, 1.0)
    bpy.context.collection.objects.link(rim)


def create_base_knob(name: str, x_pos: float = 0.0, y_pos: float = 0.0):
    """
    Create base knob geometry (cylinder) with Geometry Nodes.

    Returns the object and the node tree for adding features.
    """
    # Create mesh
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Position
    obj.location = (x_pos, y_pos, 0)

    # Geometry Nodes modifier
    mod = obj.modifiers.new("KnobGeometry", "NODES")
    tree = bpy.data.node_groups.new(f"{name}Tree", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    gi = nk.group_input(0, 0)
    go = nk.group_output(1800, 0)

    return obj, nk, gi, go


def build_base_geometry(nk: NodeKit, total_height: float, diameter: float, x: float = 200, y: float = 0):
    """Build base cylinder geometry."""
    # Create cylinder
    cyl = nk.n("GeometryNodeMeshCylinder", "BaseCylinder", x, y)
    cyl.inputs["Vertices"].default_value = 64
    cyl.inputs["Radius"].default_value = diameter / 2
    cyl.inputs["Depth"].default_value = total_height

    # Position (standing up)
    transform = nk.n("GeometryNodeTransform", "BaseTransform", x + 200, y)
    nk.link(cyl.outputs["Mesh"], transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (0, 0, total_height / 2)

    return transform.outputs["Geometry"], total_height


def create_test_material(base_color=(0.4, 0.4, 0.45), metallic=0.0, roughness=0.3):
    """Create a simple test material."""
    mat = bpy.data.materials.new("TestMaterial")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness

    output = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    return mat


def test_knurling_patterns():
    """Test knurling patterns: straight, diamond, helical."""
    clear_scene()
    setup_scene()

    # Output path
    output_dir = Path(__file__).parent / "build"
    output_dir.mkdir(parents=True, exist_ok=True)

    patterns = [
        ("Straight", KnurlPattern.STRAIGHT, -0.08, 0),
        ("Diamond", KnurlPattern.DIAMOND, 0, 0),
        ("Helical", KnurlPattern.HELICAL, 0.08, 0),
    ]

    for name, pattern, x_pos, y_pos in patterns:
        obj, nk, gi, go = create_base_knob(f"Knurl_{name}", x_pos, y_pos)

        # Build base
        geo, total_height = build_base_geometry(nk, 0.028, 0.020)

        # Apply knurling
        config = KnurlingConfig(
            enabled=True,
            pattern=pattern,
            count=30,
            depth=0.0008,
            z_start=0.0,
            z_end=1.0,
            fade=0.1,
            profile=0.5,
            cross_angle=0.5 if pattern == KnurlPattern.DIAMOND else 0.0,
            helix_pitch=0.01 if pattern == KnurlPattern.HELICAL else 0.0,
        )

        geo = build_knurling(nk, geo, config, total_height, 0.020, 600, 0)

        # Set material
        mat = create_test_material(base_color=(0.3, 0.3, 0.35), metallic=0.8, roughness=0.25)
        set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 1600, 0)
        set_mat.inputs["Material"].default_value = mat
        nk.link(geo, set_mat.inputs["Geometry"])

        nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    # Render
    output_path = str(output_dir / "test_knurling_patterns.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {output_path}")

    return output_path


def test_ribbing():
    """Test horizontal ribbing."""
    clear_scene()
    setup_scene()

    output_dir = Path(__file__).parent / "build"
    output_dir.mkdir(parents=True, exist_ok=True)

    obj, nk, gi, go = create_base_knob("RibTest", 0, 0)

    # Build base
    geo, total_height = build_base_geometry(nk, 0.028, 0.020)

    # Apply ribbing
    config = RibbingConfig(
        enabled=True,
        count=6,
        depth=0.0006,
        width=0.001,
        spacing=0.003,
        z_start=0.1,
        z_end=0.9,
        profile=0.5,
    )

    geo = build_ribbing(nk, geo, config, total_height, 0.020, 600, 0)

    # Set material
    mat = create_test_material(base_color=(0.25, 0.25, 0.28), metallic=0.0, roughness=0.35)
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 1600, 0)
    set_mat.inputs["Material"].default_value = mat
    nk.link(geo, set_mat.inputs["Geometry"])

    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    # Render
    output_path = str(output_dir / "test_ribbing.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {output_path}")

    return output_path


def test_grooves():
    """Test groove patterns: single, multi."""
    clear_scene()
    setup_scene()

    output_dir = Path(__file__).parent / "build"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Single groove
    obj1, nk1, gi1, go1 = create_base_knob("GrooveSingle", -0.05, 0)
    geo1, total_height1 = build_base_geometry(nk1, 0.028, 0.020)

    config1 = GrooveConfig(
        enabled=True,
        pattern=GroovePattern.SINGLE,
        depth=0.001,
        width=0.002,
        z_position=0.4,
    )
    geo1 = build_grooves(nk1, geo1, config1, total_height1, 0.020, 600, 0)

    mat1 = create_test_material(base_color=(0.5, 0.5, 0.52), metallic=0.0, roughness=0.3)
    set_mat1 = nk1.n("GeometryNodeSetMaterial", "SetMaterial", 1600, 0)
    set_mat1.inputs["Material"].default_value = mat1
    nk1.link(geo1, set_mat1.inputs["Geometry"])
    nk1.link(set_mat1.outputs["Geometry"], go1.inputs["Geometry"])

    # Multi groove
    obj2, nk2, gi2, go2 = create_base_knob("GrooveMulti", 0.05, 0)
    geo2, total_height2 = build_base_geometry(nk2, 0.028, 0.020)

    config2 = GrooveConfig(
        enabled=True,
        pattern=GroovePattern.MULTI,
        depth=0.0006,
        width=0.001,
        count=3,
        spacing=0.004,
        z_position=0.5,
    )
    geo2 = build_grooves(nk2, geo2, config2, total_height2, 0.020, 600, 0)

    mat2 = create_test_material(base_color=(0.45, 0.45, 0.48), metallic=0.0, roughness=0.3)
    set_mat2 = nk2.n("GeometryNodeSetMaterial", "SetMaterial", 1600, 0)
    set_mat2.inputs["Material"].default_value = mat2
    nk2.link(geo2, set_mat2.inputs["Geometry"])
    nk2.link(set_mat2.outputs["Geometry"], go2.inputs["Geometry"])

    # Render
    output_path = str(output_dir / "test_grooves.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {output_path}")

    return output_path


def test_indicators():
    """Test indicator types: line, dot, pointer."""
    clear_scene()
    setup_scene()

    output_dir = Path(__file__).parent / "build"
    output_dir.mkdir(parents=True, exist_ok=True)

    types = [
        ("Line", IndicatorType.LINE, -0.08, 0),
        ("Dot", IndicatorType.DOT, 0, 0),
        ("Pointer", IndicatorType.POINTER, 0.08, 0),
    ]

    for name, ind_type, x_pos, y_pos in types:
        obj, nk, gi, go = create_base_knob(f"Indicator_{name}", x_pos, y_pos)

        # Build base
        geo, total_height = build_base_geometry(nk, 0.028, 0.020)

        # Create indicator
        config = IndicatorConfig(
            enabled=True,
            indicator_type=ind_type,
            length=0.012,
            width=0.08,
            height=0.0005,
            dot_diameter=0.004,
        )

        ind_geo = build_indicator(nk, 0.020, 0.008, 0.020, config, 400, 300)
        if ind_geo:
            # Join base and indicator
            join = nk.n("GeometryNodeJoinGeometry", "JoinIndicator", 1400, 0)
            nk.link(geo, join.inputs["Geometry"])
            nk.link(ind_geo, join.inputs["Geometry"])
            geo = join.outputs["Geometry"]

        # Set material
        mat = create_test_material(base_color=(0.2, 0.35, 0.7), metallic=0.0, roughness=0.25)
        set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 1600, 0)
        set_mat.inputs["Material"].default_value = mat
        nk.link(geo, set_mat.inputs["Geometry"])

        nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    # Render
    output_path = str(output_dir / "test_indicators.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {output_path}")

    return output_path


def test_collet_cap():
    """Test collet and cap features."""
    clear_scene()
    setup_scene()

    output_dir = Path(__file__).parent / "build"
    output_dir.mkdir(parents=True, exist_ok=True)

    obj, nk, gi, go = create_base_knob("ColletCap", 0, 0)

    # Build base
    geo, total_height = build_base_geometry(nk, 0.028, 0.020)

    # Create collet
    collet_config = ColletConfig(
        enabled=True,
        height=0.010,
        diameter=0.024,
        thickness=0.002,
        z_position=0.0,
        gap=0.001,
        metallic=0.9,
        color=(0.7, 0.7, 0.72),
    )
    collet_geo = build_collet(nk, collet_config, 400, -200)

    # Create cap
    cap_config = CapConfig(
        enabled=True,
        diameter=0.012,
        height=0.004,
        inset=0.001,
        domed=False,
        color=(0.15, 0.15, 0.15),
    )
    cap_geo = build_cap(nk, 0.008, 0.020, 0.020, cap_config, 400, -400)

    # Join all parts
    join = nk.n("GeometryNodeJoinGeometry", "JoinAll", 1200, 0)
    nk.link(geo, join.inputs["Geometry"])
    if collet_geo:
        nk.link(collet_geo, join.inputs["Geometry"])
    if cap_geo:
        nk.link(cap_geo, join.inputs["Geometry"])

    geo = join.outputs["Geometry"]

    # Set material
    mat = create_test_material(base_color=(0.3, 0.3, 0.32), metallic=0.0, roughness=0.3)
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 1600, 0)
    set_mat.inputs["Material"].default_value = mat
    nk.link(geo, set_mat.inputs["Geometry"])

    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    # Render
    output_path = str(output_dir / "test_collet_cap.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {output_path}")

    return output_path


def test_combined():
    """Test combined features (Neve 88RS style)."""
    clear_scene()
    setup_scene()

    output_dir = Path(__file__).parent / "build"
    output_dir.mkdir(parents=True, exist_ok=True)

    obj, nk, gi, go = create_base_knob("Combined", 0, 0)

    # Build base
    geo, total_height = build_base_geometry(nk, 0.028, 0.020)

    # Add subtle knurling
    knurl_config = KnurlingConfig(
        enabled=True,
        pattern=KnurlPattern.STRAIGHT,
        count=20,
        depth=0.0003,
        z_start=0.0,
        z_end=0.6,
        fade=0.1,
        profile=0.5,
    )
    geo = build_knurling(nk, geo, knurl_config, total_height, 0.020, 600, 0)

    # Add collet
    collet_config = ColletConfig(
        enabled=True,
        height=0.010,
        diameter=0.024,
        thickness=0.002,
        z_position=0.0,
        gap=0.001,
        metallic=0.9,
        color=(0.7, 0.7, 0.72),
    )
    collet_geo = build_collet(nk, collet_config, 400, -200)

    # Add cap
    cap_config = CapConfig(
        enabled=True,
        diameter=0.014,
        height=0.003,
        inset=0.001,
        domed=False,
        color=(0.15, 0.15, 0.15),
    )
    cap_geo = build_cap(nk, 0.008, 0.020, 0.020, cap_config, 400, -400)

    # Add indicator
    ind_config = IndicatorConfig(
        enabled=True,
        indicator_type=IndicatorType.LINE,
        length=0.012,
        width=0.08,
        height=0.0005,
    )
    ind_geo = build_indicator(nk, 0.020, 0.008, 0.020, ind_config, 400, 300)

    # Join all
    join = nk.n("GeometryNodeJoinGeometry", "JoinAll", 1200, 0)
    nk.link(geo, join.inputs["Geometry"])
    if collet_geo:
        nk.link(collet_geo, join.inputs["Geometry"])
    if cap_geo:
        nk.link(cap_geo, join.inputs["Geometry"])
    if ind_geo:
        nk.link(ind_geo, join.inputs["Geometry"])

    geo = join.outputs["Geometry"]

    # Set material
    mat = create_test_material(base_color=(0.6, 0.6, 0.62), metallic=0.0, roughness=0.3)
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 1600, 0)
    set_mat.inputs["Material"].default_value = mat
    nk.link(geo, set_mat.inputs["Geometry"])

    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    # Render
    output_path = str(output_dir / "test_combined_neve88rs.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {output_path}")

    return output_path


def main():
    """Run all tests."""
    print("=" * 60)
    print("Surface Features Test Suite")
    print("=" * 60)

    results = []

    print("\n[1/6] Testing knurling patterns...")
    try:
        path = test_knurling_patterns()
        results.append(("Knurling Patterns", "OK", path))
    except Exception as e:
        results.append(("Knurling Patterns", f"FAILED: {e}", None))
        import traceback
        traceback.print_exc()

    print("\n[2/6] Testing ribbing...")
    try:
        path = test_ribbing()
        results.append(("Ribbing", "OK", path))
    except Exception as e:
        results.append(("Ribbing", f"FAILED: {e}", None))
        import traceback
        traceback.print_exc()

    print("\n[3/6] Testing grooves...")
    try:
        path = test_grooves()
        results.append(("Grooves", "OK", path))
    except Exception as e:
        results.append(("Grooves", f"FAILED: {e}", None))
        import traceback
        traceback.print_exc()

    print("\n[4/6] Testing indicators...")
    try:
        path = test_indicators()
        results.append(("Indicators", "OK", path))
    except Exception as e:
        results.append(("Indicators", f"FAILED: {e}", None))
        import traceback
        traceback.print_exc()

    print("\n[5/6] Testing collet and cap...")
    try:
        path = test_collet_cap()
        results.append(("Collet & Cap", "OK", path))
    except Exception as e:
        results.append(("Collet & Cap", f"FAILED: {e}", None))
        import traceback
        traceback.print_exc()

    print("\n[6/6] Testing combined features...")
    try:
        path = test_combined()
        results.append(("Combined (Neve 88RS)", "OK", path))
    except Exception as e:
        results.append(("Combined (Neve 88RS)", f"FAILED: {e}", None))
        import traceback
        traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, status, _ in results if status == "OK")
    total = len(results)

    for name, status, path in results:
        print(f"  {name}: {status}")
        if path:
            print(f"    -> {path}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
