"""
Charlotte Digital Twin - Render Elevation Map and Email

This script:
1. Builds the Charlotte map with real elevations
2. Renders a driver's eye view
3. Emails the render to you

Run in Blender:
    blender --background --python scripts/19_render_and_email.py

Or with GUI:
    blender --python scripts/19_render_and_email.py
"""

import bpy
import sys
import os
import math
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
from datetime import datetime

# Add lib to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# Import the elevation map builder
from lib.elevation_enhanced import create_enhanced_elevation_manager

# =============================================================================
# CONFIGURATION - Edit these values
# =============================================================================

# Email settings (use environment variables or app passwords)
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'your_email@gmail.com')
EMAIL_TO = os.environ.get('EMAIL_TO', 'bret@example.com')  # Change this!
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')  # Use app password, not real password
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# Render settings
RENDER_RESOLUTION_X = 1920
RENDER_RESOLUTION_Y = 1080
RENDER_SAMPLES = 128
RENDER_ENGINE = 'CYCLES'  # or 'BLENDER_EEVEE'

# Output
OUTPUT_DIR = script_dir.parent / 'output' / 'renders'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# ELEVATION MAP SETUP
# =============================================================================

REF_LAT = 35.226
REF_LON = -80.843
BASE_ELEVATION = 220.0


def latlon_to_local(lat: float, lon: float):
    """Convert lat/lon to local scene coordinates."""
    meters_per_deg_lat = 111000
    meters_per_deg_lon = 111000 * math.cos(math.radians(REF_LAT))
    x = (lon - REF_LON) * meters_per_deg_lon
    y = (lat - REF_LAT) * meters_per_deg_lat
    return (x, y)


def get_elevation_z(elevation_manager, lat: float, lon: float) -> float:
    """Get Z coordinate for a lat/lon (relative to base elevation)."""
    if elevation_manager:
        elevation = elevation_manager.get_elevation(lat, lon)
        return elevation - BASE_ELEVATION
    return 0.0


def setup_scene():
    """Set up the Blender scene with elevation data."""
    print("\n" + "=" * 60)
    print("CHARLOTTE ELEVATION MAP - RENDER SETUP")
    print("=" * 60)

    # Clear existing objects (optional - comment out to keep existing)
    # bpy.ops.object.select_all(action='SELECT')
    # bpy.ops.object.delete()

    # Create elevation manager
    elevation_manager = create_enhanced_elevation_manager()
    print(f"Loaded {len(elevation_manager.known_points)} elevation points")

    # Create collection
    if "ElevationMap" not in bpy.data.collections:
        coll = bpy.data.collections.new("ElevationMap")
        bpy.context.scene.collection.children.link(coll)
    else:
        coll = bpy.data.collections["ElevationMap"]

    # 1. Create terrain mesh
    print("\n[1/5] Creating terrain mesh...")
    terrain = create_terrain_mesh(elevation_manager)
    if terrain:
        coll.objects.link(terrain)

    # 2. Create road network visualization
    print("\n[2/5] Creating road network...")
    roads = create_road_network(elevation_manager)
    for road in roads:
        coll.objects.link(road)

    # 3. Create elevation markers
    print("\n[3/5] Creating elevation markers...")
    markers = create_elevation_markers(elevation_manager)
    for marker in markers:
        coll.objects.link(marker)

    # 4. Create race loop path
    print("\n[4/5] Creating race loop path...")
    race_loop = create_race_loop_path(elevation_manager)
    if race_loop:
        coll.objects.link(race_loop)

    # 5. Setup camera and lighting
    print("\n[5/5] Setting up camera and lighting...")
    camera, sun = setup_camera_and_lighting(elevation_manager)
    if camera:
        coll.objects.link(camera)
        bpy.context.scene.camera = camera
    if sun:
        coll.objects.link(sun)

    return elevation_manager


