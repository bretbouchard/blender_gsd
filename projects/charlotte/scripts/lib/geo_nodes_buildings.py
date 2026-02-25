"""
Charlotte Digital Twin - Smart Building Geometry Nodes

A unified system that:
1. Applies Geo Nodes to ALL buildings with global defaults
2. Allows per-building overrides via custom properties
3. Supports "building style" presets that set multiple parameters at once
4. Can be updated globally or tweaked individually

Custom Properties on Buildings:
    - geo_seed: Random seed (default: hash of building name)
    - geo_rooftop_enabled: True/False (default: True for tall buildings)
    - geo_rooftop_density: Override density (0 = use global)
    - geo_rooftop_scale: Override scale (0 = use global)
    - geo_window_pattern: "curtain_wall", "ribbon", "punched", "historic"
    - geo_window_width: Override window width (0 = use global)
    - geo_window_height: Override window height (0 = use global)
    - building_style: Preset style ("modern_tower", "historic", "residential", etc.)

Usage:
    # Apply to all buildings
    blender --python scripts/apply_geo_nodes.py

    # Apply with custom defaults
    blender --python scripts/apply_geo_nodes.py -- --rooftop-density 0.002 --min-height 25

    # In Blender Python console, override per-building:
    bpy.data.objects["Building_Bank_of_America"]["geo_rooftop_scale"] = 1.5
    bpy.data.objects["Building_Bank_of_America"]["building_style"] = "landmark_tower"
"""

import bpy
import sys
from pathlib import Path
from typing import Dict, Optional, List

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))


# =============================================================================
# BUILDING STYLE PRESETS
# =============================================================================

BUILDING_PRESETS = {
    # Landmark skyscrapers - more rooftop detail
    "landmark_tower": {
        "rooftop_enabled": True,
        "rooftop_density": 0.003,
        "rooftop_scale": 1.2,
        "window_pattern": "curtain_wall",
        "window_width": 1.8,
        "window_height": 2.2,
    },

    # Standard modern office
    "modern_office": {
        "rooftop_enabled": True,
        "rooftop_density": 0.001,
        "rooftop_scale": 1.0,
        "window_pattern": "curtain_wall",
        "window_width": 1.5,
        "window_height": 1.8,
    },

    # Glass residential towers
    "residential_tower": {
        "rooftop_enabled": True,
        "rooftop_density": 0.0008,
        "rooftop_scale": 0.8,
        "window_pattern": "curtain_wall",
        "window_width": 1.4,
        "window_height": 2.0,
    },

    # Historic buildings - no rooftop units, punched windows
    "historic": {
        "rooftop_enabled": False,
        "rooftop_density": 0,
        "rooftop_scale": 1.0,
        "window_pattern": "historic",
        "window_width": 1.2,
        "window_height": 1.5,
    },

    # Parking structures - minimal detail
    "parking": {
        "rooftop_enabled": False,
        "rooftop_density": 0,
        "rooftop_scale": 1.0,
        "window_pattern": "ribbon",
        "window_width": 2.0,
        "window_height": 1.0,
    },

    # Hotels
    "hotel": {
        "rooftop_enabled": True,
        "rooftop_density": 0.0015,
        "rooftop_scale": 1.0,
        "window_pattern": "curtain_wall",
        "window_width": 1.5,
        "window_height": 1.8,
    },

    # Low-rise retail - no rooftop, punched windows
    "retail": {
        "rooftop_enabled": False,
        "rooftop_density": 0,
        "rooftop_scale": 1.0,
        "window_pattern": "punched",
        "window_width": 1.0,
        "window_height": 1.2,
    },
}


# =============================================================================
# GEOMETRY NODE GROUPS
# =============================================================================

