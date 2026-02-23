"""
Simple Car Chase - Extended road, right lane, 2x speed
- Road extends before and after all car positions
- Cars drive in the right lane (positive Y offset)
- Cars move 2x faster (15 seconds instead of 30)

Run:
    blender -b --python simple_chase.py -o "//output/frame_" -F PNG -s 1 -e 360 -a
"""

import bpy
import math
import random

# Clear everything
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Settings - 2x SPEED = 15 seconds
FPS = 24
DURATION = 15  # Half the time = 2x speed
TOTAL_FRAMES = FPS * DURATION  # 360 frames

# Car dimensions
CAR_LENGTH = 5.0
CAR_WIDTH = 2.2

# Follow distance settings - 2 to 4 car lengths gap
MIN_GAP = CAR_LENGTH * 2.0  # 10m
MAX_GAP = CAR_LENGTH * 4.0  # 20m

# Lane settings - RIGHT LANE
# Road is 20m wide, center line at Y=0
# Right lane is positive Y, about +3m from center
RIGHT_LANE_Y = 3.0
LANE_VARIATION = CAR_WIDTH * 0.25  # 0.55m variation

scene = bpy.context.scene
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES

# Gray sky
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.6, 0.7, 0.8, 1.0)

# ============================================================================
# ROAD - Extended before and after car positions
# ============================================================================

# Cars start at -100m (last car) and go to 550m (hero end)
# So road should go from about -150m to 650m for good coverage
ROAD_START = -200
ROAD_END = 700
ROAD_CENTER = (ROAD_START + ROAD_END) / 2

bpy.ops.mesh.primitive_plane_add(size=1, location=(ROAD_CENTER, RIGHT_LANE_Y, 0))
road = bpy.context.active_object
road.scale = (ROAD_END - ROAD_START, 20, 1)

mat = bpy.data.materials.new("Asphalt")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.2, 0.2, 0.2, 1.0)
bsdf.inputs["Roughness"].default_value = 0.9
road.data.materials.append(mat)

# Center line - along the whole road
for i in range(int((ROAD_END - ROAD_START) / 20)):
    x = ROAD_START + 10 + i * 20
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, RIGHT_LANE_Y, 0.01))
    line = bpy.context.active_object
    line.scale = (8, 0.3, 1)
    mat = bpy.data.materials.new(f"Line_{i}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.9, 0.8, 0.2, 1.0)
    line.data.materials.append(mat)

print(f"Road: {ROAD_START}m to {ROAD_END}m ({ROAD_END - ROAD_START}m long)")

# ============================================================================
# CARS
# ============================================================================

def create_car(name, color):
    """Create a simple car."""
    bpy.ops.mesh.primitive_cube_add()
    car = bpy.context.active_object
    car.name = name
    car.scale = (CAR_LENGTH, CAR_WIDTH, 1.5)
    car.location = (0, 0, 1.5)

    mat = bpy.data.materials.new(f"{name}_mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = 0.7
    bsdf.inputs["Roughness"].default_value = 0.3
    car.data.materials.append(mat)
    return car

# All cars
all_cars = []

# HERO - Red car leads
hero = create_car("Hero", (0.9, 0.1, 0.1, 1.0))
all_cars.append(hero)

# PURSUIT - 5 blue cars
for i in range(5):
    car = create_car(f"Pursuit_{i}", (0.1, 0.2, 0.6, 1.0))
    all_cars.append(car)

print(f"Cars created: {len(all_cars)}")

# ============================================================================
# PATHS - Right lane, follow distance system
# ============================================================================

PATH_LENGTH = 550

def create_path(name, start_x, end_x, y_offset):
    """Create a straight path at specified Y offset (right lane)."""
    curve = bpy.data.curves.new(name, type='CURVE')
    curve.dimensions = '3D'
    spline = curve.splines.new('POLY')
    spline.points.add(1)
    spline.points[0].co = (start_x, y_offset, 0, 1)
    spline.points[1].co = (end_x, y_offset, 0, 1)

    path_obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(path_obj)
    return path_obj

# Calculate follow distances and lane offsets
follow_distances = [0]  # Hero doesn't follow anyone
lane_offsets = [RIGHT_LANE_Y]  # Hero in right lane

for i in range(5):
    gap = random.uniform(MIN_GAP, MAX_GAP)
    origin_distance = CAR_LENGTH + gap
    follow_distances.append(origin_distance)
    print(f"Pursuit_{i}: {gap:.2f}m gap -> origin offset {origin_distance:.2f}m")

    # Slight variation within right lane
    lane_offsets.append(RIGHT_LANE_Y + random.uniform(-LANE_VARIATION, LANE_VARIATION))

# Cumulative offsets from hero
cumulative_offsets = [0]
for i in range(1, len(follow_distances)):
    cumulative_offsets.append(cumulative_offsets[i-1] + follow_distances[i])

print(f"Cumulative offsets: {cumulative_offsets}")

# Create paths for all cars
paths = []

# Hero path (right lane)
hero_path = create_path("HeroPath", 0, PATH_LENGTH, lane_offsets[0])
paths.append(hero_path)

# Pursuit paths
for i in range(5):
    offset = cumulative_offsets[i + 1]
    start_x = 0 - offset
    end_x = PATH_LENGTH - offset
    y_offset = lane_offsets[i + 1]

    path = create_path(f"PursuitPath_{i}", start_x, end_x, y_offset)
    paths.append(path)
    print(f"PursuitPath_{i}: x={start_x:.1f} to {end_x:.1f}, y={y_offset:.2f}")

# ============================================================================
# ANIMATION - 2x speed (same path, less time)
# ============================================================================

for i, car in enumerate(all_cars):
    con = car.constraints.new('FOLLOW_PATH')
    con.target = paths[i]
    con.use_curve_follow = True
    con.use_fixed_location = True
    con.forward_axis = 'FORWARD_X'
    con.up_axis = 'UP_Z'

    con.offset_factor = 0.0
    con.keyframe_insert("offset_factor", frame=1)
    con.offset_factor = 1.0
    con.keyframe_insert("offset_factor", frame=TOTAL_FRAMES)

print(f"Animation complete - {DURATION}s @ {FPS}fps = {TOTAL_FRAMES} frames")

# ============================================================================
# CAMERA
# ============================================================================

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35

camera = bpy.data.objects.new("Camera", cam_data)
bpy.context.collection.objects.link(camera)
camera.location = (250, -80 + RIGHT_LANE_Y, 60)
camera.rotation_euler = (math.radians(75), 0, 0)

track = camera.constraints.new('TRACK_TO')
track.target = hero
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

scene.camera = camera

# ============================================================================
# RENDER
# ============================================================================

scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 8
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.image_settings.file_format = 'PNG'

import os
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(output_dir, exist_ok=True)

print("\n" + "="*60)
print("CAR CHASE - RIGHT LANE, 2X SPEED")
print("="*60)
print(f"Car length: {CAR_LENGTH}m")
print(f"Gap range: {MIN_GAP}m to {MAX_GAP}m")
print(f"Lane: Right lane at Y={RIGHT_LANE_Y}m")
print(f"Speed: 2x (15 seconds instead of 30)")
print(f"Road: {ROAD_START}m to {ROAD_END}m")
print("="*60)
