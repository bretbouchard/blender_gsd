"""
Charlotte Digital Twin - Traffic Infrastructure Generation

Phase 2 of Driving Game implementation.
Generates traffic signals, signs, and turn lane arrows.

Usage in Blender:
    import bpy
    bpy.ops.script.python_file_run(filepath="scripts/11_generate_traffic_infrastructure.py")
"""

import bpy
import sys
from pathlib import Path
from typing import Dict, List, Any
import math

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.geo_nodes_traffic import (
    create_traffic_signal_node_group,
    create_traffic_sign_node_group,
    create_turn_arrow_node_group,
    generate_all_traffic_infrastructure,
    SignalType,
    SignType,
    ArrowType,
)


def main():
    """Generate all traffic infrastructure for Charlotte."""
    print("\n" + "=" * 60)
    print("Charlotte Traffic Infrastructure Generation")
    print("=" * 60)

    # Step 1: Create node groups
    print("\n[1/6] Creating geometry node groups...")

    signal_ng = create_traffic_signal_node_group()
    if signal_ng:
        print(f"  ✓ Traffic signal: {signal_ng.name}")
    else:
        print("  ✗ Failed to create signal node group")
        return

    sign_ng = create_traffic_sign_node_group()
    if sign_ng:
        print(f"  ✓ Traffic sign: {sign_ng.name}")
    else:
        print("  ✗ Failed to create sign node group")

    arrow_ng = create_turn_arrow_node_group()
    if arrow_ng:
        print(f"  ✓ Turn arrow: {arrow_ng.name}")
    else:
        print("  ✗ Failed to create arrow node group")

    # Step 2: Create materials
    print("\n[2/6] Creating traffic materials...")
    materials = create_traffic_materials()

    # Step 3: Generate infrastructure
    print("\n[3/6] Generating traffic infrastructure...")
    stats = generate_all_traffic_infrastructure()

    # Step 4: Assign materials
    print("\n[4/6] Assigning materials...")
    assign_materials(materials)

    # Step 5: Create traffic light system
    print("\n[5/6] Setting up traffic light system...")
    setup_traffic_light_system()

    # Step 6: Summary
    print("\n[6/6] Summary...")
    print_summary(stats)

    # Save
    output_path = Path(__file__).parent.parent / 'output' / 'charlotte_traffic.blend'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"\nSaved to {output_path}")


