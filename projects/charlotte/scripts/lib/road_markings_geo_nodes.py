"""
Charlotte Digital Twin - Comprehensive Road Markings Generator

Geometry nodes and Python generators for all road markings:
- Center lines (yellow double solid)
- Lane dividers (white dashed)
- Edge lines (white solid)
- Crosswalks
- Stop lines
- Street lights
- Manholes
- Traffic signals
"""

import bpy
import bmesh
from mathutils import Vector
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import math

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))
from lib.road_markings import (
    estimate_road_width,
    MarkingType,
    MARKING_SPECS,
    get_marking_rules,
    get_street_light_spec,
    MANHOLE_SPEC,
    get_traffic_signal_spec,
    COLOR_WHITE,
    COLOR_YELLOW,
)


# =============================================================================
# MARKING MESH GENERATORS
# =============================================================================

def create_center_line_mesh(width: float = 0.15, double: bool = True) -> bpy.types.Mesh:
    """
    Create a center line marking mesh.

    Args:
        width: Line width in meters
        double: If True, create double line (two parallel lines)
    """
    mesh = bpy.data.meshes.new("CenterLine")

    vertices = []
    faces = []

    if double:
        # Double yellow line: two 15cm lines with 10cm gap
        gap = 0.10
        # Left line
        vertices.extend([
            (-gap/2 - width, 0, 0.01),
            (-gap/2, 0, 0.01),
            (-gap/2, 1.0, 0.01),
            (-gap/2 - width, 1.0, 0.01),
        ])
        faces.append((0, 1, 2, 3))

        # Right line
        vertices.extend([
            (gap/2, 0, 0.01),
            (gap/2 + width, 0, 0.01),
            (gap/2 + width, 1.0, 0.01),
            (gap/2, 1.0, 0.01),
        ])
        faces.append((4, 5, 6, 7))
    else:
        # Single line
        vertices.extend([
            (-width/2, 0, 0.01),
            (width/2, 0, 0.01),
            (width/2, 1.0, 0.01),
            (-width/2, 1.0, 0.01),
        ])
        faces.append((0, 1, 2, 3))

    mesh.from_pydata(vertices, [], faces)
    return mesh


def create_lane_divider_mesh(width: float = 0.15, length: float = 3.0) -> bpy.types.Mesh:
    """Create a lane divider dash mesh."""
    mesh = bpy.data.meshes.new("LaneDivider")

    vertices = [
        (-width/2, 0, 0.01),
        (width/2, 0, 0.01),
        (width/2, length, 0.01),
        (-width/2, length, 0.01),
    ]
    faces = [(0, 1, 2, 3)]

    mesh.from_pydata(vertices, [], faces)
    return mesh


def create_edge_line_mesh(width: float = 0.20) -> bpy.types.Mesh:
    """Create an edge line marking mesh (continuous)."""
    mesh = bpy.data.meshes.new("EdgeLine")

    vertices = [
        (0, 0, 0.01),
        (width, 0, 0.01),
        (width, 1.0, 0.01),
        (0, 1.0, 0.01),
    ]
    faces = [(0, 1, 2, 3)]

    mesh.from_pydata(vertices, [], faces)
    return mesh


def create_crosswalk_mesh(road_width: float, length: float = 3.0) -> bpy.types.Mesh:
    """Create a zebra crosswalk mesh scaled to road width."""
    mesh = bpy.data.meshes.new("Crosswalk")

    stripe_width = 0.40
    gap_width = 0.60
    num_stripes = int(road_width / (stripe_width + gap_width)) + 1

    vertices = []
    faces = []

    current_x = -road_width / 2

    for i in range(num_stripes):
        x1 = current_x
        x2 = current_x + stripe_width
        y1 = 0
        y2 = length

        v_base = len(vertices)
        vertices.extend([
            (x1, y1, 0.02),
            (x2, y1, 0.02),
            (x2, y2, 0.02),
            (x1, y2, 0.02),
        ])
        faces.append((v_base, v_base + 1, v_base + 2, v_base + 3))

        current_x += stripe_width + gap_width

    mesh.from_pydata(vertices, [], faces)
    return mesh


def create_stop_line_mesh(road_width: float, thickness: float = 0.60) -> bpy.types.Mesh:
    """Create a stop line mesh across road width."""
    mesh = bpy.data.meshes.new("StopLine")

    vertices = [
        (-road_width/2, 0, 0.02),
        (road_width/2, 0, 0.02),
        (road_width/2, thickness, 0.02),
        (-road_width/2, thickness, 0.02),
    ]
    faces = [(0, 1, 2, 3)]

    mesh.from_pydata(vertices, [], faces)
    return mesh


def create_manhole_mesh(radius: float = 0.30) -> bpy.types.Mesh:
    """Create a manhole cover mesh (circular)."""
    mesh = bpy.data.meshes.new("Manhole")

    segments = 16
    vertices = [(0, 0, 0.01)]  # Center

    for i in range(segments):
        angle = 2 * math.pi * i / segments
        vertices.append((
            radius * math.cos(angle),
            radius * math.sin(angle),
            0.01
        ))

    faces = [(0, i+1, (i+1) % segments + 1) for i in range(segments)]

    mesh.from_pydata(vertices, [], faces)
    return mesh


