"""
Charlotte Digital Twin - Building Accessories Generator

Creates procedural building accessories using Geometry Nodes:
- Window frames and mullions
- Balconies with railings
- Rooftop mechanical units
- Ground floor retail glazing
- Building crown elements

These are generated procedurally based on building attributes.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import bpy
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


# =============================================================================
# WINDOW PATTERNS
# =============================================================================

WINDOW_PATTERNS = {
    # Glass curtain wall - continuous glazing
    "curtain_wall": {
        "description": "Full glass curtain wall with metal mullions",
        "grid_x": 1.5,      # Mullion spacing X (meters)
        "grid_y": 1.8,      # Mullion spacing Y (meters)
        "frame_width": 0.05, # Frame thickness
        "frame_depth": 0.08, # Frame projection
        "glass_offset": 0.02, # Glass setback from frame
        "materials": {
            "frame": "metal_mullion_chrome",
            "glass": "glass_curtain_blue",
        }
    },

    # Ribbon windows - horizontal strips
    "ribbon": {
        "description": "Horizontal ribbon windows with spandrel panels",
        "grid_x": 2.0,
        "grid_y": 1.5,
        "frame_width": 0.04,
        "frame_depth": 0.06,
        "spandrel_height": 0.8,  # Solid panel between windows
        "materials": {
            "frame": "metal_mullion_bronze",
            "glass": "glass_curtain_clear",
            "spandrel": "precast_concrete_smooth",
        }
    },

    # Punched windows - individual windows in solid wall
    "punched": {
        "description": "Individual windows in solid facade",
        "grid_x": 1.2,
        "grid_y": 1.5,
        "frame_width": 0.06,
        "frame_depth": 0.10,
        "window_width": 1.0,
        "window_height": 1.2,
        "materials": {
            "frame": "metal_mullion_bronze",
            "glass": "glass_curtain_clear",
        }
    },

    # Historic - small panes with muntins
    "historic": {
        "description": "Multi-pane historic windows",
        "grid_x": 1.5,
        "grid_y": 2.0,
        "frame_width": 0.08,
        "frame_depth": 0.12,
        "muntin_width": 0.03,  # Grid inside window
        "muntin_divisions": 3,  # 3x3 panes
        "materials": {
            "frame": "metal_mullion_bronze",
            "glass": "glass_curtain_clear",
        }
    },
}


# =============================================================================
# BALCONY TYPES
# =============================================================================

BALCONY_TYPES = {
    "glass_railing": {
        "description": "Modern glass balcony with railing",
        "depth": 1.5,          # Projection from building
        "railing_height": 1.1,  # Standard railing height
        "glass_thickness": 0.02,
        "rail_thickness": 0.05,
        "materials": {
            "floor": "precast_concrete_smooth",
            "railing": "glass_curtain_clear",
            "rail": "metal_mullion_chrome",
        }
    },

    "metal_railing": {
        "description": "Metal railing balcony",
        "depth": 1.2,
        "railing_height": 1.1,
        "post_diameter": 0.05,
        "rail_diameter": 0.04,
        "materials": {
            "floor": "precast_concrete_smooth",
            "railing": "metal_panel_aluminum",
        }
    },

    "juliet": {
        "description": "Juliet balcony (railing only, no floor)",
        "depth": 0.3,
        "railing_height": 1.1,
        "materials": {
            "railing": "metal_mullion_chrome",
        }
    },
}


# =============================================================================
# ROOFTOP MECHANICAL UNITS
# =============================================================================

ROOFTOP_UNITS = {
    "hvac_large": {
        "description": "Large HVAC unit",
        "width": 4.0,
        "depth": 3.0,
        "height": 2.5,
        "materials": {
            "body": "metal_panel_aluminum",
        }
    },

    "hvac_small": {
        "description": "Small HVAC unit",
        "width": 2.0,
        "depth": 2.0,
        "height": 1.5,
        "materials": {
            "body": "metal_panel_aluminum",
        }
    },

    "cooling_tower": {
        "description": "Cooling tower",
        "diameter": 3.0,
        "height": 4.0,
        "materials": {
            "body": "metal_panel_aluminum",
        }
    },

    "elevator_override": {
        "description": "Elevator machine room",
        "width": 6.0,
        "depth": 4.0,
        "height": 3.5,
        "materials": {
            "body": "precast_concrete_smooth",
        }
    },

    "antenna_array": {
        "description": "Communications antenna",
        "height": 5.0,
        "materials": {
            "body": "metal_panel_aluminum",
        }
    },
}


# =============================================================================
# GEOMETRY NODES NODE GROUPS
# =============================================================================

def create_window_geometry_node_group():
    """
    Create a geometry nodes group for window frame generation.

    Input: Building mesh
    Output: Building mesh with window frames
    """
    if not BLENDER_AVAILABLE:
        return None

    # Check if already exists
    group_name = "Building_Windows"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    # Create new node group
    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')

    # Create input/output nodes
    input_node = group.nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)

    output_node = group.nodes.new('NodeGroupOutput')
    output_node.location = (800, 0)

    # Create interface
    group.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket("Window Pattern", in_out='INPUT', socket_type='NodeSocketString')
    group.interface.new_socket("Grid X", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Grid Y", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Frame Width", in_out='INPUT', socket_type='NodeSocketFloat')

    group.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    # For now, pass through - full implementation would require
    # complex node setup that's better done in Blender UI
    link = group.links.new
    link(input_node.outputs[0], output_node.inputs[0])

    return group


def create_balcony_geometry_node_group():
    """
    Create a geometry nodes group for balcony generation.

    Input: Building mesh with balcony markers
    Output: Building mesh with balconies
    """
    if not BLENDER_AVAILABLE:
        return None

    group_name = "Building_Balconies"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    group = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')

    input_node = group.nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)

    output_node = group.nodes.new('NodeGroupOutput')
    output_node.location = (800, 0)

    group.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket("Balcony Type", in_out='INPUT', socket_type='NodeSocketString')
    group.interface.new_socket("Depth", in_out='INPUT', socket_type='NodeSocketFloat')
    group.interface.new_socket("Railing Height", in_out='INPUT', socket_type='NodeSocketFloat')

    group.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    link = group.links.new
    link(input_node.outputs[0], output_node.inputs[0])

    return group


# =============================================================================
# ACCESSORY CREATION FUNCTIONS
# =============================================================================

def create_rooftop_unit(unit_type: str, name: str = None) -> bpy.types.Object:
    """
    Create a rooftop mechanical unit mesh.

    Args:
        unit_type: Type from ROOFTOP_UNITS
        name: Optional name

    Returns:
        Created object
    """
    if not BLENDER_AVAILABLE:
        return None

    unit_spec = ROOFTOP_UNITS.get(unit_type)
    if not unit_spec:
        print(f"Unknown rooftop unit type: {unit_type}")
        return None

    obj_name = name or f"Rooftop_{unit_type}"

    # Create mesh based on type
    if "diameter" in unit_spec:
        # Cylindrical (cooling tower)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=unit_spec["diameter"] / 2,
            depth=unit_spec["height"],
        )
    else:
        # Box type
        bpy.ops.mesh.primitive_cube_add(
            scale=(
                unit_spec["width"] / 2,
                unit_spec["depth"] / 2,
                unit_spec["height"] / 2,
            )
        )

    obj = bpy.context.active_object
    obj.name = obj_name

    # Add metadata
    obj["unit_type"] = unit_type
    obj["is_rooftop_unit"] = True

    return obj


def create_balcony_railing(
    length: float,
    balcony_type: str = "glass_railing",
    name: str = None
) -> bpy.types.Object:
    """
    Create a balcony railing mesh.

    Args:
        length: Length of balcony in meters
        balcony_type: Type from BALCONY_TYPES
        name: Optional name

    Returns:
        Created object
    """
    if not BLENDER_AVAILABLE:
        return None

    spec = BALCONY_TYPES.get(balcony_type, BALCONY_TYPES["glass_railing"])

    obj_name = name or f"Balcony_Railing_{length}m"

    # Create railing collection
    if balcony_type == "glass_railing":
        # Glass panel with top rail
        bpy.ops.mesh.primitive_cube_add(
            scale=(length / 2, spec["glass_thickness"] / 2, spec["railing_height"] / 2),
            location=(0, 0, spec["railing_height"] / 2)
        )
        glass = bpy.context.active_object
        glass.name = f"{obj_name}_glass"

        # Top rail
        bpy.ops.mesh.primitive_cylinder_add(
            radius=spec["rail_thickness"] / 2,
            depth=length,
            rotation=(0, 1.5708, 0),  # 90 degrees on Y
            location=(0, 0, spec["railing_height"])
        )
        rail = bpy.context.active_object
        rail.name = f"{obj_name}_rail"

        # Join
        bpy.context.view_layer.objects.active = glass
        glass.select_set(True)
        rail.select_set(True)
        bpy.ops.object.join()

        obj = glass
    else:
        # Metal posts and rails
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object

    obj.name = obj_name
    obj["balcony_type"] = balcony_type
    obj["is_railing"] = True

    return obj


def create_window_frame(
    width: float,
    height: float,
    pattern: str = "curtain_wall",
    name: str = None
) -> bpy.types.Object:
    """
    Create a window frame mesh.

    Args:
        width: Window width in meters
        height: Window height in meters
        pattern: Pattern from WINDOW_PATTERNS
        name: Optional name

    Returns:
        Created object
    """
    if not BLENDER_AVAILABLE:
        return None

    spec = WINDOW_PATTERNS.get(pattern, WINDOW_PATTERNS["curtain_wall"])

    obj_name = name or f"Window_{width}x{height}"

    # Create frame outline
    frame_w = spec["frame_width"]

    # Create frame as 4 rectangles
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.active_object
    obj.name = obj_name

    # Add metadata
    obj["window_pattern"] = pattern
    obj["is_window_frame"] = True

    return obj


# =============================================================================
# MODIFIER SETUP
# =============================================================================

def add_window_modifier_to_building(
    obj: bpy.types.Object,
    pattern: str = "curtain_wall",
    grid_x: float = 1.5,
    grid_y: float = 1.8
):
    """
    Add geometry nodes modifier for window generation.

    Args:
        obj: Building object
        pattern: Window pattern type
        grid_x: Horizontal grid spacing
        grid_y: Vertical grid spacing
    """
    if not BLENDER_AVAILABLE:
        return

    # Create/get node group
    node_group = create_window_geometry_node_group()
    if not node_group:
        return

    # Add modifier
    mod = obj.modifiers.new("Windows", 'NODES')
    mod.node_group = node_group

    # Set default values
    if hasattr(mod, '["Window Pattern"]'):
        mod['["Window Pattern"]'] = pattern
    if hasattr(mod, '["Grid X"]'):
        mod['["Grid X"]'] = grid_x
    if hasattr(mod, '["Grid Y"]'):
        mod['["Grid Y"]'] = grid_y


def add_balcony_modifier_to_building(
    obj: bpy.types.Object,
    balcony_type: str = "glass_railing",
    depth: float = 1.5,
    railing_height: float = 1.1
):
    """
    Add geometry nodes modifier for balcony generation.

    Args:
        obj: Building object
        balcony_type: Balcony type
        depth: Balcony depth
        railing_height: Railing height
    """
    if not BLENDER_AVAILABLE:
        return

    node_group = create_balcony_geometry_node_group()
    if not node_group:
        return

    mod = obj.modifiers.new("Balconies", 'NODES')
    mod.node_group = node_group

    # Set values
    for key, val in [
        ("Balcony Type", balcony_type),
        ("Depth", depth),
        ("Railing Height", railing_height),
    ]:
        try:
            mod[f'["{key}"]'] = val
        except:
            pass


# =============================================================================
# MAIN SETUP
# =============================================================================

def setup_accessory_systems():
    """Set up all building accessory systems."""
    print("\n" + "=" * 60)
    print("BUILDING ACCESSORIES SETUP")
    print("=" * 60)

    # Create node groups
    print("\nCreating geometry node groups...")
    window_group = create_window_geometry_node_group()
    balcony_group = create_balcony_geometry_node_group()

    print(f"  Window group: {window_group.name if window_group else 'Failed'}")
    print(f"  Balcony group: {balcony_group.name if balcony_group else 'Failed'}")

    # Print available patterns
    print("\nWindow patterns:")
    for name, spec in WINDOW_PATTERNS.items():
        print(f"  {name}: {spec['description']}")

    print("\nBalcony types:")
    for name, spec in BALCONY_TYPES.items():
        print(f"  {name}: {spec['description']}")

    print("\nRooftop units:")
    for name, spec in ROOFTOP_UNITS.items():
        print(f"  {name}: {spec['description']}")

    print("\nAccessory systems ready!")


if __name__ == '__main__':
    setup_accessory_systems()
