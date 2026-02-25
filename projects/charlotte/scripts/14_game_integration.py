"""
Charlotte Digital Twin - Game Integration

Phase 5 of Driving Game implementation.
Sets up collision, LOD, NPC paths, spawn points, and exports for game engines.

Usage in Blender:
    import bpy
    bpy.ops.script.python_file_run(filepath="scripts/14_game_integration.py")
"""

import bpy
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.game_integration import (
    setup_collision_for_object,
    create_collision_proxy,
    setup_road_collision,
    create_lod_object,
    create_lod_system_for_object,
    setup_scene_lod,
    generate_lane_centerline,
    create_npc_path_curve,
    generate_all_npc_paths,
    export_npc_paths_json,
    export_for_unity,
    export_for_unreal,
    export_gltf,
    generate_vehicle_spawn_points,
    create_spawn_point_objects,
    setup_game_integration,
    CollisionType,
    LODLevel,
    ExportTarget,
    CollisionConfig,
    LODConfig,
    NPCPathConfig,
)


def main():
    """Run complete game integration for Charlotte."""
    print("\n" + "=" * 60)
    print("Charlotte Game Integration - Phase 5")
    print("=" * 60)

    # Step 1: Setup collision for all game objects
    print("\n[1/6] Setting up collision...")
    collision_stats = setup_all_collision()

    # Step 2: Create LOD system
    print("\n[2/6] Creating LOD system...")
    lod_stats = create_all_lod()

    # Step 3: Generate NPC paths
    print("\n[3/6] Generating NPC navigation paths...")
    npc_stats = generate_npc_navigation()

    # Step 4: Create spawn points
    print("\n[4/6] Creating vehicle spawn points...")
    spawn_stats = create_vehicle_spawns()

    # Step 5: Setup game-specific metadata
    print("\n[5/6] Setting up game metadata...")
    metadata_stats = setup_game_metadata()

    # Step 6: Export for game engines
    print("\n[6/6] Exporting for game engines...")
    export_stats = export_all_formats()

    # Summary
    print_summary(collision_stats, lod_stats, npc_stats, spawn_stats, metadata_stats, export_stats)

    # Save
    output_path = Path(__file__).parent.parent / 'output' / 'charlotte_game_ready.blend'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"\nSaved to {output_path}")


def setup_all_collision() -> Dict[str, Any]:
    """Setup collision for all scene objects."""
    stats = {
        'roads': 0,
        'buildings': 0,
        'furniture': 0,
        'proxies': 0,
        'triggers': 0,
        'errors': 0,
    }

    # Get objects by type
    road_objects = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'MESH' and (
            obj.get('road_class') or
            'road' in obj.name.lower() or
            'surface' in obj.name.lower()
        )
    ]

    building_objects = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'MESH' and (
            obj.get('building_id') or
            'building' in obj.name.lower()
        )
    ]

    furniture_objects = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'MESH' and obj.get('object_type') in ('bench', 'trash_can', 'hydrant', 'pole', 'sign')
    ]

    # Setup road collision (trimesh for accurate tire physics)
    road_config = CollisionConfig(
        collision_type=CollisionType.TRIMESH,
        physics_material="asphalt"
    )
    road_result = setup_road_collision(road_objects, road_config)
    stats['roads'] = road_result.get('setup', 0)
    stats['proxies'] += road_result.get('proxies_created', 0)

    # Setup building collision (convex hull for performance)
    for obj in building_objects:
        try:
            config = CollisionConfig(
                collision_type=CollisionType.CONVEX_HULL,
                physics_material="concrete"
            )
            setup_collision_for_object(obj, config)

            # Create collision proxy for complex buildings
            if len(obj.data.polygons) > 500:
                proxy = create_collision_proxy(obj, CollisionType.CONVEX_HULL, 0.3)
                if proxy:
                    bpy.context.collection.objects.link(proxy)
                    stats['proxies'] += 1

            stats['buildings'] += 1
        except Exception:
            stats['errors'] += 1

    # Setup furniture collision (convex hull or box)
    for obj in furniture_objects:
        try:
            # Use box for simple objects
            config = CollisionConfig(
                collision_type=CollisionType.BOX,
                physics_material="metal"
            )
            setup_collision_for_object(obj, config)
            stats['furniture'] += 1
        except Exception:
            stats['errors'] += 1

    # Create trigger zones at intersections
    trigger_stats = create_intersection_triggers()
    stats['triggers'] = trigger_stats.get('created', 0)

    print(f"  Roads: {stats['roads']}")
    print(f"  Buildings: {stats['buildings']}")
    print(f"  Furniture: {stats['furniture']}")
    print(f"  Collision proxies: {stats['proxies']}")
    print(f"  Trigger zones: {stats['triggers']}")

    return stats


