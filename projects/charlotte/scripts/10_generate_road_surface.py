"""
Charlotte Digital Twin - Road Surface & Collision Generation

Phase 1 of Driving Game implementation.
Converts road curves to actual driveable surfaces with collision.

Usage in Blender:
    import bpy
    bpy.ops.script.python_file_run(filepath="scripts/10_generate_road_surface.py")
"""

import bpy
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.geo_nodes_road_surface import (
    create_road_surface_node_group,
    create_collision_node_group,
    create_curb_node_group,
    apply_road_surface_to_curves,
    ROAD_SPECS,
    FRICTION_VALUES,
)


def main():
    """Generate road surfaces and collision for Charlotte."""
    print("\n" + "=" * 60)
    print("Charlotte Road Surface & Collision Generation")
    print("=" * 60)

    # Step 1: Create geometry node groups
    print("\n[1/5] Creating geometry node groups...")

    surface_ng = create_road_surface_node_group()
    if surface_ng:
        print(f"  ✓ Road surface: {surface_ng.name}")
    else:
        print("  ✗ Failed to create road surface node group")
        return

    collision_ng = create_collision_node_group()
    if collision_ng:
        print(f"  ✓ Collision: {collision_ng.name}")
    else:
        print("  ✗ Failed to create collision node group")

    curb_ng = create_curb_node_group()
    if curb_ng:
        print(f"  ✓ Curbs: {curb_ng.name}")
    else:
        print("  ✗ Failed to create curb node group")

    # Step 2: Apply to road curves
    print("\n[2/5] Applying road surfaces to curves...")
    stats = apply_road_surface_to_curves(surface_ng, collision_ng)

    print(f"  Total curves: {stats.get('total_curves', 0)}")
    print(f"  Surfaces: {stats.get('surface_applied', 0)}")
    print(f"  Collisions: {stats.get('collision_created', 0)}")

    # Step 3: Create materials
    print("\n[3/5] Setting up materials...")
    materials = create_road_materials()

    # Step 4: Organize collections
    print("\n[4/5] Organizing collections...")
    organize_collections()

    # Step 5: Summary
    print("\n[5/5] Summary...")
    print_summary(stats, materials)

    # Save
    output_path = Path(__file__).parent.parent / 'output' / 'charlotte_road_surface.blend'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"\nSaved to {output_path}")


def create_road_materials() -> Dict[str, bpy.types.Material]:
    """
    Create basic road materials.

    Creates:
    - asphalt_road (main road surface)
    - concrete_curb (curb surface)
    - road_marking_white (white paint)
    - road_marking_yellow (yellow paint)
    """
    materials = {}

    # Asphalt material
    if "asphalt_road" not in bpy.data.materials:
        mat = bpy.data.materials.new("asphalt_road")
        mat.use_nodes = True

        # Get node tree
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create nodes
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)

        # Set asphalt color (dark gray)
        principled.inputs["Base Color"].default_value = (0.15, 0.15, 0.15, 1.0)
        principled.inputs["Roughness"].default_value = 0.9
        principled.inputs["Specular IOR Level"].default_value = 0.2

        # Link
        links.new(principled.outputs["BSDF"], output.inputs["Surface"])

        materials["asphalt_road"] = mat
        print(f"  Created: asphalt_road")
    else:
        materials["asphalt_road"] = bpy.data.materials["asphalt_road"]

    # Concrete curb material
    if "concrete_curb" not in bpy.data.materials:
        mat = bpy.data.materials.new("concrete_curb")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)

        # Concrete color (light gray)
        principled.inputs["Base Color"].default_value = (0.6, 0.58, 0.55, 1.0)
        principled.inputs["Roughness"].default_value = 0.85

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])

        materials["concrete_curb"] = mat
        print(f"  Created: concrete_curb")
    else:
        materials["concrete_curb"] = bpy.data.materials["concrete_curb"]

    # White marking material
    if "road_marking_white" not in bpy.data.materials:
        mat = bpy.data.materials.new("road_marking_white")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)

        # White color
        principled.inputs["Base Color"].default_value = (0.95, 0.95, 0.95, 1.0)
        principled.inputs["Roughness"].default_value = 0.3
        principled.inputs["Emission Color"].default_value = (0.3, 0.3, 0.3, 1.0)

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])

        materials["road_marking_white"] = mat
        print(f"  Created: road_marking_white")
    else:
        materials["road_marking_white"] = bpy.data.materials["road_marking_white"]

    # Yellow marking material
    if "road_marking_yellow" not in bpy.data.materials:
        mat = bpy.data.materials.new("road_marking_yellow")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)

        # Yellow color
        principled.inputs["Base Color"].default_value = (0.9, 0.8, 0.1, 1.0)
        principled.inputs["Roughness"].default_value = 0.3
        principled.inputs["Emission Color"].default_value = (0.2, 0.15, 0.0, 1.0)

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])

        materials["road_marking_yellow"] = mat
        print(f"  Created: road_marking_yellow")
    else:
        materials["road_marking_yellow"] = bpy.data.materials["road_marking_yellow"]

    return materials


