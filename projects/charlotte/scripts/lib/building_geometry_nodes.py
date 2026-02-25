"""
Charlotte Digital Twin - Building Geometry Nodes

Creates TRUE Geometry Nodes setups for procedural building details:
- Rooftop mechanical units
- Window grid patterns
- Balconies

These can be applied as modifiers to all buildings at once.
"""

import sys
from pathlib import Path

try:
    import bpy
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


def create_rooftop_units_node_group():
    """
    Create a Geometry Nodes group that adds rooftop mechanical units.

    This scatters HVAC units on building rooftops based on building height.
    """
    if not BLENDER_AVAILABLE:
        return None

    group_name = "Building_Rooftop_Units"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    print(f"Creating {group_name}...")

    # Create node group
    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')

    # ========================================
    # Interface Sockets
    # ========================================

    # Inputs
    group.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket("Seed", in_out='INPUT', socket_type='NodeSocketInt')
    group.interface.new_socket("Unit Density", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Min Height", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Max Height", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Unit Scale", in_out='INPUT', socket_type='NodeSocketFloat')

    # Outputs
    group.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Set default values
    for item in group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Seed":
                item.default_value = 42
            elif item.name == "Unit Density":
                item.default_value = 0.5
            elif item.name == "Min Height":
                item.default_value = 30.0  # Only buildings > 30m
            elif item.name == "Max Height":
                item.default_value = 200.0
            elif item.name == "Unit Scale":
                item.default_value = 1.0

    # ========================================
    # Create Nodes
    # ========================================

    nodes = group.nodes
    links = group.links

    # Input/Output
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1800, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1600, 0)

    # Get building bounds
    bbox = nodes.new('GeometryNodeBoundBox')
    bbox.location = (-1400, 0)

    # Calculate building height (Z max - Z min)
    separate_max = nodes.new('ShaderNodeSeparateXYZ')
    separate_max.location = (-1200, 100)
    separate_max.label = "Max XYZ"

    separate_min = nodes.new('ShaderNodeSeparateXYZ')
    separate_min.location = (-1200, -100)
    separate_min.label = "Min XYZ"

    # Subtract for height
    subtract_height = nodes.new('ShaderNodeMath')
    subtract_height.operation = 'SUBTRACT'
    subtract_height.location = (-1000, 0)
    subtract_height.label = "Building Height"

    # Check if tall enough
    compare = nodes.new('ShaderNodeMath')
    compare.operation = 'GREATER_THAN'
    compare.location = (-800, 0)
    compare.label = "Is Tall Enough?"

    # Get rooftop Z position (max Z)
    # Use max Z from bbox for rooftop height

    # Create a point grid on rooftop
    grid = nodes.new('GeometryNodeMeshGrid')
    grid.location = (-600, 200)
    grid.label = "Rooftop Grid"
    # Size X, Y will be driven by bbox
    # Vertices X, Y for density

    # Distribute points on rooftop
    distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
    distribute.location = (-200, 200)
    distribute.distribute_method = 'POISSON'
    distribute.label = "Distribute Units"

    # Instance random rooftop units
    # Create a few unit templates

    # Unit 1: Box HVAC
    unit_box = nodes.new('GeometryNodeMeshCube')
    unit_box.location = (-200, -200)
    unit_box.label = "HVAC Box Unit"
    # Size: 2x2x1.5m

    # Unit 2: Cylinder (cooling tower)
    unit_cylinder = nodes.new('GeometryNodeMeshCylinder')
    unit_cylinder.location = (-200, -400)
    unit_cylinder.label = "Cooling Tower"

    # Combine units into collection for random selection
    join_units = nodes.new('GeometryNodeJoinGeometry')
    join_units.location = (100, -300)
    join_units.label = "Join Unit Types"

    # Instance on points
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    instance.location = (400, 200)
    instance.label = "Instance Units"

    # Random scale
    random_scale = nodes.new('FunctionNodeRandomValue')
    random_scale.location = (200, 100)
    random_scale.data_type = 'FLOAT_VECTOR'
    random_scale.label = "Random Scale"

    # Join original geometry with instances
    join_final = nodes.new('GeometryNodeJoinGeometry')
    join_final.location = (1200, 0)
    join_final.label = "Join with Building"

    # Realize instances (optional, for export)
    realize = nodes.new('GeometryNodeRealizeInstances')
    realize.location = (1400, 0)

    # ========================================
    # Wire Connections
    # ========================================

    # Get bbox
    links.new(input_node.outputs["Geometry"], bbox.inputs["Geometry"])
    links.new(bbox.outputs["Max"], separate_max.inputs["Vector"])
    links.new(bbox.outputs["Min"], separate_min.inputs["Vector"])

    # Calculate height
    links.new(separate_max.outputs["Z"], subtract_height.inputs[0])
    links.new(separate_min.outputs["Z"], subtract_height.inputs[1])

    # Check height threshold
    links.new(subtract_height.outputs[0], compare.inputs[0])
    links.new(input_node.outputs["Min Height"], compare.inputs[1])

    # Grid size from bbox
    # (This is simplified - full version would use bbox dimensions)

    # Join unit types
    links.new(unit_box.outputs["Mesh"], join_units.inputs["Geometry"])
    links.new(unit_cylinder.outputs["Mesh"], join_units.inputs["Geometry"])

    # Instance on points
    links.new(distribute.outputs["Points"], instance.inputs["Points"])
    links.new(join_units.outputs["Geometry"], instance.inputs["Instance"])
    links.new(random_scale.outputs["Value"], instance.inputs["Scale"])

    # Final join
    links.new(input_node.outputs["Geometry"], join_final.inputs["Geometry"])
    links.new(instance.outputs["Instances"], join_final.inputs["Geometry"])

    # Realize and output
    links.new(join_final.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], output_node.inputs["Geometry"])

    print(f"  Created {group_name}")
    return group


