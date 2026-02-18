"""
Test Fader Geometry Generation

Creates test renders for all fader types and presets.
"""

from __future__ import annotations
import bpy
import sys
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit
from lib.control_system.faders import (
    FaderConfig, FaderKnobConfig, TrackConfig, ScaleConfig, LEDMeterConfig,
    FaderType, FaderKnobStyle, TrackStyle, ScalePosition,
    FADER_PRESETS, get_fader_preset
)
from lib.control_system.fader_geo import build_fader


def clear_scene():
    """Clear scene for clean test."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Clear node trees
    for nt in bpy.data.node_groups:
        bpy.data.node_groups.remove(nt)

    # Clear materials
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)


def setup_render_scene():
    """Setup basic render scene."""
    # Camera
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    bpy.context.collection.objects.link(cam)
    cam.location = (0.15, -0.15, 0.12)
    cam.rotation_euler = (math.radians(60), 0, math.radians(30))
    bpy.context.scene.camera = cam

    # Key light
    key = bpy.data.objects.new("KeyLight", bpy.data.lights.new("KeyLight", 'AREA'))
    bpy.context.collection.objects.link(key)
    key.location = (0.2, -0.2, 0.3)
    key.data.energy = 500
    key.data.size = 0.2

    # Fill light
    fill = bpy.data.objects.new("FillLight", bpy.data.lights.new("FillLight", 'AREA'))
    bpy.context.collection.objects.link(fill)
    fill.location = (-0.15, -0.15, 0.2)
    fill.data.energy = 200
    fill.data.size = 0.15

    # Render settings
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.render.film_transparent = True


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


def create_fader_object(config: FaderConfig, name: str, x_pos: float = 0.0, y_pos: float = 0.0):
    """
    Create fader object with Geometry Nodes.

    Returns the object.
    """
    # Create mesh
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Position
    obj.location = (x_pos, y_pos, 0)

    # Geometry Nodes modifier
    mod = obj.modifiers.new("FaderGeometry", "NODES")
    tree = bpy.data.node_groups.new(f"{name}Tree", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    gi = nk.group_input(0, 0)
    go = nk.group_output(1200, 0)

    # Build fader geometry
    fader_geo = build_fader(nk, config, 200, 0)

    # Set material
    mat = create_test_material(
        base_color=config.knob.color,
        metallic=config.knob.metallic,
        roughness=config.knob.roughness
    )
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 1000, 0)
    set_mat.inputs["Material"].default_value = mat

    if fader_geo:
        nk.link(fader_geo, set_mat.inputs["Geometry"])

    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    return obj


def test_basic_channel_fader():
    """Test 1: Basic channel fader with all components."""
    print("\n=== Test 1: Basic Channel Fader ===")

    config = FaderConfig(
        name="BasicChannel",
        fader_type=FaderType.CHANNEL,
        travel_length=0.100,
        position=0.7,
        knob=FaderKnobConfig(
            style=FaderKnobStyle.ROUNDED,
            width=0.025,
            depth=0.012,
            height=0.020,
            color=(0.2, 0.2, 0.22),
            metallic=0.8,
            roughness=0.3
        ),
        track=TrackConfig(
            style=TrackStyle.COVERED_SLOT,
            width=0.015,
            depth=0.008,
            end_caps_enabled=True
        ),
        scale=ScaleConfig(
            enabled=True,
            position=ScalePosition.LEFT,
            tick_spacing=0.010,
            major_tick_height=0.008
        ),
        led_meter=LEDMeterConfig(
            enabled=True,
            position="beside_track",
            segment_count=10,
            segment_height=0.008,
            segment_width=0.004
        )
    )

    clear_scene()
    setup_render_scene()

    obj = create_fader_object(config, "BasicChannel", 0, 0)

    # Update depsgraph
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    # Render
    output_dir = ROOT / "projects/fader_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test1_channel_fader.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_ssl_preset():
    """Test 2: SSL 4000 channel fader preset."""
    print("\n=== Test 2: SSL 4000 Preset ===")

    config = get_fader_preset("ssl_4000_channel")

    clear_scene()
    setup_render_scene()

    obj = create_fader_object(config, "SSL4000", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/fader_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test2_ssl_preset.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_neve_preset():
    """Test 3: Neve 88RS channel fader preset."""
    print("\n=== Test 3: Neve 88RS Preset ===")

    config = get_fader_preset("neve_88rs_channel")

    clear_scene()
    setup_render_scene()

    obj = create_fader_object(config, "Neve88RS", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/fader_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test3_neve_preset.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_short_fader():
    """Test 4: Short fader preset."""
    print("\n=== Test 4: Short Fader ===")

    config = get_fader_preset("short_compact")

    clear_scene()
    setup_render_scene()

    obj = create_fader_object(config, "ShortFader", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/fader_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test4_short_fader.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_mini_fader():
    """Test 5: Mini fader preset."""
    print("\n=== Test 5: Mini Fader ===")

    config = get_fader_preset("mini_pocket")

    clear_scene()
    setup_render_scene()

    obj = create_fader_object(config, "MiniFader", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/fader_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test5_mini_fader.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_knob_styles():
    """Test 6: All knob styles in one render."""
    print("\n=== Test 6: All Knob Styles ===")

    styles = [
        FaderKnobStyle.SQUARE,
        FaderKnobStyle.ROUNDED,
        FaderKnobStyle.ANGLED,
        FaderKnobStyle.TAPERED
    ]

    clear_scene()
    setup_render_scene()

    output_dir = ROOT / "projects/fader_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create 4 faders in a row
    for i, style in enumerate(styles):
        config = FaderConfig(
            name=f"KnobStyle_{style.name}",
            travel_length=0.080,
            position=0.6,
            knob=FaderKnobConfig(
                style=style,
                width=0.020,
                depth=0.010,
                height=0.015,
                color=(0.15, 0.15, 0.17),
                metallic=0.9,
                roughness=0.2
            ),
            track=TrackConfig(style=TrackStyle.EXPOSED),
            scale=ScaleConfig(enabled=False),
            led_meter=LEDMeterConfig(enabled=False)
        )

        create_fader_object(config, f"Fader_{style.name}", i * 0.035, 0)

    bpy.context.view_layer.update()

    # Adjust camera to see all
    cam = bpy.data.objects["Camera"]
    cam.location = (0.05, -0.15, 0.10)

    output_path = str(output_dir / "test6_knob_styles.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return True


def run_all_tests():
    """Run all fader tests."""
    print("=" * 60)
    print("Fader Geometry Tests")
    print("=" * 60)

    tests = [
        ("Basic Channel Fader", test_basic_channel_fader),
        ("SSL 4000 Preset", test_ssl_preset),
        ("Neve 88RS Preset", test_neve_preset),
        ("Short Fader", test_short_fader),
        ("Mini Fader", test_mini_fader),
        ("Knob Styles", test_knob_styles),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "OK" if success else "FAILED", None))
            print(f"  [PASS] {name}")
        except Exception as e:
            results.append((name, "FAILED", str(e)))
            print(f"  [FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, s, _ in results if s == "OK")
    total = len(results)
    print(f"Passed: {passed}/{total}")

    for name, status, error in results:
        symbol = "✓" if status == "OK" else "✗"
        print(f"  {symbol} {name}")
        if error:
            print(f"    Error: {error}")

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