def create_intersection_triggers() -> Dict[str, int]:
    """Create trigger zones at intersections for game logic."""
    stats = {'created': 0, 'errors': 0}

    # Find intersection markers
    intersection_objects = [
        obj for obj in bpy.context.scene.objects
        if obj.get('is_intersection') or 'intersection' in obj.name.lower()
    ]

    for i, intersection in enumerate(intersection_objects):
        try:
            # Create trigger zone
            trigger = bpy.data.objects.new(f"Trigger_Intersection_{i}", None)
            trigger.empty_display_type = 'CUBE'
            trigger.empty_display_size = 15.0  # 15m trigger radius

            trigger.location = intersection.location
            trigger.location.z += 2.0  # Slight height offset

            # Store trigger metadata
            trigger["trigger_type"] = "intersection"
            trigger["is_trigger"] = True
            trigger["trigger_radius"] = 15.0
            trigger["trigger_actions"] = ["check_traffic_light", "yield_right_of_way"]

            bpy.context.collection.objects.link(trigger)
            stats['created'] += 1

        except Exception:
            stats['errors'] += 1

    return stats


def create_all_lod() -> Dict[str, int]:
    """Create LOD system for complex objects."""
    stats = {
        'objects_processed': 0,
        'lod_created': 0,
        'buildings': 0,
        'roads': 0,
        'vegetation': 0,
        'errors': 0,
    }

    # Objects that need LOD
    lod_candidates = []

    # Buildings
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue

        if obj.get('building_id') or 'building' in obj.name.lower():
            obj["needs_lod"] = True
            obj["object_type"] = "building"
            lod_candidates.append(obj)

        # Large road sections
        elif obj.get('road_class') and len(obj.data.polygons) > 2000:
            obj["needs_lod"] = True
            obj["object_type"] = "road"
            lod_candidates.append(obj)

        # Trees and vegetation
        elif obj.get('vegetation_type') or 'tree' in obj.name.lower():
            obj["needs_lod"] = True
            obj["object_type"] = "vegetation"
            lod_candidates.append(obj)

    # Create LOD for each candidate (limit for performance)
    for obj in lod_candidates[:50]:
        try:
            lod_objects = create_lod_system_for_object(
                obj,
                levels=[LODLevel.LOD0, LODLevel.LOD1, LODLevel.LOD2]
            )
            stats['lod_created'] += len(lod_objects)
            stats['objects_processed'] += 1

            # Track by type
            obj_type = obj.get('object_type', 'unknown')
            if obj_type == 'building':
                stats['buildings'] += 1
            elif obj_type == 'road':
                stats['roads'] += 1
            elif obj_type == 'vegetation':
                stats['vegetation'] += 1

        except Exception:
            stats['errors'] += 1

    print(f"  Objects processed: {stats['objects_processed']}")
    print(f"  LOD objects created: {stats['lod_created']}")
    print(f"  Buildings: {stats['buildings']}")
    print(f"  Roads: {stats['roads']}")
    print(f"  Vegetation: {stats['vegetation']}")

    return stats


def generate_npc_navigation() -> Dict[str, Any]:
    """Generate NPC navigation paths from road curves."""
    stats = {
        'roads_processed': 0,
        'paths_created': 0,
        'total_length_km': 0.0,
        'spawn_points': 0,
        'errors': 0,
    }

    # Find all road curves
    road_curves = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'CURVE' and (
            obj.get('road_class') or
            'road' in obj.name.lower()
        )
    ]

    # Generate NPC paths
    path_result = generate_all_npc_paths(road_curves, "NPC_Paths")
    stats['roads_processed'] = path_result.get('roads_processed', 0)
    stats['paths_created'] = path_result.get('paths_created', 0)
    stats['total_length_km'] = path_result.get('total_length', 0) / 1000

    # Export paths to JSON for game engine
    npc_path_objects = [
        obj for obj in bpy.context.scene.objects
        if obj.get('path_type') == 'npc_lane'
    ]

    output_dir = Path(__file__).parent.parent / 'exports' / 'navigation'
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / 'npc_paths.json'
    export_npc_paths_json(npc_path_objects, str(json_path))
    print(f"  Exported NPC paths to: {json_path}")

    print(f"  Roads processed: {stats['roads_processed']}")
    print(f"  NPC paths created: {stats['paths_created']}")
    print(f"  Total path length: {stats['total_length_km']:.2f} km")

    return stats