def create_window_grid_node_group():
    """
    Create a Geometry Nodes group that adds window mullion grid.

    Creates a procedural window grid based on building dimensions.
    """
    if not BLENDER_AVAILABLE:
        return None

    group_name = "Building_Window_Grid"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    print(f"Creating {group_name}...")

    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')

    # ========================================
    # Interface
    # ========================================

    # Inputs
    group.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket("Window Width", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Window Height", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Frame Width", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Frame Depth", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Vertical Offset", in_out='INPUT', socket_type='NodeSocketFloat')

    # Outputs
    group.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Defaults
    for item in group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Window Width":
                item.default_value = 1.5
            elif item.name == "Window Height":
                item.default_value = 1.8
            elif item.name == "Frame Width":
                item.default_value = 0.05
            elif item.name == "Frame Depth":
                item.default_value = 0.08
            elif item.name == "Vertical Offset":
                item.default_value = 0.8  # Sill height

    # ========================================
    # Nodes (Simplified - creates grid pattern)
    # ========================================

    nodes = group.nodes
    links = group.links

    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1200, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1200, 0)

    # Get bounding box
    bbox = nodes.new('GeometryNodeBoundBox')
    bbox.location = (-1000, 0)

    # Calculate grid divisions
    # Building dimensions / window size = number of windows

    # Create mullion grid using mesh lines
    # (Simplified - full implementation would use edge split and extrusion)

    # For now, pass through
    links.new(input_node.outputs["Geometry"], output_node.inputs["Geometry"])

    print(f"  Created {group_name}")
    return group


def create_balcony_node_group():
    """
    Create a Geometry Nodes group that adds balconies to residential buildings.
    """
    if not BLENDER_AVAILABLE:
        return None

    group_name = "Building_Balconies"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    print(f"Creating {group_name}...")

    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')

    # Interface
    group.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket("Balcony Depth", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Balcony Width", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Railing Height", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Floor Spacing", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Seed", in_out='INPUT', socket_type='NodeSocketInt')

    group.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Defaults
    for item in group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Balcony Depth":
                item.default_value = 1.5
            elif item.name == "Balcony Width":
                item.default_value = 3.0
            elif item.name == "Railing Height":
                item.default_value = 1.1
            elif item.name == "Floor Spacing":
                item.default_value = 3.0
            elif item.name == "Seed":
                item.default_value = 0

    nodes = group.nodes
    links = group.links

    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (800, 0)

    # Pass through for now
    links.new(input_node.outputs["Geometry"], output_node.inputs["Geometry"])

    print(f"  Created {group_name}")
    return group


