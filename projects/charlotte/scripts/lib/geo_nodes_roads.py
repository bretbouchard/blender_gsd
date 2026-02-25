"""
Charlotte Digital Twin - Road Infrastructure Geometry Nodes

Creates procedural road infrastructure including:
- Street lights (spacing, type, height)
- Sidewalks (width, curb style)
- Manhole covers (patterns, density)
- Traffic signals (at intersections)
- Road markings (lane lines, crosswalks)
- Street furniture (benches, trash cans, bollards)

Custom Properties on Road Objects:
    - road_light_spacing: Meters between lights (default: 30)
    - road_light_type: "modern", "historic", "highway"
    - road_light_height: Pole height in meters (default: 8)
    - road_sidewalk_width: Width in meters (default: 2)
    - road_sidewalk_enabled: True/False
    - road_manhole_density: Density factor (default: 0.5)
    - road_furniture_density: Street furniture density (default: 0.3)
    - road_style: Preset ("urban_main", "residential", "highway", "downtown")

Usage:
    blender --python scripts/apply_road_geo_nodes.py
"""

import bpy
import sys
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent))


# =============================================================================
# ROAD STYLE PRESETS
# =============================================================================

ROAD_PRESETS = {
    # Downtown Charlotte - heavy street furniture, historic lights
    "downtown": {
        "light_spacing": 25,
        "light_type": "modern",
        "light_height": 10,
        "sidewalk_enabled": True,
        "sidewalk_width": 4,
        "manhole_density": 0.8,
        "furniture_density": 0.7,
        "crosswalk_enabled": True,
        "lane_markings": True,
    },

    # Main urban roads
    "urban_main": {
        "light_spacing": 30,
        "light_type": "modern",
        "light_height": 10,
        "sidewalk_enabled": True,
        "sidewalk_width": 2.5,
        "manhole_density": 0.6,
        "furniture_density": 0.4,
        "crosswalk_enabled": True,
        "lane_markings": True,
    },

    # Residential streets
    "residential": {
        "light_spacing": 40,
        "light_type": "modern",
        "light_height": 6,
        "sidewalk_enabled": True,
        "sidewalk_width": 1.5,
        "manhole_density": 0.2,
        "furniture_density": 0.1,
        "crosswalk_enabled": False,
        "lane_markings": False,
    },

    # Highway/interstate
    "highway": {
        "light_spacing": 60,
        "light_type": "highway",
        "light_height": 12,
        "sidewalk_enabled": False,
        "sidewalk_width": 0,
        "manhole_density": 0,
        "furniture_density": 0,
        "crosswalk_enabled": False,
        "lane_markings": True,
    },

    # Service/alley roads
    "service": {
        "light_spacing": 50,
        "light_type": "modern",
        "light_height": 5,
        "sidewalk_enabled": False,
        "sidewalk_width": 0,
        "manhole_density": 0.3,
        "furniture_density": 0,
        "crosswalk_enabled": False,
        "lane_markings": False,
    },

    # Parking lots
    "parking": {
        "light_spacing": 20,
        "light_type": "parking",
        "light_height": 8,
        "sidewalk_enabled": False,
        "sidewalk_width": 0,
        "manhole_density": 0.1,
        "furniture_density": 0,
        "crosswalk_enabled": False,
        "lane_markings": True,
    },
}


# =============================================================================
# GEOMETRY NODE GROUPS
# =============================================================================

