"""
LED/Indicator System Test Script

Tests all LED types with Workbench renderer for clear geometry visualization.
"""

from __future__ import annotations
import bpy
import sys
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit
from lib.control_system.leds import (
    LEDConfig,
    LEDBarConfig,
    VUMeterConfig,
    SevenSegmentConfig,
    BezelConfig,
    LEDShape,
    LEDLens,
    BezelStyle,
    BarDirection,
    get_led_preset,
)
from lib.control_system.led_geo import (
    build_single_led,
    build_led_bar,
    build_vu_meter,
    build_seven_segment,
)


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
    cam.location = (0.05, -0.08, 0.08)
    cam.rotation_euler = (math.radians(55), 0, math.radians(20))
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


def create_toon_material(base_color=(0.4, 0.4, 0.45), emission_color=None, emission_strength=0.0):
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

    # Add emission if LED is active
    if emission_color and emission_strength > 0:
        emission = nt.nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = (*emission_color, 1.0)
        emission.inputs["Strength"].default_value = emission_strength

        # Mix shader
        mix = nt.nodes.new("ShaderNodeMixShader")
        mix.inputs["Fac"].default_value = 0.3

        nt.links.new(toon.outputs["BSDF"], mix.inputs[1])
        nt.links.new(emission.outputs["Emission"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], output.inputs["Surface"])

        toon.location = (-400, 0)
        emission.location = (-400, -200)
        mix.location = (-200, 0)
        output.location = (100, 0)
    else:
        nt.links.new(toon.outputs["BSDF"], output.inputs["Surface"])

        toon.location = (-200, 0)
        output.location = (100, 0)

    return mat


def create_led_object(config: LEDConfig, name: str, x_pos: float = 0.0, y_pos: float = 0.0):
    """Create LED object with Geometry Nodes."""
    # Create mesh
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Position
    obj.location = (x_pos, y_pos, 0)

    # Geometry Nodes modifier
    mod = obj.modifiers.new("LEDGeometry", "NODES")
    tree = bpy.data.node_groups.new(f"{name}Tree", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    gi = nk.group_input(0, 0)
    go = nk.group_output(1600, 0)

    # Build LED geometry
    led_geo = build_single_led(nk, config, 100, 0)

    # Set material
    emission_color = config.color if config.active else None
    emission_strength = config.brightness * config.value if config.active else 0.0
    mat = create_toon_material(
        base_color=config.color if config.active else config.color_off,
        emission_color=emission_color,
        emission_strength=emission_strength
    )
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 1400, 0)
    set_mat.inputs["Material"].default_value = mat

    if led_geo:
        nk.link(led_geo, set_mat.inputs["Geometry"])

    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    return obj


def create_led_bar_object(config: LEDBarConfig, name: str, x_pos: float = 0.0, y_pos: float = 0.0):
    """Create LED bar object with Geometry Nodes."""
    # Create mesh
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Position
    obj.location = (x_pos, y_pos, 0)

    # Geometry Nodes modifier
    mod = obj.modifiers.new("LEDBarGeometry", "NODES")
    tree = bpy.data.node_groups.new(f"{name}Tree", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    gi = nk.group_input(0, 0)
    go = nk.group_output(1200, 0)

    # Build LED bar geometry
    bar_geo = build_led_bar(nk, config, 100, 0)

    # Set material (green segments, dark frame)
    mat = create_toon_material(base_color=(0.2, 0.8, 0.2))
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 1000, 0)
    set_mat.inputs["Material"].default_value = mat

    if bar_geo:
        nk.link(bar_geo, set_mat.inputs["Geometry"])

    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    return obj


def create_vu_meter_object(config: VUMeterConfig, name: str, x_pos: float = 0.0, y_pos: float = 0.0):
    """Create VU meter object with Geometry Nodes."""
    # Create mesh
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Position
    obj.location = (x_pos, y_pos, 0)

    # Geometry Nodes modifier
    mod = obj.modifiers.new("VUMeterGeometry", "NODES")
    tree = bpy.data.node_groups.new(f"{name}Tree", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    gi = nk.group_input(0, 0)
    go = nk.group_output(600, 0)

    # Build VU meter geometry
    vu_geo = build_vu_meter(nk, config, 100, 0)

    # Set material (dark housing, red needle)
    mat = create_toon_material(base_color=(0.2, 0.2, 0.22))
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 400, 0)
    set_mat.inputs["Material"].default_value = mat

    if vu_geo:
        nk.link(vu_geo, set_mat.inputs["Geometry"])

    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    return obj


