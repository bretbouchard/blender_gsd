"""
30-Second Car Chase Sequence

Specific chase setup:
- 1 hero car (red sports car)
- 5 pursuit cars
- Weave through traffic for 3 blocks
- Dramatic 90-degree drift turn at full speed
- 2 pursuit cars crash at the corner
- 3 pursuit cars make the turn and continue

Run in Blender:
    blender --python projects/city_chase/30_second_chase.py

Duration: 30 seconds @ 24fps = 720 frames
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector
from pathlib import Path

# Add lib to path
import sys
script_dir = Path(__file__).parent
lib_path = script_dir.parent.parent / "lib"
if str(lib_path) not in sys.path:
    sys.path.insert(0, str(lib_path))


# ============================================================================
# CONFIGURATION
# ============================================================================

FPS = 24
DURATION = 30.0  # seconds
TOTAL_FRAMES = int(DURATION * FPS)  # 720 frames

# Block dimensions
BLOCK_SIZE = 100.0  # meters
ROAD_WIDTH = 20.0

# Timing breakdown
PHASE_1_END = 15.0  # Seconds - weave through traffic (3 blocks straight)
PHASE_2_END = 18.0  # Seconds - the drift turn
PHASE_3_END = 30.0  # Seconds - aftermath, continue chase

# Frame markers
FRAME_STRAIGHT_START = 1
FRAME_STRAIGHT_END = int(PHASE_1_END * FPS)  # 360
FRAME_TURN_START = FRAME_STRAIGHT_END + 1
FRAME_TURN_END = int(PHASE_2_END * FPS)  # 432
FRAME_AFTERMATH_START = FRAME_TURN_END + 1
FRAME_AFTERMATH_END = TOTAL_FRAMES

# Colors
HERO_COLOR = (0.9, 0.1, 0.1)  # Red
PURSUIT_COLOR = (0.1, 0.1, 0.3)  # Dark blue
TRAFFIC_COLORS = [
    (0.8, 0.8, 0.8),  # White
    (0.1, 0.1, 0.1),  # Black
    (0.1, 0.2, 0.7),  # Blue
    (0.7, 0.7, 0.2),  # Yellow
    (0.1, 0.5, 0.2),  # Green
    (0.6, 0.6, 0.6),  # Silver
]


# ============================================================================
# SCENE SETUP
# ============================================================================

def clear_scene():
    """Clear existing objects."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # Remove orphaned data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def setup_scene():
    """Configure scene settings."""
    scene = bpy.context.scene
    scene.render.fps = FPS
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES

    # World
    if not scene.world:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.4, 0.5, 0.6, 1.0)

    return scene


def create_collections():
    """Create collection hierarchy."""
    collections = {}

    main = bpy.data.collections.new("Chase_Sequence")
    bpy.context.collection.children.link(main)
    collections["main"] = main

    for name in ["Roads", "Buildings", "Traffic", "Hero", "Pursuit", "Cameras", "Effects"]:
        col = bpy.data.collections.new(name)
        main.children.link(col)
        collections[name.lower()] = col

    return collections


# ============================================================================
# ROAD BUILDING
# ============================================================================

