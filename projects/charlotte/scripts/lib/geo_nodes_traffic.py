"""
Traffic Infrastructure Geometry Nodes Generator

Creates traffic signals, signs, and lane markers for driving game.

Usage:
    from lib.geo_nodes_traffic import (
        create_traffic_signal_node_group,
        create_traffic_sign_node_group,
        create_turn_arrow_node_group,
        generate_all_traffic_infrastructure,
    )
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass
import math

# Add lib to path for blender_gsd tools
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "lib"))

try:
    import bpy
    from mathutils import Vector, Matrix
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class SignalType(Enum):
    """Traffic signal types."""
    THREE_LIGHT = "3_light"           # Standard R/Y/G vertical
    FIVE_LIGHT = "5_light"            # With left/right arrows
    PEDESTRIAN = "pedestrian"         # Walk/Don't Walk
    SINGLE_RED = "single_red"         # Flashing red only


class SignType(Enum):
    """Traffic sign types."""
    STOP = "stop"
    YIELD = "yield"
    SPEED_LIMIT = "speed_limit"
    NO_ENTRY = "no_entry"
    NO_LEFT_TURN = "no_left_turn"
    NO_RIGHT_TURN = "no_right_turn"
    NO_U_TURN = "no_u_turn"
    ONE_WAY = "one_way"
    PARKING = "parking"
    DEAD_END = "dead_end"
    SPEED_BUMP = "speed_bump"


class ArrowType(Enum):
    """Turn lane arrow types."""
    STRAIGHT = "straight"
    LEFT = "left"
    RIGHT = "right"
    LEFT_STRAIGHT = "left_straight"   # Combined
    RIGHT_STRAIGHT = "right_straight"
    LEFT_RIGHT = "left_right"         # Both turns


@dataclass
class SignalSpec:
    """Traffic signal specifications."""
    pole_height: float = 5.0
    pole_diameter: float = 0.12
    mast_length: float = 3.0
    mast_diameter: float = 0.08
    housing_width: float = 0.5
    housing_height: float = 1.4
    housing_depth: float = 0.25
    light_diameter: float = 0.3
    visor_length: float = 0.3


@dataclass
class SignSpec:
    """Traffic sign specifications."""
    post_height: float = 2.1          # To bottom of sign
    post_diameter: float = 0.075
    sign_width: float = 0.75
    sign_height: float = 0.75
    thickness: float = 0.003          # Sheet metal thickness


@dataclass
class ArrowSpec:
    """Turn arrow specifications."""
    length: float = 2.0
    width: float = 0.5
    line_width: float = 0.15
    offset_from_stop: float = 15.0    # Meters before stop line


# =============================================================================
# SIGNAL SPECIFICATIONS
# =============================================================================

SIGNAL_SPECS = {
    SignalType.THREE_LIGHT: SignalSpec(
        pole_height=5.0,
        mast_length=3.0,
        housing_height=1.0,  # 3 lights
    ),
    SignalType.FIVE_LIGHT: SignalSpec(
        pole_height=5.5,
        mast_length=4.0,
        housing_height=1.4,  # 5 lights with arrows
    ),
    SignalType.PEDESTRIAN: SignalSpec(
        pole_height=3.5,
        mast_length=1.5,
        housing_height=0.5,
        housing_width=0.3,
    ),
    SignalType.SINGLE_RED: SignalSpec(
        pole_height=4.0,
        mast_length=0.0,  # No mast, pole-mounted
        housing_height=0.35,
        housing_width=0.35,
    ),
}

SIGN_SPECS = {
    SignType.STOP: SignSpec(
        sign_width=0.75,
        sign_height=0.75,
    ),
    SignType.YIELD: SignSpec(
        sign_width=0.9,
        sign_height=0.75,
    ),
    SignType.SPEED_LIMIT: SignSpec(
        sign_width=0.6,
        sign_height=0.6,
    ),
    SignType.NO_ENTRY: SignSpec(
        sign_width=0.6,
        sign_height=0.6,
    ),
}


# =============================================================================
# TRAFFIC SIGNAL NODE GROUP
# =============================================================================

def create_traffic_signal_node_group(name: str = "TrafficSignal_Generator") -> Optional[bpy.types.NodeGroup]:
    """
    Create geometry node group for traffic signals.

    Generates a complete traffic signal with:
    - Pole
    - Mast arm (optional)
    - Signal housing
    - Light positions (for emissive materials)
    - Visors

    Inputs:
        - Signal_Type (Int: 0=3-light, 1=5-light, 2=pedestrian, 3=single)
        - Pole_Height (Float)
        - Mast_Length (Float)
        - Rotation (Float, facing direction)

    Outputs:
        - Mesh geometry
    """
    if not BLENDER_AVAILABLE:
        return None

    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    node_group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nodes = node_group.nodes
    links = node_group.links

    # Define interface
    interface = node_group.interface
    interface.new_socket("Signal Type", socket_type="NodeSocketInt", in_out="INPUT")
    interface.new_socket("Pole Height", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Mast Length", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Rotation", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    # Set defaults
    node_group.inputs["Signal Type"].default_value = 0
    node_group.inputs["Pole Height"].default_value = 5.0
    node_group.inputs["Mast Length"].default_value = 3.0
    node_group.inputs["Rotation"].default_value = 0.0

    # Create nodes
    # Group Input
    gi = nodes.new("NodeGroupInput")
    gi.location = (0, 0)

    # Group Output
    go = nodes.new("NodeGroupOutput")
    go.location = (2000, 0)

    # ========================================
    # Create pole (cylinder)
    # ========================================
    pole = nodes.new("GeometryNodeMeshCylinder")
    pole.location = (200, 200)
    pole.inputs["Radius"].default_value = 0.06  # 12cm diameter
    pole.inputs["Depth"].default_value = 5.0
    pole.inputs["Vertices"].default_value = 16

    # Fill cap at bottom
    pole.inputs["Fill Cap"].default_value = True

    # Transform pole (stand upright)
    pole_transform = nodes.new("GeometryNodeTransform")
    pole_transform.location = (400, 200)
    pole_transform.inputs["Translation"].default_value = (0, 0, 2.5)
    pole_transform.inputs["Rotation"].default_value = (0, 0, 0)

    # ========================================
    # Create mast arm (cylinder)
    # ========================================
    mast = nodes.new("GeometryNodeMeshCylinder")
    mast.location = (200, 0)
    mast.inputs["Radius"].default_value = 0.04
    mast.inputs["Depth"].default_value = 3.0
    mast.inputs["Vertices"].default_value = 12

    # Transform mast (horizontal, at top of pole)
    mast_transform = nodes.new("GeometryNodeTransform")
    mast_transform.location = (400, 0)
    mast_transform.inputs["Translation"].default_value = (1.5, 0, 5.0)
    mast_transform.inputs["Rotation"].default_value = (1.5708, 0, 0)  # 90 degrees X

    # ========================================
    # Create signal housing (box)
    # ========================================
    housing = nodes.new("GeometryNodeMeshCube")
    housing.location = (200, -200)
    housing.inputs["Size X"].default_value = 0.5
    housing.inputs["Size Y"].default_value = 0.25
    housing.inputs["Size Z"].default_value = 1.0

    # Transform housing (at end of mast)
    housing_transform = nodes.new("GeometryNodeTransform")
    housing_transform.location = (400, -200)
    housing_transform.inputs["Translation"].default_value = (3.0, 0, 4.5)

    # ========================================
    # Create lights (spheres for positions)
    # ========================================
    # Light 1 (red)
    light1 = nodes.new("GeometryNodeMeshIcoSphere")
    light1.location = (200, -400)
    light1.inputs["Radius"].default_value = 0.12
    light1.inputs["Subdivisions"].default_value = 2

    light1_transform = nodes.new("GeometryNodeTransform")
    light1_transform.location = (400, -400)
    light1_transform.inputs["Translation"].default_value = (3.15, 0, 4.9)

    # Light 2 (yellow)
    light2 = nodes.new("GeometryNodeMeshIcoSphere")
    light2.location = (200, -500)
    light2.inputs["Radius"].default_value = 0.12
    light2.inputs["Subdivisions"].default_value = 2

    light2_transform = nodes.new("GeometryNodeTransform")
    light2_transform.location = (400, -500)
    light2_transform.inputs["Translation"].default_value = (3.15, 0, 4.5)

    # Light 3 (green)
    light3 = nodes.new("GeometryNodeMeshIcoSphere")
    light3.location = (200, -600)
    light3.inputs["Radius"].default_value = 0.12
    light3.inputs["Subdivisions"].default_value = 2

    light3_transform = nodes.new("GeometryNodeTransform")
    light3_transform.location = (400, -600)
    light3_transform.inputs["Translation"].default_value = (3.15, 0, 4.1)

    # ========================================
    # Join all geometry
    # ========================================
    join = nodes.new("GeometryNodeJoinGeometry")
    join.location = (800, 0)

    # Apply rotation to entire signal
    final_transform = nodes.new("GeometryNodeTransform")
    final_transform.location = (1000, 0)

    # Store signal type attribute
    store_type = nodes.new("GeometryNodeStoreNamedAttribute")
    store_type.location = (1200, 0)
    store_type.inputs["Name"].default_value = "signal_type"
    store_type.inputs["Data Type"].default_value = "INT"

    type_val = nodes.new("FunctionNodeInputInt")
    type_val.location = (1000, -200)

    # Store light zone attribute (for emissive)
    store_light = nodes.new("GeometryNodeStoreNamedAttribute")
    store_light.location = (1400, 0)
    store_light.inputs["Name"].default_value = "is_light"
    store_light.inputs["Data Type"].default_value = "BOOL"

    # Realize instances
    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (1600, 0)

    # ========================================
    # Wire connections
    # ========================================
    links.new(pole.outputs["Mesh"], pole_transform.inputs["Geometry"])
    links.new(mast.outputs["Mesh"], mast_transform.inputs["Geometry"])
    links.new(housing.outputs["Mesh"], housing_transform.inputs["Geometry"])

    links.new(light1.outputs["Mesh"], light1_transform.inputs["Geometry"])
    links.new(light2.outputs["Mesh"], light2_transform.inputs["Geometry"])
    links.new(light3.outputs["Mesh"], light3_transform.inputs["Geometry"])

    links.new(pole_transform.outputs["Geometry"], join.inputs["Geometry"])
    links.new(mast_transform.outputs["Geometry"], join.inputs["Geometry"])
    links.new(housing_transform.outputs["Geometry"], join.inputs["Geometry"])
    links.new(light1_transform.outputs["Geometry"], join.inputs["Geometry"])
    links.new(light2_transform.outputs["Geometry"], join.inputs["Geometry"])
    links.new(light3_transform.outputs["Geometry"], join.inputs["Geometry"])

    links.new(join.outputs["Geometry"], final_transform.inputs["Geometry"])
    links.new(gi.outputs["Rotation"], final_transform.inputs["Rotation"].subscript(2))  # Z rotation

    links.new(final_transform.outputs["Geometry"], store_type.inputs["Geometry"])
    links.new(gi.outputs["Signal Type"], type_val.inputs[0])
    links.new(type_val.outputs[0], store_type.inputs["Value"])

    links.new(store_type.outputs["Geometry"], store_light.inputs["Geometry"])
    links.new(store_light.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    return node_group


# =============================================================================
# TRAFFIC SIGN NODE GROUP
# =============================================================================

def create_traffic_sign_node_group(name: str = "TrafficSign_Generator") -> Optional[bpy.types.NodeGroup]:
    """
    Create geometry node group for traffic signs.

    Generates a sign with:
    - Post
    - Sign face (shape varies by type)
    - Optional backing

    Inputs:
        - Sign_Type (Int: 0=stop, 1=yield, 2=speed, 3=no_entry, etc.)
        - Post_Height (Float)
        - Sign_Width (Float)
        - Rotation (Float)

    Outputs:
        - Mesh geometry
    """
    if not BLENDER_AVAILABLE:
        return None

    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    node_group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nodes = node_group.nodes
    links = node_group.links

    # Define interface
    interface = node_group.interface
    interface.new_socket("Sign Type", socket_type="NodeSocketInt", in_out="INPUT")
    interface.new_socket("Post Height", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Sign Width", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Rotation", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    # Set defaults
    node_group.inputs["Sign Type"].default_value = 0
    node_group.inputs["Post Height"].default_value = 2.1
    node_group.inputs["Sign Width"].default_value = 0.75
    node_group.inputs["Rotation"].default_value = 0.0

    # Group Input/Output
    gi = nodes.new("NodeGroupInput")
    gi.location = (0, 0)

    go = nodes.new("NodeGroupOutput")
    go.location = (1600, 0)

    # ========================================
    # Create post (cylinder)
    # ========================================
    post = nodes.new("GeometryNodeMeshCylinder")
    post.location = (200, 100)
    post.inputs["Radius"].default_value = 0.0375  # 7.5cm diameter
    post.inputs["Depth"].default_value = 2.1
    post.inputs["Vertices"].default_value = 12

    post_transform = nodes.new("GeometryNodeTransform")
    post_transform.location = (400, 100)
    post_transform.inputs["Translation"].default_value = (0, 0, 1.05)

    # ========================================
    # Create sign face (cube - thin)
    # ========================================
    sign_face = nodes.new("GeometryNodeMeshCube")
    sign_face.location = (200, -100)
    sign_face.inputs["Size X"].default_value = 0.75
    sign_face.inputs["Size Y"].default_value = 0.003  # Thin metal
    sign_face.inputs["Size Z"].default_value = 0.75

    # Transform sign (at top of post)
    sign_transform = nodes.new("GeometryNodeTransform")
    sign_transform.location = (400, -100)
    sign_transform.inputs["Translation"].default_value = (0, 0, 2.5)

    # ========================================
    # Join and final transform
    # ========================================
    join = nodes.new("GeometryNodeJoinGeometry")
    join.location = (600, 0)

    final_transform = nodes.new("GeometryNodeTransform")
    final_transform.location = (800, 0)

    # Store sign type
    store_type = nodes.new("GeometryNodeStoreNamedAttribute")
    store_type.location = (1000, 0)
    store_type.inputs["Name"].default_value = "sign_type"
    store_type.inputs["Data Type"].default_value = "INT"

    type_val = nodes.new("FunctionNodeInputInt")
    type_val.location = (800, -200)

    # Realize
    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (1200, 0)

    # Wire
    links.new(post.outputs["Mesh"], post_transform.inputs["Geometry"])
    links.new(sign_face.outputs["Mesh"], sign_transform.inputs["Geometry"])

    links.new(post_transform.outputs["Geometry"], join.inputs["Geometry"])
    links.new(sign_transform.outputs["Geometry"], join.inputs["Geometry"])

    links.new(join.outputs["Geometry"], final_transform.inputs["Geometry"])
    links.new(gi.outputs["Rotation"], final_transform.inputs["Rotation"].subscript(2))

    links.new(final_transform.outputs["Geometry"], store_type.inputs["Geometry"])
    links.new(gi.outputs["Sign Type"], type_val.inputs[0])
    links.new(type_val.outputs[0], store_type.inputs["Value"])

    links.new(store_type.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    return node_group


# =============================================================================
# TURN ARROW NODE GROUP
# =============================================================================

def create_turn_arrow_node_group(name: str = "TurnArrow_Generator") -> Optional[bpy.types.NodeGroup]:
    """
    Create geometry node group for turn lane arrows.

    Generates painted arrows on road surface:
    - Straight
    - Left turn
    - Right turn
    - Combined arrows

    Inputs:
        - Arrow_Type (Int: 0=straight, 1=left, 2=right, 3=left+straight, etc.)
        - Arrow_Length (Float)
        - Arrow_Width (Float)
        - Line_Width (Float)

    Outputs:
        - Mesh (flat arrow geometry)
    """
    if not BLENDER_AVAILABLE:
        return None

    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    node_group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nodes = node_group.nodes
    links = node_group.links

    # Define interface
    interface = node_group.interface
    interface.new_socket("Arrow Type", socket_type="NodeSocketInt", in_out="INPUT")
    interface.new_socket("Arrow Length", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Arrow Width", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Line Width", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Rotation", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    # Defaults
    node_group.inputs["Arrow Type"].default_value = 0
    node_group.inputs["Arrow Length"].default_value = 2.0
    node_group.inputs["Arrow Width"].default_value = 0.5
    node_group.inputs["Line Width"].default_value = 0.15
    node_group.inputs["Rotation"].default_value = 0.0

    # Group Input/Output
    gi = nodes.new("NodeGroupInput")
    gi.location = (0, 0)

    go = nodes.new("NodeGroupOutput")
    go.location = (1400, 0)

    # ========================================
    # Create straight arrow (simplified)
    # This is a basic implementation - a real one would use curves
    # ========================================

    # Main shaft of arrow (rectangle)
    shaft = nodes.new("GeometryNodeMeshCube")
    shaft.location = (200, 0)
    shaft.inputs["Size X"].default_value = 0.15
    shaft.inputs["Size Y"].default_value = 0.001
    shaft.inputs["Size Z"].default_value = 1.2

    shaft_transform = nodes.new("GeometryNodeTransform")
    shaft_transform.location = (400, 0)
    shaft_transform.inputs["Translation"].default_value = (0, 0, 0)

    # Arrow head (triangle approximated with cube)
    head = nodes.new("GeometryNodeMeshCube")
    head.location = (200, -150)
    head.inputs["Size X"].default_value = 0.5
    head.inputs["Size Y"].default_value = 0.001
    head.inputs["Size Z"].default_value = 0.4

    head_transform = nodes.new("GeometryNodeTransform")
    head_transform.location = (400, -150)
    head_transform.inputs["Translation"].default_value = (0, 0, 0.8)

    # ========================================
    # Join and transform
    # ========================================
    join = nodes.new("GeometryNodeJoinGeometry")
    join.location = (600, 0)

    final_transform = nodes.new("GeometryNodeTransform")
    final_transform.location = (800, 0)

    # Store arrow type and mark as paint
    store_type = nodes.new("GeometryNodeStoreNamedAttribute")
    store_type.location = (1000, 0)
    store_type.inputs["Name"].default_value = "arrow_type"
    store_type.inputs["Data Type"].default_value = "INT"

    # Mark as road marking
    store_marking = nodes.new("GeometryNodeStoreNamedAttribute")
    store_marking.location = (1200, 0)
    store_marking.inputs["Name"].default_value = "material_zone"
    store_marking.inputs["Data Type"].default_value = "INT"

    zone_val = nodes.new("FunctionNodeInputInt")
    zone_val.location = (1000, -200)
    zone_val.outputs[0].default_value = 2  # Marking zone

    # Realize
    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (1400, 0)

    # Wire
    links.new(shaft.outputs["Mesh"], shaft_transform.inputs["Geometry"])
    links.new(head.outputs["Mesh"], head_transform.inputs["Geometry"])

    links.new(shaft_transform.outputs["Geometry"], join.inputs["Geometry"])
    links.new(head_transform.outputs["Geometry"], join.inputs["Geometry"])

    links.new(join.outputs["Geometry"], final_transform.inputs["Geometry"])
    links.new(gi.outputs["Rotation"], final_transform.inputs["Rotation"].subscript(2))

    links.new(final_transform.outputs["Geometry"], store_type.inputs["Geometry"])
    links.new(gi.outputs["Arrow Type"], store_type.inputs["Value"])

    links.new(store_type.outputs["Geometry"], store_marking.inputs["Geometry"])
    links.new(zone_val.outputs[0], store_marking.inputs["Value"])

    links.new(store_marking.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    return node_group


# =============================================================================
# PLACEMENT LOGIC
# =============================================================================

def detect_intersections_from_roads() -> List[Dict[str, Any]]:
    """
    Detect intersection positions from road curves.

    Finds where multiple roads meet and determines:
    - Position
    - Approaching road directions
    - Road types (for signal priority)
    """
    if not BLENDER_AVAILABLE:
        return []

    intersections = []
    road_curves = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'CURVE' and obj.get('road_class')
    ]

    # Collect all endpoints
    endpoints = {}  # position -> list of roads

    for curve in road_curves:
        if not curve.data.splines:
            continue

        spline = curve.data.splines[0]
        points = [curve.matrix_world @ Vector(p.co[:3]) for p in spline.points]

        if len(points) < 2:
            continue

        # Start point
        start_pos = points[0]
        key = f"{start_pos.x:.1f}_{start_pos.y:.1f}"
        if key not in endpoints:
            endpoints[key] = []
        endpoints[key].append({
            'curve': curve,
            'position': start_pos,
            'direction': (points[1] - points[0]).normalized(),
            'end_type': 'start'
        })

        # End point
        end_pos = points[-1]
        key = f"{end_pos.x:.1f}_{end_pos.y:.1f}"
        if key not in endpoints:
            endpoints[key] = []
        endpoints[key].append({
            'curve': curve,
            'position': end_pos,
            'direction': (points[-2] - points[-1]).normalized(),
            'end_type': 'end'
        })

    # Find intersections (3+ roads at same point)
    for key, roads in endpoints.items():
        if len(roads) >= 2:
            # Calculate average position
            avg_pos = Vector((
                sum(r['position'].x for r in roads) / len(roads),
                sum(r['position'].y for r in roads) / len(roads),
                sum(r['position'].z for r in roads) / len(roads)
            ))

            # Determine signal type based on road types
            road_classes = [r['curve'].get('road_class', 'local') for r in roads]
            has_primary = any(c in ['highway', 'arterial'] for c in road_classes)

            intersections.append({
                'position': avg_pos,
                'roads': roads,
                'road_count': len(roads),
                'has_primary': has_primary,
                'signal_type': SignalType.THREE_LIGHT if has_primary else SignalType.SINGLE_RED,
            })

    return intersections


def determine_sign_placement(road_curves: List[bpy.types.Object]) -> List[Dict[str, Any]]:
    """
    Determine where to place traffic signs.

    Rules:
    - STOP: At 4-way stops, T-intersections on minor road
    - YIELD: At roundabouts, merge lanes
    - SPEED_LIMIT: Every 500m, after major intersections
    """
    signs = []

    for curve in road_curves:
        if not curve.data.splines:
            continue

        highway_type = curve.get('highway_type', 'residential')
        road_name = curve.get('name', curve.name)

        # Speed limit signs
        if highway_type in ['primary', 'secondary', 'tertiary', 'residential']:
            speed_limits = {
                'primary': 45,
                'secondary': 35,
                'tertiary': 30,
                'residential': 25,
            }
            speed = speed_limits.get(highway_type, 25)

            # Place at start of road
            spline = curve.data.splines[0]
            points = [curve.matrix_world @ Vector(p.co[:3]) for p in spline.points]

            if len(points) >= 2:
                direction = (points[1] - points[0]).normalized()
                # Offset to right side of road
                right_offset = Vector((-direction.y, direction.x, 0)) * 5.0

                signs.append({
                    'type': SignType.SPEED_LIMIT,
                    'position': points[0] + right_offset,
                    'rotation': math.atan2(direction.y, direction.x),
                    'speed_value': speed,
                    'road_name': road_name,
                })

    return signs


def determine_arrow_placement(road_curves: List[bpy.types.Object]) -> List[Dict[str, Any]]:
    """
    Determine where to place turn lane arrows.

    Places arrows based on:
    - Lanes attribute
    - Turn lane tags
    - Intersection approaches
    """
    arrows = []

    for curve in road_curves:
        if not curve.data.splines:
            continue

        lanes = curve.get('lanes', 2)
        turn_lanes = curve.get('turn:lanes', '')

        if lanes < 2:
            continue

        spline = curve.data.splines[0]
        points = [curve.matrix_world @ Vector(p.co[:3]) for p in spline.points]

        if len(points) < 2:
            continue

        # For roads with explicit turn lanes
        if turn_lanes:
            lane_dirs = turn_lanes.split('|')
            road_width = curve.get('road_width', 7.0)
            lane_width = road_width / len(lane_dirs)

            direction = (points[-1] - points[0]).normalized()
            perpendicular = Vector((-direction.y, direction.x, 0))

            # Place arrow 15m before end of road
            arrow_pos = points[-1] - direction * 15.0

            for i, lane_dir in enumerate(lane_dirs):
                # Offset for this lane
                lane_offset = -road_width/2 + lane_width * (i + 0.5)
                lane_pos = arrow_pos + perpendicular * lane_offset

                # Determine arrow type
                if 'left' in lane_dir and 'through' in lane_dir:
                    arrow_type = ArrowType.LEFT_STRAIGHT
                elif 'right' in lane_dir and 'through' in lane_dir:
                    arrow_type = ArrowType.RIGHT_STRAIGHT
                elif 'left' in lane_dir and 'right' in lane_dir:
                    arrow_type = ArrowType.LEFT_RIGHT
                elif 'left' in lane_dir:
                    arrow_type = ArrowType.LEFT
                elif 'right' in lane_dir:
                    arrow_type = ArrowType.RIGHT
                else:
                    arrow_type = ArrowType.STRAIGHT

                arrows.append({
                    'type': arrow_type,
                    'position': lane_pos,
                    'rotation': math.atan2(direction.y, direction.x),
                    'road_name': curve.get('name', curve.name),
                })

    return arrows


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_all_traffic_infrastructure() -> Dict[str, int]:
    """
    Generate all traffic infrastructure for the scene.

    Returns:
        Dict with counts of generated objects
    """
    if not BLENDER_AVAILABLE:
        return {'error': 'Blender not available'}

    print("\n=== Generating Traffic Infrastructure ===")

    stats = {
        'signals': 0,
        'signs': 0,
        'arrows': 0,
        'errors': 0
    }

    # Create node groups
    signal_ng = create_traffic_signal_node_group()
    sign_ng = create_traffic_sign_node_group()
    arrow_ng = create_turn_arrow_node_group()

    if not signal_ng or not sign_ng or not arrow_ng:
        print("Failed to create node groups")
        return stats

    # Create collections
    collections = {}
    for name in ['Traffic_Signals', 'Traffic_Signs', 'Turn_Arrows']:
        if name not in bpy.data.collections:
            coll = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(coll)
        collections[name] = bpy.data.collections[name]

    # Get road curves
    road_curves = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'CURVE' and obj.get('road_class')
    ]

    # Generate signals at intersections
    print("Detecting intersections...")
    intersections = detect_intersections_from_roads()
    print(f"Found {len(intersections)} potential intersections")

    for intersection in intersections:
        if intersection['road_count'] >= 2 and intersection['has_primary']:
            # Create signal
            try:
                obj = bpy.data.objects.new(
                    f"Signal_{stats['signals']}",
                    None
                )
                obj.location = intersection['position']

                # Add geometry nodes modifier
                mod = obj.modifiers.new(name="Signal", type='NODES')
                mod.node_group = signal_ng
                mod["Signal Type"] = 0  # 3-light
                mod["Pole Height"] = 5.0
                mod["Mast Length"] = 3.0

                bpy.context.collection.objects.link(obj)
                collections['Traffic_Signals'].objects.link(obj)
                stats['signals'] += 1

            except Exception as e:
                print(f"Error creating signal: {e}")
                stats['errors'] += 1

    # Generate signs
    print("Determining sign placement...")
    signs = determine_sign_placement(road_curves)
    print(f"Placing {len(signs)} signs")

    for sign_data in signs:
        try:
            obj = bpy.data.objects.new(
                f"Sign_{sign_data['type'].value}_{stats['signs']}",
                None
            )
            obj.location = sign_data['position']
            obj.rotation_euler[2] = sign_data['rotation']

            mod = obj.modifiers.new(name="Sign", type='NODES')
            mod.node_group = sign_ng
            mod["Sign Type"] = list(SignType).index(sign_data['type'])

            bpy.context.collection.objects.link(obj)
            collections['Traffic_Signs'].objects.link(obj)
            stats['signs'] += 1

        except Exception as e:
            print(f"Error creating sign: {e}")
            stats['errors'] += 1

    # Generate turn arrows
    print("Determining arrow placement...")
    arrows = determine_arrow_placement(road_curves)
    print(f"Placing {len(arrows)} turn arrows")

    for arrow_data in arrows:
        try:
            obj = bpy.data.objects.new(
                f"Arrow_{arrow_data['type'].value}_{stats['arrows']}",
                None
            )
            obj.location = arrow_data['position']
            obj.location.z = 0.02  # Slightly above road
            obj.rotation_euler[2] = arrow_data['rotation']

            mod = obj.modifiers.new(name="Arrow", type='NODES')
            mod.node_group = arrow_ng
            mod["Arrow Type"] = list(ArrowType).index(arrow_data['type'])

            bpy.context.collection.objects.link(obj)
            collections['Turn_Arrows'].objects.link(obj)
            stats['arrows'] += 1

        except Exception as e:
            print(f"Error creating arrow: {e}")
            stats['errors'] += 1

    print(f"\n=== Summary ===")
    print(f"Traffic signals: {stats['signals']}")
    print(f"Traffic signs: {stats['signs']}")
    print(f"Turn arrows: {stats['arrows']}")
    print(f"Errors: {stats['errors']}")

    return stats


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    generate_all_traffic_infrastructure()