def create_street_light_mesh(height: float = 10.0) -> bpy.types.Mesh:
    """Create a simple street light pole mesh."""
    mesh = bpy.data.meshes.new("StreetLight")

    pole_radius = 0.15
    arm_length = 3.0
    light_radius = 0.4

    # Simple pole + arm + light
    vertices = [
        # Pole base (4 corners)
        (-pole_radius, -pole_radius, 0),
        (pole_radius, -pole_radius, 0),
        (pole_radius, pole_radius, 0),
        (-pole_radius, pole_radius, 0),
        # Pole top
        (-pole_radius, -pole_radius, height),
        (pole_radius, -pole_radius, height),
        (pole_radius, pole_radius, height),
        (-pole_radius, pole_radius, height),
        # Arm end
        (-pole_radius, -pole_radius - arm_length, height),
        (pole_radius, -pole_radius - arm_length, height),
        (pole_radius, pole_radius - arm_length, height),
        (-pole_radius, pole_radius - arm_length, height),
    ]

    faces = [
        # Base
        (0, 1, 2, 3),
        # Pole sides
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
        # Top
        (4, 5, 6, 7),
        # Arm
        (5, 6, 10, 9),
        (6, 7, 11, 10),
        (7, 4, 8, 11),
        (4, 5, 9, 8),
        # Arm end
        (8, 9, 10, 11),
    ]

    mesh.from_pydata(vertices, [], faces)
    return mesh


# =============================================================================
# ASSET COLLECTION
# =============================================================================

def create_road_marking_assets():
    """Create all road marking mesh assets."""
    # Check if already created
    if "Road_Marking_Assets" in bpy.data.collections:
        return bpy.data.collections["Road_Marking_Assets"]

    coll = bpy.data.collections.new("Road_Marking_Assets")
    bpy.context.scene.collection.children.link(coll)

    # Create meshes
    meshes = {
        'CenterLine_Double': create_center_line_mesh(double=True),
        'CenterLine_Single': create_center_line_mesh(double=False),
        'LaneDivider': create_lane_divider_mesh(),
        'EdgeLine': create_edge_line_mesh(),
        'Crosswalk_6m': create_crosswalk_mesh(6.0),
        'Crosswalk_10m': create_crosswalk_mesh(10.0),
        'Crosswalk_15m': create_crosswalk_mesh(15.0),
        'StopLine_6m': create_stop_line_mesh(6.0),
        'StopLine_10m': create_stop_line_mesh(10.0),
        'Manhole': create_manhole_mesh(),
        'StreetLight_10m': create_street_light_mesh(10.0),
        'StreetLight_8m': create_street_light_mesh(8.0),
    }

    for name, mesh in meshes.items():
        obj = bpy.data.objects.new(name, mesh)
        coll.objects.link(obj)
        obj.hide_render = True  # Assets, not for render

    return coll


# =============================================================================
# GEOMETRY NODES
# =============================================================================