def create_road_segment(start, end, width=ROAD_WIDTH, name="Road"):
    """Create a road curve segment."""
    curve = bpy.data.curves.new(name, type='CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = width / 2
    curve.fill_mode = 'FULL'

    spline = curve.splines.new('POLY')
    spline.points.add(1)
    spline.points[0].co = (*start, 1.0)
    spline.points[1].co = (*end, 1.0)

    obj = bpy.data.objects.new(name, curve)

    # Asphalt material
    mat = bpy.data.materials.new(f"{name}_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.12, 0.12, 0.12, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.95

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    return obj


def create_intersection(center, size=ROAD_WIDTH * 2, name="Intersection"):
    """Create road intersection pad."""
    bpy.ops.mesh.primitive_plane_add(
        size=size,
        location=center
    )
    obj = bpy.context.active_object
    obj.name = name

    # Same asphalt material
    mat = bpy.data.materials.new(f"{name}_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.12, 0.12, 0.12, 1.0)

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    return obj


def build_roads(collections):
    """Build the road network for the chase."""
    roads = []

    # Main straight road (3 blocks east)
    for i in range(4):  # 4 segments for 3 blocks
        start = (i * BLOCK_SIZE, 0, 0)
        end = ((i + 1) * BLOCK_SIZE, 0, 0)
        road = create_road_segment(start, end, name=f"Main_Road_{i}")
        collections["roads"].objects.link(road)
        roads.append(road)

    # The turn corner
    corner_x = 3 * BLOCK_SIZE

    # Turn road (north after corner)
    for i in range(4):  # Continue north
        start = (corner_x, i * BLOCK_SIZE, 0)
        end = (corner_x, (i + 1) * BLOCK_SIZE, 0)
        road = create_road_segment(start, end, name=f"Turn_Road_{i}")
        collections["roads"].objects.link(road)
        roads.append(road)

    # Intersection at the turn
    intersection = create_intersection((corner_x, 0, 0), name="Turn_Intersection")
    collections["roads"].objects.link(intersection)
    roads.append(intersection)

    # Cross traffic roads
    for i in range(4):
        # North-south cross streets
        start = (i * BLOCK_SIZE, -BLOCK_SIZE, 0)
        end = (i * BLOCK_SIZE, BLOCK_SIZE, 0)
        road = create_road_segment(start, end, name=f"Cross_Road_{i}")
        collections["roads"].objects.link(road)
        roads.append(road)

    # Road markings at turn (visual cue for drift)
    create_turn_markings(corner_x, 0, collections)

    return roads


def create_turn_markings(x, y, collections):
    """Create visual markings at the turn corner."""
    # Skid marks (decal planes)
    for i in range(3):
        bpy.ops.mesh.primitive_plane_add(
            size=5,
            location=(x - 10 + i * 5, y - 2, 0.01)
        )
        mark = bpy.context.active_object
        mark.name = f"SkidMark_{i}"
        mark.scale = (1, 0.3, 1)

        mat = bpy.data.materials.new(f"SkidMark_Mat_{i}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1.0)
            bsdf.inputs["Alpha"].default_value = 0.5
        mat.blend_method = 'BLEND'

        if mark.data.materials:
            mark.data.materials[0] = mat
        else:
            mark.data.materials.append(mat)

        collections["roads"].objects.link(mark)


# ============================================================================
# BUILDING GENERATION
# ============================================================================

def create_building(position, size, height, name):
    """Create a single building."""
    bm = bmesh.new()
    mesh = bpy.data.meshes.new(name)

    w, d = size
    x, y, z = position

    verts = [
        bm.verts.new((x - w/2, y - d/2, z)),
        bm.verts.new((x + w/2, y - d/2, z)),
        bm.verts.new((x + w/2, y + d/2, z)),
        bm.verts.new((x - w/2, y + d/2, z)),
        bm.verts.new((x - w/2, y - d/2, z + height)),
        bm.verts.new((x + w/2, y - d/2, z + height)),
        bm.verts.new((x + w/2, y + d/2, z + height)),
        bm.verts.new((x - w/2, y + d/2, z + height)),
    ]
    bm.verts.ensure_lookup_table()

    # Faces
    bm.faces.new([verts[0], verts[3], verts[2], verts[1]])
    bm.faces.new([verts[4], verts[5], verts[6], verts[7]])
    bm.faces.new([verts[0], verts[1], verts[5], verts[4]])
    bm.faces.new([verts[1], verts[2], verts[6], verts[5]])
    bm.faces.new([verts[2], verts[3], verts[7], verts[6]])
    bm.faces.new([verts[3], verts[0], verts[4], verts[7]])

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)

    # Random building material
    mat = bpy.data.materials.new(f"{name}_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")

    style = random.choice(["glass", "concrete", "steel"])
    colors = {
        "glass": (0.4, 0.5, 0.6),
        "concrete": (0.5, 0.48, 0.45),
        "steel": (0.45, 0.47, 0.5),
    }

    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*colors[style], 1.0)
        bsdf.inputs["Metallic"].default_value = 0.8 if style == "glass" else 0.1

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    return obj


def build_city(collections):
    """Place buildings along the chase route."""
    buildings = []
    random.seed(42)

    # Buildings along straight section (avoid road area)
    for block in range(3):
        block_x = block * BLOCK_SIZE + BLOCK_SIZE / 2

        # North side of road
        for i in range(3):
            x = block_x + random.uniform(-30, 30)
            y = random.uniform(30, 80)
            w = random.uniform(15, 35)
            d = random.uniform(15, 35)
            h = random.uniform(30, 100)

            building = create_building(
                (x, y, 0), (w, d), h,
                f"Building_S{block}_{i}_N"
            )
            collections["buildings"].objects.link(building)
            buildings.append(building)

        # South side of road
        for i in range(3):
            x = block_x + random.uniform(-30, 30)
            y = random.uniform(-80, -30)
            w = random.uniform(15, 35)
            d = random.uniform(15, 35)
            h = random.uniform(30, 100)

            building = create_building(
                (x, y, 0), (w, d), h,
                f"Building_S{block}_{i}_S"
            )
            collections["buildings"].objects.link(building)
            buildings.append(building)

    # Buildings along turn section (north road)
    corner_x = 3 * BLOCK_SIZE
    for block in range(3):
        block_y = block * BLOCK_SIZE + BLOCK_SIZE / 2

        # East side
        for i in range(3):
            x = corner_x + random.uniform(30, 80)
            y = block_y + random.uniform(-30, 30)
            w = random.uniform(15, 35)
            d = random.uniform(15, 35)
            h = random.uniform(40, 120)

            building = create_building(
                (x, y, 0), (w, d), h,
                f"Building_T{block}_{i}_E"
            )
            collections["buildings"].objects.link(building)
            buildings.append(building)

        # West side (with gap for incoming road)
        for i in range(2):
            x = corner_x - random.uniform(50, 90)
            y = block_y + random.uniform(-30, 30)
            w = random.uniform(15, 30)
            d = random.uniform(15, 30)
            h = random.uniform(30, 80)

            building = create_building(
                (x, y, 0), (w, d), h,
                f"Building_T{block}_{i}_W"
            )
            collections["buildings"].objects.link(building)
            buildings.append(building)

    return buildings


# ============================================================================
# VEHICLE CREATION
# ============================================================================

def create_vehicle(name, color, scale=1.0, is_hero=False):
    """Create a vehicle mesh."""
    bm = bmesh.new()
    mesh = bpy.data.meshes.new(name)

    # Sports car proportions
    length = 4.5 * scale
    width = 2.0 * scale
    height = 1.2 * scale

    # Main body
    verts = [
        bm.verts.new((-length/2, -width/2, 0)),
        bm.verts.new((length/2, -width/2, 0)),
        bm.verts.new((length/2, width/2, 0)),
        bm.verts.new((-length/2, width/2, 0)),
        bm.verts.new((-length/2 + 0.5, -width/2, height)),
        bm.verts.new((length/2 - 0.5, -width/2, height)),
        bm.verts.new((length/2 - 0.5, width/2, height)),
        bm.verts.new((-length/2 + 0.5, width/2, height)),
    ]

    # Cabin (for hero only)
    if is_hero:
        cabin_h = height + 0.4
        cabin_l = length * 0.3
        verts.extend([
            bm.verts.new((-cabin_l, -width/2 + 0.2, height)),
            bm.verts.new((cabin_l, -width/2 + 0.2, height)),
            bm.verts.new((cabin_l, width/2 - 0.2, height)),
            bm.verts.new((-cabin_l, width/2 - 0.2, height)),
            bm.verts.new((-cabin_l + 0.2, -width/2 + 0.3, cabin_h)),
            bm.verts.new((cabin_l - 0.2, -width/2 + 0.3, cabin_h)),
            bm.verts.new((cabin_l - 0.2, width/2 - 0.3, cabin_h)),
            bm.verts.new((-cabin_l + 0.2, width/2 - 0.3, cabin_h)),
        ])

    bm.verts.ensure_lookup_table()

    # Body faces
    bm.faces.new([verts[0], verts[3], verts[2], verts[1]])  # Bottom
    bm.faces.new([verts[4], verts[5], verts[6], verts[7]])  # Top
    bm.faces.new([verts[0], verts[1], verts[5], verts[4]])  # Front
    bm.faces.new([verts[1], verts[2], verts[6], verts[5]])  # Right
    bm.faces.new([verts[2], verts[3], verts[7], verts[6]])  # Back
    bm.faces.new([verts[3], verts[0], verts[4], verts[7]])  # Left

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)

    # Car paint material
    mat = bpy.data.materials.new(f"{name}_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.9
        bsdf.inputs["Roughness"].default_value = 0.2

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    return obj


def create_traffic_vehicles(collections, count=15):
    """Create traffic vehicles scattered on roads."""
    vehicles = []
    random.seed(123)

    for i in range(count):
        color = random.choice(TRAFFIC_COLORS)
        vehicle = create_vehicle(f"Traffic_{i:03d}", color, scale=0.9)
        collections["traffic"].objects.link(vehicle)
        vehicles.append(vehicle)

        # Position on roads (straight section)
        if i < count // 2:
            # Eastbound lane
            x = random.uniform(50, 250)
            y = random.uniform(-6, -2)
        else:
            # Westbound lane
            x = random.uniform(50, 250)
            y = random.uniform(2, 6)

        vehicle.location = (x, y, 0.6)
        vehicle.rotation_euler[2] = 0 if i < count // 2 else math.pi

    return vehicles


# ============================================================================
# CHASE PATH & ANIMATION
# ============================================================================

def create_chase_path():
    """
    Create the chase path:
    - Start at (0, 0)
    - Go straight east for 3 blocks (300m)
    - Sharp 90-degree turn north
    - Continue north
    """
    path = []

    # Phase 1: Straight weaving (0-15 seconds)
    # Weave pattern through traffic
    for t in range(60):  # 60 waypoints over 15 seconds
        progress = t / 59
        x = progress * 300  # 0 to 300 meters

        # Weaving motion (3 S-curves over 3 blocks)
        weave = math.sin(progress * math.pi * 3) * 5  # +/- 5m weave
        y = weave

        path.append((x, y, 0))

    # Phase 2: The drift turn (15-18 seconds)
    # Aggressive 90-degree turn
    turn_center = (300, 0, 0)
    turn_radius = 25  # Tight drift radius

    for t in range(20):  # 20 waypoints for turn
        angle = (t / 19) * (math.pi / 2)  # 0 to 90 degrees

        # Spiral outward during drift
        r = turn_radius + t * 0.5  # Widening drift

        x = turn_center[0] + r * math.cos(math.pi - angle)
        y = turn_center[1] + r * math.sin(math.pi - angle)

        path.append((x, y, 0))

    # Phase 3: After turn (18-30 seconds)
    # Continue north with slight weave
    for t in range(40):
        progress = t / 39
        y = progress * 250  # Continue north
        x = 300 + math.sin(progress * math.pi * 2) * 3  # Slight weave

        path.append((x, y, 0))

    return path


def animate_hero(hero_car, path, collections):
    """Animate the hero car along the chase path."""
    # Create path curve
    curve_data = bpy.data.curves.new("Hero_Path", type='CURVE')
    curve_data.dimensions = '3D'

    spline = curve_data.splines.new('POLY')
    spline.points.add(len(path) - 1)

    for i, point in enumerate(path):
        spline.points[i].co = (*point, 1.0)

    path_obj = bpy.data.objects.new("Hero_Path", curve_data)
    collections["main"].objects.link(path_obj)

    # Follow path constraint
    constraint = hero_car.constraints.new('FOLLOW_PATH')
    constraint.target = path_obj
    constraint.use_curve_follow = True
    constraint.use_fixed_location = True
    constraint.forward_axis = 'FORWARD_X'
    constraint.up_axis = 'UP_Z'

    # Keyframe animation using constraint offset_factor (Blender 5.0+)
    # Start
    constraint.offset_factor = 0.0
    constraint.keyframe_insert("offset_factor", frame=1)

    # End of straight section (weaving)
    straight_progress = 60 / len(path)  # Progress at end of straight
    constraint.offset_factor = straight_progress
    constraint.keyframe_insert("offset_factor", frame=FRAME_STRAIGHT_END)

    # End of turn
    turn_progress = 80 / len(path)
    constraint.offset_factor = turn_progress
    constraint.keyframe_insert("offset_factor", frame=FRAME_TURN_END)

    # End
    constraint.offset_factor = 1.0
    constraint.keyframe_insert("offset_factor", frame=TOTAL_FRAMES)

    # Note: Interpolation setting skipped for Blender 5.0+ compatibility
    # Default interpolation (Bezier) will be used

    return path_obj


def animate_pursuit(pursuit_car, path, offset_frames, crash_at_turn=False, collections=None):
    """Animate a pursuit car following the hero with offset."""
    # Create path curve (copy of hero path)
    curve_data = bpy.data.curves.new(f"{pursuit_car.name}_Path", type='CURVE')
    curve_data.dimensions = '3D'

    spline = curve_data.splines.new('POLY')
    spline.points.add(len(path) - 1)

    for i, point in enumerate(path):
        spline.points[i].co = (*point, 1.0)

    path_obj = bpy.data.objects.new(f"{pursuit_car.name}_Path", curve_data)
    if collections:
        collections["main"].objects.link(path_obj)

    # Follow path constraint
    constraint = pursuit_car.constraints.new('FOLLOW_PATH')
    constraint.target = path_obj
    constraint.use_curve_follow = True
    constraint.use_fixed_location = True
    constraint.forward_axis = 'FORWARD_X'
    constraint.up_axis = 'UP_Z'

    if crash_at_turn:
        # This car crashes at the turn - animate to crash point then stop
        # Animate to turn point
        turn_progress = 65 / len(path)  # Just before turn

        # Use constraint offset_factor (Blender 5.0+)
        constraint.offset_factor = 0.0
        constraint.keyframe_insert("offset_factor", frame=1 + offset_frames)

        constraint.offset_factor = turn_progress
        constraint.keyframe_insert("offset_factor", frame=FRAME_TURN_START - 10 + offset_frames // 2)

        # Crash animation (stop and spin)
        crash_frame = FRAME_TURN_START + offset_frames // 2

        # Get position at crash
        crash_point = path[65] if len(path) > 65 else path[-1]
        pursuit_car.location = crash_point
        pursuit_car.keyframe_insert("location", frame=crash_frame)

        # Crash movement - slide and spin
        pursuit_car.location = (crash_point[0] + 10, crash_point[1] + 15, 0)
        pursuit_car.keyframe_insert("location", frame=crash_frame + 20)

        pursuit_car.rotation_euler[2] = 0
        pursuit_car.keyframe_insert("rotation_euler", index=2, frame=crash_frame)
        pursuit_car.rotation_euler[2] = math.pi * 2.5  # Spin
        pursuit_car.keyframe_insert("rotation_euler", index=2, frame=crash_frame + 30)

        # Add crash effect (smoke/debris placeholder)
        create_crash_effect(crash_point, crash_frame, collections)

    else:
        # This car makes the turn - follow full path
        # Use constraint offset_factor (Blender 5.0+)
        constraint.offset_factor = 0.0
        constraint.keyframe_insert("offset_factor", frame=1 + offset_frames)

        constraint.offset_factor = 1.0
        constraint.keyframe_insert("offset_factor", frame=TOTAL_FRAMES + offset_frames)


def create_crash_effect(position, frame, collections):
    """Create crash visual effect (placeholder particles/debris)."""
    # Create debris chunks
    for i in range(5):
        bpy.ops.mesh.primitive_cube_add(
            size=0.5,
            location=position
        )
        debris = bpy.context.active_object
        debris.name = f"Debris_{i}"
        debris.scale = (random.uniform(0.3, 1), random.uniform(0.3, 1), random.uniform(0.2, 0.5))

        # Animate debris flying
        debris.keyframe_insert("location", frame=frame)

        debris.location = (
            position[0] + random.uniform(-10, 10),
            position[1] + random.uniform(-10, 10),
            random.uniform(0.5, 3)
        )
        debris.keyframe_insert("location", frame=frame + 30)

        # Fade out
        debris.scale = (0.1, 0.1, 0.1)
        debris.keyframe_insert("scale", frame=frame + 60)

        if collections:
            collections["effects"].objects.link(debris)
        else:
            bpy.context.collection.objects.unlink(debris)


# ============================================================================
# TRAFFIC ANIMATION (WEAVING)
# ============================================================================

def animate_traffic_weave(traffic_vehicles, hero_path):
    """Animate traffic vehicles reacting to weaving hero car."""
    # Traffic moves slowly and gets passed by hero
    for i, vehicle in enumerate(traffic_vehicles):
        # Simple linear movement
        start_x = vehicle.location.x
        start_y = vehicle.location.y

        vehicle.keyframe_insert("location", frame=1)

        # Move slightly
        if i < len(traffic_vehicles) // 2:
            # Eastbound
            vehicle.location.x = start_x + random.uniform(20, 50)
        else:
            # Westbound
            vehicle.location.x = start_x - random.uniform(20, 50)

        # Slight lane shift (reacting to hero)
        vehicle.location.y = start_y + random.uniform(-2, 2)

        vehicle.keyframe_insert("location", frame=FRAME_STRAIGHT_END)

        # Stop or continue slowly after hero passes
        vehicle.keyframe_insert("location", frame=TOTAL_FRAMES)


# ============================================================================
# CAMERAS
# ============================================================================

def create_cameras(collections, hero_car):
    """Create chase cameras."""
    cameras = []

    # 1. Close follow camera
    cam_data = bpy.data.cameras.new("Follow_Camera")
    cam_data.lens = 50.0
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = 2.8
    cam_data.dof.focus_distance = 20.0

    follow_cam = bpy.data.objects.new("Follow_Camera", cam_data)
    follow_cam.location = (-25, 12, 5)
    collections["cameras"].objects.link(follow_cam)

    # Track to hero
    track = follow_cam.constraints.new('TRACK_TO')
    track.target = hero_car
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'

    # Parent to hero for follow
    follow_cam.parent = hero_car
    cameras.append(follow_cam)

    # 2. Wide aerial camera
    cam_data2 = bpy.data.cameras.new("Aerial_Camera")
    cam_data2.lens = 35.0

    aerial_cam = bpy.data.objects.new("Aerial_Camera", cam_data2)
    aerial_cam.location = (150, 150, 100)
    collections["cameras"].objects.link(aerial_cam)

    track2 = aerial_cam.constraints.new('TRACK_TO')
    track2.target = hero_car

    cameras.append(aerial_cam)

    # 3. Corner camera (for the turn)
    cam_data3 = bpy.data.cameras.new("Corner_Camera")
    cam_data3.lens = 24.0

    corner_cam = bpy.data.objects.new("Corner_Camera", cam_data3)
    corner_cam.location = (320, -40, 8)
    corner_cam.rotation_euler = (math.radians(80), 0, math.radians(45))
    collections["cameras"].objects.link(corner_cam)

    cameras.append(corner_cam)

    # Set follow camera as active
    bpy.context.scene.camera = follow_cam

    return cameras


# ============================================================================
# RENDER SETUP
# ============================================================================

def setup_render():
    """Configure render settings for EEVEE (fast rendering)."""
    scene = bpy.context.scene

    # Use EEVEE for fast rendering (30-60x faster than Cycles)
    scene.render.engine = 'BLENDER_EEVEE'

    # EEVEE settings
    scene.eevee.taa_render_samples = 8  # Fast preview (8 samples)
    scene.eevee.use_taa_reprojection = False

    # Enable EEVEE motion blur
    scene.eevee.use_motion_blur = True
    scene.eevee.motion_blur_samples = 4  # Fast motion blur
    scene.eevee.motion_blur_shutter = 0.5

    # Output resolution (1080p)
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS

    # File format - PNG sequence
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.compression = 90

    print("  Render engine: EEVEE (fast mode)")
    print(f"  Resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
    print(f"  Samples: {scene.eevee.taa_render_samples}")
    print(f"  Motion blur: {scene.eevee.motion_blur_samples} samples")


# ============================================================================
# MAIN BUILD
# ============================================================================

def build_chase_sequence():
    """Build the complete 30-second chase sequence."""
    print("\n" + "="*60)
    print("BUILDING 30-SECOND CAR CHASE SEQUENCE")
    print("="*60 + "\n")

    print("Phase 1: Clearing scene...")
    clear_scene()

    print("Phase 2: Setting up scene...")
    scene = setup_scene()
    collections = create_collections()

    print("Phase 3: Building roads...")
    roads = build_roads(collections)
    print(f"  Created {len(roads)} road segments")

    print("Phase 4: Building city...")
    buildings = build_city(collections)
    print(f"  Created {len(buildings)} buildings")

    print("Phase 5: Creating vehicles...")
    # Hero car
    hero_car = create_vehicle("Hero_Car", HERO_COLOR, scale=1.2, is_hero=True)
    hero_car.location = (0, 0, 0.6)
    collections["hero"].objects.link(hero_car)

    # Pursuit cars (5 total, 2 will crash)
    pursuit_cars = []
    for i in range(5):
        pursuit = create_vehicle(f"Pursuit_{i:02d}", PURSUIT_COLOR, scale=1.1)
        pursuit.location = (-30 - i * 15, 0, 0.6)
        collections["pursuit"].objects.link(pursuit)
        pursuit_cars.append(pursuit)

    print(f"  Created 1 hero + 5 pursuit cars")

    # Traffic
    traffic = create_traffic_vehicles(collections, count=15)
    print(f"  Created {len(traffic)} traffic vehicles")

    print("Phase 6: Creating chase path...")
    path = create_chase_path()
    print(f"  Path has {len(path)} waypoints")

    print("Phase 7: Animating hero car...")
    hero_path = animate_hero(hero_car, path, collections)

    print("Phase 8: Animating pursuit cars...")
    # First 2 crash at the turn
    for i in range(2):
        animate_pursuit(
            pursuit_cars[i], path,
            offset_frames=(i + 1) * 20,
            crash_at_turn=True,
            collections=collections
        )
        print(f"  {pursuit_cars[i].name} will CRASH at turn")

    # Last 3 make the turn
    for i in range(2, 5):
        animate_pursuit(
            pursuit_cars[i], path,
            offset_frames=(i + 1) * 15,
            crash_at_turn=False,
            collections=collections
        )
        print(f"  {pursuit_cars[i].name} makes the turn")

    print("Phase 9: Animating traffic...")
    animate_traffic_weave(traffic, path)

    print("Phase 10: Setting up cameras...")
    cameras = create_cameras(collections, hero_car)

    print("Phase 11: Render setup...")
    setup_render()

    # Summary
    print("\n" + "="*60)
    print("BUILD COMPLETE!")
    print("="*60)
    print(f"\nScene: 30-second car chase")
    print(f"Duration: {DURATION}s @ {FPS}fps = {TOTAL_FRAMES} frames")
    print(f"\nTimeline:")
    print(f"  0-15s:  Weave through traffic (3 blocks straight)")
    print(f"  15-18s: Dramatic 90-degree drift turn")
    print(f"  18-30s: Continue chase (2 crashed, 3 following)")
    print(f"\nVehicles:")
    print(f"  1 Hero car (red sports car)")
    print(f"  2 Pursuit cars crash at turn")
    print(f"  3 Pursuit cars make turn and continue")
    print(f"  {len(traffic)} Traffic vehicles")
    print(f"\nCameras:")
    print(f"  Follow camera (active)")
    print(f"  Aerial camera")
    print(f"  Corner camera (for turn)")
    print(f"\nReady to render!")
    print(f"  Blender: Render -> Render Animation")
    print(f"  CLI: blender -b chase_file.blend -a")
    print("="*60 + "\n")

    return {
        "hero": hero_car,
        "pursuit": pursuit_cars,
        "traffic": traffic,
        "cameras": cameras,
        "path": path,
    }


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    result = build_chase_sequence()
