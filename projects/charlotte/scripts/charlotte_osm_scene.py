"""
Charlotte 277 Highway Scene - Real OSM Data Integration

Creates a scene using actual OpenStreetMap data for Charlotte's I-277 highway
and downtown buildings.

Uses the charlotte_digital_twin module for data acquisition and geometry generation.

Usage:
    blender --background --python projects/charlotte/scripts/charlotte_osm_scene.py
"""

import bpy
import math
import sys
import os
from pathlib import Path

# Find the project root by looking for the lib directory
# When run with --python, __file__ may not be reliable
script_path = Path(__file__).resolve() if '__file__' in dir() else Path(os.getcwd()) / "projects/charlotte/scripts/charlotte_osm_scene.py"
project_root = script_path.parent.parent.parent  # scripts -> charlotte -> projects -> blender_gsd

# Fallback if that doesn't work
if not (project_root / "lib").exists():
    # Try absolute path
    project_root = Path("/Users/bretbouchard/apps/blender_gsd")

# Change to project root and add to path
os.chdir(str(project_root))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now we can safely import other modules
from mathutils import Vector, Euler
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

# Import Charlotte Digital Twin modules
from lib.charlotte_digital_twin.data_acquisition import OSMDownloader, OverpassClient
from lib.charlotte_digital_twin.geometry import (
    GeometryConfig,
    SceneOrigin,
    CoordinateTransformer,
    CHARLOTTE_ORIGINS,
    DetailLevel,
    RoadType,
    BuildingType,
    RoadSegment,
    BuildingFootprint,
)


# === DOWNTOWN CHARLOTTE BOUNDS ===
# Tighter bounds around downtown for I-277 loop
DOWNTOWN_BOUNDS = {
    "north": 35.235,   # North of I-277
    "south": 35.215,   # South of I-277
    "east": -80.825,   # East side
    "west": -80.865,   # West side
}

# Scene mode: "full_downtown" or "i277_only"
SCENE_MODE = "i277_only"


@dataclass
class SceneOriginLocal:
    """Local scene origin definition."""
    lat: float
    lon: float
    name: str = "origin"


# Scene origin - Charlotte downtown center
SCENE_ORIGIN = SceneOriginLocal(
    lat=35.2271,
    lon=-80.8431,
    name="downtown_charlotte",
)


@dataclass
class RealRoadSegment:
    """Road segment from OSM data."""
    osm_id: int
    name: str
    highway_type: str
    coordinates: List[Tuple[float, float, float]]  # World coordinates
    lanes: int
    oneway: bool
    is_bridge: bool
    is_tunnel: bool


@dataclass
class RealBuilding:
    """Building from OSM data."""
    osm_id: int
    name: str
    building_type: str
    footprint: List[Tuple[float, float, float]]  # World coordinates
    height: Optional[float]
    levels: Optional[int]


def clear_scene():
    """Clear existing objects for clean scene."""
    bpy.ops.object.select_all(action='DESELECT')

    for obj in bpy.data.objects:
        obj.select_set(True)

    bpy.ops.object.delete()

    # Clear orphaned data
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for mat in bpy.data.materials:
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    for curve in bpy.data.curves:
        if curve.users == 0:
            bpy.data.curves.remove(curve)


def download_osm_data(bounds: Dict[str, float]) -> Any:
    """Download OSM data for the specified bounds."""
    print("\n[DATA] Downloading OSM data for downtown Charlotte...")
    print(f"  Bounds: {bounds['south']:.4f}, {bounds['west']:.4f} to {bounds['north']:.4f}, {bounds['east']:.4f}")

    downloader = OSMDownloader()

    try:
        osm_data = downloader.download_charlotte_extract(bounds=bounds)
        print(f"  Downloaded: {len(osm_data.nodes)} nodes, {len(osm_data.ways)} ways")
        return osm_data
    except Exception as e:
        print(f"  Error downloading OSM data: {e}")
        print("  Falling back to cached data or simplified geometry...")
        return None