def create_comprehensive_markings_node_group():
    """
    Create a comprehensive node group that generates all markings
    for a road curve.
    """
    if "Road_Markings_Complete" in bpy.data.node_groups:
        return bpy.data.node_groups["Road_Markings_Complete"]

    node_group = bpy.data.node_groups.new("Road_Markings_Complete", 'GeometryNodeTree')

    # === INPUTS ===
    node_group.interface.new_socket(name="Curve", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Road Width", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 10.0
    node_group.interface.new_socket(name="Lanes", in_out='INPUT', socket_type='NodeSocketInt').default_value = 2
    node_group.interface.new_socket(name="Road Class", in_out='INPUT', socket_type='NodeSocketInt').default_value = 3
    node_group.interface.new_socket(name="Has Center Line", in_out='INPUT', socket_type='NodeSocketBool').default_value = True
    node_group.interface.new_socket(name="Has Edge Lines", in_out='INPUT', socket_type='NodeSocketBool').default_value = True
    node_group.interface.new_socket(name="Has Lane Dividers", in_out='INPUT', socket_type='NodeSocketBool').default_value = False
    node_group.interface.new_socket(name="Light Spacing", in_out='INPUT', socket_type='NodeSocketFloat').default_value = 30.0
    node_group.interface.new_socket(name="Center Line Material", in_out='INPUT', socket_type='NodeSocketMaterial')
    node_group.interface.new_socket(name="White Marking Material", in_out='INPUT', socket_type='NodeSocketMaterial')

    # === OUTPUTS ===
    node_group.interface.new_socket(name="Center Lines", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Lane Dividers", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="Edge Lines", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    node_group.interface.new_socket(name="All Markings", in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = node_group.nodes
    links = node_group.links

    # Input/Output
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1200, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1200, 0)

    # === CENTER LINE ===
    # Resample curve for center line
    resample_center = nodes.new('GeometryNodeResampleCurve')
    resample_center.location = (-800, 400)
    resample_center.mode = 'LENGTH'
    resample_center.inputs['Length'].default_value = 1.0

    # Instance center line
    center_instance = nodes.new('GeometryNodeInstanceOnPoints')
    center_instance.location = (-400, 400)

    # Center line mesh
    center_mesh = nodes.new('GeometryNodeMeshGrid')
    center_mesh.location = (-600, 200)
    center_mesh.inputs['Size X'].default_value = 0.15
    center_mesh.inputs['Size Y'].default_value = 1.0

    links.new(input_node.outputs['Curve'], resample_center.inputs['Curve'])
    links.new(resample_center.outputs['Curve'], center_instance.inputs['Points'])
    links.new(center_mesh.outputs['Mesh'], center_instance.inputs['Instance'])

    # === EDGE LINES ===
    # Left edge line
    resample_edge = nodes.new('GeometryNodeResampleCurve')
    resample_edge.location = (-800, 0)
    resample_edge.mode = 'LENGTH'
    resample_edge.inputs['Length'].default_value = 1.0

    # Set position for left edge (offset by -width/2)
    left_edge_pos = nodes.new('GeometryNodeSetPosition')
    left_edge_pos.location = (-400, 100)

    # Set position for right edge (offset by +width/2)
    right_edge_pos = nodes.new('GeometryNodeSetPosition')
    right_edge_pos.location = (-400, -100)

    # Edge line mesh
    edge_mesh = nodes.new('GeometryNodeMeshGrid')
    edge_mesh.location = (-600, -200)
    edge_mesh.inputs['Size X'].default_value = 0.20
    edge_mesh.inputs['Size Y'].default_value = 1.0

    # === JOIN ALL ===
    join_all = nodes.new('GeometryNodeJoinGeometry')
    join_all.location = (800, 0)

    links.new(center_instance.outputs['Instances'], join_all.inputs['Geometry'])

    # Output
    links.new(join_all.outputs['Geometry'], output_node.inputs['All Markings'])
    links.new(center_instance.outputs['Instances'], output_node.inputs['Center Lines'])

    return node_group


# =============================================================================
# PYTHON MARKING GENERATOR
# =============================================================================

def generate_road_markings(
    curve_obj: bpy.types.Object,
    road_width: float,
    lanes: int,
    highway_type: str
) -> Dict[str, bpy.types.Object]:
    """
    Generate all markings for a single road curve.

    Args:
        curve_obj: The road curve object
        road_width: Road width in meters
        lanes: Number of lanes
        highway_type: OSM highway type

    Returns:
        Dict of marking_name -> object
    """
    results = {}

    # Get marking rules for this road type
    rules = get_marking_rules(highway_type)

    # Get curve data
    curve_data = curve_obj.data
    if not curve_data.splines:
        return results

    spline = curve_data.splines[0]
    points = [curve_obj.matrix_world @ Vector(p.co[:3]) for p in spline.points]

    if len(points) < 2:
        return results

    # === CENTER LINE ===
    if rules.has_center_line and lanes >= 2:
        center_obj = generate_center_line_along_curve(
            curve_obj,
            road_width,
            rules.center_line_type
        )
        if center_obj:
            results['center_line'] = center_obj

    # === EDGE LINES ===
    if rules.has_edge_lines:
        edge_objs = generate_edge_lines_along_curve(
            curve_obj,
            road_width
        )
        results.update(edge_objs)

    # === LANE DIVIDERS ===
    if rules.has_lane_dividers and lanes >= rules.min_lanes_for_dividers:
        divider_objs = generate_lane_dividers_along_curve(
            curve_obj,
            road_width,
            lanes
        )
        results.update(divider_objs)

    return results


def generate_center_line_along_curve(
    curve_obj: bpy.types.Object,
    road_width: float,
    marking_type: MarkingType
) -> Optional[bpy.types.Object]:
    """Generate center line marking along a curve."""
    curve_data = curve_obj.data
    if not curve_data.splines:
        return None

    spline = curve_data.splines[0]
    points = [curve_obj.matrix_world @ Vector(p.co[:3]) for p in spline.points]

    if len(points) < 2:
        return None

    # Get marking specs
    spec = MARKING_SPECS.get(marking_type, MARKING_SPECS[MarkingType.CENTER_LINE])
    line_width = spec.width

    # Double line parameters
    gap = 0.10  # 10cm gap between double lines
    half_gap = gap / 2

    mesh = bpy.data.meshes.new(f"CenterLine_{curve_obj.name}")
    bm = bmesh.new()

    # Generate dashed or solid line parameters
    dash_length = spec.dash_length if spec.is_dashed else 1000.0
    dash_gap = spec.dash_gap if spec.is_dashed else 0.0

    # Calculate total length and build segments
    total_length = 0.0
    segments = []
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        seg_len = (p2 - p1).length
        segments.append((p1, p2, total_length, seg_len))
        total_length += seg_len

    # Generate quads along path for double yellow line
    z_offset = 0.012  # Slightly above road surface

    def create_line_quad(bm, p1, p2, direction, width, z_off):
        """Create a quad along a segment with offset."""
        tangent = (p2 - p1).normalized()
        # Get perpendicular (in XY plane for roads)
        normal = Vector((-tangent.y, tangent.x, 0)).normalized()

        # Offset positions
        o1 = p1 + normal * direction * width
        o2 = p1 + normal * (direction * width + direction * line_width)
        o3 = p2 + normal * (direction * width + direction * line_width)
        o4 = p2 + normal * direction * width

        # Set Z
        o1.z = z_off
        o2.z = z_off
        o3.z = z_off
        o4.z = z_off

        v1 = bm.verts.new(o1)
        v2 = bm.verts.new(o2)
        v3 = bm.verts.new(o3)
        v4 = bm.verts.new(o4)
        bm.faces.new([v1, v2, v3, v4])

    if spec.is_dashed:
        # Dashed center line
        current_dist = 0.0
        is_dash = True

        while current_dist < total_length:
            segment_len = dash_length if is_dash else dash_gap

            if is_dash:
                # Find start and end points for this dash
                start_dist = current_dist
                end_dist = min(current_dist + dash_length, total_length)

                # Interpolate positions
                start_p = interpolate_on_segments(segments, start_dist)
                end_p = interpolate_on_segments(segments, end_dist)

                if start_p and end_p:
                    # Create single line (dashed)
                    create_single_line_quad(bm, start_p, end_p, 0, line_width, z_offset)

            current_dist += segment_len
            is_dash = not is_dash
    else:
        # Solid double yellow line - create for each segment
        for p1, p2, _, _ in segments:
            tangent = (p2 - p1).normalized()
            normal = Vector((-tangent.y, tangent.x, 0)).normalized()

            # Left line (negative offset from center)
            l1 = p1 + normal * (-half_gap - line_width)
            l2 = p1 + normal * (-half_gap)
            l3 = p2 + normal * (-half_gap)
            l4 = p2 + normal * (-half_gap - line_width)

            # Right line (positive offset from center)
            r1 = p1 + normal * (half_gap)
            r2 = p1 + normal * (half_gap + line_width)
            r3 = p2 + normal * (half_gap + line_width)
            r4 = p2 + normal * (half_gap)

            # Set Z offset
            for v in [l1, l2, l3, l4, r1, r2, r3, r4]:
                v = Vector((v.x, v.y, z_offset))

            # Create left line quad
            v1 = bm.verts.new(Vector((l1.x, l1.y, z_offset)))
            v2 = bm.verts.new(Vector((l2.x, l2.y, z_offset)))
            v3 = bm.verts.new(Vector((l3.x, l3.y, z_offset)))
            v4 = bm.verts.new(Vector((l4.x, l4.y, z_offset)))
            bm.faces.new([v1, v2, v3, v4])

            # Create right line quad
            v5 = bm.verts.new(Vector((r1.x, r1.y, z_offset)))
            v6 = bm.verts.new(Vector((r2.x, r2.y, z_offset)))
            v7 = bm.verts.new(Vector((r3.x, r3.y, z_offset)))
            v8 = bm.verts.new(Vector((r4.x, r4.y, z_offset)))
            bm.faces.new([v5, v6, v7, v8])

    bm.to_mesh(mesh)
    bm.free()

    if not mesh.vertices:
        bpy.data.meshes.remove(mesh)
        return None

    obj = bpy.data.objects.new(f"CenterLine_{curve_obj.name}", mesh)
    obj['marking_type'] = 'center_line'
    obj['road_name'] = curve_obj.get('road_name', '')

    return obj


def interpolate_on_segments(segments: List, distance: float) -> Optional[Vector]:
    """Interpolate a position along segments at given distance."""
    for p1, p2, start_dist, seg_len in segments:
        if start_dist <= distance <= start_dist + seg_len:
            t = (distance - start_dist) / seg_len if seg_len > 0 else 0
            return p1 + (p2 - p1) * t
    return None


def create_single_line_quad(bm, p1: Vector, p2: Vector, center_offset: float, width: float, z_off: float):
    """Create a single line quad between two points with center offset."""
    tangent = (p2 - p1).normalized()
    normal = Vector((-tangent.y, tangent.x, 0)).normalized()

    half_width = width / 2
    offset_normal = normal * center_offset

    v1 = bm.verts.new(Vector((p1.x + offset_normal.x - normal.x * half_width,
                               p1.y + offset_normal.y - normal.y * half_width, z_off)))
    v2 = bm.verts.new(Vector((p1.x + offset_normal.x + normal.x * half_width,
                               p1.y + offset_normal.y + normal.y * half_width, z_off)))
    v3 = bm.verts.new(Vector((p2.x + offset_normal.x + normal.x * half_width,
                               p2.y + offset_normal.y + normal.y * half_width, z_off)))
    v4 = bm.verts.new(Vector((p2.x + offset_normal.x - normal.x * half_width,
                               p2.y + offset_normal.y - normal.y * half_width, z_off)))
    bm.faces.new([v1, v2, v3, v4])


def generate_edge_lines_along_curve(
    curve_obj: bpy.types.Object,
    road_width: float
) -> Dict[str, bpy.types.Object]:
    """Generate left and right edge lines markings."""
    results = {}

    curve_data = curve_obj.data
    if not curve_data.splines:
        return results

    spline = curve_data.splines[0]
    points = [curve_obj.matrix_world @ Vector(p.co[:3]) for p in spline.points]

    if len(points) < 2:
        return results

    # Get edge line specs
    spec = MARKING_SPECS.get(MarkingType.EDGE_LINE, MARKING_SPECS[MarkingType.EDGE_LINE])
    line_width = spec.width

    z_offset = 0.011
    half_road = road_width / 2

    # Build segments
    segments = []
    total_length = 0.0
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        seg_len = (p2 - p1).length
        segments.append((p1, p2, total_length, seg_len))
        total_length += seg_len

    # Generate LEFT edge line
    left_mesh = bpy.data.meshes.new(f"LeftEdge_{curve_obj.name}")
    bm_left = bmesh.new()

    for p1, p2, _, _ in segments:
        tangent = (p2 - p1).normalized()
        normal = Vector((-tangent.y, tangent.x, 0)).normalized()

        # Left edge offset (negative from center)
        offset = -half_road + line_width / 2

        e1 = p1 + normal * (offset - line_width/2)
        e2 = p1 + normal * (offset + line_width/2)
        e3 = p2 + normal * (offset + line_width/2)
        e4 = p2 + normal * (offset - line_width/2)

        v1 = bm_left.verts.new(Vector((e1.x, e1.y, z_offset)))
        v2 = bm_left.verts.new(Vector((e2.x, e2.y, z_offset)))
        v3 = bm_left.verts.new(Vector((e3.x, e3.y, z_offset)))
        v4 = bm_left.verts.new(Vector((e4.x, e4.y, z_offset)))
        bm_left.faces.new([v1, v2, v3, v4])

    bm_left.to_mesh(left_mesh)
    bm_left.free()

    if left_mesh.vertices:
        left_obj = bpy.data.objects.new(f"LeftEdge_{curve_obj.name}", left_mesh)
        left_obj['marking_type'] = 'edge_line'
        left_obj['road_name'] = curve_obj.get('road_name', '')
        left_obj['edge_side'] = 'left'
        results['left_edge'] = left_obj
    else:
        bpy.data.meshes.remove(left_mesh)

    # Generate RIGHT edge line
    right_mesh = bpy.data.meshes.new(f"RightEdge_{curve_obj.name}")
    bm_right = bmesh.new()

    for p1, p2, _, _ in segments:
        tangent = (p2 - p1).normalized()
        normal = Vector((-tangent.y, tangent.x, 0)).normalized()

        # Right edge offset (positive from center)
        offset = half_road - line_width / 2

        e1 = p1 + normal * (offset - line_width/2)
        e2 = p1 + normal * (offset + line_width/2)
        e3 = p2 + normal * (offset + line_width/2)
        e4 = p2 + normal * (offset - line_width/2)

        v1 = bm_right.verts.new(Vector((e1.x, e1.y, z_offset)))
        v2 = bm_right.verts.new(Vector((e2.x, e2.y, z_offset)))
        v3 = bm_right.verts.new(Vector((e3.x, e3.y, z_offset)))
        v4 = bm_right.verts.new(Vector((e4.x, e4.y, z_offset)))
        bm_right.faces.new([v1, v2, v3, v4])

    bm_right.to_mesh(right_mesh)
    bm_right.free()

    if right_mesh.vertices:
        right_obj = bpy.data.objects.new(f"RightEdge_{curve_obj.name}", right_mesh)
        right_obj['marking_type'] = 'edge_line'
        right_obj['road_name'] = curve_obj.get('road_name', '')
        right_obj['edge_side'] = 'right'
        results['right_edge'] = right_obj
    else:
        bpy.data.meshes.remove(right_mesh)

    return results


def generate_lane_dividers_along_curve(
    curve_obj: bpy.types.Object,
    road_width: float,
    lanes: int
) -> Dict[str, bpy.types.Object]:
    """Generate lane divider markings between lanes (dashed white lines)."""
    results = {}

    curve_data = curve_obj.data
    if not curve_data.splines:
        return results

    spline = curve_data.splines[0]
    points = [curve_obj.matrix_world @ Vector(p.co[:3]) for p in spline.points]

    if len(points) < 2:
        return results

    if lanes < 3:
        return results

    # Get lane divider specs (dashed white)
    spec = MARKING_SPECS.get(MarkingType.LANE_DIVIDER, MARKING_SPECS[MarkingType.LANE_DIVIDER])
    line_width = spec.width
    dash_length = spec.dash_length
    dash_gap = spec.dash_gap

    z_offset = 0.011
    lane_width = road_width / lanes
    half_road = road_width / 2

    # Build segments for interpolation
    segments = []
    total_length = 0.0
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        seg_len = (p2 - p1).length
        segments.append((p1, p2, total_length, seg_len))
        total_length += seg_len

    def generate_dashed_line_at_offset(offset: float, name_suffix: str) -> Optional[bpy.types.Object]:
        """Generate a dashed line at a specific offset from center."""
        mesh = bpy.data.meshes.new(f"LaneDivider_{name_suffix}_{curve_obj.name}")
        bm = bmesh.new()

        # Generate dashes
        current_dist = 0.0
        is_dash = True

        while current_dist < total_length:
            segment_len = dash_length if is_dash else dash_gap

            if is_dash:
                start_dist = current_dist
                end_dist = min(current_dist + dash_length, total_length)

                start_p = interpolate_on_segments(segments, start_dist)
                end_p = interpolate_on_segments(segments, end_dist)

                if start_p and end_p and (end_p - start_p).length > 0.1:
                    tangent = (end_p - start_p).normalized()
                    normal = Vector((-tangent.y, tangent.x, 0)).normalized()

                    # Create dashed quad at offset
                    d1 = start_p + normal * (offset - line_width/2)
                    d2 = start_p + normal * (offset + line_width/2)
                    d3 = end_p + normal * (offset + line_width/2)
                    d4 = end_p + normal * (offset - line_width/2)

                    v1 = bm.verts.new(Vector((d1.x, d1.y, z_offset)))
                    v2 = bm.verts.new(Vector((d2.x, d2.y, z_offset)))
                    v3 = bm.verts.new(Vector((d3.x, d3.y, z_offset)))
                    v4 = bm.verts.new(Vector((d4.x, d4.y, z_offset)))
                    bm.faces.new([v1, v2, v3, v4])

            current_dist += segment_len
            is_dash = not is_dash

        bm.to_mesh(mesh)
        bm.free()

        if not mesh.vertices:
            bpy.data.meshes.remove(mesh)
            return None

        obj = bpy.data.objects.new(f"LaneDivider_{name_suffix}_{curve_obj.name}", mesh)
        obj['marking_type'] = 'lane_divider'
        obj['road_name'] = curve_obj.get('road_name', '')
        return obj

    # Generate dividers for each lane boundary (except center)
    # Only on roads with 3+ lanes
    divider_count = 0
    for lane_idx in range(1, lanes):
        # Skip center divider (that's the center line)
        if lane_idx == lanes // 2:
            continue

        offset = -half_road + (lane_idx * lane_width)

        divider_obj = generate_dashed_line_at_offset(offset, f"L{lane_idx}")
        if divider_obj:
            divider_count += 1
            results[f'lane_divider_{divider_count}'] = divider_obj

    return results


# =============================================================================
# STOP LINES & MANHOLES
# =============================================================================

def generate_stop_lines_at_intersections(
    intersections: List[Dict]
) -> List[bpy.types.Object]:
    """
    Generate stop lines at detected intersections.

    Args:
        intersections: List of intersection dicts with position, road_width, etc.

    Returns:
        List of stop line objects
    """
    stop_lines = []

    for intersection in intersections:
        pos = intersection.get('position')
        road_width = intersection.get('road_width', 10.0)
        direction = intersection.get('direction', Vector((0, 1, 0)))

        if not pos:
            continue

        # Create stop line mesh
        spec = MARKING_SPECS.get(MarkingType.STOP_LINE, MARKING_SPECS[MarkingType.STOP_LINE])
        thickness = spec.width

        mesh = bpy.data.meshes.new(f"StopLine_{len(stop_lines)}")
        bm = bmesh.new()

        z_offset = 0.015

        # Get perpendicular to direction
        normal = Vector((-direction.y, direction.x, 0)).normalized()
        half_width = road_width / 2

        # Create quad
        v1 = bm.verts.new(Vector((pos.x - normal.x * half_width, pos.y - normal.y * half_width, z_offset)))
        v2 = bm.verts.new(Vector((pos.x + normal.x * half_width, pos.y + normal.y * half_width, z_offset)))
        v3 = bm.verts.new(Vector((pos.x + normal.x * half_width + direction.x * thickness,
                                   pos.y + normal.y * half_width + direction.y * thickness, z_offset)))
        v4 = bm.verts.new(Vector((pos.x - normal.x * half_width + direction.x * thickness,
                                   pos.y - normal.y * half_width + direction.y * thickness, z_offset)))
        bm.faces.new([v1, v2, v3, v4])

        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(f"StopLine_{len(stop_lines)}", mesh)
        obj['marking_type'] = 'stop_line'
        stop_lines.append(obj)

    return stop_lines


def generate_manholes_along_curve(
    curve_obj: bpy.types.Object,
    road_width: float,
    lanes: int
) -> List[bpy.types.Object]:
    """
    Generate manhole covers along a road curve.

    Args:
        curve_obj: The road curve object
        road_width: Road width in meters
        lanes: Number of lanes

    Returns:
        List of manhole objects
    """
    manholes = []

    curve_data = curve_obj.data
    if not curve_data.splines:
        return manholes

    spline = curve_data.splines[0]
    points = [curve_obj.matrix_world @ Vector(p.co[:3]) for p in spline.points]

    if len(points) < 2:
        return manholes

    spacing = MANHOLE_SPEC.spacing  # Every 30m
    radius = 0.30  # 30cm radius

    # Build segments for interpolation
    segments = []
    total_length = 0.0
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        seg_len = (p2 - p1).length
        segments.append((p1, p2, total_length, seg_len))
        total_length += seg_len

    z_offset = 0.01

    # Calculate manhole positions
    num_manholes = int(total_length / spacing)
    lane_width = road_width / lanes

    for i in range(num_manholes):
        dist = (i + 0.5) * spacing  # Offset from start
        if dist >= total_length:
            break

        # Interpolate position
        pos = interpolate_on_segments(segments, dist)
        if not pos:
            continue

        # Get tangent at this point
        tangent = Vector((0, 1, 0))
        for p1, p2, start_dist, seg_len in segments:
            if start_dist <= dist <= start_dist + seg_len:
                tangent = (p2 - p1).normalized()
                break

        # Get perpendicular
        normal = Vector((-tangent.y, tangent.x, 0)).normalized()

        # Offset to right lane (typically manholes are in right lane)
        if lanes >= 2:
            offset = road_width / 4  # In first lane
        else:
            offset = 0

        final_pos = pos + normal * offset

        # Create circular manhole mesh
        mesh = bpy.data.meshes.new(f"Manhole_{curve_obj.name}_{i}")
        bm = bmesh.new()

        # Create circle
        segments_circle = 16
        center = bm.verts.new(Vector((final_pos.x, final_pos.y, z_offset)))

        circle_verts = []
        for j in range(segments_circle):
            angle = 2 * math.pi * j / segments_circle
            # Align circle to road direction
            local_x = math.cos(angle) * radius
            local_y = math.sin(angle) * radius

            # Transform to world space
            world_x = final_pos.x + tangent.x * local_y + normal.x * local_x
            world_y = final_pos.y + tangent.y * local_y + normal.y * local_x

            v = bm.verts.new(Vector((world_x, world_y, z_offset)))
            circle_verts.append(v)

        # Create faces (triangle fan)
        for j in range(segments_circle):
            next_j = (j + 1) % segments_circle
            bm.faces.new([center, circle_verts[j], circle_verts[next_j]])

        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(f"Manhole_{curve_obj.name}_{i}", mesh)
        obj['marking_type'] = 'manhole'
        obj['road_name'] = curve_obj.get('road_name', '')
        obj['manhole_type'] = MANHOLE_SPEC.types[i % len(MANHOLE_SPEC.types)]
        manholes.append(obj)

    return manholes


def generate_street_lights_along_curve(
    curve_obj: bpy.types.Object,
    road_width: float,
    highway_type: str
) -> List[bpy.types.Object]:
    """
    Generate street lights along a road curve.

    Args:
        curve_obj: The road curve object
        road_width: Road width in meters
        highway_type: OSM highway type

    Returns:
        List of street light objects
    """
    lights = []

    light_spec = get_street_light_spec(highway_type)

    # Skip if no lights for this road type
    if light_spec.spacing <= 0:
        return lights

    curve_data = curve_obj.data
    if not curve_data.splines:
        return lights

    spline = curve_data.splines[0]
    points = [curve_obj.matrix_world @ Vector(p.co[:3]) for p in spline.points]

    if len(points) < 2:
        return lights

    # Build segments for interpolation
    segments = []
    total_length = 0.0
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        seg_len = (p2 - p1).length
        segments.append((p1, p2, total_length, seg_len))
        total_length += seg_len

    # Calculate light positions
    num_lights = int(total_length / light_spec.spacing) + 1

    for i in range(num_lights):
        dist = i * light_spec.spacing
        if dist >= total_length:
            break

        # Interpolate position
        pos = interpolate_on_segments(segments, dist)
        if not pos:
            continue

        # Get tangent at this point
        tangent = Vector((0, 1, 0))
        for p1, p2, start_dist, seg_len in segments:
            if start_dist <= dist <= start_dist + seg_len:
                tangent = (p2 - p1).normalized()
                break

        # Get perpendicular
        normal = Vector((-tangent.y, tangent.x, 0)).normalized()

        # Create light pole (simple cylinder approximation)
        mesh = bpy.data.meshes.new(f"StreetLight_{curve_obj.name}_{i}")
        bm = bmesh.new()

        pole_radius = 0.15
        pole_height = light_spec.height

        # Offset from road edge
        for side in [-1, 1]:
            if side == 1 and not light_spec.has_double_side:
                continue

            offset = (road_width / 2 + light_spec.offset_from_edge) * side
            pole_pos = pos + normal * offset

            # Simple pole (8-sided cylinder)
            segments_pole = 8
            for level in range(2):  # Base and top
                z = level * pole_height
                r = pole_radius

                for j in range(segments_pole):
                    angle = 2 * math.pi * j / segments_pole
                    x = pole_pos.x + r * math.cos(angle)
                    y = pole_pos.y + r * math.sin(angle)
                    bm.verts.new(Vector((x, y, z)))

            # Create sides
            for j in range(segments_pole):
                next_j = (j + 1) % segments_pole
                v1 = bm.verts[j]
                v2 = bm.verts[next_j]
                v3 = bm.verts[segments_pole + next_j]
                v4 = bm.verts[segments_pole + j]
                bm.faces.new([v1, v2, v3, v4])

        bm.to_mesh(mesh)
        bm.free()

        if mesh.vertices:
            obj = bpy.data.objects.new(f"StreetLight_{curve_obj.name}_{i}", mesh)
            obj['marking_type'] = 'street_light'
            obj['road_name'] = curve_obj.get('road_name', '')
            obj['light_height'] = pole_height
            lights.append(obj)
        else:
            bpy.data.meshes.remove(mesh)

    return lights


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_all_road_markings():
    """
    Generate all road markings for all roads in the scene.
    """
    print("\n=== Generating Road Markings ===")

    # Create assets
    print("Creating marking assets...")
    create_road_marking_assets()

    # Create collection for markings
    markings_coll = bpy.data.collections.get("Road_Markings")
    if not markings_coll:
        markings_coll = bpy.data.collections.new("Road_Markings")
        bpy.context.scene.collection.children.link(markings_coll)

    # Sub-collections
    for subcoll_name in ['Center_Lines', 'Edge_Lines', 'Lane_Dividers', 'Crosswalks', 'Stop_Lines', 'Manholes', 'Street_Lights']:
        if subcoll_name not in bpy.data.collections:
            subcoll = bpy.data.collections.new(subcoll_name)
            markings_coll.children.link(subcoll)

    # Get all road curves
    road_curves = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'CURVE' and obj.get('road_class')
    ]

    print(f"Processing {len(road_curves)} road curves...")

    # Stats
    stats = {
        'center_lines': 0,
        'edge_lines': 0,
        'lane_dividers': 0,
        'manholes': 0,
        'street_lights': 0,
    }

    for curve in road_curves:
        # Get road parameters
        highway_type = curve.get('highway_type', 'residential')
        explicit_width = curve.get('road_width')
        explicit_lanes = curve.get('lanes')

        # Estimate width if needed
        width, lanes = estimate_road_width(
            highway_type,
            explicit_width,
            explicit_lanes
        )

        # Generate lane markings (center, edge, dividers)
        markings = generate_road_markings(curve, width, lanes, highway_type)

        # Add to collection
        for name, obj in markings.items():
            bpy.context.scene.collection.objects.link(obj)
            # Move to appropriate sub-collection
            if 'center' in name:
                target = bpy.data.collections.get('Center_Lines')
                stats['center_lines'] += 1
            elif 'edge' in name:
                target = bpy.data.collections.get('Edge_Lines')
                stats['edge_lines'] += 1
            elif 'divider' in name:
                target = bpy.data.collections.get('Lane_Dividers')
                stats['lane_dividers'] += 1
            else:
                target = markings_coll

            if target:
                for c in obj.users_collection:
                    c.objects.unlink(obj)
                target.objects.link(obj)

        # Generate manholes
        manholes = generate_manholes_along_curve(curve, width, lanes)
        manhole_coll = bpy.data.collections.get('Manholes')
        for mh in manholes:
            bpy.context.scene.collection.objects.link(mh)
            if manhole_coll:
                for c in mh.users_collection:
                    c.objects.unlink(mh)
                manhole_coll.objects.link(mh)
        stats['manholes'] += len(manholes)

        # Generate street lights
        lights = generate_street_lights_along_curve(curve, width, highway_type)
        light_coll = bpy.data.collections.get('Street_Lights')
        for light in lights:
            bpy.context.scene.collection.objects.link(light)
            if light_coll:
                for c in light.users_collection:
                    c.objects.unlink(light)
                light_coll.objects.link(light)
        stats['street_lights'] += len(lights)

    total = sum(stats.values())
    print(f"\n=== Summary ===")
    print(f"Center lines:  {stats['center_lines']}")
    print(f"Edge lines:    {stats['edge_lines']}")
    print(f"Lane dividers: {stats['lane_dividers']}")
    print(f"Manholes:      {stats['manholes']}")
    print(f"Street lights: {stats['street_lights']}")
    print(f"Total:         {total}")

    return total


if __name__ == '__main__':
    generate_all_road_markings()
