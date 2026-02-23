"""
Charlotte 277 Highway Scene - 120mph Car Chase

Creates a 30-second animation of a car driving 120mph on I-277 in downtown Charlotte.
Route: Mint St to Elizabeth Ave via I-277

Uses the ProceduralCarFactory for dynamic vehicle system with full style/color control.
"""

import bpy
import math
import sys
from mathutils import Vector, Euler
from pathlib import Path

# Add lib to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent  # blender_gsd root
sys.path.insert(0, str(project_root / "lib"))

# Import the procedural car system
from animation.vehicle.procedural_car import ProceduralCarFactory, STYLE_PRESETS, COLOR_PRESETS


# === CHARLOTTE COORDINATES ===
# I-277 runs in a loop around downtown Charlotte
# Scale: 1 Blender unit = 1 meter (realistic scale)

LOCATIONS = {
    "origin": (0, 0, 0),
    "mint_st": (0, 0, 0),  # Start here
    "277_west": (-50, 80, 0),
    "277_north": (30, 150, 0),
    "277_east": (100, 80, 0),
    "elizabeth_ave": (80, -20, 0),
}

# Highway curve control points - simpler path for visibility
I277_PATH_POINTS = [
    LOCATIONS["mint_st"],
    (-20, 40, 0),
    (-40, 80, 0),
    (-20, 130, 0),
    (30, 150, 0),
    (80, 130, 0),
    (100, 80, 0),
    (90, 20, 0),
    LOCATIONS["elizabeth_ave"],
]


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