def create_traffic_materials() -> Dict[str, bpy.types.Material]:
    """
    Create materials for traffic infrastructure.

    Materials:
    - traffic_pole_metal (galvanized steel)
    - traffic_signal_housing (black/yellow)
    - traffic_light_red (emissive)
    - traffic_light_yellow (emissive)
    - traffic_light_green (emissive)
    - sign_stop_red
    - sign_yield_yellow
    - sign_speed_white
    - road_paint_white
    """
    materials = {}

    # Pole material (galvanized steel)
    if "traffic_pole_metal" not in bpy.data.materials:
        mat = bpy.data.materials.new("traffic_pole_metal")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)
        principled.inputs["Base Color"].default_value = (0.5, 0.5, 0.52, 1.0)
        principled.inputs["Roughness"].default_value = 0.4
        principled.inputs["Metallic"].default_value = 0.9

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])
        materials["traffic_pole_metal"] = mat
        print("  Created: traffic_pole_metal")

    # Signal housing (black)
    if "traffic_signal_housing" not in bpy.data.materials:
        mat = bpy.data.materials.new("traffic_signal_housing")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)
        principled.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
        principled.inputs["Roughness"].default_value = 0.3

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])
        materials["traffic_signal_housing"] = mat
        print("  Created: traffic_signal_housing")

    # Traffic lights (emissive)
    light_colors = {
        "traffic_light_red": (1.0, 0.0, 0.0, 1.0),
        "traffic_light_yellow": (1.0, 0.8, 0.0, 1.0),
        "traffic_light_green": (0.0, 1.0, 0.0, 1.0),
        "traffic_light_off": (0.1, 0.1, 0.1, 1.0),
    }

    for name, color in light_colors.items():
        if name not in bpy.data.materials:
            mat = bpy.data.materials.new(name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            nodes.clear()

            output = nodes.new("ShaderNodeOutputMaterial")
            output.location = (400, 0)

            principled = nodes.new("ShaderNodeBsdfPrincipled")
            principled.location = (0, 0)
            principled.inputs["Base Color"].default_value = color[:3] + (1.0,)

            # Add emission for glow
            if "off" not in name:
                principled.inputs["Emission Color"].default_value = color
                principled.inputs["Emission Strength"].default_value = 5.0

            links.new(principled.outputs["BSDF"], output.inputs["Surface"])
            materials[name] = mat
            print(f"  Created: {name}")

    # Sign materials
    sign_materials = {
        "sign_stop_red": (0.8, 0.0, 0.0, 1.0),
        "sign_yield_yellow": (0.9, 0.8, 0.0, 1.0),
        "sign_speed_white": (1.0, 1.0, 1.0, 1.0),
        "sign_no_entry_red": (0.8, 0.0, 0.0, 1.0),
        "sign_post_metal": (0.6, 0.6, 0.6, 1.0),
    }

    for name, color in sign_materials.items():
        if name not in bpy.data.materials:
            mat = bpy.data.materials.new(name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            nodes.clear()

            output = nodes.new("ShaderNodeOutputMaterial")
            output.location = (400, 0)

            principled = nodes.new("ShaderNodeBsdfPrincipled")
            principled.location = (0, 0)
            principled.inputs["Base Color"].default_value = color
            principled.inputs["Roughness"].default_value = 0.4

            links.new(principled.outputs["BSDF"], output.inputs["Surface"])
            materials[name] = mat
            print(f"  Created: {name}")

    return materials


def assign_materials(materials: Dict[str, bpy.types.Material]):
    """Assign materials to traffic objects based on their type."""

    # Assign to signals
    for obj in bpy.data.collections.get("Traffic_Signals", []).objects:
        if "signal_type" in obj:
            # Assign pole and housing materials
            if len(obj.material_slots) == 0:
                obj.data.materials.append(materials.get("traffic_pole_metal"))
            # Lights would need face selection - simplified for now

    # Assign to signs
    for obj in bpy.data.collections.get("Traffic_Signals", []).objects:
        sign_type = obj.get("sign_type", 0)

        if len(obj.material_slots) == 0:
            if sign_type == SignType.STOP.value:
                obj.data.materials.append(materials.get("sign_stop_red"))
            elif sign_type == SignType.YIELD.value:
                obj.data.materials.append(materials.get("sign_yield_yellow"))
            else:
                obj.data.materials.append(materials.get("sign_speed_white"))

    # Assign to arrows
    for obj in bpy.data.collections.get("Turn_Arrows", []).objects:
        if len(obj.material_slots) == 0:
            obj.data.materials.append(materials.get("road_marking_white", materials.get("sign_speed_white")))


def setup_traffic_light_system():
    """
    Set up traffic light timing system.

    Creates a simple traffic light controller that can:
    - Cycle through red/yellow/green
    - Sync multiple signals at same intersection
    """

    # Create a controller empty for each intersection
    intersections = {}

    for obj in bpy.data.collections.get("Traffic_Signals", []).objects:
        # Group by approximate position
        key = f"{obj.location.x:.0f}_{obj.location.y:.0f}"
        if key not in intersections:
            intersections[key] = []
        intersections[key].append(obj)

    # Create controllers
    controllers_coll = bpy.data.collections.get("Traffic_Controllers")
    if not controllers_coll:
        controllers_coll = bpy.data.collections.new("Traffic_Controllers")
        bpy.context.scene.collection.children.link(controllers_coll)

    for key, signals in intersections.items():
        # Create empty as controller
        controller = bpy.data.objects.new(f"TrafficController_{key}", None)
        controller.empty_display_type = 'SPHERE'
        controller.empty_display_size = 0.5

        # Position at center of signals
        avg_pos = signals[0].location
        for sig in signals[1:]:
            avg_pos += sig.location
        avg_pos /= len(signals)
        controller.location = avg_pos

        # Store configuration
        controller["controller_type"] = "traffic_signal"
        controller["signals"] = [s.name for s in signals]
        controller["cycle_time"] = 60  # seconds
        controller["green_time"] = 30
        controller["yellow_time"] = 3
        controller["red_time"] = 27
        controller["current_phase"] = 0  # 0=green, 1=yellow, 2=red

        bpy.context.collection.objects.link(controller)
        controllers_coll.objects.link(controller)

    print(f"  Created {len(intersections)} traffic controllers")


def print_summary(stats: Dict):
    """Print generation summary."""

    # Count objects in collections
    signals = len(bpy.data.collections.get("Traffic_Signals", []).objects)
    signs = len(bpy.data.collections.get("Traffic_Signs", []).objects)
    arrows = len(bpy.data.collections.get("Turn_Arrows", []).objects)
    controllers = len(bpy.data.collections.get("Traffic_Controllers", []).objects)

    print("\n" + "=" * 60)
    print("Traffic Infrastructure Summary")
    print("=" * 60)

    print(f"\nObjects Generated:")
    print(f"  Traffic signals: {signals}")
    print(f"  Traffic signs:   {signs}")
    print(f"  Turn arrows:     {arrows}")
    print(f"  Controllers:     {controllers}")

    print(f"\nNode Groups Created:")
    for ng_name in ["TrafficSignal_Generator", "TrafficSign_Generator", "TurnArrow_Generator"]:
        if ng_name in bpy.data.node_groups:
            print(f"  ✓ {ng_name}")
        else:
            print(f"  ✗ {ng_name}")

    # Material count
    traffic_mats = [m for m in bpy.data.materials if "traffic" in m.name.lower() or "sign" in m.name.lower()]
    print(f"\nMaterials: {len(traffic_mats)} traffic-related")


# =============================================================================
# ADDITIONAL PLACEMENT UTILITIES
# =============================================================================

def add_stop_signs_at_intersections():
    """Add stop signs at minor road intersections."""

    road_curves = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'CURVE' and obj.get('road_class')
    ]

    # Find T-intersections and minor road terminations
    # This is a simplified version - real implementation would be more sophisticated

    stop_positions = []

    for curve in road_curves:
        road_class = curve.get('road_class', 'local')

        # Only add stop signs on local/residential roads
        if road_class not in ['local', 'residential']:
            continue

        if not curve.data.splines:
            continue

        spline = curve.data.splines[0]
        points = [curve.matrix_world @ Vector(p.co[:3]) for p in spline.points]

        if len(points) < 2:
            continue

        # Check if endpoint doesn't connect to another road
        # (simplified - just add at residential road ends)
        end_point = points[-1]
        direction = (points[-1] - points[-2]).normalized()
        right_offset = Vector((-direction.y, direction.x, 0)) * 3.0

        stop_positions.append({
            'position': end_point + right_offset,
            'rotation': math.atan2(direction.y, direction.x) + math.pi,
        })

    return stop_positions


def add_speed_limit_signs():
    """Add speed limit signs based on road class."""

    speed_limits = {
        'motorway': 70,
        'trunk': 55,
        'primary': 45,
        'secondary': 35,
        'tertiary': 30,
        'residential': 25,
        'service': 15,
    }

    road_curves = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'CURVE' and obj.get('road_class')
    ]

    sign_positions = []

    for curve in road_curves:
        highway_type = curve.get('highway_type', 'residential')
        speed = speed_limits.get(highway_type, 25)

        if not curve.data.splines:
            continue

        spline = curve.data.splines[0]
        points = [curve.matrix_world @ Vector(p.co[:3]) for p in spline.points]

        if len(points) < 2:
            continue

        # Place at start of road
        start_point = points[0]
        direction = (points[1] - points[0]).normalized()
        right_offset = Vector((-direction.y, direction.x, 0)) * 5.0

        sign_positions.append({
            'position': start_point + right_offset,
            'rotation': math.atan2(direction.y, direction.x),
            'speed': speed,
        })

    return sign_positions


# =============================================================================
# COMMAND LINE SUPPORT
# =============================================================================

def run_from_commandline():
    """Run via blender command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate Charlotte traffic infrastructure")
    parser.add_argument('--blend', type=str, help="Input blend file with roads")
    parser.add_argument('--output', type=str, default='output/charlotte_traffic.blend',
                        help="Output blend file")

    args = parser.parse_args()

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)

    main()

    bpy.ops.wm.save_as_mainfile(filepath=args.output)


if __name__ == '__main__':
    main()