def create_vehicle_spawns() -> Dict[str, int]:
    """Create vehicle spawn points along NPC paths."""
    stats = {
        'spawn_points': 0,
        'player_spawns': 0,
        'ai_spawns': 0,
        'errors': 0,
    }

    # Get NPC paths
    npc_paths = [
        obj for obj in bpy.context.scene.objects
        if obj.get('path_type') == 'npc_lane'
    ]

    # Generate spawn points
    spawn_points = generate_vehicle_spawn_points(npc_paths, spacing=75.0)

    # Create spawn point objects (limit for performance)
    created = create_spawn_point_objects(spawn_points[:200], "Spawn_Points")
    stats['spawn_points'] = created

    # Mark some as player spawn points
    spawn_objects = [
        obj for obj in bpy.context.scene.objects
        if obj.get('spawn_type') == 'vehicle'
    ]

    # Every 10th spawn is a player spawn
    for i, obj in enumerate(spawn_objects):
        if i % 10 == 0:
            obj["spawn_type"] = "player"
            obj["spawn_index"] = stats['player_spawns']
            stats['player_spawns'] += 1
        else:
            stats['ai_spawns'] += 1

    print(f"  Total spawn points: {stats['spawn_points']}")
    print(f"  Player spawns: {stats['player_spawns']}")
    print(f"  AI spawns: {stats['ai_spawns']}")

    return stats


def setup_game_metadata() -> Dict[str, Any]:
    """Setup game-specific metadata on all objects."""
    stats = {
        'objects_tagged': 0,
        'road_segments': 0,
        'traffic_signals': 0,
        'zones_created': 0,
    }

    # Tag all objects with game metadata
    for obj in bpy.context.scene.objects:
        try:
            # Road segments
            if obj.get('road_class'):
                obj["game_layer"] = "Road"
                obj["cast_shadows"] = True
                obj["receive_shadows"] = True

                # Add friction data
                surface = obj.get('surface', 'asphalt')
                friction = {
                    'asphalt': 0.9,
                    'concrete': 0.85,
                    'gravel': 0.6,
                    'dirt': 0.5,
                }
                obj["surface_friction"] = friction.get(surface, 0.8)
                stats['road_segments'] += 1

            # Traffic signals
            elif 'signal' in obj.name.lower() or 'traffic' in obj.name.lower():
                obj["game_layer"] = "TrafficControl"
                obj["interactive"] = True
                stats['traffic_signals'] += 1

            # Buildings
            elif obj.get('building_id') or 'building' in obj.name.lower():
                obj["game_layer"] = "Building"
                obj["cast_shadows"] = True
                obj["receive_shadows"] = True

            # Vegetation
            elif 'tree' in obj.name.lower() or obj.get('vegetation_type'):
                obj["game_layer"] = "Vegetation"
                obj["cast_shadows"] = True
                obj["wind_affected"] = True

            # Furniture
            elif obj.get('object_type') in ('bench', 'trash_can', 'hydrant'):
                obj["game_layer"] = "Props"
                obj["destructible"] = True

            stats['objects_tagged'] += 1

        except Exception:
            pass

    # Create game zones
    zones_created = create_game_zones()
    stats['zones_created'] = zones_created

    print(f"  Objects tagged: {stats['objects_tagged']}")
    print(f"  Road segments: {stats['road_segments']}")
    print(f"  Traffic signals: {stats['traffic_signals']}")
    print(f"  Game zones: {stats['zones_created']}")

    return stats


def create_game_zones() -> int:
    """Create special game zones (speed zones, parking, etc.)."""
    created = 0

    # Create speed zones based on road data
    for obj in bpy.context.scene.objects:
        if not obj.get('road_class'):
            continue

        max_speed = obj.get('maxspeed', 30)
        if not isinstance(max_speed, (int, float)):
            max_speed = 30

        # Create speed zone trigger
        if max_speed <= 25:
            zone_type = "residential"
        elif max_speed <= 35:
            zone_type = "urban"
        elif max_speed <= 45:
            zone_type = "arterial"
        else:
            zone_type = "highway"

        obj["speed_zone"] = zone_type
        obj["speed_limit_mph"] = int(max_speed)
        created += 1

    return created


