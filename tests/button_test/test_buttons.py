"""
Test Button Geometry Generation

Creates test renders for all button types and presets with clear visualization.
Uses Workbench renderer with matcap and outlines for clear shape visibility.
"""

from __future__ import annotations
import bpy
import sys
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit
from lib.control_system.buttons import (
    ButtonConfig, ButtonCapConfig, IlluminationConfig,
    ButtonType, ButtonShape, ButtonSurface,
    BUTTON_PRESETS, get_button_preset, list_button_presets
)
from lib.control_system.button_geo import build_button


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
    """Setup render scene with Workbench for clear shape visualization."""
    # Camera
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    bpy.context.collection.objects.link(cam)
    cam.location = (0.08, -0.08, 0.10)
    cam.rotation_euler = (math.radians(60), 0, math.radians(30))
    bpy.context.scene.camera = cam

    # Key light
    key = bpy.data.objects.new("KeyLight", bpy.data.lights.new("KeyLight", 'AREA'))
    bpy.context.collection.objects.link(key)
    key.location = (0.1, -0.1, 0.15)
    key.data.energy = 800
    key.data.size = 0.1

    # Fill light
    fill = bpy.data.objects.new("FillLight", bpy.data.lights.new("FillLight", 'AREA'))
    bpy.context.collection.objects.link(fill)
    fill.location = (-0.08, -0.08, 0.1)
    fill.data.energy = 400
    fill.data.size = 0.08

    # Render settings - Workbench for cleaner visualization
    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080

    # Workbench settings for better shape visualization
    shading = bpy.context.scene.display.shading
    shading.light = 'MATCAP'
    shading.show_object_outline = True
    shading.object_outline_color = (0.0, 0.0, 0.0)
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = 'BOTH'


def create_toon_material(base_color=(0.4, 0.4, 0.45)):
    """Create a toon/cel shader material for clear visualization."""
    mat = bpy.data.materials.new("ToonMaterial")
    nt = mat.node_tree
    nt.nodes.clear()

    # Create toon BSDF for cel-shaded look
    toon = nt.nodes.new("ShaderNodeBsdfToon")
    toon.inputs["Color"].default_value = (*base_color, 1.0)
    toon.inputs["Size"].default_value = 0.5
    toon.inputs["Smooth"].default_value = 0.05

    # Output
    output = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(toon.outputs["BSDF"], output.inputs["Surface"])

    # Position nodes
    toon.location = (-200, 0)
    output.location = (100, 0)

    return mat


def create_button_object(config: ButtonConfig, name: str, x_pos: float = 0.0, y_pos: float = 0.0):
    """Create button object with Geometry Nodes."""
    # Create mesh
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Position
    obj.location = (x_pos, y_pos, 0)

    # Geometry Nodes modifier
    mod = obj.modifiers.new("ButtonGeometry", "NODES")
    tree = bpy.data.node_groups.new(f"{name}Tree", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    gi = nk.group_input(0, 0)
    go = nk.group_output(800, 0)

    # Build button geometry
    button_geo = build_button(nk, config, 100, 0)

    # Set material
    mat = create_toon_material(base_color=config.color)
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 600, 0)
    set_mat.inputs["Material"].default_value = mat

    if button_geo:
        nk.link(button_geo, set_mat.inputs["Geometry"])

    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    return obj


