"""
Charlotte Digital Twin - Race Loop Setup

Creates the complete Uptown Charlotte race loop with:
- Accurate vehicle dimensions (real-world scale)
- Driver camera at correct eye height
- Path highlighting system
- Checkpoint gates
- Integration with elevation data

Route (3.5 km loop):
    Start: Church St & MLK Jr Blvd
    → S Church St south to W Morehead St
    → Right onto Morehead, ramp to I-277 East
    → I-277 to College St exit
    → College St north to E 5th St
    → Right onto E 5th St
    → Right onto N Caldwell St
    → Right onto E Trade St
    → Left onto S Church St (finish)

Usage in Blender:
    import bpy
    bpy.ops.script.python_file_run(filepath="scripts/15_race_loop.py")
"""

import bpy
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import math

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.race_loop import (
    RACE_LOOP_WAYPOINTS,
    VEHICLE_SPECS,
    VehicleDimensions,
    RaceLoopManager,
    PathHighlightConfig,
    PathHighlightType,
    create_path_highlight_material,
    create_driver_camera_rig,
    create_third_person_camera_rig,
)


def main():
    """Setup the complete race loop."""
    print("\n" + "=" * 60)
    print("Charlotte Race Loop Setup")
    print("=" * 60)

    # Step 1: Create race loop manager
    print("\n[1/6] Initializing race loop...")
    manager = RaceLoopManager(RACE_LOOP_WAYPOINTS)

    # Step 2: Create collections
    print("\n[2/6] Creating collections...")
    collections = create_collections()

    # Step 3: Create path highlights and checkpoints
    print("\n[3/6] Creating path highlights...")
    highlight_stats = create_path_highlights(manager, collections)

    # Step 4: Create path curve
    print("\n[4/6] Creating race path curve...")
    path_curve = manager.create_path_curve("RaceLoop_MainPath")
    if path_curve:
        collections['RaceLoop'].objects.link(path_curve)
        print(f"  Path created with {len(RACE_LOOP_WAYPOINTS)} waypoints")

    # Step 5: Spawn player vehicle
    print("\n[5/6] Spawning player vehicle...")
    vehicle_stats = spawn_player_vehicle(manager, collections)

    # Step 6: Create camera system
    print("\n[6/6] Setting up cameras...")
    camera_stats = setup_cameras(manager, collections, vehicle_stats)

    # Summary
    print_summary(highlight_stats, vehicle_stats, camera_stats)

    # Save
    output_path = Path(__file__).parent.parent / 'output' / 'charlotte_race_loop.blend'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"\nSaved to {output_path}")


def create_collections() -> Dict[str, bpy.types.Collection]:
    """Create necessary collections for the race loop."""
    collections = {}

    # Main RaceLoop collection
    if "RaceLoop" not in bpy.data.collections:
        collections['RaceLoop'] = bpy.data.collections.new("RaceLoop")
        bpy.context.scene.collection.children.link(collections['RaceLoop'])
    else:
        collections['RaceLoop'] = bpy.data.collections["RaceLoop"]

    # Path highlights
    if "RaceLoop_PathHighlights" not in bpy.data.collections:
        collections['PathHighlights'] = bpy.data.collections.new("RaceLoop_PathHighlights")
        collections['RaceLoop'].children.link(collections['PathHighlights'])
    else:
        collections['PathHighlights'] = bpy.data.collections["RaceLoop_PathHighlights"]

    # Checkpoints
    if "RaceLoop_Checkpoints" not in bpy.data.collections:
        collections['Checkpoints'] = bpy.data.collections.new("RaceLoop_Checkpoints")
        collections['RaceLoop'].children.link(collections['Checkpoints'])
    else:
        collections['Checkpoints'] = bpy.data.collections["RaceLoop_Checkpoints"]

    # Vehicles
    if "RaceLoop_Vehicles" not in bpy.data.collections:
        collections['Vehicles'] = bpy.data.collections.new("RaceLoop_Vehicles")
        collections['RaceLoop'].children.link(collections['Vehicles'])
    else:
        collections['Vehicles'] = bpy.data.collections["RaceLoop_Vehicles"]

    # Cameras
    if "RaceLoop_Cameras" not in bpy.data.collections:
        collections['Cameras'] = bpy.data.collections.new("RaceLoop_Cameras")
        collections['RaceLoop'].children.link(collections['Cameras'])
    else:
        collections['Cameras'] = bpy.data.collections["RaceLoop_Cameras"]

    return collections