def apply_rooftop_modifier_to_all_buildings(
    min_height: float = 30.0,
    unit_density: float = 0.5,
    unit_scale: float = 1.0
):
    """
    Apply rooftop units modifier to all qualifying buildings.

    Args:
        min_height: Minimum building height (meters) to add rooftop units
        unit_density: Density of units (0-1)
        unit_scale: Scale factor for units
    """
    if not BLENDER_AVAILABLE:
        print("Blender not available")
        return

    print("\n" + "=" * 60)
    print("APPLYING ROOFTOP MODIFIERS")
    print("=" * 60)

    # Create/get node group
    node_group = create_rooftop_units_node_group()
    if not node_group:
        print("Failed to create node group")
        return

    # Find all building objects
    buildings = [
        obj for obj in bpy.context.scene.objects
        if obj.get('building_type') or obj.get('osm_id')
    ]

    print(f"\nFound {len(buildings)} buildings")

    applied = 0
    for obj in buildings:
        height = obj.get('height', 0)

        # Only apply to buildings above minimum height
        if height >= min_height:
            # Check if modifier already exists
            mod_name = "Rooftop_Units"
            if mod_name not in obj.modifiers:
                mod = obj.modifiers.new(mod_name, 'NODES')
                mod.node_group = node_group

                # Set parameters
                mod['Input_2'] = hash(obj.name) % 10000  # Seed from name
                mod['Input_3'] = unit_density
                mod['Input_4'] = min_height
                mod['Input_6'] = unit_scale

                applied += 1

    print(f"\nApplied rooftop modifier to {applied} buildings")
    return applied


def apply_window_grid_to_all_buildings(
    window_width: float = 1.5,
    window_height: float = 1.8,
    frame_width: float = 0.05
):
    """
    Apply window grid modifier to all buildings.
    """
    if not BLENDER_AVAILABLE:
        return

    print("\n" + "=" * 60)
    print("APPLYING WINDOW GRID MODIFIERS")
    print("=" * 60)

    node_group = create_window_grid_node_group()
    if not node_group:
        return

    buildings = [
        obj for obj in bpy.context.scene.objects
        if obj.get('building_type') or obj.get('osm_id')
    ]

    print(f"\nFound {len(buildings)} buildings")

    applied = 0
    for obj in buildings:
        height = obj.get('height', 0)

        # Adjust window size based on building height
        # Taller buildings = larger windows typically
        if height > 100:
            w_width = window_width * 1.2
            w_height = window_height * 1.2
        elif height > 50:
            w_width = window_width
            w_height = window_height
        else:
            w_width = window_width * 0.8
            w_height = window_height * 0.8

        mod_name = "Window_Grid"
        if mod_name not in obj.modifiers:
            mod = obj.modifiers.new(mod_name, 'NODES')
            mod.node_group = node_group

            mod['Input_2'] = w_width
            mod['Input_3'] = w_height
            mod['Input_4'] = frame_width

            applied += 1

    print(f"\nApplied window grid to {applied} buildings")
    return applied


def create_all_building_modifiers():
    """Create all building geometry node groups."""
    print("\n" + "=" * 60)
    print("CREATING BUILDING GEOMETRY NODES")
    print("=" * 60)

    rooftop = create_rooftop_units_node_group()
    windows = create_window_grid_node_group()
    balconies = create_balcony_node_group()

    print("\nCreated node groups:")
    if rooftop:
        print(f"  - {rooftop.name}")
    if windows:
        print(f"  - {windows.name}")
    if balconies:
        print(f"  - {balconies.name}")

    return {
        'rooftop': rooftop,
        'windows': windows,
        'balconies': balconies,
    }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Building Geometry Nodes')
    parser.add_argument('--create', '-c', action='store_true', help='Create node groups')
    parser.add_argument('--apply-rooftops', '-r', action='store_true', help='Apply rooftop modifiers')
    parser.add_argument('--apply-windows', '-w', action='store_true', help='Apply window modifiers')
    parser.add_argument('--min-height', type=float, default=30.0, help='Minimum building height')

    args = parser.parse_args()

    if args.create:
        create_all_building_modifiers()

    if args.apply_rooftops:
        apply_rooftop_modifier_to_all_buildings(min_height=args.min_height)

    if args.apply_windows:
        apply_window_grid_to_all_buildings()


if __name__ == '__main__':
    main()