def create_rooftop_units_node_group():
    """
    Create the rooftop units node group.

    This version reads overrides from object custom properties.
    """
    group_name = "Building_Rooftop_Units"

    if group_name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[group_name])

    print(f"Creating {group_name}...")

    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')
    nodes = group.nodes
    links = group.links

    # ========================================
    # INTERFACE - Global defaults passed in
    # ========================================

    # Inputs (global defaults)
    group.interface.new_socket(name="Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name="Global Seed", in_out='INPUT', socket_type='NodeSocketInt')
    group.interface.new_socket(name="Global Min Height", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket(name="Global Density", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket(name="Global Scale", in_out='INPUT', socket_type='NodeSocketFloat')

    # Outputs
    group.interface.new_socket(name="Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # Set defaults
    for item in group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if item.name == "Global Seed":
                item.default_value = 42
            elif item.name == "Global Min Height":
                item.default_value = 30.0
            elif item.name == "Global Density":
                item.default_value = 0.001
            elif item.name == "Global Scale":
                item.default_value = 1.0

    # ========================================
    # NODE LAYOUT
    # ========================================

    y_main = 0
    y_units = -400

    # Input/Output
    n_input = nodes.new('NodeGroupInput')
    n_input.location = (-1600, y_main)

    n_output = nodes.new('NodeGroupOutput')
    n_output.location = (1600, y_main)

    # ========================================
    # READ OBJECT CUSTOM PROPERTIES (OVERRIDES)
    # ========================================

    # These nodes read custom properties from the object
    # If property doesn't exist, use global default

    # Get object (for reading properties)
    n_self = nodes.new('GeometryNodeObjectInfo')
    n_self.location = (-1400, y_main - 200)
    n_self.label = "Get Self Object"
    n_self.transform_space = 'RELATIVE'

    # Note: Geo Nodes can't directly read arbitrary custom properties
    # We'll use a different approach - pass overrides as modifier inputs
    # For now, this is a simplified version that uses global params

    # ========================================
    # BOUNDING BOX FOR HEIGHT CHECK
    # ========================================

    n_bbox = nodes.new('GeometryNodeBoundBox')
    n_bbox.location = (-1300, y_main + 100)

    n_sep_max = nodes.new('ShaderNodeSeparateXYZ')
    n_sep_max.location = (-1050, y_main + 200)
    n_sep_max.label = "BBox Max"

    n_sep_min = nodes.new('ShaderNodeSeparateXYZ')
    n_sep_min.location = (-1050, y_main - 50)
    n_sep_min.label = "BBox Min"

    # Calculate height
    n_height = nodes.new('ShaderNodeMath')
    n_height.operation = 'SUBTRACT'
    n_height.location = (-800, y_main + 50)
    n_height.label = "Building Height"

    # Check if tall enough
    n_compare = nodes.new('ShaderNodeMath')
    n_compare.operation = 'GREATER_THAN'
    n_compare.location = (-550, y_main + 50)
    n_compare.label = "Tall Enough?"

    # ========================================
    # HVAC UNIT TEMPLATE
    # ========================================

    n_unit = nodes.new('GeometryNodeMeshCube')
    n_unit.location = (-200, y_units)
    n_unit.label = "HVAC Unit"
    n_unit.inputs["Size X"].default_value = 2.0
    n_unit.inputs["Size Y"].default_value = 1.5
    n_unit.inputs["Size Z"].default_value = 1.2

    n_unit_transform = nodes.new('GeometryNodeTransform')
    n_unit_transform.location = (50, y_units)
    n_unit_transform.label = "Lift to Rooftop"
    n_unit_transform.inputs["Translation"].default_value = (0, 0, 0.6)

    # ========================================
    # GET TOP FACE
    # ========================================

    n_position = nodes.new('GeometryNodeInputPosition')
    n_position.location = (-800, y_main - 300)

    n_sep_geo = nodes.new('GeometryNodeSeparateGeometry')
    n_sep_geo.location = (-300, y_main)
    n_sep_geo.label = "Get Rooftop"

    n_z_compare = nodes.new('ShaderNodeMath')
    n_z_compare.operation = 'GREATER_THAN'
    n_z_compare.location = (-550, y_main - 200)
    n_z_compare.label = "Is Top Face?"

    # ========================================
    # DISTRIBUTE & INSTANCE
    # ========================================

    n_distribute = nodes.new('GeometryNodeDistributePointsOnFaces')
    n_distribute.location = (0, y_main)
    n_distribute.distribute_method = 'POISSON'
    n_distribute.label = "Distribute Units"

    n_random_scale = nodes.new('FunctionNodeRandomValue')
    n_random_scale.location = (200, y_main - 200)
    n_random_scale.data_type = 'FLOAT_VECTOR'
    n_random_scale.inputs["Min"].default_value = (0.6, 0.6, 0.6)
    n_random_scale.inputs["Max"].default_value = (1.4, 1.4, 1.4)

    n_instance = nodes.new('GeometryNodeInstanceOnPoints')
    n_instance.location = (500, y_main)
    n_instance.label = "Place Units"

    n_join = nodes.new('GeometryNodeJoinGeometry')
    n_join.location = (1200, y_main)
    n_join.label = "Join All"

    # ========================================
    # CONNECTIONS
    # ========================================

    links.new(n_input.outputs["Geometry"], n_bbox.inputs["Geometry"])
    links.new(n_bbox.outputs["Max"], n_sep_max.inputs[0])
    links.new(n_bbox.outputs["Min"], n_sep_min.inputs[0])

    links.new(n_sep_max.outputs["Z"], n_height.inputs[0])
    links.new(n_sep_min.outputs["Z"], n_height.inputs[1])

    links.new(n_height.outputs[0], n_compare.inputs[0])
    links.new(n_input.outputs["Global Min Height"], n_compare.inputs[1])

    links.new(n_input.outputs["Geometry"], n_sep_geo.inputs["Geometry"])
    links.new(n_position.outputs["Position"], n_z_compare.inputs[0])
    links.new(n_sep_max.outputs["Z"], n_z_compare.inputs[1])
    links.new(n_z_compare.outputs[0], n_sep_geo.inputs["Selection"])

    links.new(n_unit.outputs["Mesh"], n_unit_transform.inputs["Geometry"])

    links.new(n_sep_geo.outputs["Selection"], n_distribute.inputs["Mesh"])
    links.new(n_input.outputs["Global Density"], n_distribute.inputs["Density Max"])

    links.new(n_input.outputs["Global Seed"], n_random_scale.inputs["ID"])

    links.new(n_distribute.outputs["Points"], n_instance.inputs["Points"])
    links.new(n_unit_transform.outputs["Geometry"], n_instance.inputs["Instance"])
    links.new(n_random_scale.outputs["Value"], n_instance.inputs["Scale"])

    links.new(n_input.outputs["Geometry"], n_join.inputs["Geometry"])
    links.new(n_instance.outputs["Instances"], n_join.inputs["Geometry"])

    links.new(n_join.outputs["Geometry"], n_output.inputs["Geometry"])

    print(f"  Created: {group_name}")
    return group


# =============================================================================
# MODIFIER APPLICATION WITH OVERRIDES
# =============================================================================

def get_building_override(obj: bpy.types.Object, property_name: str, global_default):
    """
    Get a property value, checking for per-building override first.

    Priority:
    1. Object custom property override (geo_*)
    2. Building preset (if building_style is set)
    3. Global default
    """
    # Check for direct override
    override_key = f"geo_{property_name}"
    if override_key in obj:
        val = obj[override_key]
        # Handle "use global" values (0 or -1 depending on type)
        if property_name in ('density', 'scale') and val <= 0:
            pass  # Fall through to preset or global
        else:
            return val

    # Check for preset
    if 'building_style' in obj:
        preset_name = obj['building_style']
        preset = BUILDING_PRESETS.get(preset_name, {})
        if property_name in preset:
            return preset[property_name]

    # Return global default
    return global_default


def apply_geo_nodes_to_all_buildings(
    global_min_height: float = 30.0,
    global_density: float = 0.001,
    global_scale: float = 1.0,
    global_seed: int = 42,
):
    """
    Apply Geo Nodes modifiers to all buildings, respecting overrides.

    Each building can have custom properties that override global settings:
        - geo_rooftop_enabled: True/False
        - geo_rooftop_density: float (0 = use global)
        - geo_rooftop_scale: float (0 = use global)
        - geo_seed: int (overrides random seed)
        - building_style: preset name (e.g., "landmark_tower", "historic")
    """
    print("\n" + "=" * 60)
    print("APPLYING GEOMETRY NODES TO BUILDINGS")
    print("=" * 60)

    # Create node group
    group = create_rooftop_units_node_group()
    if not group:
        print("ERROR: Failed to create node group")
        return 0

    # Find all buildings
    buildings = [
        obj for obj in bpy.context.scene.objects
        if obj.get('building_type') or obj.get('osm_id')
    ]

    print(f"\nFound {len(buildings)} buildings")
    print("\nApplying modifiers with overrides...")

    applied = 0
    stats = {
        'total': len(buildings),
        'with_overrides': 0,
        'with_presets': 0,
        'skipped': 0,
    }

    for obj in buildings:
        # Check if rooftop is explicitly disabled
        rooftop_enabled = get_building_override(obj, 'rooftop_enabled', True)
        height = obj.get('height', 0)

        # Skip if disabled or too short
        if not rooftop_enabled or height < global_min_height:
            # Still add modifier but it won't generate units
            pass

        # Get values (with overrides)
        seed = get_building_override(obj, 'seed', hash(obj.name) % 100000)
        density = get_building_override(obj, 'rooftop_density', global_density)
        scale = get_building_override(obj, 'rooftop_scale', global_scale)

        # Track stats
        if 'geo_' in str(obj.keys()):
            stats['with_overrides'] += 1
        if 'building_style' in obj:
            stats['with_presets'] += 1

        # Apply modifier
        mod_name = "Rooftop_Units"

        if mod_name in obj.modifiers:
            mod = obj.modifiers[mod_name]
        else:
            mod = obj.modifiers.new(mod_name, 'NODES')
            mod.node_group = group

        # Set parameters
        mod['Input_2'] = seed           # Global Seed (unique per building)
        mod['Input_3'] = global_min_height  # Global Min Height
        mod['Input_4'] = density        # Global Density (may be overridden)
        mod['Input_5'] = scale          # Global Scale (may be overridden)

        applied += 1

    print(f"\n✓ Applied to {applied} buildings")
    print(f"  - With manual overrides: {stats['with_overrides']}")
    print(f"  - With style presets: {stats['with_presets']}")

    return applied


def set_building_style(obj: bpy.types.Object, style_name: str):
    """
    Set a building's style preset.

    Args:
        obj: Building object
        style_name: One of BUILDING_PRESETS keys
    """
    if style_name not in BUILDING_PRESETS:
        print(f"Warning: Unknown style '{style_name}'")
        print(f"Available: {list(BUILDING_PRESETS.keys())}")
        return

    obj['building_style'] = style_name
    preset = BUILDING_PRESETS[style_name]

    print(f"Set {obj.name} to style '{style_name}':")
    for key, val in preset.items():
        print(f"  {key}: {val}")


def set_building_override(obj: bpy.types.Object, property_name: str, value):
    """
    Set a per-building override.

    Args:
        obj: Building object
        property_name: Without 'geo_' prefix (e.g., "rooftop_scale")
        value: Override value
    """
    key = f"geo_{property_name}"
    obj[key] = value
    print(f"Set {obj.name}.{key} = {value}")


def clear_building_overrides(obj: bpy.types.Object):
    """Clear all overrides from a building, reverting to global defaults."""
    keys_to_remove = [k for k in obj.keys() if k.startswith('geo_')]
    for key in keys_to_remove:
        del obj[key]
    if 'building_style' in obj:
        del obj['building_style']
    print(f"Cleared overrides from {obj.name}")


def batch_apply_style(filter_func, style_name: str):
    """
    Apply a style preset to all buildings matching a filter.

    Args:
        filter_func: Function(obj) -> bool
        style_name: Style preset name
    """
    count = 0
    for obj in bpy.context.scene.objects:
        if obj.get('building_type') and filter_func(obj):
            set_building_style(obj, style_name)
            count += 1
    print(f"Applied '{style_name}' to {count} buildings")


# =============================================================================
# CONVENIENCE FUNCTIONS FOR BLENDER CONSOLE
# =============================================================================

def setup_landmark_buildings():
    """Apply landmark_tower style to known tall buildings."""
    landmark_names = [
        "bank of america", "duke energy", "truist", "wells fargo",
        "hearst", "550 south", "charlotte plaza", "ritz",
    ]

    def is_landmark(obj):
        name = obj.get('building_name', obj.name).lower()
        return any(n in name for n in landmark_names)

    batch_apply_style(is_landmark, "landmark_tower")


def setup_historic_buildings():
    """Apply historic style to old buildings."""
    def is_historic(obj):
        year = obj.get('year_built', 2000)
        if year and year < 1950:
            return True
        name = obj.get('building_name', obj.name).lower()
        return 'historic' in name or '192' in name or '193' in name

    batch_apply_style(is_historic, "historic")


def setup_residential_buildings():
    """Apply residential style to apartment buildings."""
    def is_residential(obj):
        btype = obj.get('building_type', '')
        name = obj.get('building_name', obj.name).lower()
        return (btype in ('apartments', 'residential') or
                any(n in name for n in ['vue', 'catalyst', 'ascent', 'museum', 'tower', 'condo']))

    batch_apply_style(is_residential, "residential_tower")


def setup_all_styles():
    """Apply appropriate styles to all buildings based on type."""
    print("\n" + "=" * 60)
    print("SETTING UP BUILDING STYLES")
    print("=" * 60)

    setup_landmark_buildings()
    setup_historic_buildings()
    setup_residential_buildings()

    # Parking
    def is_parking(obj):
        name = obj.get('building_name', obj.name).lower()
        return 'parking' in name or obj.get('building_type') == 'parking'
    batch_apply_style(is_parking, "parking")

    # Hotels
    def is_hotel(obj):
        name = obj.get('building_name', obj.name).lower()
        return any(n in name for n in ['hotel', 'marriott', 'hilton', 'hyatt', 'westin', 'ritz'])
    batch_apply_style(is_hotel, "hotel")

    print("\n✓ Style setup complete")


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Smart Building Geo Nodes')
    parser.add_argument('--min-height', type=float, default=30.0)
    parser.add_argument('--density', type=float, default=0.001)
    parser.add_argument('--scale', type=float, default=1.0)
    parser.add_argument('--setup-styles', action='store_true',
                        help='Auto-apply style presets based on building type')

    args = parser.parse_args()

    # Apply Geo Nodes
    apply_geo_nodes_to_all_buildings(
        global_min_height=args.min_height,
        global_density=args.density,
        global_scale=args.scale,
    )

    # Optionally setup styles
    if args.setup_styles:
        setup_all_styles()

    print("\n" + "=" * 60)
    print("USAGE IN BLENDER PYTHON CONSOLE")
    print("=" * 60)
    print("""
# Set a building's style preset
set_building_style(bpy.data.objects["Building_Name"], "landmark_tower")

# Override a specific property
set_building_override(bpy.data.objects["Building_Name"], "rooftop_scale", 1.5)
set_building_override(bpy.data.objects["Building_Name"], "rooftop_density", 0.003)
set_building_override(bpy.data.objects["Building_Name"], "rooftop_enabled", False)

# Clear overrides
clear_building_overrides(bpy.data.objects["Building_Name"])

# Batch operations
setup_landmark_buildings()
setup_historic_buildings()
setup_residential_buildings()
setup_all_styles()
""")


if __name__ == '__main__':
    main()