def create_ground_plane():
    """Create ground plane."""
    bpy.ops.mesh.primitive_plane_add(size=400, location=(40, 60, -0.1))
    ground = bpy.context.active_object
    ground.name = "Charlotte_Ground"

    mat = bpy.data.materials.new(name="Ground_Mat")
    bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.use_nodes else None
    if mat.node_tree:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if not bsdf:
            bsdf = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs["Base Color"].default_value = (0.15, 0.2, 0.15, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.95
    else:
        mat.diffuse_color = (0.15, 0.2, 0.15, 1.0)
    ground.data.materials.append(mat)

    return ground


def create_highway_path():
    """Create I-277 highway path as a Blender curve."""
    curve = bpy.data.curves.new("I277_Path", type='CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = 0.0
    curve.fill_mode = 'FULL'

    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(I277_PATH_POINTS) - 1)

    for i, point in enumerate(I277_PATH_POINTS):
        bp = spline.bezier_points[i]
        bp.co = (point[0], point[1], point[2])
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    path_obj = bpy.data.objects.new("I277_Highway_Path", curve)
    bpy.context.collection.objects.link(path_obj)

    return path_obj


def create_highway_road():
    """Create visible highway road surface with actual flat geometry."""
    # 3 lanes: ~3.7m per lane = ~11m, plus shoulders = 30m total width
    road_width = 30  # meters (3 lanes wide)

    # Create curve for the path
    curve = bpy.data.curves.new("I277_Road_Curve", type='CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = 0  # No bevel initially
    curve.fill_mode = 'FULL'

    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(I277_PATH_POINTS) - 1)

    for i, point in enumerate(I277_PATH_POINTS):
        bp = spline.bezier_points[i]
        bp.co = (point[0], point[1], point[2])
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    curve_obj = bpy.data.objects.new("I277_Road_Curve", curve)
    bpy.context.collection.objects.link(curve_obj)

    # Use a custom bevel object for flat road (not round tube)
    # Create a simple rectangle profile
    bevel_curve = bpy.data.curves.new("Road_Profile", type='CURVE')
    bevel_curve.dimensions = '2D'
    bevel_curve.fill_mode = 'BOTH'

    # Create rectangular profile (flat road cross-section)
    bevel_spline = bevel_curve.splines.new('POLY')
    bevel_spline.points.add(3)  # 4 points total for rectangle
    # Flat profile: horizontal line with slight thickness
    bevel_spline.points[0].co = (-road_width/2, 0, 0, 1)
    bevel_spline.points[1].co = (-road_width/2, 0.05, 0, 1)  # Slight thickness
    bevel_spline.points[2].co = (road_width/2, 0.05, 0, 1)
    bevel_spline.points[3].co = (road_width/2, 0, 0, 1)
    bevel_spline.use_cyclic_u = True

    bevel_obj = bpy.data.objects.new("Road_Profile_Obj", bevel_curve)
    bpy.context.collection.objects.link(bevel_obj)

    # Apply custom bevel profile
    curve.bevel_mode = 'OBJECT'
    curve.bevel_object = bevel_obj

    # Move road slightly above ground
    curve_obj.location.z = 0.02

    # Dark asphalt material
    mat = bpy.data.materials.new(name="Highway_Asphalt")
    if mat.node_tree:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.15, 0.15, 0.15, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.9
    else:
        mat.diffuse_color = (0.15, 0.15, 0.15, 1.0)
    curve_obj.data.materials.append(mat)

    # Add center line
    create_road_markings(road_width)

    # Hide the profile object
    bevel_obj.hide_viewport = True
    bevel_obj.hide_render = True

    return curve_obj


def create_road_markings(road_width):
    """Create dashed center line on road."""
    curve = bpy.data.curves.new("Center_Line", type='CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = 0.15
    curve.bevel_resolution = 0

    spline = curve.splines.new('BEZIER')
    spline.bezier_points.add(len(I277_PATH_POINTS) - 1)

    for i, point in enumerate(I277_PATH_POINTS):
        bp = spline.bezier_points[i]
        bp.co = (point[0], point[1], point[2] + 0.15)
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    line_obj = bpy.data.objects.new("Road_Center_Line", curve)
    bpy.context.collection.objects.link(line_obj)

    # Yellow line material
    mat = bpy.data.materials.new(name="Yellow_Line")
    if mat.node_tree:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.9, 0.8, 0.1, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.5
    else:
        mat.diffuse_color = (0.9, 0.8, 0.1, 1.0)
    line_obj.data.materials.append(mat)


def create_buildings():
    """Create downtown Charlotte building silhouettes."""
    buildings = []

    # Buildings positioned OUTSIDE the highway loop
    # Road is 30m wide (15m from center on each side)
    # Buildings need to be at least 20m away from the path center
    building_data = [
        # (x, y, width, depth, height in meters) - all OUTSIDE the loop
        (-70, 40, 25, 20, 60),    # Far left of start
        (-80, 100, 30, 25, 80),   # Far west side
        (-60, 140, 20, 20, 50),   # NW corner outside
        (0, 180, 35, 30, 100),    # Far north (Bank of America style)
        (80, 170, 25, 25, 70),    # NE area outside
        (130, 100, 20, 25, 55),   # Far east side
        (140, 40, 25, 20, 45),    # SE area outside
        (60, -40, 20, 15, 35),    # Far south
        (-60, -20, 20, 15, 40),   # SW outside
        (-90, 60, 18, 18, 30),    # Far west
        (120, 80, 22, 22, 35),    # Far east
    ]

    for i, (x, y, w, d, h) in enumerate(building_data):
        bpy.ops.mesh.primitive_cube_add()
        building = bpy.context.active_object
        building.name = f"Building_{i:03d}"
        building.scale = (w/2, d/2, h/2)
        building.location = (x, y, h/2)

        # Gray building color with slight variation
        gray = 0.35 + (i % 5) * 0.03
        mat = bpy.data.materials.new(name=f"BuildingMat_{i}")
        if mat.node_tree:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = (gray, gray, gray + 0.02, 1.0)
                bsdf.inputs["Roughness"].default_value = 0.6
        else:
            mat.diffuse_color = (gray, gray, gray + 0.02, 1.0)
        building.data.materials.append(mat)

        buildings.append(building)

    return buildings


def create_hero_car():
    """Create hero car using the ProceduralCarFactory with full style control."""
    print("  Creating hero car with ProceduralCarFactory...")

    try:
        factory = ProceduralCarFactory()

        # Create a sports car in bright red
        car = factory.create_car(
            name="Hero_Car",
            style="sports",
            color="red",
            seed=42,
            position=(0, 0, 0)
        )

        # Verify the modifier has inputs set correctly
        for mod in car.modifiers:
            if mod.type == 'NODES':
                print(f"  Geometry Nodes modifier: {mod.name}")
                # Debug: show what inputs are set
                inputs_set = []
                for item in mod.node_group.interface.items_tree:
                    if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                        try:
                            val = mod[item.name]
                            inputs_set.append(f"{item.name}={val}")
                        except:
                            pass
                print(f"  Inputs: {inputs_set[:8]}...")
                break

        return car, []

    except Exception as e:
        print(f"  Error with ProceduralCarFactory: {e}")
        import traceback
        traceback.print_exc()
        print("  Falling back to direct part loading...")
        return load_procedural_car_parts_fallback()


def load_procedural_car_parts_fallback():
    """Fallback: Load and assemble procedural car from blend file with specific style."""
    # Path from this script: blender_gsd/projects/charlotte/scripts/ -> blender_gsd/assets/
    car_blend = Path(__file__).parent.parent.parent.parent / "assets" / "vehicles" / "procedural_car_wired.blend"

    if not car_blend.exists():
        print(f"  Car blend not found: {car_blend}")
        return None, []

    try:
        # Import all objects from the car blend
        with bpy.data.libraries.load(str(car_blend)) as (data_from, data_to):
            data_to.objects = [name for name in data_from.objects if name != "Plane"]

        # Create parent empty for the car assembly
        car_root = bpy.data.objects.new("Hero_Car", None)
        car_root.empty_display_type = 'PLAIN_AXES'
        bpy.context.collection.objects.link(car_root)

        # Link all objects and hide them initially
        for obj in data_to.objects:
            if obj is None:
                continue
            bpy.context.collection.objects.link(obj)
            obj.parent = car_root
            obj.hide_viewport = True
            obj.hide_render = True

        # Sports car style: select specific parts
        # Front Base 5 - sporty front end
        # Back Base 5 - matching sporty rear
        # Central Base 1 - standard middle
        style_parts = {
            "front base 5": None,
            "back base 5": None,
            "central base 1": None,
            "wheel 1": None,  # Use wheel 1 for all 4 wheels
        }

        for obj in data_to.objects:
            if obj is None:
                continue
            name_lower = obj.name.lower()

            for part_name in style_parts:
                if part_name in name_lower and style_parts[part_name] is None:
                    style_parts[part_name] = obj
                    break

        # Show selected body parts
        body_parts = [style_parts["front base 5"], style_parts["back base 5"], style_parts["central base 1"]]
        for part in body_parts:
            if part:
                part.hide_viewport = False
                part.hide_render = False

        # Create 4 wheels from the wheel template
        wheels = []
        wheel_template = style_parts["wheel 1"]
        if wheel_template:
            wheel_positions = [
                (1.4, 0.8, 0.1),   # Front right
                (1.4, -0.8, 0.1),  # Front left
                (-1.4, 0.8, 0.1),  # Rear right
                (-1.4, -0.8, 0.1), # Rear left
            ]

            for x, y, z in wheel_positions:
                wheel = wheel_template.copy()
                wheel.data = wheel_template.data
                bpy.context.collection.objects.link(wheel)
                wheel.parent = car_root
                wheel.location = (x, y, z)
                wheel.hide_viewport = False
                wheel.hide_render = False
                wheels.append(wheel)

        # Apply red sports car material
        mat = bpy.data.materials.new(name="Sports_Car_Red")
        if mat.use_nodes:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf:
                bsdf.inputs["Base Color"].default_value = (0.85, 0.1, 0.1, 1.0)
                bsdf.inputs["Metallic"].default_value = 0.9
                bsdf.inputs["Roughness"].default_value = 0.15

        for part in body_parts:
            if part and part.type == 'MESH':
                # Add to existing materials or replace
                if part.data.materials:
                    part.data.materials[0] = mat
                else:
                    part.data.materials.append(mat)

        # Store car metadata for launch control compatibility
        car_root["launch_control_version"] = "1.0"
        car_root["vehicle_type"] = "sports_car"
        car_root["max_speed_kmh"] = 320.0
        car_root["wheel_radius"] = 0.35

        print(f"  Created sports car with {len(body_parts)} body parts and {len(wheels)} wheels")
        return car_root, wheels

    except Exception as e:
        print(f"  Error assembling car: {e}")
        import traceback
        traceback.print_exc()
        return None, []


def create_simple_car():
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
        # Cylinder default: aligned along Z axis
        # For car wheels: need to lie flat with tread facing out (along Y axis)
        # Rotate 90° around X to lay it flat, tread facing Y direction
        bpy.ops.mesh.primitive_cylinder_add(
            radius=wheel_radius,
            depth=0.25,
            rotation=(math.pi/2, 0, 0)
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


def create_path_animation(car, path_obj, duration_frames=720):
    """Create path following animation with car in right lane."""
    # Create an empty to follow the path (this will be the car's parent)
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

    # Animate the offset_factor directly on the constraint
    # Frame 1: start of path
    constraint.offset_factor = 0.0
    empty.keyframe_insert(data_path='constraints["Follow Path"].offset_factor', frame=1)

    # Frame 720: end of path
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
        print(f"  Note: Could not set interpolation ({e}), using default")

    # Parent the car to the empty with right-lane offset
    car.parent = empty
    # Car's X is forward, Y is left/right (width 2.2m)
    # Right lane means negative Y offset from path center
    car.location.x = 0
    car.location.y = -5.0  # Right lane offset (negative Y = right side)
    car.location.z = 0.5   # Raise car slightly above road surface
    car.rotation_euler = Euler((0, 0, 0), 'XYZ')

    # Set animation range
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = duration_frames

    return empty  # Return the follower so camera can use it


def create_chase_camera(path_follower):
    """Create chase camera parented to the same path follower as the car."""
    cam_data = bpy.data.cameras.new("Chase_Camera")
    cam_obj = bpy.data.objects.new("Chase_Camera", cam_data)

    bpy.context.collection.objects.link(cam_obj)

    cam_data.type = 'PERSP'
    cam_data.lens = 35  # Wider lens for more context
    cam_data.clip_end = 500

    # Parent camera to the same path follower
    # This ensures camera moves with the car
    cam_obj.parent = path_follower
    # Position behind and above the car for a chase view
    cam_obj.location = (0, -12, 6)  # Behind and above
    cam_obj.rotation_euler = Euler((0.9, 0, 0), 'XYZ')  # Angled down ~50 degrees

    bpy.context.scene.camera = cam_obj

    return cam_obj


def create_lighting():
    """Create sun and ambient light."""
    sun_data = bpy.data.lights.new("Sun", type='SUN')
    sun_obj = bpy.data.objects.new("Sun", sun_data)
    sun_obj.location = (50, 50, 200)
    sun_obj.rotation_euler = Euler((0.6, 0.2, 0.5), 'XYZ')

    sun_data.energy = 3.0
    sun_data.color = (1.0, 0.95, 0.9)

    bpy.context.collection.objects.link(sun_obj)

    # World lighting - bright sky
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


def setup_scene():
    """Main scene setup."""
    print("\n" + "="*50)
    print("CHARLOTTE 277 HIGHWAY SCENE SETUP")
    print("="*50)

    print("\n[1/6] Clearing scene...")
    clear_scene()

    print("[2/6] Creating ground plane...")
    ground = create_ground_plane()

    print("[3/6] Creating I-277 highway...")
    path_obj = create_highway_path()
    road = create_highway_road()

    print("[4/6] Creating downtown buildings...")
    buildings = create_buildings()

    print("[5/6] Creating hero car...")
    car, wheels = create_hero_car()

    print("[6/6] Setting up animation (30 sec @ 120mph)...")
    path_follower = create_path_animation(car, path_obj, duration_frames=720)

    print("\nAdding camera and lighting...")
    camera = create_chase_camera(path_follower)
    sun = create_lighting()

    # Render settings - use Eevee for faster preview
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.fps = 24
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080

    print("\n" + "="*50)
    print("SCENE SETUP COMPLETE!")
    print("="*50)
    print(f"\nScene contains:")
    print(f"  - Hero car: {car.name}")
    print(f"  - Highway path: {path_obj.name}")
    print(f"  - Road surface: {road.name}")
    print(f"  - Buildings: {len(buildings)}")
    print(f"  - Camera: {camera.name} (chase view - behind and above)")
    print(f"  - Animation: 1-720 frames (30 seconds @ 24fps)")
    print(f"  - Speed: 120 mph")

    return {
        'car': car,
        'wheels': wheels,
        'path': path_obj,
        'road': road,
        'camera': camera,
        'buildings': buildings,
    }


def get_project_dir():
    """Get the Charlotte project root directory."""
    return Path(__file__).parent.parent


def render_first_frame(output_path=None):
    """Render first frame for review."""
    if output_path is None:
        output_path = str(get_project_dir() / "renders" / "charlotte_277_frame_001.png")

    bpy.context.scene.frame_set(1)
    bpy.context.scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)

    print(f"\nRendered first frame to: {output_path}")
    return output_path


def save_scene(output_path=None):
    """Save the scene."""
    if output_path is None:
        output_path = str(get_project_dir() / "scenes" / "charlotte_277_scene.blend")

    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"Saved scene to: {output_path}")
    return output_path


# Run setup when executed
if __name__ == "__main__":
    scene = setup_scene()
    save_scene()
    render_first_frame()