def create_path_highlights(
    manager: RaceLoopManager,
    collections: Dict[str, bpy.types.Collection]
) -> Dict[str, int]:
    """Create visual path markers and checkpoints."""
    stats = {
        'arrows': 0,
        'checkpoints': 0,
        'total': 0,
    }

    # Create highlight material
    config = PathHighlightConfig(
        highlight_type=PathHighlightType.ARROW,
        color=(1.0, 0.85, 0.0, 1.0),  # Golden yellow
        emissive_strength=3.0,
        spacing=15.0,
        size=2.5,
    )

    # Create materials
    arrow_mat = create_path_highlight_material(
        "PathArrow_Material",
        config.color,
        config.emissive_strength
    )

    checkpoint_mat = create_path_highlight_material(
        "Checkpoint_Material",
        (0.0, 1.0, 0.5, 1.0),  # Green
        5.0
    )

    # Create markers for each waypoint
    for i, wp in enumerate(RACE_LOOP_WAYPOINTS):
        x, y = manager.latlon_to_local(wp.lat, wp.lon)
        z = 0.1  # On ground

        # Calculate rotation to next waypoint
        if i < len(RACE_LOOP_WAYPOINTS) - 1:
            next_wp = RACE_LOOP_WAYPOINTS[i + 1]
            next_x, next_y = manager.latlon_to_local(next_wp.lat, next_wp.lon)
            rotation = math.atan2(next_y - y, next_x - x)
        else:
            # Point back to start
            first_wp = RACE_LOOP_WAYPOINTS[0]
            first_x, first_y = manager.latlon_to_local(first_wp.lat, first_wp.lon)
            rotation = math.atan2(first_y - y, first_x - x)

        if wp.is_checkpoint:
            # Create checkpoint gate
            from lib.race_loop import create_checkpoint_gate
            gate = create_checkpoint_gate(
                (x, y, z),
                rotation,
                width=12.0,
                height=5.5,
                name=f"Checkpoint_{wp.name}"
            )
            if gate:
                bpy.context.collection.objects.link(gate)
                collections['Checkpoints'].objects.link(gate)

                # Apply material to children
                for child in gate.children:
                    if hasattr(child, 'data') and hasattr(child.data, 'materials'):
                        child.data.materials.append(checkpoint_mat)

                # Store metadata
                gate["waypoint_index"] = i
                gate["instruction"] = wp.instruction
                gate["speed_limit"] = wp.speed_limit_kmh

                stats['checkpoints'] += 1
        else:
            # Create arrow marker
            from lib.race_loop import create_arrow_marker
            arrow = create_arrow_marker(
                (x, y, z),
                rotation,
                size=config.size,
                name=f"Arrow_{i}_{wp.name}"
            )
            if arrow:
                bpy.context.collection.objects.link(arrow)
                collections['PathHighlights'].objects.link(arrow)

                # Apply material
                if arrow.data:
                    arrow.data.materials.append(arrow_mat)

                # Store metadata
                arrow["waypoint_index"] = i
                arrow["segment_type"] = wp.segment_type
                arrow["speed_limit"] = wp.speed_limit_kmh
                arrow["instruction"] = wp.instruction

                stats['arrows'] += 1

        stats['total'] += 1

    print(f"  Arrows: {stats['arrows']}")
    print(f"  Checkpoints: {stats['checkpoints']}")

    return stats