def extract_highways(osm_data: Any, transformer: CoordinateTransformer, i277_only: bool = False) -> List[RealRoadSegment]:
    """Extract highway segments from OSM data.

    Args:
        osm_data: OSM data object
        transformer: Coordinate transformer
        i277_only: If True, only extract I-277 segments for car chase scene
    """
    print("\n[ROADS] Extracting highways from OSM data...")
    if i277_only:
        print("  Mode: I-277 highway only (car chase focus)")

    highways = []

    if i277_only:
        # Only motorways for I-277 scene
        highway_types = {"motorway", "motorway_link"}
    else:
        # Full downtown includes all major roads
        highway_types = {"motorway", "motorway_link", "trunk", "trunk_link", "primary"}

    downloader = OSMDownloader()
    raw_roads = downloader.extract_roads(osm_data, highway_types)

    i277_names = {"I 277", "I-277", "Interstate 277", "John Belk Freeway", "Brookshire Freeway"}

    for road in raw_roads:
        # Filter for I-277 only if requested
        if i277_only:
            road_name = road.get("name", "")
            # Check if this is I-277 (by name or ref tag)
            is_i277 = (
                road_name in i277_names or
                road.get("ref", "") in i277_names or
                "277" in road_name or
                "277" in road.get("ref", "")
            )
            if not is_i277:
                continue

        # Transform coordinates to world space
        world_coords = []
        for coord in road["coordinates"]:
            world = transformer.latlon_to_world(coord["lat"], coord["lon"])
            world_coords.append((world.x, world.y, world.z))

        if len(world_coords) < 2:
            continue

        # Parse lanes
        lanes = 2
        if road.get("lanes"):
            try:
                lanes = int(road["lanes"])
            except ValueError:
                pass

        segment = RealRoadSegment(
            osm_id=road["osm_id"],
            name=road.get("name", ""),
            highway_type=road["highway_type"],
            coordinates=world_coords,
            lanes=lanes,
            oneway=road.get("oneway", False),
            is_bridge=road.get("bridge", False),
            is_tunnel=road.get("tunnel", False),
        )
        highways.append(segment)

    print(f"  Extracted {len(highways)} highway segments")
    return highways


def extract_buildings(osm_data: Any, transformer: CoordinateTransformer) -> List[RealBuilding]:
    """Extract buildings from OSM data."""
    print("\n[BUILDINGS] Extracting buildings from OSM data...")

    buildings = []
    downloader = OSMDownloader()
    raw_buildings = downloader.extract_buildings(osm_data, min_height=10)  # Only buildings 10m+

    for building in raw_buildings:
        # Transform footprint to world coordinates
        footprint = []
        for coord in building["footprint"]:
            world = transformer.latlon_to_world(coord["lat"], coord["lon"])
            footprint.append((world.x, world.y, world.z))

        if len(footprint) < 3:
            continue

        # Parse height
        height = building.get("height")
        if height:
            try:
                height = float(height)
            except (ValueError, TypeError):
                height = None

        # Parse levels
        levels = building.get("levels")
        if levels:
            try:
                levels = int(levels)
            except (ValueError, TypeError):
                levels = None

        bldg = RealBuilding(
            osm_id=building["osm_id"],
            name=building.get("name", ""),
            building_type=building.get("building_type", "yes"),
            footprint=footprint,
            height=height,
            levels=levels,
        )
        buildings.append(bldg)

    print(f"  Extracted {len(buildings)} buildings")
    return buildings


