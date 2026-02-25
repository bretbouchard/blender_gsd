"""
Charlotte Digital Twin - Environment & Terrain Generation

Phase 3 of Driving Game implementation.
Generates terrain, sidewalks, vegetation, and street furniture.

Usage in Blender:
    import bpy
    bpy.ops.script.python_file_run(filepath="scripts/12_generate_environment.py")
"""

import bpy
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
import math
import random

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.geo_nodes_environment import (
    create_terrain_node_group,
    create_sidewalk_node_group,
    create_vegetation_scatter_node_group,
    create_bench_node_group,
    create_trash_can_node_group,
    create_fire_hydrant_node_group,
    generate_all_environment,
    VegetationConfig,
    FurnitureConfig,
    SidewalkType,
    TreeType,
)


def main():
    """Generate all environment for Charlotte."""
    print("\n" + "=" * 60)
    print("Charlotte Environment & Terrain Generation")
    print("=" * 60)

    # Step 1: Create node groups
    print("\n[1/6] Creating geometry node groups...")
    node_groups = create_all_node_groups()

    # Step 2: Create materials
    print("\n[2/6] Creating environment materials...")
    materials = create_environment_materials()

    # Step 3: Generate terrain
    print("\n[3/6] Generating terrain...")
    terrain_stats = generate_terrain(node_groups['terrain'])

    # Step 4: Generate sidewalks
    print("\n[4/6] Generating sidewalks...")
    sidewalk_stats = generate_sidewalks(node_groups['sidewalk'])

    # Step 5: Generate vegetation
    print("\n[5/6] Generating vegetation...")
    vegetation_stats = generate_vegetation(node_groups['vegetation'])

    # Step 6: Generate street furniture
    print("\n[6/6] Generating street furniture...")
    furniture_stats = generate_street_furniture(node_groups)

    # Summary
    total_stats = {
        **terrain_stats,
        **sidewalk_stats,
        **vegetation_stats,
        **furniture_stats,
    }
    print_summary(total_stats)

    # Save
    output_path = Path(__file__).parent.parent / 'output' / 'charlotte_environment.blend'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"\nSaved to {output_path}")


def create_all_node_groups() -> Dict[str, bpy.types.NodeGroup]:
    """Create all environment node groups."""
    node_groups = {}

    ng_creators = [
        ("terrain", create_terrain_node_group),
        ("sidewalk", create_sidewalk_node_group),
        ("vegetation", create_vegetation_scatter_node_group),
        ("bench", create_bench_node_group),
        ("trash_can", create_trash_can_node_group),
        ("fire_hydrant", create_fire_hydrant_node_group),
    ]

    for name, creator in ng_creators:
        ng = creator()
        if ng:
            node_groups[name] = ng
            print(f"  ✓ {ng.name}")
        else:
            print(f"  ✗ Failed to create {name}")

    return node_groups