def spawn_player_vehicle(
    manager: RaceLoopManager,
    collections: Dict[str, bpy.types.Collection]
) -> Dict[str, Any]:
    """Spawn the player vehicle with proper dimensions."""
    stats = {
        'spawned': False,
        'vehicle_type': 'sports_car',
        'dimensions': {},
        'position': (0, 0, 0),
    }

    # Spawn sports car (lower, more exciting driving feel)
    vehicle = manager.spawn_vehicle(vehicle_type='sports_car')

    if vehicle:
        bpy.context.collection.objects.link(vehicle)
        collections['Vehicles'].objects.link(vehicle)

        # Get spec
        spec = VEHICLE_SPECS['sports_car']
        stats['spawned'] = True
        stats['dimensions'] = {
            'length': spec.length,
            'width': spec.width,
            'height': spec.height,
            'eye_height': spec.driver_eye_height,
        }
        stats['position'] = tuple(vehicle.location)

        print(f"  Vehicle: {spec.name}")
        print(f"  Length: {spec.length}m")
        print(f"  Width: {spec.width}m")
        print(f"  Height: {spec.height}m")
        print(f"  Driver eye height: {spec.driver_eye_height}m")

        # Link children (camera, collision)
        for child in vehicle.children:
            bpy.context.collection.objects.link(child)
            if child.type == 'CAMERA':
                collections['Cameras'].objects.link(child)

    return stats


def setup_cameras(
    manager: RaceLoopManager,
    collections: Dict[str, bpy.types.Collection],
    vehicle_stats: Dict[str, Any]
) -> Dict[str, Any]:
    """Setup camera system."""
    stats = {
        'driver_camera': False,
        'third_person_camera': False,
        'active_camera': None,
    }

    if not vehicle_stats['spawned']:
        return stats

    spec = VEHICLE_SPECS['sports_car']

    # Driver camera (already created with vehicle)
    if manager.camera_rig:
        stats['driver_camera'] = True
        stats['active_camera'] = 'driver'
        bpy.context.scene.camera = manager.camera_rig

        print(f"  Driver camera at {spec.driver_eye_height}m height")

    # Create third-person camera as alternate view
    third_cam = create_third_person_camera_rig(
        spec,
        distance=10.0,
        height=4.0,
        name="ThirdPersonCamera"
    )

    if third_cam:
        bpy.context.collection.objects.link(third_cam)
        collections['Cameras'].objects.link(third_cam)

        # Parent to vehicle
        if manager.vehicle:
            third_cam.parent = manager.vehicle

        stats['third_person_camera'] = True
        print(f"  Third-person camera created")

    # Create overview camera for debugging
    overview_cam_data = bpy.data.cameras.new("OverviewCamera_Data")
    overview_cam = bpy.data.objects.new("OverviewCamera", overview_cam_data)

    # Position above the race loop center
    overview_cam.location = (0, 0, 500)  # High above
    overview_cam.rotation_euler = (math.radians(90), 0, 0)

    overview_cam_data.lens = 100
    overview_cam_data.type = 'ORTHO'
    overview_cam_data.ortho_scale = 600

    bpy.context.collection.objects.link(overview_cam)
    collections['Cameras'].objects.link(overview_cam)

    return stats