def export_all_formats() -> Dict[str, Any]:
    """Export scene for multiple game engines."""
    stats = {
        'unity': {},
        'unreal': {},
        'gltf': {},
        'total_files': 0,
    }

    # Get exportable objects
    export_objects = [
        obj for obj in bpy.context.scene.objects
        if obj.type in ('MESH', 'CURVE') and not obj.get('is_collision_proxy')
    ]

    base_output = Path(__file__).parent.parent / 'exports'

    # Export for Unity
    print("\n  Exporting for Unity...")
    unity_dir = base_output / 'unity'
    stats['unity'] = export_for_unity(export_objects, str(unity_dir))
    stats['total_files'] += len(stats['unity'].get('exported_files', []))

    for f in stats['unity'].get('exported_files', []):
        print(f"    {Path(f).name}")

    # Export for Unreal
    print("\n  Exporting for Unreal Engine...")
    unreal_dir = base_output / 'unreal'
    stats['unreal'] = export_for_unreal(export_objects, str(unreal_dir))
    stats['total_files'] += len(stats['unreal'].get('exported_files', []))

    for f in stats['unreal'].get('exported_files', []):
        print(f"    {Path(f).name}")

    # Export GLTF for web/cross-platform
    print("\n  Exporting GLTF...")
    gltf_dir = base_output / 'gltf'
    gltf_dir.mkdir(parents=True, exist_ok=True)

    stats['gltf'] = export_gltf(export_objects, str(gltf_dir / 'charlotte_roads.glb'))
    stats['total_files'] += len(stats['gltf'].get('exported_files', []))

    for f in stats['gltf'].get('exported_files', []):
        print(f"    {Path(f).name}")

    # Export collision separately
    collision_objects = [
        obj for obj in bpy.context.scene.objects
        if obj.get('is_collision_proxy')
    ]

    if collision_objects:
        print("\n  Exporting collision meshes...")
        bpy.ops.object.select_all(action='DESELECT')
        for obj in collision_objects:
            obj.select_set(True)

        collision_path = base_output / 'collision' / 'charlotte_collision.fbx'
        collision_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            bpy.ops.export_scene.fbx(
                filepath=str(collision_path),
                use_selection=True,
                axis_forward='-Z',
                axis_up='Y',
                use_mesh_modifiers=True,
            )
            stats['total_files'] += 1
            print(f"    {collision_path.name}")
        except Exception as e:
            print(f"    Collision export failed: {e}")

    return stats


def print_summary(
    collision: Dict,
    lod: Dict,
    npc: Dict,
    spawn: Dict,
    metadata: Dict,
    export: Dict
):
    """Print comprehensive summary."""
    print("\n" + "=" * 60)
    print("Game Integration Summary")
    print("=" * 60)

    print("\n[Collision System]")
    print(f"  Road surfaces: {collision.get('roads', 0)}")
    print(f"  Buildings: {collision.get('buildings', 0)}")
    print(f"  Street furniture: {collision.get('furniture', 0)}")
    print(f"  Collision proxies: {collision.get('proxies', 0)}")
    print(f"  Trigger zones: {collision.get('triggers', 0)}")

    print("\n[LOD System]")
    print(f"  Objects processed: {lod.get('objects_processed', 0)}")
    print(f"  LOD variants created: {lod.get('lod_created', 0)}")
    print(f"  Buildings with LOD: {lod.get('buildings', 0)}")
    print(f"  Roads with LOD: {lod.get('roads', 0)}")

    print("\n[NPC Navigation]")
    print(f"  Roads processed: {npc.get('roads_processed', 0)}")
    print(f"  Lane paths created: {npc.get('paths_created', 0)}")
    print(f"  Total path length: {npc.get('total_length_km', 0):.2f} km")

    print("\n[Spawn System]")
    print(f"  Total spawn points: {spawn.get('spawn_points', 0)}")
    print(f"  Player starts: {spawn.get('player_spawns', 0)}")
    print(f"  AI spawns: {spawn.get('ai_spawns', 0)}")

    print("\n[Game Metadata]")
    print(f"  Objects tagged: {metadata.get('objects_tagged', 0)}")
    print(f"  Road segments: {metadata.get('road_segments', 0)}")
    print(f"  Traffic signals: {metadata.get('traffic_signals', 0)}")
    print(f"  Speed zones: {metadata.get('zones_created', 0)}")

    print("\n[Export]")
    print(f"  Total files exported: {export.get('total_files', 0)}")

    # List export errors if any
    all_errors = []
    for target in ['unity', 'unreal', 'gltf']:
        errors = export.get(target, {}).get('errors', [])
        all_errors.extend(errors)

    if all_errors:
        print("\n[Export Errors]")
        for error in all_errors:
            print(f"  - {error}")

    print("\n" + "=" * 60)
    print("Charlotte is game-ready!")
    print("=" * 60)


# =============================================================================
# COMMAND LINE SUPPORT
# =============================================================================

def run_from_commandline():
    """Run via blender command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Charlotte Game Integration")
    parser.add_argument('--blend', type=str, help="Input blend file")
    parser.add_argument('--output', type=str, default='output/charlotte_game_ready.blend',
                        help="Output blend file")
    parser.add_argument('--export-unity', action='store_true', help="Export for Unity")
    parser.add_argument('--export-unreal', action='store_true', help="Export for Unreal")
    parser.add_argument('--export-gltf', action='store_true', help="Export as GLTF")
    parser.add_argument('--skip-lod', action='store_true', help="Skip LOD generation")
    parser.add_argument('--skip-paths', action='store_true', help="Skip NPC path generation")

    args = parser.parse_args()

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)

    main()


if __name__ == '__main__':
    main()