def create_terrain_mesh(elevation_manager, size_meters=2000.0, resolution=50.0):
    """Create terrain mesh with elevation."""
    center_x, center_y = 0, 0  # Center at reference point
    half_size = size_meters / 2
    cols = int(size_meters / resolution) + 1
    rows = int(size_meters / resolution) + 1

    vertices = []
    min_z, max_z = float('inf'), float('-inf')

    for row in range(rows):
        for col in range(cols):
            x = center_x - half_size + col * resolution
            y = center_y - half_size + row * resolution

            # Convert to lat/lon
            lat = REF_LAT + y / 111000
            lon = REF_LON + x / (111000 * math.cos(math.radians(REF_LAT)))

            z = get_elevation_z(elevation_manager, lat, lon)
            vertices.append((x, y, z))
            min_z = min(min_z, z)
            max_z = max(max_z, z)

    # Generate faces
    faces = []
    for row in range(rows - 1):
        for col in range(cols - 1):
            i = row * cols + col
            faces.append((i, i + 1, i + cols + 1, i + cols))

    # Create mesh
    mesh = bpy.data.meshes.new("CharlotteTerrain")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    obj = bpy.data.objects.new("CharlotteTerrain", mesh)
    obj["elevation_min"] = min_z + BASE_ELEVATION
    obj["elevation_max"] = max_z + BASE_ELEVATION

    # Add material
    mat = bpy.data.materials.new(name="TerrainMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (0.2, 0.5, 0.2, 1.0)  # Green
    bsdf.inputs['Roughness'].default_value = 0.9
    obj.data.materials.append(mat)

    print(f"  Created terrain: {cols}x{rows} grid, Z range: {min_z:.1f} to {max_z:.1f}")
    return obj


def create_road_network(elevation_manager):
    """Create key roads with elevation."""
    roads = []

    # Major streets to visualize
    streets = [
        # (name, [(lat, lon), ...])
        ("E_Trade_St", [
            (35.2273, -80.8431),  # Tryon
            (35.2273, -80.8400),  # Caldwell
        ]),
        ("S_Church_St", [
            (35.2269, -80.8455),  # MLK
            (35.2211, -80.8456),  # Morehead
        ]),
        ("N_College_St", [
            (35.2231, -80.8648),  # I-277
            (35.2298, -80.8689),  # E 5th
        ]),
        ("W_Morehead_St", [
            (35.2211, -80.8431),  # Tryon
            (35.2211, -80.8512),  # Caldwell
        ]),
        ("I277", [
            (35.2175, -80.8583),  # Entry
            (35.2231, -80.8648),  # College
            (35.2261, -80.8673),  # Exit
        ]),
    ]

    for street_name, points in streets:
        curve_data = bpy.data.curves.new(f"Road_{street_name}", type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 3.0  # Road width
        curve_data.resolution_u = 4

        spline = curve_data.splines.new('POLY')
        spline.points.add(len(points) - 1)

        for i, (lat, lon) in enumerate(points):
            x, y = latlon_to_local(lat, lon)
            z = get_elevation_z(elevation_manager, lat, lon)
            spline.points[i].co = (x, y, z, 1.0)

        obj = bpy.data.objects.new(f"Road_{street_name}", curve_data)
        obj["road_name"] = street_name

        # Add road material (gray)
        mat = bpy.data.materials.new(name=f"RoadMat_{street_name}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (0.3, 0.3, 0.3, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.8
        obj.data.materials.append(mat)

        roads.append(obj)

    print(f"  Created {len(roads)} road curves")
    return roads


def create_elevation_markers(elevation_manager):
    """Create markers at key elevation points."""
    markers = []

    key_points = [
        ("Trade_Tryon_Highest", 35.2273, -80.8431, (1.0, 0.0, 0.0)),  # Red
        ("Church_MLK_Start", 35.2269, -80.8455, (0.0, 1.0, 0.0)),  # Green
        ("I277_College_Lowest", 35.2231, -80.8648, (0.0, 0.0, 1.0)),  # Blue
        ("Trade_Caldwell", 35.2273, -80.8397, (1.0, 1.0, 0.0)),  # Yellow
    ]

    for name, lat, lon, color in key_points:
        x, y = latlon_to_local(lat, lon)
        z = get_elevation_z(elevation_manager, lat, lon)

        # Create sphere marker
        bpy.ops.mesh.primitive_uv_sphere_add(radius=15, location=(x, y, z + 20))
        marker = bpy.context.active_object
        marker.name = f"Marker_{name}"

        # Color material
        mat = bpy.data.materials.new(name=f"MarkerMat_{name}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        bsdf.inputs['Emission Color'].default_value = (*color, 1.0)
        bsdf.inputs['Emission Strength'].default_value = 2.0
        marker.data.materials.append(mat)

        marker["elevation"] = z + BASE_ELEVATION
        markers.append(marker)

    print(f"  Created {len(markers)} elevation markers")
    return markers


def create_race_loop_path(elevation_manager):
    """Create the race loop path with elevation."""
    waypoints = [
        (35.2269, -80.8455),  # Start
        (35.2221, -80.8482),  # Church & Morehead
        (35.2175, -80.8583),  # I-277 Entry
        (35.2231, -80.8648),  # I-277 @ College
        (35.2298, -80.8689),  # College & E 5th
        (35.2318, -80.8653),  # E 5th & Caldwell
        (35.2336, -80.8620),  # Caldwell & Trade
        (35.2309, -80.8478),  # Trade & Church
        (35.2269, -80.8455),  # Finish
    ]

    curve_data = bpy.data.curves.new("RaceLoopPath", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 2.0
    curve_data.resolution_u = 4

    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(len(waypoints) - 1)

    for i, (lat, lon) in enumerate(waypoints):
        x, y = latlon_to_local(lat, lon)
        z = get_elevation_z(elevation_manager, lat, lon)

        point = spline.bezier_points[i]
        point.co = (x, y, z)
        point.handle_type_left = 'AUTO'
        point.handle_type_right = 'AUTO'

    obj = bpy.data.objects.new("RaceLoopPath", curve_data)

    # Yellow emissive material
    mat = bpy.data.materials.new(name="RaceLoopMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (1.0, 0.8, 0.0, 1.0)
    bsdf.inputs['Emission Color'].default_value = (1.0, 0.8, 0.0, 1.0)
    bsdf.inputs['Emission Strength'].default_value = 3.0
    obj.data.materials.append(mat)

    print("  Created race loop path")
    return obj


def setup_camera_and_lighting(elevation_manager):
    """Set up camera at race start and sun lighting."""
    # Camera position (elevated view showing terrain)
    start_lat, start_lon = 35.2269, -80.8455
    start_x, start_y = latlon_to_local(start_lat, start_lon)
    start_z = get_elevation_z(elevation_manager, start_lat, start_lon)

    # Create camera
    cam_data = bpy.data.cameras.new("MainCamera")
    cam_obj = bpy.data.objects.new("MainCamera", cam_data)

    # Position camera high above start, looking down at terrain
    cam_obj.location = (start_x - 400, start_y - 400, start_z + 300)
    cam_obj.rotation_euler = (math.radians(60), 0, math.radians(45))

    cam_data.lens = 35
    cam_data.angle = math.radians(60)
    cam_data.clip_end = 5000.0

    # Sun light
    sun_data = bpy.data.lights.new("Sun", type='SUN')
    sun_obj = bpy.data.objects.new("Sun", sun_data)
    sun_obj.location = (500, 500, 500)
    sun_obj.rotation_euler = (math.radians(45), math.radians(30), 0)
    sun_data.energy = 3.0
    sun_data.color = (1.0, 0.95, 0.9)

    print(f"  Camera at: {cam_obj.location}")
    print(f"  Ground elevation at start: {start_z + BASE_ELEVATION:.0f}m")

    return cam_obj, sun_obj


def setup_render_settings():
    """Configure render settings."""
    scene = bpy.context.scene

    # Resolution
    scene.render.resolution_x = RENDER_RESOLUTION_X
    scene.render.resolution_y = RENDER_RESOLUTION_Y
    scene.render.resolution_percentage = 100

    # Engine
    scene.render.engine = RENDER_ENGINE

    # Cycles settings
    if RENDER_ENGINE == 'CYCLES':
        scene.cycles.samples = RENDER_SAMPLES
        scene.cycles.use_denoising = True

    # Output format
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

    # Film transparent (for compositing)
    scene.render.film_transparent = False

    print(f"\nRender settings:")
    print(f"  Resolution: {RENDER_RESOLUTION_X}x{RENDER_RESOLUTION_Y}")
    print(f"  Engine: {RENDER_ENGINE}")
    print(f"  Samples: {RENDER_SAMPLES}")


def render_image():
    """Render the scene to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"charlotte_elevation_{timestamp}.png"
    output_path = str(OUTPUT_DIR / filename)

    bpy.context.scene.render.filepath = output_path

    print(f"\nRendering to: {output_path}")
    bpy.ops.render.render(write_still=True)

    print("Render complete!")
    return output_path


def send_email(image_path: str):
    """Send the rendered image via email."""
    if not EMAIL_PASSWORD:
        print("\nEmail not configured. Set EMAIL_PASSWORD environment variable.")
        print(f"Image saved to: {image_path}")
        return False

    print(f"\nSending email to: {EMAIL_TO}")

    # Create message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = f"Charlotte Elevation Map Render - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    # Body
    body = """
Charlotte Digital Twin - Elevation Map Render

This render shows the Charlotte Uptown area with real SRTM elevation data.

Key Features:
- Terrain mesh with accurate elevations (195m - 295m range)
- Major roads with elevation profiles
- Race loop path (yellow line)
- Elevation markers:
  - Red: Trade & Tryon (highest point - "The Hill")
  - Green: Church & MLK (race start)
  - Blue: I-277 @ College (lowest point)
  - Yellow: Trade & Caldwell

Elevation Data:
- Source: SRTM 30m (OpenTopoData API)
- Total variation: ~100m
- Trade St drop: 43m over 340m

Generated by Charlotte Digital Twin project.
    """
    msg.attach(MIMEText(body, 'plain'))

    # Attach image
    with open(image_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(image_path)}"')
        msg.attach(part)

    # Send
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        print(f"Image saved to: {image_path}")
        return False


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("CHARLOTTE ELEVATION MAP - RENDER & EMAIL")
    print("=" * 60)

    # 1. Setup scene with elevation data
    elevation_manager = setup_scene()

    # 2. Configure render settings
    setup_render_settings()

    # 3. Render
    image_path = render_image()

    # 4. Send email (if configured)
    send_email(image_path)

    # Print elevation stats
    stats = elevation_manager.get_elevation_stats()
    print("\n" + "=" * 60)
    print("ELEVATION STATISTICS")
    print("=" * 60)
    print(f"  Known points: {stats['point_count']}")
    print(f"  Elevation range: {stats['min_elevation']:.0f}m - {stats['max_elevation']:.0f}m")
    print(f"  Total variation: {stats['range']:.0f}m")
    print(f"  Mean elevation: {stats['mean_elevation']:.0f}m")

    # Save blend file
    blend_path = OUTPUT_DIR / f"charlotte_elevation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"\nBlend file saved: {blend_path}")

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