def print_summary(
    highlight_stats: Dict[str, int],
    vehicle_stats: Dict[str, Any],
    camera_stats: Dict[str, Any]
):
    """Print comprehensive summary."""
    print("\n" + "=" * 60)
    print("Race Loop Summary")
    print("=" * 60)

    print("\n[Path System]")
    print(f"  Total waypoints: {len(RACE_LOOP_WAYPOINTS)}")
    print(f"  Arrow markers: {highlight_stats['arrows']}")
    print(f"  Checkpoint gates: {highlight_stats['checkpoints']}")

    print("\n[Vehicle]")
    if vehicle_stats['spawned']:
        dims = vehicle_stats['dimensions']
        print(f"  Type: {vehicle_stats['vehicle_type']}")
        print(f"  Dimensions: {dims['length']}m x {dims['width']}m x {dims['height']}m")
        print(f"  Driver eye height: {dims['eye_height']}m")
    else:
        print("  Not spawned")

    print("\n[Cameras]")
    print(f"  Driver view: {'Active' if camera_stats['driver_camera'] else 'Not created'}")
    print(f"  Third-person: {'Created' if camera_stats['third_person_camera'] else 'Not created'}")
    print(f"  Active: {camera_stats['active_camera']}")

    print("\n[Route]")
    print("  Start: Church St & MLK Jr Blvd")
    print("  → S Church St → Morehead St")
    print("  → I-277 East → College St")
    print("  → E 5th St → N Caldwell St")
    print("  → E Trade St → S Church St")
    print("  Finish: Back to start (~3.5 km)")

    print("\n" + "=" * 60)
    print("Ready to race!")
    print("=" * 60)


# =============================================================================
# VEHICLE PREVIEW
# =============================================================================

def create_vehicle_preview_mesh(
    vehicle_type: str = 'sports_car'
) -> Optional[bpy.types.Object]:
    """
    Create a simple preview mesh showing vehicle dimensions.

    Useful for verifying scale without loading full vehicle model.
    """
    spec = VEHICLE_SPECS.get(vehicle_type, VEHICLE_SPECS['sports_car'])

    # Create box representing vehicle bounds
    mesh = bpy.data.meshes.new(f"VehiclePreview_{spec.name}")

    hw = spec.width / 2
    hl = spec.length / 2
    hh = spec.height

    # Vertices
    verts = [
        (-hw, -hl, 0),
        (hw, -hl, 0),
        (hw, hl, 0),
        (-hw, hl, 0),
        (-hw, -hl, hh),
        (hw, -hl, hh),
        (hw, hl, hh),
        (-hw, hl, hh),
    ]

    # Faces
    faces = [
        (0, 1, 2, 3),  # Bottom
        (4, 5, 6, 7),  # Top
        (0, 1, 5, 4),  # Front
        (2, 3, 7, 6),  # Back
        (0, 3, 7, 4),  # Left
        (1, 2, 6, 5),  # Right
    ]

    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(f"VehiclePreview_{spec.name}", mesh)

    # Create wireframe material
    mat = bpy.data.materials.new(f"VehiclePreview_Mat")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.2, 0.5, 1.0, 0.3)
    mat.blend_method = 'BLEND'
    obj.data.materials.append(mat)

    # Add driver eye position marker
    eye_empty = bpy.data.objects.new("DriverEyePosition", None)
    eye_empty.empty_display_type = 'SPHERE'
    eye_empty.empty_display_size = 0.1
    eye_empty.location = (0, spec.wheelbase * 0.3, spec.driver_eye_height)
    eye_empty.parent = obj

    return obj


# =============================================================================
# COMMAND LINE SUPPORT
# =============================================================================

def run_from_commandline():
    """Run via blender command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Charlotte Race Loop Setup")
    parser.add_argument('--blend', type=str, help="Input blend file with roads")
    parser.add_argument('--output', type=str, default='output/charlotte_race_loop.blend',
                        help="Output blend file")
    parser.add_argument('--vehicle', type=str, default='sports_car',
                        choices=list(VEHICLE_SPECS.keys()),
                        help="Vehicle type to spawn")
    parser.add_argument('--preview', action='store_true',
                        help="Create vehicle preview mesh only")

    args = parser.parse_args()

    if args.preview:
        # Just create vehicle preview
        preview = create_vehicle_preview_mesh(args.vehicle)
        if preview:
            bpy.context.collection.objects.link(preview)
        print(f"Created preview for {args.vehicle}")
    else:
        if args.blend:
            bpy.ops.wm.open_mainfile(filepath=args.blend)

        main()


if __name__ == '__main__':
    main()
