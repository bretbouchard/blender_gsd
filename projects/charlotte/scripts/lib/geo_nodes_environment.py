"""
Environment & Terrain Geometry Nodes Generator

Creates terrain, sidewalks, vegetation, and street furniture for driving game.

Usage:
    from lib.geo_nodes_environment import (
        create_terrain_node_group,
        create_sidewalk_node_group,
        create_vegetation_scatter_node_group,
        create_street_furniture_node_group,
        generate_all_environment,
    )
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
from dataclasses import dataclass
import math
import random

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

class SidewalkType(Enum):
    """Sidewalk surface types."""
    CONCRETE = "concrete"
    BRICK = "brick"
    ASPHALT = "asphalt"
    COBBLESTONE = "cobblestone"


class TreeType(Enum):
    """Tree types for vegetation."""
    OAK = "oak"
    MAPLE = "maple"
    PINE = "pine"
    DOGWOOD = "dogwood"
    CREPE_MYRTLE = "crepe_myrtle"


class FurnitureType(Enum):
    """Street furniture types."""
    BENCH = "bench"
    TRASH_CAN = "trash_can"
    MAILBOX = "mailbox"
    FIRE_HYDRANT = "fire_hydrant"
    BUS_STOP = "bus_stop"
    BIKE_RACK = "bike_rack"
    LAMP_POST = "lamp_post"
    BOLLARD = "bollard"


@dataclass
class TerrainConfig:
    """Terrain generation configuration."""
    resolution: float = 10.0          # Grid resolution in meters
    base_elevation: float = 200.0     # Charlotte base elevation
    elevation_scale: float = 1.0      # Multiplier for height variation
    subdivision_levels: int = 2       # For smoothing


@dataclass
class SidewalkConfig:
    """Sidewalk configuration."""
    width: float = 1.5
    height: float = 0.15              # Above road level
    material: SidewalkType = SidewalkType.CONCRETE


@dataclass
class VegetationConfig:
    """Vegetation distribution configuration."""
    tree_spacing: float = 15.0        # Meters between trees along roads
    tree_offset: float = 3.0          # Offset from road edge
    min_tree_height: float = 4.0
    max_tree_height: float = 12.0
    grass_density: float = 0.5        # 0-1 coverage in non-road areas


@dataclass
class FurnitureConfig:
    """Street furniture configuration."""
    bench_spacing: float = 50.0       # Meters between benches
    trash_can_spacing: float = 30.0
    fire_hydrant_spacing: float = 100.0
    mailbox_spacing: float = 200.0


# =============================================================================
# TERRAIN NODE GROUP
# =============================================================================

def create_terrain_node_group(name: str = "Terrain_from_Elevation") -> Optional[bpy.types.NodeGroup]:
    """
    Create geometry node group for terrain generation.

    Generates terrain mesh from:
    - Elevation attribute data
    - Grid-based subdivision
    - Optional displacement

    Inputs:
        - Size X (Float)
        - Size Y (Float)
        - Resolution (Float, grid cell size)
        - Base Elevation (Float)
        - Elevation Scale (Float)

    Outputs:
        - Terrain mesh
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
    interface.new_socket("Size X", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Size Y", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Resolution", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Base Elevation", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Elevation Scale", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    # Defaults
    node_group.inputs["Size X"].default_value = 5000.0
    node_group.inputs["Size Y"].default_value = 5000.0
    node_group.inputs["Resolution"].default_value = 10.0
    node_group.inputs["Base Elevation"].default_value = 200.0
    node_group.inputs["Elevation Scale"].default_value = 1.0

    # Group Input/Output
    gi = nodes.new("NodeGroupInput")
    gi.location = (0, 0)

    go = nodes.new("NodeGroupOutput")
    go.location = (2000, 0)

    # ========================================
    # Create base grid
    # ========================================
    grid = nodes.new("GeometryNodeMeshGrid")
    grid.location = (200, 0)

    # Calculate vertices from size/resolution
    # We'll use a fixed reasonable size for now
    grid.inputs["Vertices X"].default_value = 100
    grid.inputs["Vertices Y"].default_value = 100
    grid.inputs["Size X"].default_value = 5000.0
    grid.inputs["Size Y"].default_value = 5000.0

    # ========================================
    # Add displacement based on position
    # ========================================
    # Get position
    pos = nodes.new("GeometryNodeInputPosition")
    pos.location = (400, 200)

    # Separate XYZ for manipulation
    sep_xyz = nodes.new("ShaderNodeSeparateXYZ")
    sep_xyz.location = (600, 200)

    # Create noise-based elevation variation
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (400, -100)
    noise.inputs["Scale"].default_value = 0.001
    noise.inputs["Detail"].default_value = 4
    noise.inputs["Roughness"].default_value = 0.5

    # Scale noise for elevation
    scale_noise = nodes.new("ShaderNodeMath")
    scale_noise.location = (600, -100)
    scale_noise.operation = 'MULTIPLY'
    scale_noise.inputs[1].default_value = 50.0  # Max elevation variation

    # Add base elevation
    add_base = nodes.new("ShaderNodeMath")
    add_base.location = (800, -100)
    add_base.operation = 'ADD'
    add_base.inputs[1].default_value = 200.0

    # Combine back to vector
    combine_xyz = nodes.new("ShaderNodeCombineXYZ")
    combine_xyz.location = (1000, 100)

    # Set position
    set_pos = nodes.new("GeometryNodeSetPosition")
    set_pos.location = (1200, 0)

    # ========================================
    # Store terrain attributes
    # ========================================
    store_elevation = nodes.new("GeometryNodeStoreNamedAttribute")
    store_elevation.location = (1400, 0)
    store_elevation.inputs["Name"].default_value = "elevation"
    store_elevation.inputs["Data Type"].default_value = "FLOAT"

    # Store material zone
    store_zone = nodes.new("GeometryNodeStoreNamedAttribute")
    store_zone.location = (1600, 0)
    store_zone.inputs["Name"].default_value = "material_zone"
    store_zone.inputs["Data Type"].default_value = "INT"

    zone_val = nodes.new("FunctionNodeInputInt")
    zone_val.location = (1400, -200)
    zone_val.outputs[0].default_value = 10  # Terrain zone

    # Realize
    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (1800, 0)

    # ========================================
    # Wire connections
    # ========================================
    links.new(grid.outputs["Mesh"], set_pos.inputs["Geometry"])

    links.new(pos.outputs["Position"], sep_xyz.inputs["Vector"])
    links.new(sep_xyz.outputs["X"], noise.inputs["Vector"])  # Use X for noise
    links.new(sep_xyz.outputs["Y"], noise.inputs["Vector"].subscript(0))  # Also Y
    links.new(noise.outputs["Fac"], scale_noise.inputs[0])
    links.new(scale_noise.outputs[0], add_base.inputs[0])
    links.new(gi.outputs["Base Elevation"], add_base.inputs[1])

    links.new(sep_xyz.outputs["X"], combine_xyz.inputs["X"])
    links.new(sep_xyz.outputs["Y"], combine_xyz.inputs["Y"])
    links.new(add_base.outputs[0], combine_xyz.inputs["Z"])

    links.new(combine_xyz.outputs["Vector"], set_pos.inputs["Position"])
    links.new(set_pos.outputs["Geometry"], store_elevation.inputs["Geometry"])
    links.new(add_base.outputs[0], store_elevation.inputs["Value"])

    links.new(store_elevation.outputs["Geometry"], store_zone.inputs["Geometry"])
    links.new(zone_val.outputs[0], store_zone.inputs["Value"])

    links.new(store_zone.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    return node_group


# =============================================================================
# SIDEWALK NODE GROUP
# =============================================================================

def create_sidewalk_node_group(name: str = "Sidewalk_from_Footway") -> Optional[bpy.types.NodeGroup]:
    """
    Create geometry node group for sidewalk generation.

    Generates sidewalks from footway curves:
    - Flat walking surface
    - Optional curb connection
    - Material zone assignment

    Inputs:
        - Width (Float)
        - Height (Float, above road)
        - Material Type (Int: 0=concrete, 1=brick, etc.)

    Outputs:
        - Sidewalk mesh
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
    interface.new_socket("Width", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Height", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Material Type", socket_type="NodeSocketInt", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="INPUT")  # Curve input
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    # Defaults
    node_group.inputs["Width"].default_value = 1.5
    node_group.inputs["Height"].default_value = 0.15
    node_group.inputs["Material Type"].default_value = 0

    # Group Input/Output
    gi = nodes.new("NodeGroupInput")
    gi.location = (0, 0)

    go = nodes.new("NodeGroupOutput")
    go.location = (1600, 0)

    # ========================================
    # Create profile curve (rectangle for sidewalk)
    # ========================================
    profile = nodes.new("GeometryNodeCurvePrimitiveQuadrilateral")
    profile.location = (200, -200)
    profile.inputs["Mode"].default_value = "RECTANGLE"
    profile.inputs["Width"].default_value = 1.5
    profile.inputs["Height"].default_value = 0.01  # Thin, we'll lift it

    # ========================================
    # Convert curve to mesh
    # ========================================
    curve_to_mesh = nodes.new("GeometryNodeCurveToMesh")
    curve_to_mesh.location = (400, 0)

    # ========================================
    # Lift sidewalk above ground
    # ========================================
    transform = nodes.new("GeometryNodeTransform")
    transform.location = (600, 0)
    transform.inputs["Translation"].default_value = (0, 0, 0.15)

    # ========================================
    # Store sidewalk attributes
    # ========================================
    store_zone = nodes.new("GeometryNodeStoreNamedAttribute")
    store_zone.location = (800, 0)
    store_zone.inputs["Name"].default_value = "material_zone"
    store_zone.inputs["Data Type"].default_value = "INT"

    zone_val = nodes.new("FunctionNodeInputInt")
    zone_val.location = (600, -200)
    zone_val.outputs[0].default_value = 5  # Sidewalk zone

    store_type = nodes.new("GeometryNodeStoreNamedAttribute")
    store_type.location = (1000, 0)
    store_type.inputs["Name"].default_value = "sidewalk_type"
    store_type.inputs["Data Type"].default_value = "INT"

    # Realize
    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (1400, 0)

    # ========================================
    # Wire connections
    # ========================================
    links.new(gi.outputs["Geometry"], curve_to_mesh.inputs["Curve"])
    links.new(profile.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])
    links.new(gi.outputs["Width"], profile.inputs["Width"])

    links.new(curve_to_mesh.outputs["Mesh"], transform.inputs["Geometry"])
    links.new(gi.outputs["Height"], transform.inputs["Translation"].subscript(2))

    links.new(transform.outputs["Geometry"], store_zone.inputs["Geometry"])
    links.new(zone_val.outputs[0], store_zone.inputs["Value"])

    links.new(store_zone.outputs["Geometry"], store_type.inputs["Geometry"])
    links.new(gi.outputs["Material Type"], store_type.inputs["Value"])

    links.new(store_type.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    return node_group


# =============================================================================
# VEGETATION SCATTER NODE GROUP
# =============================================================================

def create_vegetation_scatter_node_group(name: str = "Vegetation_Scatter") -> Optional[bpy.types.NodeGroup]:
    """
    Create geometry node group for vegetation distribution.

    Distributes trees, bushes, grass based on:
    - Distance from roads/buildings
    - Terrain type
    - Density parameters

    Inputs:
        - Terrain (Geometry)
        - Exclusion Zones (Geometry, roads/buildings)
        - Tree Density (Float, 0-1)
        - Grass Density (Float, 0-1)
        - Tree Collection (Collection)

    Outputs:
        - Vegetation instances
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
    interface.new_socket("Tree Density", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Grass Density", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Min Distance", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Terrain", socket_type="NodeSocketGeometry", in_out="INPUT")
    interface.new_socket("Exclusion Zones", socket_type="NodeSocketGeometry", in_out="INPUT")
    interface.new_socket("Tree Collection", socket_type="NodeSocketCollection", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    # Defaults
    node_group.inputs["Tree Density"].default_value = 0.3
    node_group.inputs["Grass Density"].default_value = 0.5
    node_group.inputs["Min Distance"].default_value = 3.0

    # Group Input/Output
    gi = nodes.new("NodeGroupInput")
    gi.location = (0, 0)

    go = nodes.new("NodeGroupOutput")
    go.location = (1800, 0)

    # ========================================
    # Distribute points on terrain
    # ========================================
    distribute_points = nodes.new("GeometryNodeDistributePointsOnFaces")
    distribute_points.location = (200, 200)
    distribute_points.inputs["Density"].default_value = 0.001  # Per square meter

    # ========================================
    # Proximity check for exclusion zones
    # ========================================
    proximity = nodes.new("GeometryNodeProximity")
    proximity.location = (200, -100)
    proximity.inputs["Target Geometry"].default_value = None

    # Compare distance
    compare = nodes.new("FunctionNodeCompare")
    compare.location = (400, -100)
    compare.operation = 'GREATER_THAN'

    # ========================================
    # Delete points too close to exclusion zones
    # ========================================
    delete_close = nodes.new("GeometryNodeDeleteGeometry")
    delete_close.location = (600, 100)

    # ========================================
    # Random selection based on density
    # ========================================
    random_value = nodes.new("FunctionNodeRandomValue")
    random_value.location = (400, 0)
    random_value.inputs["Probability"].default_value = 0.3

    select_points = nodes.new("GeometryNodeDeleteGeometry")
    select_points.location = (800, 100)

    # ========================================
    # Instance trees at points
    # ========================================
    instance_tree = nodes.new("GeometryNodeInstanceOnPoints")
    instance_tree.location = (1000, 100)

    # Tree instance (simple cone for now - real would use collection)
    tree_cone = nodes.new("GeometryNodeMeshCone")
    tree_cone.location = (800, 300)
    tree_cone.inputs["Radius Top"].default_value = 0.0
    tree_cone.inputs["Radius Bottom"].default_value = 2.0
    tree_cone.inputs["Depth"].default_value = 8.0
    tree_cone.inputs["Vertices"].default_value = 8

    tree_transform = nodes.new("GeometryNodeTransform")
    tree_transform.location = (1000, 300)
    tree_transform.inputs["Translation"].default_value = (0, 0, 4.0)

    # ========================================
    # Store vegetation attributes
    # ========================================
    store_type = nodes.new("GeometryNodeStoreNamedAttribute")
    store_type.location = (1200, 100)
    store_type.inputs["Name"].default_value = "vegetation_type"
    store_type.inputs["Data Type"].default_value = "INT"

    type_val = nodes.new("FunctionNodeInputInt")
    type_val.location = (1000, -100)
    type_val.outputs[0].default_value = 0  # Tree type

    store_height = nodes.new("GeometryNodeStoreNamedAttribute")
    store_height.location = (1400, 100)
    store_height.inputs["Name"].default_value = "tree_height"
    store_height.inputs["Data Type"].default_value = "FLOAT"

    # Realize
    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (1600, 100)

    # ========================================
    # Wire connections
    # ========================================
    links.new(gi.outputs["Terrain"], distribute_points.inputs["Mesh"])

    # Note: Exclusion zone proximity would need proper geometry input
    # This is simplified for the node group structure

    links.new(distribute_points.outputs["Points"], select_points.inputs["Geometry"])
    links.new(random_value.outputs["Value"], select_points.inputs["Selection"])

    links.new(select_points.outputs["Geometry"], instance_tree.inputs["Points"])
    links.new(tree_cone.outputs["Mesh"], tree_transform.inputs["Geometry"])
    links.new(tree_transform.outputs["Geometry"], instance_tree.inputs["Instance"])

    links.new(instance_tree.outputs["Instances"], store_type.inputs["Geometry"])
    links.new(type_val.outputs[0], store_type.inputs["Value"])

    links.new(store_type.outputs["Geometry"], store_height.inputs["Geometry"])
    links.new(store_height.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    return node_group


# =============================================================================
# STREET FURNITURE NODE GROUPS
# =============================================================================

def create_bench_node_group(name: str = "Bench_Generator") -> Optional[bpy.types.NodeGroup]:
    """Create geometry node group for a park bench."""
    if not BLENDER_AVAILABLE:
        return None

    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    node_group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nodes = node_group.nodes
    links = node_group.links

    interface = node_group.interface
    interface.new_socket("Rotation", socket_type="NodeSocketFloat", in_out="INPUT")
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    node_group.inputs["Rotation"].default_value = 0.0

    gi = nodes.new("NodeGroupInput")
    gi.location = (0, 0)

    go = nodes.new("NodeGroupOutput")
    go.location = (1200, 0)

    # Bench seat (box)
    seat = nodes.new("GeometryNodeMeshCube")
    seat.location = (200, 0)
    seat.inputs["Size X"].default_value = 1.5
    seat.inputs["Size Y"].default_value = 0.4
    seat.inputs["Size Z"].default_value = 0.05

    seat_transform = nodes.new("GeometryNodeTransform")
    seat_transform.location = (400, 0)
    seat_transform.inputs["Translation"].default_value = (0, 0, 0.45)

    # Bench legs (2 small boxes)
    leg1 = nodes.new("GeometryNodeMeshCube")
    leg1.location = (200, -150)
    leg1.inputs["Size X"].default_value = 0.08
    leg1.inputs["Size Y"].default_value = 0.35
    leg1.inputs["Size Z"].default_value = 0.4

    leg1_transform = nodes.new("GeometryNodeTransform")
    leg1_transform.location = (400, -150)
    leg1_transform.inputs["Translation"].default_value = (0.6, 0, 0.2)

    leg2_transform = nodes.new("GeometryNodeTransform")
    leg2_transform.location = (400, -250)
    leg2_transform.inputs["Translation"].default_value = (-0.6, 0, 0.2)

    # Backrest
    back = nodes.new("GeometryNodeMeshCube")
    back.location = (200, 100)
    back.inputs["Size X"].default_value = 1.5
    back.inputs["Size Y"].default_value = 0.03
    back.inputs["Size Z"].default_value = 0.5

    back_transform = nodes.new("GeometryNodeTransform")
    back_transform.location = (400, 100)
    back_transform.inputs["Translation"].default_value = (0, -0.15, 0.7)

    # Join
    join = nodes.new("GeometryNodeJoinGeometry")
    join.location = (600, 0)

    # Final rotation
    final_transform = nodes.new("GeometryNodeTransform")
    final_transform.location = (800, 0)

    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (1000, 0)

    # Wire
    links.new(seat.outputs["Mesh"], seat_transform.inputs["Geometry"])
    links.new(leg1.outputs["Mesh"], leg1_transform.inputs["Geometry"])
    links.new(leg1.outputs["Mesh"], leg2_transform.inputs["Geometry"])
    links.new(back.outputs["Mesh"], back_transform.inputs["Geometry"])

    links.new(seat_transform.outputs["Geometry"], join.inputs["Geometry"])
    links.new(leg1_transform.outputs["Geometry"], join.inputs["Geometry"])
    links.new(leg2_transform.outputs["Geometry"], join.inputs["Geometry"])
    links.new(back_transform.outputs["Geometry"], join.inputs["Geometry"])

    links.new(join.outputs["Geometry"], final_transform.inputs["Geometry"])
    links.new(gi.outputs["Rotation"], final_transform.inputs["Rotation"].subscript(2))

    links.new(final_transform.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    return node_group


def create_trash_can_node_group(name: str = "TrashCan_Generator") -> Optional[bpy.types.NodeGroup]:
    """Create geometry node group for a trash can."""
    if not BLENDER_AVAILABLE:
        return None

    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    node_group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nodes = node_group.nodes
    links = node_group.links

    interface = node_group.interface
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    go = nodes.new("NodeGroupOutput")
    go.location = (800, 0)

    # Cylinder body
    body = nodes.new("GeometryNodeMeshCylinder")
    body.location = (200, 0)
    body.inputs["Radius"].default_value = 0.25
    body.inputs["Depth"].default_value = 1.0
    body.inputs["Vertices"].default_value = 16

    transform = nodes.new("GeometryNodeTransform")
    transform.location = (400, 0)
    transform.inputs["Translation"].default_value = (0, 0, 0.5)

    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (600, 0)

    links.new(body.outputs["Mesh"], transform.inputs["Geometry"])
    links.new(transform.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    return node_group


def create_fire_hydrant_node_group(name: str = "FireHydrant_Generator") -> Optional[bpy.types.NodeGroup]:
    """Create geometry node group for a fire hydrant."""
    if not BLENDER_AVAILABLE:
        return None

    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])

    node_group = bpy.data.node_groups.new(name, "GeometryNodeTree")
    nodes = node_group.nodes
    links = node_group.links

    interface = node_group.interface
    interface.new_socket("Geometry", socket_type="NodeSocketGeometry", in_out="OUTPUT")

    go = nodes.new("NodeGroupOutput")
    go.location = (1000, 0)

    # Main body (cylinder)
    body = nodes.new("GeometryNodeMeshCylinder")
    body.location = (200, 0)
    body.inputs["Radius"].default_value = 0.12
    body.inputs["Depth"].default_value = 0.6
    body.inputs["Vertices"].default_value = 12

    body_transform = nodes.new("GeometryNodeTransform")
    body_transform.location = (400, 0)
    body_transform.inputs["Translation"].default_value = (0, 0, 0.3)

    # Cap (sphere)
    cap = nodes.new("GeometryNodeMeshIcoSphere")
    cap.location = (200, -100)
    cap.inputs["Radius"].default_value = 0.13
    cap.inputs["Subdivisions"].default_value = 2

    cap_transform = nodes.new("GeometryNodeTransform")
    cap_transform.location = (400, -100)
    cap_transform.inputs["Translation"].default_value = (0, 0, 0.6)

    # Side outlet (small cylinder)
    outlet = nodes.new("GeometryNodeMeshCylinder")
    outlet.location = (200, -200)
    outlet.inputs["Radius"].default_value = 0.05
    outlet.inputs["Depth"].default_value = 0.15
    outlet.inputs["Vertices"].default_value = 8

    outlet_transform = nodes.new("GeometryNodeTransform")
    outlet_transform.location = (400, -200)
    outlet_transform.inputs["Translation"].default_value = (0.15, 0, 0.35)
    outlet_transform.inputs["Rotation"].default_value = (0, 1.5708, 0)

    # Join
    join = nodes.new("GeometryNodeJoinGeometry")
    join.location = (600, 0)

    realize = nodes.new("GeometryNodeRealizeInstances")
    realize.location = (800, 0)

    links.new(body.outputs["Mesh"], body_transform.inputs["Geometry"])
    links.new(cap.outputs["Mesh"], cap_transform.inputs["Geometry"])
    links.new(outlet.outputs["Mesh"], outlet_transform.inputs["Geometry"])

    links.new(body_transform.outputs["Geometry"], join.inputs["Geometry"])
    links.new(cap_transform.outputs["Geometry"], join.inputs["Geometry"])
    links.new(outlet_transform.outputs["Geometry"], join.inputs["Geometry"])

    links.new(join.outputs["Geometry"], realize.inputs["Geometry"])
    links.new(realize.outputs["Geometry"], go.inputs["Geometry"])

    return node_group


# =============================================================================
# PLACEMENT FUNCTIONS
# =============================================================================

def get_footway_curves() -> List[bpy.types.Object]:
    """Get all footway curves from scene."""
    return [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'CURVE' and obj.get('highway_type') == 'footway'
    ]


def calculate_sidewalk_positions(footways: List[bpy.types.Object]) -> List[Dict]:
    """Calculate sidewalk positions from footways."""
    positions = []

    for footway in footways:
        if not footway.data.splines:
            continue

        spline = footway.data.splines[0]
        points = [footway.matrix_world @ Vector(p.co[:3]) for p in spline.points]

        positions.append({
            'curve': footway,
            'points': points,
            'width': 1.5,
            'name': footway.get('name', footway.name),
        })

    return positions


def calculate_tree_positions(
    road_curves: List[bpy.types.Object],
    terrain_bounds: Tuple[float, float, float, float],
    config: VegetationConfig
) -> List[Dict]:
    """Calculate tree positions avoiding roads and buildings."""
    positions = []
    min_x, min_y, max_x, max_y = terrain_bounds

    # Collect road/building exclusion zones
    exclusion_zones = []

    for road in road_curves:
        if not road.data.splines:
            continue
        spline = road.data.splines[0]
        points = [road.matrix_world @ Vector(p.co[:3]) for p in spline.points]

        # Buffer road by offset
        road_width = road.get('road_width', 7.0)
        buffer = road_width / 2 + config.tree_offset

        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            direction = (p2 - p1).normalized()
            perpendicular = Vector((-direction.y, direction.x, 0))

            # Tree position on right side
            right_pos = (p1 + p2) / 2 + perpendicular * buffer

            positions.append({
                'position': right_pos,
                'tree_type': random.choice(list(TreeType)),
                'height': random.uniform(config.min_tree_height, config.max_tree_height),
                'road_name': road.get('name', ''),
            })

    return positions


def calculate_furniture_positions(
    sidewalk_positions: List[Dict],
    config: FurnitureConfig
) -> Dict[str, List[Dict]]:
    """Calculate street furniture positions along sidewalks."""
    furniture = {
        'benches': [],
        'trash_cans': [],
        'fire_hydrants': [],
        'mailboxes': [],
    }

    bench_dist = 0
    trash_dist = 0
    hydrant_dist = 0
    mailbox_dist = 0

    for sidewalk in sidewalk_positions:
        points = sidewalk['points']
        if len(points) < 2:
            continue

        # Calculate total length
        total_length = sum(
            (points[i+1] - points[i]).length
            for i in range(len(points) - 1)
        )

        # Place furniture at intervals
        current_dist = 0

        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i+1]
            segment_length = (p2 - p1).length
            direction = (p2 - p1).normalized()
            perpendicular = Vector((-direction.y, direction.x, 0))

            # Offset to edge of sidewalk
            offset = sidewalk['width'] / 2 - 0.3

            # Check each furniture type
            if current_dist >= config.bench_spacing - bench_dist:
                pos = p1 + perpendicular * offset
                furniture['benches'].append({
                    'position': pos,
                    'rotation': math.atan2(direction.y, direction.x) + math.pi/2,
                })
                bench_dist = current_dist

            if current_dist >= config.trash_can_spacing - trash_dist:
                pos = p1 + perpendicular * offset
                furniture['trash_cans'].append({
                    'position': pos,
                })
                trash_dist = current_dist

            if current_dist >= config.fire_hydrant_spacing - hydrant_dist:
                pos = p1 + perpendicular * offset
                furniture['fire_hydrants'].append({
                    'position': pos,
                })
                hydrant_dist = current_dist

            if current_dist >= config.mailbox_spacing - mailbox_dist:
                pos = p1 + perpendicular * offset
                furniture['mailboxes'].append({
                    'position': pos,
                })
                mailbox_dist = current_dist

            current_dist += segment_length

    return furniture


# =============================================================================
# MAIN GENERATOR
# =============================================================================

def generate_all_environment() -> Dict[str, int]:
    """
    Generate all environment elements.

    Returns:
        Dict with counts of generated objects
    """
    if not BLENDER_AVAILABLE:
        return {'error': 'Blender not available'}

    print("\n=== Generating Environment ===")

    stats = {
        'terrain': 0,
        'sidewalks': 0,
        'trees': 0,
        'benches': 0,
        'trash_cans': 0,
        'fire_hydrants': 0,
        'errors': 0,
    }

    # Create node groups
    terrain_ng = create_terrain_node_group()
    sidewalk_ng = create_sidewalk_node_group()
    vegetation_ng = create_vegetation_scatter_node_group()
    bench_ng = create_bench_node_group()
    trash_ng = create_trash_can_node_group()
    hydrant_ng = create_fire_hydrant_node_group()

    # Create collections
    collections = {}
    for name in ['Terrain', 'Sidewalks', 'Vegetation', 'Street_Furniture']:
        if name not in bpy.data.collections:
            coll = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(coll)
        collections[name] = bpy.data.collections[name]

    # Sub-collections for furniture
    for subname in ['Benches', 'Trash_Cans', 'Fire_Hydrants', 'Mailboxes']:
        if subname not in collections['Street_Furniture'].children:
            coll = bpy.data.collections.new(subname)
            collections['Street_Furniture'].children.link(coll)

    # ========================================
    # Generate Terrain
    # ========================================
    print("Generating terrain...")
    try:
        # Get bounds from road curves
        road_curves = [
            obj for obj in bpy.context.scene.objects
            if obj.type == 'CURVE' and obj.get('road_class')
        ]

        if road_curves:
            all_points = []
            for curve in road_curves:
                if curve.data.splines:
                    for spline in curve.data.splines:
                        for p in spline.points:
                            all_points.append(curve.matrix_world @ Vector(p.co[:3]))

            if all_points:
                min_x = min(p.x for p in all_points) - 100
                max_x = max(p.x for p in all_points) + 100
                min_y = min(p.y for p in all_points) - 100
                max_y = max(p.y for p in all_points) + 100

                terrain_obj = bpy.data.objects.new("Terrain", None)
                mod = terrain_obj.modifiers.new(name="Terrain", type='NODES')
                mod.node_group = terrain_ng
                mod["Size X"] = max_x - min_x
                mod["Size Y"] = max_y - min_y
                terrain_obj.location = (min_x, min_y, 0)

                bpy.context.collection.objects.link(terrain_obj)
                collections['Terrain'].objects.link(terrain_obj)
                stats['terrain'] = 1

    except Exception as e:
        print(f"Error generating terrain: {e}")
        stats['errors'] += 1

    # ========================================
    # Generate Sidewalks
    # ========================================
    print("Generating sidewalks...")
    try:
        footways = get_footway_curves()
        print(f"Found {len(footways)} footways")

        for footway in footways:
            try:
                # Apply sidewalk modifier to footway curve
                mod = footway.modifiers.new(name="Sidewalk", type='NODES')
                mod.node_group = sidewalk_ng
                mod["Width"] = 1.5
                mod["Height"] = 0.15

                # Move to sidewalk collection
                for c in list(footway.users_collection):
                    c.objects.unlink(footway)
                collections['Sidewalks'].objects.link(footway)
                stats['sidewalks'] += 1

            except Exception as e:
                stats['errors'] += 1

    except Exception as e:
        print(f"Error generating sidewalks: {e}")
        stats['errors'] += 1

    # ========================================
    # Generate Trees
    # ========================================
    print("Generating vegetation...")
    try:
        road_curves = [
            obj for obj in bpy.context.scene.objects
            if obj.type == 'CURVE' and obj.get('road_class')
        ]

        tree_config = VegetationConfig()
        tree_positions = calculate_tree_positions(
            road_curves,
            (0, 0, 5000, 5000),  # Placeholder bounds
            tree_config
        )

        # Create tree instances (simplified cone trees)
        for tree_data in tree_positions[:500]:  # Limit for performance
            try:
                tree_obj = bpy.data.objects.new(
                    f"Tree_{stats['trees']}",
                    None
                )
                tree_obj.location = tree_data['position']

                mod = tree_obj.modifiers.new(name="Tree", type='NODES')
                # Use a simple cone mesh

                bpy.context.collection.objects.link(tree_obj)
                collections['Vegetation'].objects.link(tree_obj)
                stats['trees'] += 1

            except Exception:
                stats['errors'] += 1

    except Exception as e:
        print(f"Error generating vegetation: {e}")
        stats['errors'] += 1

    # ========================================
    # Generate Street Furniture
    # ========================================
    print("Generating street furniture...")
    try:
        furniture_config = FurnitureConfig()
        # Would need sidewalk positions for this
        # Simplified placement for now

    except Exception as e:
        print(f"Error generating furniture: {e}")
        stats['errors'] += 1

    print(f"\n=== Summary ===")
    print(f"Terrain: {stats['terrain']}")
    print(f"Sidewalks: {stats['sidewalks']}")
    print(f"Trees: {stats['trees']}")
    print(f"Errors: {stats['errors']}")

    return stats


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    generate_all_environment()