def organize_collections():
    """Organize road objects into proper collections."""

    # Ensure main collection exists
    if "Roads" not in bpy.data.collections:
        roads_coll = bpy.data.collections.new("Roads")
        bpy.context.scene.collection.children.link(roads_coll)

    # Create sub-collections
    subcollections = [
        "Roads_Surface",
        "Roads_Surface_Collision",
        "Roads_Curves",
        "Roads_Markings",
    ]

    roads_coll = bpy.data.collections["Roads"]

    for name in subcollections:
        if name not in bpy.data.collections:
            coll = bpy.data.collections.new(name)
            roads_coll.children.link(coll)

    # Move objects to appropriate collections
    for obj in bpy.context.scene.objects:
        if obj.type == 'CURVE' and obj.get('road_class'):
            # Move curves to Roads_Curves
            curves_coll = bpy.data.collections.get("Roads_Curves")
            if curves_coll and obj.name not in curves_coll.objects:
                for c in list(obj.users_collection):
                    c.objects.unlink(obj)
                curves_coll.objects.link(obj)

        elif "_collision" in obj.name:
            # Move collision objects
            coll = bpy.data.collections.get("Roads_Surface_Collision")
            if coll and obj.name not in coll.objects:
                for c in list(obj.users_collection):
                    c.objects.unlink(obj)
                coll.objects.link(obj)


def print_summary(stats: Dict, materials: Dict):
    """Print generation summary."""

    # Count road curves
    road_curves = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'CURVE' and obj.get('road_class')
    ]

    # Count by type
    type_counts = {}
    for obj in road_curves:
        hw_type = obj.get('highway_type', 'unknown')
        type_counts[hw_type] = type_counts.get(hw_type, 0) + 1

    print("\n" + "=" * 60)
    print("Road Surface Generation Summary")
    print("=" * 60)

    print(f"\nRoad Curves: {len(road_curves)}")
    print("\nBy Type:")
    for hw_type, count in sorted(type_counts.items()):
        spec = ROAD_SPECS.get(hw_type, {})
        width = spec.get('width', 'N/A')
        print(f"  {hw_type:20} {count:5} roads (width: {width}m)")

    print(f"\nMaterials Created: {len(materials)}")
    for name in materials:
        print(f"  {name}")

    print(f"\nGeometry Applied:")
    print(f"  Surfaces: {stats.get('surface_applied', 0)}")
    print(f"  Collisions: {stats.get('collision_created', 0)}")

    # Calculate total road area (approximate)
    total_length = 0
    total_area = 0
    for obj in road_curves:
        if obj.type == 'CURVE' and obj.data.splines:
            for spline in obj.data.splines:
                length = spline.calc_length()
                width = obj.get('road_width', 7.0)
                total_length += length
                total_area += length * width

    print(f"\nApproximate Dimensions:")
    print(f"  Total Length: {total_length/1000:.1f} km")
    print(f"  Total Area: {total_area/1000000:.2f} sq km")


# =============================================================================
# COMMAND LINE SUPPORT
# =============================================================================

def run_from_commandline():
    """Run via blender command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate Charlotte road surfaces")
    parser.add_argument('--blend', type=str, help="Input blend file with curves")
    parser.add_argument('--output', type=str, default='output/charlotte_roads.blend',
                        help="Output blend file")

    args = parser.parse_args()

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)

    main()

    bpy.ops.wm.save_as_mainfile(filepath=args.output)


if __name__ == '__main__':
    main()