def create_environment_materials() -> Dict[str, bpy.types.Material]:
    """Create materials for environment elements."""
    materials = {}

    # Terrain / Grass material
    if "terrain_grass" not in bpy.data.materials:
        mat = bpy.data.materials.new("terrain_grass")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)
        principled.inputs["Base Color"].default_value = (0.2, 0.4, 0.15, 1.0)
        principled.inputs["Roughness"].default_value = 0.9

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])
        materials["terrain_grass"] = mat
        print("  Created: terrain_grass")

    # Sidewalk concrete
    if "sidewalk_concrete" not in bpy.data.materials:
        mat = bpy.data.materials.new("sidewalk_concrete")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)
        principled.inputs["Base Color"].default_value = (0.6, 0.58, 0.55, 1.0)
        principled.inputs["Roughness"].default_value = 0.85

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])
        materials["sidewalk_concrete"] = mat
        print("  Created: sidewalk_concrete")

    # Sidewalk brick
    if "sidewalk_brick" not in bpy.data.materials:
        mat = bpy.data.materials.new("sidewalk_brick")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)
        principled.inputs["Base Color"].default_value = (0.6, 0.3, 0.25, 1.0)
        principled.inputs["Roughness"].default_value = 0.8

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])
        materials["sidewalk_brick"] = mat
        print("  Created: sidewalk_brick")

    # Tree trunk
    if "tree_trunk" not in bpy.data.materials:
        mat = bpy.data.materials.new("tree_trunk")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)
        principled.inputs["Base Color"].default_value = (0.3, 0.2, 0.1, 1.0)
        principled.inputs["Roughness"].default_value = 0.9

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])
        materials["tree_trunk"] = mat
        print("  Created: tree_trunk")

    # Tree foliage
    if "tree_foliage" not in bpy.data.materials:
        mat = bpy.data.materials.new("tree_foliage")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)
        principled.inputs["Base Color"].default_value = (0.15, 0.4, 0.15, 1.0)
        principled.inputs["Roughness"].default_value = 0.7
        principled.inputs["Specular IOR Level"].default_value = 0.3

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])
        materials["tree_foliage"] = mat
        print("  Created: tree_foliage")

    # Bench wood
    if "bench_wood" not in bpy.data.materials:
        mat = bpy.data.materials.new("bench_wood")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)
        principled.inputs["Base Color"].default_value = (0.4, 0.25, 0.15, 1.0)
        principled.inputs["Roughness"].default_value = 0.6

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])
        materials["bench_wood"] = mat
        print("  Created: bench_wood")

    # Bench metal
    if "bench_metal" not in bpy.data.materials:
        mat = bpy.data.materials.new("bench_metal")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)
        principled.inputs["Base Color"].default_value = (0.2, 0.2, 0.2, 1.0)
        principled.inputs["Roughness"].default_value = 0.4
        principled.inputs["Metallic"].default_value = 0.8

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])
        materials["bench_metal"] = mat
        print("  Created: bench_metal")

    # Fire hydrant red
    if "fire_hydrant_red" not in bpy.data.materials:
        mat = bpy.data.materials.new("fire_hydrant_red")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (400, 0)

        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)
        principled.inputs["Base Color"].default_value = (0.8, 0.1, 0.1, 1.0)
        principled.inputs["Roughness"].default_value = 0.5

        links.new(principled.outputs["BSDF"], output.inputs["Surface"])
        materials["fire_hydrant_red"] = mat
        print("  Created: fire_hydrant_red")

    return materials


def generate_terrain(terrain_ng: bpy.types.NodeGroup) -> Dict[str, int]:
    """Generate terrain mesh."""
    stats = {'terrain': 0, 'terrain_errors': 0}

    try:
        # Get scene bounds from existing objects
        all_objects = [
            obj for obj in bpy.context.scene.objects
            if obj.type in ('CURVE', 'MESH')
        ]

        if not all_objects:
            print("  No objects found for bounds calculation")
            return stats

        # Calculate bounds
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        min_z = 0

        for obj in all_objects:
            if obj.type == 'CURVE' and obj.data.splines:
                for spline in obj.data.splines:
                    for p in spline.points:
                        world_p = obj.matrix_world @ bpy.mathutils.Vector(p.co[:3])
                        min_x = min(min_x, world_p.x)
                        max_x = max(max_x, world_p.x)
                        min_y = min(min_y, world_p.y)
                        max_y = max(max_y, world_p.y)
                        min_z = min(min_z, world_p.z)

        # Add buffer
        buffer = 200
        min_x -= buffer
        max_x += buffer
        min_y -= buffer
        max_y += buffer

        size_x = max_x - min_x
        size_y = max_y - min_y

        print(f"  Terrain bounds: {size_x:.0f}x{size_y:.0f}m")

        # Create terrain object
        terrain_obj = bpy.data.objects.new("Charlotte_Terrain", None)
        terrain_obj.location = ((min_x + max_x) / 2, (min_y + max_y) / 2, min_z - 0.1)

        # Add geometry nodes modifier
        mod = terrain_obj.modifiers.new(name="Terrain", type='NODES')
        mod.node_group = terrain_ng
        mod["Size X"] = size_x
        mod["Size Y"] = size_y
        mod["Resolution"] = 10.0
        mod["Base Elevation"] = 200.0

        # Link to scene and collection
        bpy.context.collection.objects.link(terrain_obj)

        # Create/Get Terrain collection
        if "Terrain" not in bpy.data.collections:
            coll = bpy.data.collections.new("Terrain")
            bpy.context.scene.collection.children.link(coll)
        bpy.data.collections["Terrain"].objects.link(terrain_obj)

        stats['terrain'] = 1

    except Exception as e:
        print(f"  Error generating terrain: {e}")
        stats['terrain_errors'] = 1

    return stats