def create_street_lights_node_group():
    """
    Create Geometry Nodes for placing street lights along roads.

    Places lights along road edges at regular intervals.
    """
    group_name = "Road_Street_Lights"

    if group_name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[group_name])

    print(f"Creating {group_name}...")

    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    nodes = group.nodes
    links = group.links

    # ========================================
    # INTERFACE
    # ========================================

    # Inputs
    group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name="Seed", in_out='INPUT', socket_type='NodeSocketInt')
    group.interface.new_socket(name="Spacing", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket(name="Pole Height", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket(name="Offset", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket(name="Enabled", in_out='INPUT', socket_type='NodeSocketBool')

    # Outputs
    group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Defaults
    for item in group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Seed":
                item.default_value = 42
            elif item.name == "Spacing":
                item.default_value = 30.0
                item.min_value = 10
                item.max_value = 100
                item.description = "Distance between lights (meters)"
            elif item.name == "Pole Height":
                item.default_value = 8.0
                item.min_value = 4
                item.max_value = 15
            elif item.name == "Offset":
                item.default_value = 2.0
                item.description = "Distance from road edge"
            elif item.name == "Enabled":
                item.default_value = True

    # ========================================
    # NODE LAYOUT
    # ========================================

    y_main = 0
    y_light = -400

    # Input/Output
    n_input = nodes.new('NodeGroupInput')
    n_input.location = (-1600, y_main)

    n_output = nodes.new('NodeGroupOutput')
    n_output.location = (1600, y_main)

    # ========================================
    # STREET LIGHT TEMPLATE
    # ========================================

    # Pole (cylinder)
    n_pole = nodes.new('GeometryNodeMeshCylinder')
    n_pole.location = (-200, y_light)
    n_pole.label = "Light Pole"
    n_pole.inputs["Radius Top"].default_value = 0.1
    n_pole.inputs["Radius Bottom"].default_value = 0.15
    n_pole.inputs["Depth"].default_value = 8.0  # Will be overridden
    n_pole.inputs["Vertices"].default_value = 8

    # Lamp head (cube)
    n_lamp = nodes.new('GeometryNodeMeshCube')
    n_lamp.location = (50, y_light)
    n_lamp.label = "Lamp Head"
    n_lamp.inputs["Size X"].default_value = 0.6
    n_lamp.inputs["Size Y"].default_value = 0.3
    n_lamp.inputs["Size Z"].default_value = 0.2

    # Transform lamp to top of pole
    n_lamp_transform = nodes.new('GeometryNodeTransform')
    n_lamp_transform.location = (250, y_light)
    n_lamp_transform.label = "Position Lamp"
    n_lamp_transform.inputs["Translation"].default_value = (0, 0, 8.1)

    # Join pole + lamp
    n_join_light = nodes.new('GeometryNodeJoinGeometry')
    n_join_light.location = (450, y_light)
    n_join_light.label = "Complete Light"

    # ========================================
    # RESAMPLE CURVE (for spacing points)
    # ========================================

    n_resample = nodes.new('GeometryNodeResampleCurve')
    n_resample.location = (-600, y_main + 100)
    n_resample.label = "Set Light Spacing"
    n_resample.mode = 'LENGTH'

    # Curve to points
    n_curve_to_points = nodes.new('GeometryNodeCurveToPoints')
    n_curve_to_points.location = (-350, y_main + 100)
    n_curve_to_points.label = "Get Points"
    n_curve_to_points.mode = 'EVALUATED'

    # ========================================
    # INSTANCE ON POINTS
    # ========================================

    n_instance = nodes.new('GeometryNodeInstanceOnPoints')
    n_instance.location = (700, y_main)
    n_instance.label = "Place Lights"

    # Offset from road
    n_offset = nodes.new('GeometryNodeSetPosition')
    n_offset.location = (950, y_main)
    n_offset.label = "Offset from Road"

    # ========================================
    # JOIN WITH ORIGINAL
    # ========================================

    n_join = nodes.new('GeometryNodeJoinGeometry')
    n_join.location = (1300, y_main)

    # ========================================
    # CONNECTIONS
    # ========================================

    # Light template
    links.new(n_pole.outputs["Mesh"], n_join_light.inputs["Geometry"])
    links.new(n_lamp.outputs["Mesh"], n_lamp_transform.inputs["Geometry"])
    links.new(n_lamp_transform.outputs["Geometry"], n_join_light.inputs["Geometry"])

    # Resample curve for spacing
    links.new(n_input.outputs["Geometry"], n_resample.inputs["Curve"])
    links.new(n_input.outputs["Spacing"], n_resample.inputs["Length"])

    # Get points
    links.new(n_resample.outputs["Curve"], n_curve_to_points.inputs["Curve"])

    # Instance
    links.new(n_curve_to_points.outputs["Points"], n_instance.inputs["Points"])
    links.new(n_join_light.outputs["Geometry"], n_instance.inputs["Instance"])

    # Offset
    links.new(n_instance.outputs["Instances"], n_offset.inputs["Geometry"])

    # Join
    links.new(n_input.outputs["Geometry"], n_join.inputs["Geometry"])
    links.new(n_offset.outputs["Geometry"], n_join.inputs["Geometry"])

    # Output
    links.new(n_join.outputs["Geometry"], n_output.inputs["Geometry"])

    print(f"  Created: {group_name}")
    return group


def create_sidewalk_node_group():
    """
    Create Geometry Nodes for adding sidewalks along roads.

    Extrudes geometry to create sidewalk on both sides.
    """
    group_name = "Road_Sidewalk"

    if group_name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[group_name])

    print(f"Creating {group_name}...")

    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    nodes = group.nodes
    links = group.links

    # ========================================
    # INTERFACE
    # ========================================

    group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name="Width", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket(name="Height", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket(name="Enabled", in_out='INPUT', socket_type='NodeSocketBool')

    group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    for item in group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Width":
                item.default_value = 2.0
                item.min_value = 0.5
                item.max_value = 6
            elif item.name == "Height":
                item.default_value = 0.15
                item.min_value = 0.05
                item.max_value = 0.3
            elif item.name == "Enabled":
                item.default_value = True

    # ========================================
    # NODES
    # ========================================

    y_main = 0

    n_input = nodes.new('NodeGroupInput')
    n_input.location = (-800, y_main)

    n_output = nodes.new('NodeGroupOutput')
    n_output.location = (800, y_main)

    # Extrude for sidewalk
    n_extrude = nodes.new('GeometryNodeExtrudeMesh')
    n_extrude.location = (-200, y_main)
    n_extrude.label = "Create Sidewalk"
    n_extrude.mode = 'EDGES'

    # Set Z position for curb height
    n_set_pos = nodes.new('GeometryNodeSetPosition')
    n_set_pos.location = (100, y_main)
    n_set_pos.label = "Curb Height"

    # Join
    n_join = nodes.new('GeometryNodeJoinGeometry')
    n_join.location = (500, y_main)

    # ========================================
    # CONNECTIONS
    # ========================================

    links.new(n_input.outputs["Geometry"], n_extrude.inputs["Mesh"])
    links.new(n_input.outputs["Width"], n_extrude.inputs["Offset Scale"])
    links.new(n_extrude.outputs["Mesh"], n_set_pos.inputs["Geometry"])
    links.new(n_input.outputs["Geometry"], n_join.inputs["Geometry"])
    links.new(n_set_pos.outputs["Geometry"], n_join.inputs["Geometry"])
    links.new(n_join.outputs["Geometry"], n_output.inputs["Geometry"])

    print(f"  Created: {group_name}")
    return group


def create_manhole_node_group():
    """
    Create Geometry Nodes for placing manhole covers on roads.
    """
    group_name = "Road_Manhole_Covers"

    if group_name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[group_name])

    print(f"Creating {group_name}...")

    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    nodes = group.nodes
    links = group.links

    # ========================================
    # INTERFACE
    # ========================================

    group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name="Seed", in_out='INPUT', socket_type='NodeSocketInt')
    group.interface.new_socket(name="Density", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket(name="Radius", in_out='INPUT', socket_type='NodeSocketFloat')

    group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    for item in group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Seed":
                item.default_value = 42
            elif item.name == "Density":
                item.default_value = 0.5
                item.min_value = 0
                item.max_value = 2
                item.description = "Higher = more manholes"
            elif item.name == "Radius":
                item.default_value = 0.3
                item.min_value = 0.2
                item.max_value = 0.5

    # ========================================
    # NODES
    # ========================================

    y_main = 0
    y_manhole = -400

    n_input = nodes.new('NodeGroupInput')
    n_input.location = (-1200, y_main)

    n_output = nodes.new('NodeGroupOutput')
    n_output.location = (1200, y_main)

    # Manhole cover (cylinder)
    n_manhole = nodes.new('GeometryNodeMeshCylinder')
    n_manhole.location = (-200, y_manhole)
    n_manhole.label = "Manhole Cover"
    n_manhole.inputs["Radius Top"].default_value = 0.3
    n_manhole.inputs["Radius Bottom"].default_value = 0.3
    n_manhole.inputs["Depth"].default_value = 0.02
    n_manhole.inputs["Vertices"].default_value = 16

    # Distribute points on road surface
    n_distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
    n_distribute.location = (-400, y_main)
    n_distribute.distribute_method = 'POISSON'
    n_distribute.label = "Distribute Manholes"

    # Instance
    n_instance = nodes.new('GeometryNodeInstanceOnPoints')
    n_instance.location = (200, y_main)
    n_instance.label = "Place Covers"

    # Join
    n_join = nodes.new('GeometryNodeJoinGeometry')
    n_join.location = (800, y_main)

    # ========================================
    # CONNECTIONS
    # ========================================

    links.new(n_input.outputs["Geometry"], n_distribute.inputs["Mesh"])
    links.new(n_input.outputs["Density"], n_distribute.inputs["Density Max"])
    links.new(n_input.outputs["Seed"], n_distribute.inputs["Seed"])

    links.new(n_distribute.outputs["Points"], n_instance.inputs["Points"])
    links.new(n_manhole.outputs["Mesh"], n_instance.inputs["Instance"])

    links.new(n_input.outputs["Geometry"], n_join.inputs["Geometry"])
    links.new(n_instance.outputs["Instances"], n_join.inputs["Geometry"])
    links.new(n_join.outputs["Geometry"], n_output.inputs["Geometry"])

    print(f"  Created: {group_name}")
    return group


def create_road_furniture_node_group():
    """
    Create Geometry Nodes for street furniture (benches, trash cans, bollards).
    """
    group_name = "Road_Furniture"

    if group_name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[group_name])

    print(f"Creating {group_name}...")

    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    nodes = group.nodes
    links = group.links

    # ========================================
    # INTERFACE
    # ========================================

    group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name="Seed", in_out='INPUT', socket_type='NodeSocketInt')
    group.interface.new_socket(name="Density", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket(name="Offset", in_out='INPUT', socket_type='NodeSocketFloat')

    group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    for item in group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Seed":
                item.default_value = 42
            elif item.name == "Density":
                item.default_value = 0.3
            elif item.name == "Offset":
                item.default_value = 1.5

    # ========================================
    # NODES - Simplified pass-through for now
    # ========================================

    n_input = nodes.new('NodeGroupInput')
    n_input.location = (-400, 0)

    n_output = nodes.new('NodeGroupOutput')
    n_output.location = (400, 0)

    # Pass through (furniture templates would be added here)
    links.new(n_input.outputs["Geometry"], n_output.inputs["Geometry"])

    print(f"  Created: {group_name}")
    return group


# =============================================================================
# APPLY TO ROADS
# =============================================================================

def get_road_override(obj: bpy.types.Object, property_name: str, global_default):
    """Get road property with override support."""
    override_key = f"road_{property_name}"
    if override_key in obj:
        return obj[override_key]

    if 'road_style' in obj:
        preset = ROAD_PRESETS.get(obj['road_style'], {})
        if property_name in preset:
            return preset[property_name]

    return global_default


def apply_geo_nodes_to_all_roads(
    global_light_spacing: float = 30.0,
    global_sidewalk_width: float = 2.0,
    global_manhole_density: float = 0.5,
):
    """
    Apply Geo Nodes to all road objects with override support.
    """
    print("\n" + "=" * 60)
    print("APPLYING GEOMETRY NODES TO ROADS")
    print("=" * 60)

    # Create node groups
    lights_group = create_street_lights_node_group()
    sidewalk_group = create_sidewalk_node_group()
    manhole_group = create_manhole_node_group()
    furniture_group = create_road_furniture_node_group()

    # Find all road objects
    roads = []
    for obj in bpy.context.scene.objects:
        if obj.get('road_class') or obj.get('highway'):
            roads.append(obj)

    print(f"\nFound {len(roads)} road objects")

    applied_lights = 0
    applied_sidewalks = 0
    applied_manholes = 0

    for obj in roads:
        # Get values (with overrides)
        light_spacing = get_road_override(obj, 'light_spacing', global_light_spacing)
        sidewalk_enabled = get_road_override(obj, 'sidewalk_enabled', True)
        sidewalk_width = get_road_override(obj, 'sidewalk_width', global_sidewalk_width)
        manhole_density = get_road_override(obj, 'manhole_density', global_manhole_density)

        # Apply street lights
        if lights_group:
            mod = obj.modifiers.new("Street_Lights", 'NODES')
            mod.node_group = lights_group
            mod['Input_2'] = hash(obj.name) % 100000  # Seed
            mod['Input_3'] = light_spacing
            mod['Input_4'] = get_road_override(obj, 'light_height', 8.0)
            mod['Input_5'] = 2.0  # Offset
            mod['Input_6'] = get_road_override(obj, 'light_spacing', 30) > 0  # Enabled
            applied_lights += 1

        # Apply sidewalks
        if sidewalk_group and sidewalk_enabled:
            mod = obj.modifiers.new("Sidewalk", 'NODES')
            mod.node_group = sidewalk_group
            mod['Input_2'] = sidewalk_width
            mod['Input_3'] = 0.15  # Curb height
            mod['Input_4'] = True
            applied_sidewalks += 1

        # Apply manholes
        if manhole_group and manhole_density > 0:
            mod = obj.modifiers.new("Manholes", 'NODES')
            mod.node_group = manhole_group
            mod['Input_2'] = hash(obj.name) % 100000
            mod['Input_3'] = manhole_density * 0.001
            mod['Input_4'] = 0.3
            applied_manholes += 1

    print(f"\n✓ Applied modifiers:")
    print(f"  - Street lights: {applied_lights}")
    print(f"  - Sidewalks: {applied_sidewalks}")
    print(f"  - Manholes: {applied_manholes}")

    return applied_lights


def set_road_style(obj: bpy.types.Object, style_name: str):
    """Set a road's style preset."""
    if style_name not in ROAD_PRESETS:
        print(f"Warning: Unknown style '{style_name}'")
        print(f"Available: {list(ROAD_PRESETS.keys())}")
        return

    obj['road_style'] = style_name
    print(f"Set {obj.name} to road style '{style_name}'")


def set_road_override(obj: bpy.types.Object, property_name: str, value):
    """Set a road override."""
    key = f"road_{property_name}"
    obj[key] = value
    print(f"Set {obj.name}.{key} = {value}")


def setup_road_styles():
    """Auto-apply road styles based on road type."""
    print("\n" + "=" * 60)
    print("SETTING UP ROAD STYLES")
    print("=" * 60)

    stats = {style: 0 for style in ROAD_PRESETS}

    for obj in bpy.context.scene.objects:
        if not (obj.get('road_class') or obj.get('highway')):
            continue

        road_class = obj.get('road_class', obj.get('highway', '')).lower()

        # Determine style from road class
        if 'primary' in road_class or 'trunk' in road_class:
            style = "urban_main"
        elif 'secondary' in road_class:
            style = "urban_main"
        elif 'residential' in road_class or 'tertiary' in road_class:
            style = "residential"
        elif 'motorway' in road_class:
            style = "highway"
        elif 'service' in road_class:
            style = "service"
        elif 'footway' in road_class or 'pedestrian' in road_class:
            style = "downtown"
        else:
            style = "residential"

        obj['road_style'] = style
        stats[style] += 1

    print("\nRoads by style:")
    for style, count in stats.items():
        if count > 0:
            print(f"  {style}: {count}")


def create_all_road_node_groups():
    """Create all road geometry node groups."""
    print("\n" + "=" * 60)
    print("CREATING ROAD GEOMETRY NODE GROUPS")
    print("=" * 60)

    create_street_lights_node_group()
    create_sidewalk_node_group()
    create_manhole_node_group()
    create_road_furniture_node_group()

    print("\nCreated node groups for roads")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Road Geo Nodes')
    parser.add_argument('--create', '-c', action='store_true', help='Create only')
    parser.add_argument('--apply', '-a', action='store_true', help='Apply to roads')
    parser.add_argument('--setup-styles', action='store_true', help='Auto-setup styles')
    parser.add_argument('--light-spacing', type=float, default=30.0)
    parser.add_argument('--sidewalk-width', type=float, default=2.0)

    args = parser.parse_args()

    if args.create:
        create_all_road_node_groups()
    elif args.apply:
        apply_geo_nodes_to_all_roads(
            global_light_spacing=args.light_spacing,
            global_sidewalk_width=args.sidewalk_width,
        )
        if args.setup_styles:
            setup_road_styles()
    else:
        create_all_road_node_groups()
        apply_geo_nodes_to_all_roads()
        if args.setup_styles:
            setup_road_styles()


if __name__ == '__main__':
    main()