def test_basic_button():
    """Test 1: Basic momentary button."""
    print("\n=== Test 1: Basic Button ===")

    config = ButtonConfig(
        name="BasicButton",
        button_type=ButtonType.MOMENTARY,
        shape=ButtonShape.SQUARE,
        width=0.012,
        depth_unpressed=0.005,
        color=(0.3, 0.3, 0.35),
    )

    clear_scene()
    setup_render_scene()

    obj = create_button_object(config, "BasicButton", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/button_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test1_basic_button.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_neve_cap_buttons():
    """Test 2: Neve 1073 style buttons with colored caps."""
    print("\n=== Test 2: Neve Cap Buttons ===")

    presets = ["neve_1073_momentary", "neve_1073_cap_blue", "neve_1073_cap_green"]

    clear_scene()
    setup_render_scene()

    for i, preset_name in enumerate(presets):
        config = get_button_preset(preset_name)
        create_button_object(config, f"Neve_{i}", i * 0.018, 0)

    bpy.context.view_layer.update()

    # Adjust camera
    cam = bpy.data.objects["Camera"]
    cam.location = (0.018, -0.08, 0.10)

    output_dir = ROOT / "projects/button_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test2_neve_caps.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return True


def test_ssl_button():
    """Test 3: SSL 4000 style square button with LED."""
    print("\n=== Test 3: SSL Button ===")

    config = get_button_preset("ssl_4000_square")

    clear_scene()
    setup_render_scene()

    obj = create_button_object(config, "SSL_Button", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/button_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test3_ssl_button.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_synth_buttons():
    """Test 4: Synth style buttons (Roland, Moog, Sequential)."""
    print("\n=== Test 4: Synth Buttons ===")

    presets = ["roland_808_rubber", "moog_premium", "sequential_prophet"]

    clear_scene()
    setup_render_scene()

    for i, preset_name in enumerate(presets):
        config = get_button_preset(preset_name)
        create_button_object(config, f"Synth_{i}", i * 0.018, 0)

    bpy.context.view_layer.update()

    cam = bpy.data.objects["Camera"]
    cam.location = (0.018, -0.08, 0.10)

    output_dir = ROOT / "projects/button_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test4_synth_buttons.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return True


def test_footswitches():
    """Test 5: Guitar pedal footswitches."""
    print("\n=== Test 5: Footswitches ===")

    presets = ["boss_footswitch", "mxr_button", "ehx_footswitch"]

    clear_scene()
    setup_render_scene()

    for i, preset_name in enumerate(presets):
        config = get_button_preset(preset_name)
        create_button_object(config, f"Footswitch_{i}", i * 0.035, 0)

    bpy.context.view_layer.update()

    cam = bpy.data.objects["Camera"]
    cam.location = (0.035, -0.10, 0.12)

    output_dir = ROOT / "projects/button_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test5_footswitches.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return True


def test_modern_led():
    """Test 6: Modern LED ring button."""
    print("\n=== Test 6: Modern LED Button ===")

    config = get_button_preset("modern_led_ring")

    clear_scene()
    setup_render_scene()

    obj = create_button_object(config, "Modern_LED", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/button_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test6_modern_led.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_transport_buttons():
    """Test 7: Transport buttons (Play, Record)."""
    print("\n=== Test 7: Transport Buttons ===")

    presets = ["transport_play", "transport_record"]

    clear_scene()
    setup_render_scene()

    for i, preset_name in enumerate(presets):
        config = get_button_preset(preset_name)
        create_button_object(config, f"Transport_{i}", i * 0.025, 0)

    bpy.context.view_layer.update()

    cam = bpy.data.objects["Camera"]
    cam.location = (0.012, -0.08, 0.10)

    output_dir = ROOT / "projects/button_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test7_transport.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return True


def test_button_shapes():
    """Test 8: All button shapes."""
    print("\n=== Test 8: Button Shapes ===")

    shapes = [
        (ButtonShape.SQUARE, "Square"),
        (ButtonShape.ROUND, "Round"),
        (ButtonShape.RECTANGULAR, "Rect"),
    ]

    colors = [
        (0.7, 0.3, 0.3),
        (0.3, 0.7, 0.3),
        (0.3, 0.3, 0.7),
    ]

    clear_scene()
    setup_render_scene()

    for i, (shape, name) in enumerate(shapes):
        config = ButtonConfig(
            name=f"Shape_{name}",
            button_type=ButtonType.MOMENTARY,
            shape=shape,
            width=0.012,
            length=0.020 if shape == ButtonShape.RECTANGULAR else 0.012,
            depth_unpressed=0.005,
            color=colors[i],
        )
        create_button_object(config, f"Shape_{name}", i * 0.025, 0)

    bpy.context.view_layer.update()

    cam = bpy.data.objects["Camera"]
    cam.location = (0.025, -0.08, 0.10)

    output_dir = ROOT / "projects/button_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test8_shapes.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return True


def run_all_tests():
    """Run all button tests."""
    print("=" * 60)
    print("Button Geometry Tests (Workbench Visualization)")
    print("=" * 60)

    tests = [
        ("Basic Button", test_basic_button),
        ("Neve Cap Buttons", test_neve_cap_buttons),
        ("SSL Button", test_ssl_button),
        ("Synth Buttons", test_synth_buttons),
        ("Footswitches", test_footswitches),
        ("Modern LED Button", test_modern_led),
        ("Transport Buttons", test_transport_buttons),
        ("Button Shapes", test_button_shapes),
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