def create_seven_segment_object(config: SevenSegmentConfig, name: str, x_pos: float = 0.0, y_pos: float = 0.0):
    """Create 7-segment display object with Geometry Nodes."""
    # Create mesh
    mesh = bpy.data.meshes.new(f"{name}Mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Position
    obj.location = (x_pos, y_pos, 0)

    # Geometry Nodes modifier
    mod = obj.modifiers.new("SevenSegmentGeometry", "NODES")
    tree = bpy.data.node_groups.new(f"{name}Tree", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    gi = nk.group_input(0, 0)
    go = nk.group_output(600, 0)

    # Build 7-segment geometry
    seg_geo = build_seven_segment(nk, config, 100, 0)

    # Set material (red segments, dark background)
    mat = create_toon_material(base_color=(0.8, 0.1, 0.1))
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 400, 0)
    set_mat.inputs["Material"].default_value = mat

    if seg_geo:
        nk.link(seg_geo, set_mat.inputs["Geometry"])

    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    return obj


def test_single_led_round():
    """Test 1: Round single LED with bezel."""
    print("\n=== Test 1: Round LED ===")

    config = LEDConfig(
        name="Round LED",
        shape=LEDShape.ROUND,
        diameter=0.005,
        height=0.003,
        color=(0.0, 1.0, 0.0),  # Green
        active=True,
        bezel=BezelConfig(
            style=BezelStyle.CHROME,
            diameter=0.008,
            height=0.002,
        ),
    )

    clear_scene()
    setup_render_scene()

    obj = create_led_object(config, "LED_Round", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/led_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test1_led_round.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_single_led_square():
    """Test 2: Square LED without bezel."""
    print("\n=== Test 2: Square LED ===")

    config = LEDConfig(
        name="Square LED",
        shape=LEDShape.SQUARE,
        diameter=0.004,
        height=0.002,
        color=(1.0, 0.0, 0.0),  # Red
        active=True,
        bezel=BezelConfig(style=BezelStyle.NONE),
    )

    clear_scene()
    setup_render_scene()

    obj = create_led_object(config, "LED_Square", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/led_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test2_led_square.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_single_led_diffused():
    """Test 3: LED with diffused lens."""
    print("\n=== Test 3: Diffused LED ===")

    config = LEDConfig(
        name="Diffused LED",
        shape=LEDShape.ROUND,
        diameter=0.006,
        height=0.004,
        color=(0.0, 0.5, 1.0),  # Blue
        lens=LEDLens.DIFFUSED,
        active=True,
        bezel=BezelConfig(
            style=BezelStyle.BLACK,
            diameter=0.009,
            height=0.002,
        ),
    )

    clear_scene()
    setup_render_scene()

    obj = create_led_object(config, "LED_Diffused", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/led_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test3_led_diffused.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_led_bar_vertical():
    """Test 4: Vertical LED bar."""
    print("\n=== Test 4: Vertical LED Bar ===")

    config = LEDBarConfig(
        name="VU Meter",
        segments=10,
        segment_width=0.004,
        segment_height=0.006,
        segment_depth=0.003,
        segment_spacing=0.001,
        direction=BarDirection.VERTICAL,
        frame_enabled=True,
    )

    clear_scene()
    setup_render_scene()

    obj = create_led_bar_object(config, "LED_Bar_Vertical", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/led_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test4_led_bar_vertical.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_led_bar_horizontal():
    """Test 5: Horizontal LED bar."""
    print("\n=== Test 5: Horizontal LED Bar ===")

    config = LEDBarConfig(
        name="Level Meter",
        segments=8,
        segment_width=0.005,
        segment_height=0.004,
        segment_depth=0.003,
        segment_spacing=0.001,
        direction=BarDirection.HORIZONTAL,
        frame_enabled=True,
    )

    clear_scene()
    setup_render_scene()

    obj = create_led_bar_object(config, "LED_Bar_Horizontal", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/led_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test5_led_bar_horizontal.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_vu_meter():
    """Test 6: VU meter with needle."""
    print("\n=== Test 6: VU Meter ===")

    config = VUMeterConfig(
        name="VU Meter",
        width=0.025,
        height=0.020,
        depth=0.008,
        needle_width=0.001,
        needle_length=0.015,
        value=0.6,  # 60% deflection
        frame_enabled=True,
    )

    clear_scene()
    setup_render_scene()

    obj = create_vu_meter_object(config, "VU_Meter", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/led_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test6_vu_meter.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_seven_segment():
    """Test 7: 7-segment display."""
    print("\n=== Test 7: 7-Segment Display ===")

    config = SevenSegmentConfig(
        name="7-Segment",
        digits=3,
        segment_width=0.004,
        segment_height=0.008,
        digit_spacing=0.002,
    )

    clear_scene()
    setup_render_scene()

    obj = create_seven_segment_object(config, "Seven_Segment", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/led_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test7_seven_segment.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def test_led_preset():
    """Test 8: LED from preset."""
    print("\n=== Test 8: LED Preset ===")

    config = get_led_preset("console_power")

    clear_scene()
    setup_render_scene()

    obj = create_led_object(config, "LED_Preset", 0, 0)

    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(dg)
    mesh = eval_obj.to_mesh()

    vertex_count = len(mesh.vertices)
    print(f"  Vertices: {vertex_count}")

    output_dir = ROOT / "projects/led_test/build"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / "test8_led_preset.png")
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"  Rendered: {output_path}")

    return vertex_count > 0


def run_all_tests():
    """Run all LED tests."""
    print("=" * 60)
    print("LED/Indicator Geometry Tests (Workbench Visualization)")
    print("=" * 60)

    tests = [
        ("Round LED", test_single_led_round),
        ("Square LED", test_single_led_square),
        ("Diffused LED", test_single_led_diffused),
        ("Vertical LED Bar", test_led_bar_vertical),
        ("Horizontal LED Bar", test_led_bar_horizontal),
        ("VU Meter", test_vu_meter),
        ("7-Segment Display", test_seven_segment),
        ("LED Preset", test_led_preset),
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