def generate_sidewalks(sidewalk_ng: bpy.types.NodeGroup) -> Dict[str, int]:
    """Generate sidewalks from footways."""
    stats = {'sidewalks': 0, 'sidewalk_errors': 0}

    try:
        # Get footway curves
        footways = [
            obj for obj in bpy.context.scene.objects
            if obj.type == 'CURVE' and obj.get('highway_type') == 'footway'
        ]

        print(f"  Found {len(footways)} footways")

        # Create collection
        if "Sidewalks" not in bpy.data.collections:
            coll = bpy.data.collections.new("Sidewalks")
            bpy.context.scene.collection.children.link(coll)

        for footway in footways[:500]:  # Limit for performance
            try:
                # Apply sidewalk modifier
                mod = footway.modifiers.new(name="Sidewalk", type='NODES')
                mod.node_group = sidewalk_ng
                mod["Width"] = 1.5
                mod["Height"] = 0.15

                stats['sidewalks'] += 1

            except Exception as e:
                stats['sidewalk_errors'] += 1

        print(f"  Generated {stats['sidewalks']} sidewalks")

    except Exception as e:
        print(f"  Error generating sidewalks: {e}")
        stats['sidewalk_errors'] += 1

    return stats


def generate_vegetation(vegetation_ng: bpy.types.NodeGroup) -> Dict[str, int]:
    """Generate vegetation (trees, bushes)."""
    stats = {'trees': 0, 'vegetation_errors': 0}

    try:
        # Get road curves for tree placement
        road_curves = [
            obj for obj in bpy.context.scene.objects
            if obj.type == 'CURVE' and obj.get('road_class')
        ]

        print(f"  Placing trees along {len(road_curves)} roads")

        # Create collection
        if "Vegetation" not in bpy.data.collections:
            coll = bpy.data.collections.new("Vegetation")
            bpy.context.scene.collection.children.link(coll)

        config = VegetationConfig()
        tree_count = 0

        for road in road_curves:
            if not road.data.splines:
                continue

            highway_type = road.get('highway_type', 'residential')

            # Only plant trees along certain road types
            if highway_type not in ['primary', 'secondary', 'tertiary', 'residential']:
                continue

            spline = road.data.splines[0]
            points = [road.matrix_world @ bpy.mathutils.Vector(p.co[:3]) for p in spline.points]

            if len(points) < 2:
                continue

            road_width = road.get('road_width', 7.0)

            # Calculate tree positions along road
            total_length = sum(
                (points[i+1] - points[i]).length
                for i in range(len(points) - 1)
            )

            num_trees = int(total_length / config.tree_spacing)

            for i in range(num_trees):
                # Calculate position along road
                target_dist = (i + 0.5) * config.tree_spacing
                current_dist = 0

                for j in range(len(points) - 1):
                    segment_length = (points[j+1] - points[j]).length

                    if current_dist + segment_length >= target_dist:
                        # Interpolate position
                        t = (target_dist - current_dist) / segment_length
                        pos = points[j] + (points[j+1] - points[j]) * t

                        # Offset to side of road
                        direction = (points[j+1] - points[j]).normalized()
                        perpendicular = bpy.mathutils.Vector((-direction.y, direction.x, 0))

                        # Alternate sides
                        side = 1 if i % 2 == 0 else -1
                        tree_pos = pos + perpendicular * (road_width/2 + config.tree_offset) * side

                        # Create tree (simplified cone)
                        tree_obj = create_simple_tree(
                            f"Tree_{tree_count}",
                            tree_pos,
                            random.uniform(config.min_tree_height, config.max_tree_height)
                        )

                        if tree_obj:
                            bpy.data.collections["Vegetation"].objects.link(tree_obj)
                            tree_count += 1

                        break

                    current_dist += segment_length

            if tree_count >= 1000:  # Limit total trees
                break

        stats['trees'] = tree_count
        print(f"  Generated {tree_count} trees")

    except Exception as e:
        print(f"  Error generating vegetation: {e}")
        stats['vegetation_errors'] += 1

    return stats