def create_road_mesh(segment: RealRoadSegment, collection) -> bpy.types.Object:
    """Create a mesh object for a road segment using skin modifier for simplicity."""
    # Determine road width based on type and lanes
    width_map = {
        "motorway": 3.7 * segment.lanes,  # ~3.7m per lane
        "motorway_link": 3.5 * segment.lanes,
        "trunk": 3.5 * segment.lanes,
        "primary": 3.0 * segment.lanes,
    }
    road_width = width_map.get(segment.highway_type, 6.0)

    # Create a simple mesh from coordinates as a polyline
    # Use a skin modifier approach for simpler geometry
    coords = segment.coordinates
    if len(coords) < 2:
        return None

    # Create mesh with edges
    mesh = bpy.data.meshes.new(f"Road_{segment.osm_id}")

    # Add vertices
    vertices = [(x, y, z + 0.02) for x, y, z in coords]  # Slightly above ground
    edges = [(i, i + 1) for i in range(len(coords) - 1)]

    mesh.from_pydata(vertices, edges, [])
    mesh.update()

    obj = bpy.data.objects.new(f"Road_{segment.osm_id}", mesh)
    collection.objects.link(obj)

    # Add skin modifier for width
    skin = obj.modifiers.new(name="Skin", type='SKIN')
    skin.use_smooth_shade = True

    # Set skin radius for all vertices
    for v in obj.data.skin_vertices[0].data:
        v.radius = (road_width / 2, road_width / 2)

    # Add subdivision for smoother appearance
    subsurf = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 1
    subsurf.render_levels = 1

    # Material - brighter for visibility
    mat = bpy.data.materials.new(name=f"RoadMat_{segment.highway_type}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        # Light gray for visibility (darker roads were invisible in renders)
        gray = 0.55 if segment.highway_type == "motorway" else 0.60
        bsdf.inputs["Base Color"].default_value = (gray, gray, gray, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.7
        bsdf.inputs["Metallic"].default_value = 0.0

    obj.data.materials.append(mat)

    return obj


def create_building_mesh(building: RealBuilding, collection) -> bpy.types.Object:
    """Create extruded building mesh from footprint."""
    if len(building.footprint) < 3:
        return None

    # Calculate building height
    if building.height:
        height = building.height
    elif building.levels:
        height = building.levels * 4.0  # ~4m per floor
    else:
        height = 20.0  # Default height

    # Create mesh from footprint
    mesh = bpy.data.meshes.new(f"Building_{building.osm_id}")

    # Vertices: bottom ring + top ring
    vertices = []
    for x, y, z in building.footprint:
        vertices.append((x, y, z))  # Bottom
    for x, y, z in building.footprint:
        vertices.append((x, y, z + height))  # Top

    # Faces: bottom, top, sides
    n = len(building.footprint)
    faces = []

    # Bottom face (reversed for normals)
    bottom_face = list(range(n-1, -1, -1))
    faces.append(bottom_face)

    # Top face
    top_face = list(range(n, 2*n))
    faces.append(top_face)

    # Side faces
    for i in range(n):
        next_i = (i + 1) % n
        faces.append([i, next_i, n + next_i, n + i])

    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(f"Building_{building.osm_id}", mesh)
    collection.objects.link(obj)

    # Material based on building type
    mat = bpy.data.materials.new(name=f"BuildingMat_{building.building_type}")
    if mat.node_tree:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Color based on type
            if "office" in building.building_type or "commercial" in building.building_type:
                color = (0.4, 0.42, 0.45, 1.0)  # Blue-gray glass
            elif "residential" in building.building_type:
                color = (0.55, 0.5, 0.45, 1.0)  # Brown/tan
            else:
                color = (0.5, 0.5, 0.52, 1.0)  # Gray

            bsdf.inputs["Base Color"].default_value = color
            bsdf.inputs["Roughness"].default_value = 0.4
            bsdf.inputs["Metallic"].default_value = 0.1

    obj.data.materials.append(mat)

    return obj


def create_ground_plane(size: float = 5000, center: Tuple[float, float] = (0, 0)):
    """Create ground plane.

    Args:
        size: Size of the ground plane in meters
        center: (X, Y) center position of the ground plane
    """
    bpy.ops.mesh.primitive_plane_add(size=size, location=(center[0], center[1], -0.1))
    ground = bpy.context.active_object
    ground.name = "Charlotte_Ground"

    mat = bpy.data.materials.new(name="Ground_Mat")
    if mat.node_tree:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.12, 0.15, 0.12, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.95

    ground.data.materials.append(mat)
    return ground


def create_lighting():
    """Create sun lighting."""
    sun_data = bpy.data.lights.new("Sun", type='SUN')
    sun_obj = bpy.data.objects.new("Sun", sun_data)
    sun_obj.location = (100, 100, 300)
    sun_obj.rotation_euler = Euler((0.6, 0.2, 0.5), 'XYZ')

    sun_data.energy = 3.5
    sun_data.color = (1.0, 0.95, 0.9)

    bpy.context.collection.objects.link(sun_obj)

    # World lighting
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    if world.node_tree:
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs["Color"].default_value = (0.5, 0.6, 0.8, 1.0)
            bg.inputs["Strength"].default_value = 1.0

    return sun_obj


def create_camera(target_objects: List[bpy.types.Object], height: float = 150, center: Tuple[float, float] = None):
    """Create camera positioned to see the scene.

    Args:
        target_objects: Objects to frame (can be empty list)
        height: Camera height in meters
        center: Optional (X, Y) center position. If None, calculates from objects.
    """
    # Calculate scene center
    if center:
        cx, cy = center
    elif target_objects:
        center_vec = Vector((0, 0, 0))
        for obj in target_objects:
            center_vec += obj.location
        center_vec /= len(target_objects)
        cx, cy = center_vec.x, center_vec.y
    else:
        cx, cy = 0, 0

    cam_data = bpy.data.cameras.new("Main_Camera")
    cam_obj = bpy.data.objects.new("Main_Camera", cam_data)

    # Camera geometry:
    # - Camera at (cx, cy - d, h) with 60° pitch down
    # - Looking direction with 60° X rotation: forward is (0, 0.866, -0.5)
    # - Ground intersection from (cy - d) at height h:
    #   (cy - d) + h * (0.866 / 0.5) = (cy - d) + 1.732 * h
    # - For this to equal cy (scene center): d = 1.732 * h

    pitch_degrees = 60.0
    pitch_rad = math.radians(pitch_degrees)
    forward_y = math.sin(pitch_rad)  # 0.866
    forward_z = -math.cos(pitch_rad)  # -0.5

    # Distance back so camera looks at scene center
    camera_distance = height * (forward_y / (-forward_z))  # h * 0.866/0.5 = 1.732 * h

    # Position camera
    cam_obj.location = (cx, cy - camera_distance, height)
    cam_obj.rotation_euler = Euler((pitch_rad, 0, 0), 'XYZ')

    bpy.context.collection.objects.link(cam_obj)

    cam_data.lens = 50
    cam_data.clip_start = 0.1
    cam_data.clip_end = 10000

    bpy.context.scene.camera = cam_obj

    print(f"  Camera at ({cx:.1f}, {cy - camera_distance:.1f}, {height:.1f}) looking at scene center ({cx:.1f}, {cy:.1f})")

    return cam_obj


def create_hero_car():
    """Create a simple but visible car for the animation."""
    # Create car body at origin - will be positioned via parent
    bpy.ops.mesh.primitive_cube_add()
    car = bpy.context.active_object
    car.name = "Hero_Car"
    # Sports car proportions: ~4.5m long, 2m wide, 1.2m tall
    car.scale = (2.25, 1.0, 0.6)
    car.location = (0, 0, 0)  # Origin - will be offset via parent

    # Bright red sports car material - very visible
    mat = bpy.data.materials.new(name="Car_Red")
    if mat.node_tree:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.9, 0.1, 0.1, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.8
            bsdf.inputs["Roughness"].default_value = 0.2
    car.data.materials.append(mat)

    # Create wheels at local positions relative to car
    wheel_positions = [
        (1.4, 0.7, -0.3),   # Front right
        (1.4, -0.7, -0.3),  # Front left
        (-1.4, 0.7, -0.3),  # Rear right
        (-1.4, -0.7, -0.3), # Rear left
    ]

    wheel_radius = 0.35
    wheels = []

    for i, (x, y, z) in enumerate(wheel_positions):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=wheel_radius,
            depth=0.25,
            rotation=(0, math.pi/2, 0)
        )
        wheel = bpy.context.active_object
        wheel.name = f"Hero_Car_Wheel_{i}"
        wheel.location = (x, y, z)
        wheel.parent = car

        wmat = bpy.data.materials.new(name=f"TireMat_{i}")
        if wmat.node_tree:
            wbsdf = wmat.node_tree.nodes.get("Principled BSDF")
            if wbsdf:
                wbsdf.inputs["Base Color"].default_value = (0.1, 0.1, 0.1, 1.0)
        wheel.data.materials.append(wmat)
        wheels.append(wheel)

    car["launch_control_version"] = "1.0"
    car["vehicle_type"] = "sports_car"
    car["max_speed_kmh"] = 320.0

    return car, wheels


def create_combined_path_curve(road_segments: List[RealRoadSegment]) -> bpy.types.Object:
    """Create a single continuous path curve from road segments for car animation."""
    if not road_segments:
        return None

    # Collect all coordinates and find the longest continuous path
    # For I-277, we'll connect segments that share endpoints
    all_coords = []
    for segment in road_segments:
        for coord in segment.coordinates:
            all_coords.append(coord)

    if len(all_coords) < 2:
        return None

    # Debug: print scene bounds
    min_x = min(c[0] for c in all_coords)
    max_x = max(c[0] for c in all_coords)
    min_y = min(c[1] for c in all_coords)
    max_y = max(c[1] for c in all_coords)
    print(f"  Road network bounds: X({min_x:.1f} to {max_x:.1f}), Y({min_y:.1f} to {max_y:.1f})")
    print(f"  Scene center: ({(min_x+max_x)/2:.1f}, {(min_y+max_y)/2:.1f})")

    # Create curve from all coordinates
    # Sample every Nth point to simplify the path
    sample_rate = max(1, len(all_coords) // 100)
    sampled_coords = all_coords[::sample_rate]

    curve = bpy.data.curves.new("I277_Animation_Path", type='CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = 0.0
    curve.fill_mode = 'FULL'

    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(sampled_coords) - 1)

    for i, (x, y, z) in enumerate(sampled_coords):
        bp = spline.bezier_points[i]
        bp.co = (x, y, z + 0.5)  # Raise slightly above road
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    path_obj = bpy.data.objects.new("I277_Animation_Path", curve)
    bpy.context.collection.objects.link(path_obj)

    return path_obj


def create_car_animation(car, path_obj, duration_frames=720):
    """Create path following animation with car."""
    # Create an empty to follow the path
    empty = bpy.data.objects.new("Car_Path_Follower", None)
    empty.empty_display_type = 'PLAIN_AXES'
    bpy.context.collection.objects.link(empty)

    # Apply Follow Path constraint
    constraint = empty.constraints.new('FOLLOW_PATH')
    constraint.target = path_obj
    constraint.use_curve_follow = True
    constraint.use_fixed_location = True
    constraint.forward_axis = 'FORWARD_X'
    constraint.up_axis = 'UP_Z'

    # Animate the offset_factor
    constraint.offset_factor = 0.0
    empty.keyframe_insert(data_path='constraints["Follow Path"].offset_factor', frame=1)

    constraint.offset_factor = 1.0
    empty.keyframe_insert(data_path='constraints["Follow Path"].offset_factor', frame=duration_frames)

    # Set interpolation to LINEAR for constant speed
    try:
        if empty.animation_data and empty.animation_data.action:
            action = empty.animation_data.action
            for fcurve in action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'LINEAR'
    except Exception as e:
        print(f"  Note: Could not set interpolation ({e})")

    # Parent the car to the empty
    car.parent = empty
    car.location.x = 0
    car.location.y = -5.0  # Right lane offset
    car.location.z = 0.5
    car.rotation_euler = Euler((0, 0, 0), 'XYZ')

    # Set animation range
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = duration_frames

    return empty


def create_chase_camera(path_follower, height=35, angle=60):
    """Create chase camera parented to the car's path follower.

    Args:
        path_follower: The empty object following the path
        height: Height above the car in meters
        angle: Camera pitch angle in degrees (60 = angled down, 90 = straight down)
    """
    cam_data = bpy.data.cameras.new("Chase_Camera")
    cam_obj = bpy.data.objects.new("Chase_Camera", cam_data)

    bpy.context.collection.objects.link(cam_obj)

    cam_data.type = 'PERSP'
    cam_data.lens = 35  # Wider lens for more context
    cam_data.clip_end = 1000

    # Parent camera to the same path follower as the car
    cam_obj.parent = path_follower

    # Position camera behind and above the car
    # Negative X = behind, positive Z = above
    cam_obj.location = (-15, 0, height)

    # Angle camera down to look at car and road ahead
    # Pitch (X rotation) controls how much we look down
    cam_obj.rotation_euler = Euler((math.radians(angle), 0, 0), 'XYZ')

    bpy.context.scene.camera = cam_obj

    return cam_obj


def build_scene_from_osm():
    """Main function to build scene from OSM data."""
    print("\n" + "="*60)
    print("CHARLOTTE DIGITAL TWIN - REAL OSM DATA SCENE")
    print("="*60)

    # Determine scene mode
    i277_only = SCENE_MODE == "i277_only"
    if i277_only:
        print("\n[MODE] I-277 Highway Car Chase Scene")

    # Initialize coordinate transformer
    origin = SceneOrigin(
        lat=SCENE_ORIGIN.lat,
        lon=SCENE_ORIGIN.lon,
        name=SCENE_ORIGIN.name,
    )
    config = GeometryConfig(origin=origin)
    transformer = CoordinateTransformer(config)

    # Download OSM data
    osm_data = download_osm_data(DOWNTOWN_BOUNDS)

    if osm_data is None:
        print("\n[ERROR] Could not download OSM data. Using fallback...")
        return None

    # Clear scene
    print("\n[SCENE] Clearing existing scene...")
    clear_scene()

    # Create collections
    roads_collection = bpy.data.collections.new("OSM_Roads")
    bpy.context.collection.children.link(roads_collection)

    buildings_collection = bpy.data.collections.new("OSM_Buildings")
    bpy.context.collection.children.link(buildings_collection)

    # Extract and create roads (I-277 only or full downtown)
    highways = extract_highways(osm_data, transformer, i277_only=i277_only)
    road_objects = []

    # Calculate scene bounds from road coordinates
    all_road_coords = []
    for segment in highways:
        for coord in segment.coordinates:
            all_road_coords.append(coord)

    print("\n[GEOMETRY] Creating road meshes...")
    for segment in highways:
        obj = create_road_mesh(segment, roads_collection)
        if obj:
            road_objects.append(obj)

    # Extract and create buildings (only for full downtown mode)
    building_objects = []
    if not i277_only:
        buildings = extract_buildings(osm_data, transformer)

        print("\n[GEOMETRY] Creating building meshes...")
        for building in buildings:
            obj = create_building_mesh(building, buildings_collection)
            if obj:
                building_objects.append(obj)

    # Create ground plane - center it on the road network
    print("\n[SCENE] Creating ground plane...")
    if all_road_coords:
        min_x = min(c[0] for c in all_road_coords)
        max_x = max(c[0] for c in all_road_coords)
        min_y = min(c[1] for c in all_road_coords)
        max_y = max(c[1] for c in all_road_coords)
        ground_center = ((min_x + max_x) / 2, (min_y + max_y) / 2)
        ground_size = max(max_x - min_x, max_y - min_y) * 1.5
    else:
        ground_center = (0, 0)
        ground_size = 5000
    ground = create_ground_plane(size=ground_size, center=ground_center)
    print(f"  Ground plane: size={ground_size:.0f}m, center=({ground_center[0]:.0f}, {ground_center[1]:.0f})")

    # Create lighting
    print("[SCENE] Creating lighting...")
    sun = create_lighting()

    # For I-277 mode: add hero car with animation
    if i277_only and highways:
        print("\n[ANIMATION] Creating hero car and path animation...")

        # Calculate scene center from road bounds
        all_coords = []
        for segment in highways:
            for coord in segment.coordinates:
                all_coords.append(coord)

        if all_coords:
            min_x = min(c[0] for c in all_coords)
            max_x = max(c[0] for c in all_coords)
            min_y = min(c[1] for c in all_coords)
            max_y = max(c[1] for c in all_coords)
            scene_center = ((min_x + max_x) / 2, (min_y + max_y) / 2)
            scene_size = max(max_x - min_x, max_y - min_y)
        else:
            scene_center = (0, 0)
            scene_size = 1000

        # Create hero car
        car, wheels = create_hero_car()

        # Create animation path from road segments
        path_obj = create_combined_path_curve(highways)

        if path_obj:
            # Create car animation (30 seconds at 24fps = 720 frames)
            path_follower = create_car_animation(car, path_obj, duration_frames=720)

            print(f"  Created animation path: {path_obj.name}")
            print(f"  Animation: 1-720 frames (30 seconds @ 24fps)")

        # Use static overview camera positioned to see the whole scene
        print("\n[CAMERA] Creating overview camera...")
        camera_height = scene_size * 0.8  # Camera height proportional to scene size
        camera = create_camera(road_objects, height=camera_height, center=scene_center)

    else:
        # Full downtown mode: static camera
        print("[SCENE] Creating camera...")
        camera = create_camera(building_objects)

    # Render settings - same as working 277 scene
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.fps = 24
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080

    # Debug: Print scene summary
    print(f"\n[DEBUG] Scene objects: {len(bpy.data.objects)}")
    print(f"[DEBUG] Scene camera: {bpy.context.scene.camera.name if bpy.context.scene.camera else 'None'}")
    print(f"[DEBUG] Roads collection: {len(road_objects)} objects")

    # Stats
    print("\n" + "="*60)
    print("SCENE COMPLETE!")
    print("="*60)
    print(f"\nScene contains:")
    print(f"  - Roads: {len(road_objects)} segments")
    print(f"  - Buildings: {len(building_objects)} structures")
    print(f"  - Camera: {camera.name}")
    print(f"  - Origin: {SCENE_ORIGIN.lat:.4f}, {SCENE_ORIGIN.lon:.4f}")
    print(f"  - Mode: {SCENE_MODE}")

    return {
        'roads': road_objects,
        'buildings': building_objects,
        'camera': camera,
        'ground': ground,
        'highways': highways,  # Return for reference
    }


def get_project_dir():
    """Get project directory."""
    return Path(__file__).parent.parent


def apply_modifiers_to_roads():
    """Apply skin and subsurf modifiers to all road objects for proper rendering."""
    roads_coll = bpy.data.collections.get("OSM_Roads")
    if not roads_coll:
        return

    print("\n[RENDER] Applying road modifiers...")
    for obj in list(roads_coll.objects):
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        for mod in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                print(f"  Warning: Could not apply modifier to {obj.name}: {e}")
        obj.select_set(False)


def render_frame(output_path: Optional[str] = None, frame: int = 1):
    """Render a single frame.

    Note: Applies modifiers before rendering for proper geometry visibility.
    """
    if output_path is None:
        output_path = str(get_project_dir() / "renders" / f"charlotte_osm_frame_{frame:04d}.png")

    # Apply road modifiers before rendering (skin modifier needs to be applied for Cycles)
    apply_modifiers_to_roads()

    # Use Cycles for better geometry rendering
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 64

    bpy.context.scene.frame_set(frame)
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)

    print(f"\nRendered frame {frame} to: {output_path}")
    return output_path


def save_scene(output_path: Optional[str] = None):
    """Save the Blender scene."""
    if output_path is None:
        output_path = str(get_project_dir() / "scenes" / "charlotte_osm_scene.blend")

    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"Saved scene to: {output_path}")
    return output_path


if __name__ == "__main__":
    scene = build_scene_from_osm()

    if scene:
        save_scene()
        # Render a middle frame to see the car in action
        render_frame(frame=360)