def create_simple_tree(name: str, position: bpy.mathutils.Vector, height: float) -> bpy.types.Object:
    """Create a simple procedural tree using geometry nodes."""
    try:
        tree_obj = bpy.data.objects.new(name, None)
        tree_obj.location = position

        # Create trunk
        trunk = tree_obj.modifiers.new(name="Trunk", type='NODES')
        trunk_ng = create_simple_trunk_node_group()
        if trunk_ng:
            trunk.node_group = trunk_ng
            trunk["Height"] = height * 0.4
            trunk["Radius"] = 0.15

        # Create foliage
        foliage = tree_obj.modifiers.new(name="Foliage", type='NODES')
        foliage_ng = create_simple_foliage_node_group()
        if foliage_ng:
            foliage.node_group = foliage_ng
            foliage["Height"] = height * 0.7
            foliage["Radius"] = height * 0.25
            foliage["Offset"] = height * 0.35

        bpy.context.collection.objects.link(tree_obj)
        return tree_obj

    except Exception:
        return None


def create_simple_trunk_node_group() -> bpy.types.NodeGroup:
    """Create simple trunk geometry node group."""
    if not bpy:
        return None

    name = "Simple_Trunk"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    node_group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nodes = node_group.nodes
    links = node_group.links

    interface = node_group.interface
    interface.new_socket("Height", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Radius", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    node_group.inputs["Height"].default_value = 3.0
    node_group.inputs["Radius"].default_value = 0.15

    gi = nodes.new("NodeGroupInput")
    gi.location = (0, 0)

    go = nodes.new("NodeGroupOutput")
    go.location = (600, 0)

    trunk = nodes.new("GeometryNodeMeshCylinder")
    trunk.location = (200, 0)
    trunk.inputs["Vertices"].default_value = 8

    transform = nodes.new("GeometryNodeTransform")
    transform.location = (400, 0)
    transform.inputs["Translation"].default_value = (0, 0, 1.5)

    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (500, 0)

    links.new(gi.outputs["Radius"], trunk.inputs["Radius"])
    links.new(gi.outputs["Height"], trunk.inputs["Depth"])
    links.new(trunk.outputs["Mesh"], transform.inputs["Geometry"])
    links.new(gi.outputs["Height"], transform.inputs["Translation"].subscript(2))

    # Adjust Z translation to half height
    math_div = nodes.new("ShaderNodeMath")
    math_div.location = (200, -100)
    math_div.operation = 'DIVIDE'
    math_div.inputs[1].default_value = 2.0

    links.new(gi.outputs["Height"], math_div.inputs[0])
    links.new(math_div.outputs[0], transform.inputs["Translation"].subscript(2))

    links.new(transform.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    return node_group


def create_simple_foliage_node_group() -> bpy.types.NodeGroup:
    """Create simple foliage geometry node group."""
    if not bpy:
        return None

    name = "Simple_Foliage"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    node_group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nodes = node_group.nodes
    links = node_group.links

    interface = node_group.interface
    interface.new_socket("Height", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Radius", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Offset", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    node_group.inputs["Height"].default_value = 5.0
    node_group.inputs["Radius"].default_value = 2.0
    node_group.inputs["Offset"].default_value = 3.0

    gi = nodes.new("NodeGroupInput")
    gi.location = (0, 0)

    go = nodes.new("NodeGroupOutput")
    go.location = (600, 0)

    # Cone for foliage
    foliage = nodes.new("GeometryNodeMeshCone")
    foliage.location = (200, 0)
    foliage.inputs["Vertices"].default_value = 8

    transform = nodes.new("GeometryNodeTransform")
    transform.location = (400, 0)

    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (500, 0)

    links.new(gi.outputs["Radius"], foliage.inputs["Radius Bottom"])
    links.new(gi.outputs["Height"], foliage.inputs["Depth"])
    links.new(foliage.outputs["Mesh"], transform.inputs["Geometry"])
    links.new(gi.outputs["Offset"], transform.inputs["Translation"].subscript(2))

    links.new(transform.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    return node_group


def generate_street_furniture(node_groups: Dict) -> Dict[str, int]:
    """Generate street furniture."""
    stats = {
        'benches': 0,
        'trash_cans': 0,
        'fire_hydrants': 0,
        'furniture_errors': 0,
    }

    try:
        # Create collection
        if "Street_Furniture" not in bpy.data.collections:
            coll = bpy.data.collections.new("Street_Furniture")
            bpy.context.scene.collection.children.link(coll)

        # Get sidewalks for placement
        sidewalks = [
            obj for obj in bpy.context.scene.objects
            if obj.type == 'CURVE' and obj.get('highway_type') == 'footway'
        ]

        config = FurnitureConfig()

        # Distribute furniture along sidewalks
        for i, sidewalk in enumerate(sidewalks[:100]):  # Limit
            if not sidewalk.data.splines:
                continue

            spline = sidewalk.data.splines[0]
            points = [sidewalk.matrix_world @ bpy.mathutils.Vector(p.co[:3]) for p in spline.points]

            if len(points) < 2:
                continue

            # Place at intervals
            total_length = sum(
                (points[j+1] - points[j]).length
                for j in range(len(points) - 1)
            )

            # Bench
            if i % 5 == 0:
                bench_pos = points[0]
                bench = create_furniture_object(
                    "Bench",
                    bench_pos,
                    node_groups.get('bench')
                )
                if bench:
                    bpy.data.collections["Street_Furniture"].objects.link(bench)
                    stats['benches'] += 1

            # Trash can
            if i % 3 == 0:
                trash_pos = points[0]
                trash = create_furniture_object(
                    "TrashCan",
                    trash_pos,
                    node_groups.get('trash_can')
                )
                if trash:
                    bpy.data.collections["Street_Furniture"].objects.link(trash)
                    stats['trash_cans'] += 1

            # Fire hydrant
            if i % 10 == 0:
                hydrant_pos = points[0]
                hydrant = create_furniture_object(
                    "FireHydrant",
                    hydrant_pos,
                    node_groups.get('fire_hydrant')
                )
                if hydrant:
                    bpy.data.collections["Street_Furniture"].objects.link(hydrant)
                    stats['fire_hydrants'] += 1

        print(f"  Benches: {stats['benches']}")
        print(f"  Trash cans: {stats['trash_cans']}")
        print(f"  Fire hydrants: {stats['fire_hydrants']}")

    except Exception as e:
        print(f"  Error generating furniture: {e}")
        stats['furniture_errors'] += 1

    return stats


def create_furniture_object(
    furniture_type: str,
    position: bpy.mathutils.Vector,
    node_group: bpy.types.NodeGroup
) -> bpy.types.Object:
    """Create a furniture object with geometry nodes."""
    try:
        obj = bpy.data.objects.new(f"{furniture_type}_{random.randint(1000, 9999)}", None)
        obj.location = position

        if node_group:
            mod = obj.modifiers.new(name=furniture_type, type='NODES')
            mod.node_group = node_group

        bpy.context.collection.objects.link(obj)
        return obj

    except Exception:
        return None


def print_summary(stats: Dict):
    """Print generation summary."""
    print("\n" + "=" * 60)
    print("Environment Generation Summary")
    print("=" * 60)

    print(f"\nTerrain:")
    print(f"  Surfaces: {stats.get('terrain', 0)}")

    print(f"\nSidewalks:")
    print(f"  Generated: {stats.get('sidewalks', 0)}")

    print(f"\nVegetation:")
    print(f"  Trees: {stats.get('trees', 0)}")

    print(f"\nStreet Furniture:")
    print(f"  Benches: {stats.get('benches', 0)}")
    print(f"  Trash cans: {stats.get('trash_cans', 0)}")
    print(f"  Fire hydrants: {stats.get('fire_hydrants', 0)}")

    errors = sum(v for k, v in stats.items() if 'error' in k)
    print(f"\nErrors: {errors}")

    # Collection count
    collections = ['Terrain', 'Sidewalks', 'Vegetation', 'Street_Furniture']
    print(f"\nCollections created:")
    for coll_name in collections:
        if coll_name in bpy.data.collections:
            obj_count = len(bpy.data.collections[coll_name].objects)
            print(f"  {coll_name}: {obj_count} objects")


# =============================================================================
# COMMAND LINE SUPPORT
# =============================================================================

def run_from_commandline():
    """Run via blender command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate Charlotte environment")
    parser.add_argument('--blend', type=str, help="Input blend file")
    parser.add_argument('--output', type=str, default='output/charlotte_environment.blend',
                        help="Output blend file")

    args = parser.parse_args()

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)

    main()

    bpy.ops.wm.save_as_mainfile(filepath=args.output)


if __name__ == '__main__':
    main()
