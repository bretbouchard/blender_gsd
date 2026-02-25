"""
Charlotte Digital Twin - PBR Materials & Visual Realism

Phase 4 of Driving Game implementation.
Creates comprehensive PBR materials with weather and wear effects.

Usage in Blender:
    import bpy
    bpy.ops.script.python_file_run(filepath="scripts/13_setup_materials.py")
"""

import bpy
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.materials_pbr import (
    create_all_pbr_materials,
    create_asphalt_material,
    create_road_marking_material,
    create_wet_road_material,
    create_puddle_material,
    add_crack_pattern_to_material,
    add_patch_overlay_to_material,
    assign_materials_by_zone,
    create_material_zone_map,
    AsphaltType,
    MarkingColor,
    WeatherCondition,
    MaterialZone,
    AsphaltParams,
    WeatherParams,
)


def main():
    """Generate all PBR materials for Charlotte."""
    print("\n" + "=" * 60)
    print("Charlotte PBR Materials & Visual Realism")
    print("=" * 60)

    # Step 1: Create all base materials
    print("\n[1/6] Creating base PBR materials...")
    materials = create_all_pbr_materials()

    # Step 2: Create weather variants
    print("\n[2/6] Creating weather variants...")
    weather_materials = create_weather_variants(materials)
    materials.update(weather_materials)

    # Step 3: Create worn/aged variants
    print("\n[3/6] Creating wear variants...")
    wear_materials = create_wear_variants()
    materials.update(wear_materials)

    # Step 4: Assign materials to objects
    print("\n[4/6] Assigning materials to objects...")
    assignment_stats = assign_materials_to_scene()

    # Step 5: Set up material zones
    print("\n[5/6] Setting up material zones...")
    zone_map = create_material_zone_map()

    # Step 6: Summary
    print("\n[6/6] Summary...")
    print_summary(materials, assignment_stats)

    # Save
    output_path = Path(__file__).parent.parent / 'output' / 'charlotte_materials.blend'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"\nSaved to {output_path}")


def create_weather_variants(base_materials: Dict) -> Dict[str, bpy.types.Material]:
    """Create weather condition variants of materials."""
    variants = {}

    # Get base asphalt materials
    asphalt_materials = {
        name: mat for name, mat in base_materials.items()
        if 'asphalt' in name.lower() and 'wet' not in name.lower()
    }

    for name, base_mat in asphalt_materials.items():
        # Wet variant
        wet_mat = create_wet_road_material(base_mat, wetness=0.7)
        if wet_mat:
            variants[wet_mat.name] = wet_mat
            print(f"  Created wet variant: {wet_mat.name}")

        # Heavy rain variant
        rain_mat = create_wet_road_material(base_mat, wetness=0.9)
        if rain_mat:
            rain_mat.name = f"{base_mat.name}_rain"
            rain_mat["weather_condition"] = WeatherCondition.RAINING.value
            variants[rain_mat.name] = rain_mat
            print(f"  Created rain variant: {rain_mat.name}")

    return variants


def create_wear_variants() -> Dict[str, bpy.types.Material]:
    """Create worn/aged material variants."""
    variants = {}

    # Create heavily worn asphalt
    worn_asphalt = create_asphalt_material(
        "asphalt_heavily_worn",
        AsphaltType.WORN,
        AsphaltParams(
            condition=AsphaltType.WORN,
            crack_density=0.6,
            patch_coverage=0.3,
        )
    )
    if worn_asphalt:
        add_crack_pattern_to_material(worn_asphalt, crack_density=0.6)
        add_patch_overlay_to_material(worn_asphalt, patch_coverage=0.3)
        variants[worn_asphalt.name] = worn_asphalt
        print(f"  Created: {worn_asphalt.name}")

    # Create intersection asphalt (more wear from stopping/turning)
    intersection_asphalt = create_asphalt_material(
        "asphalt_intersection",
        AsphaltType.NORMAL,
        AsphaltParams(
            condition=AsphaltType.NORMAL,
            oil_stain_intensity=0.4,
            crack_density=0.4,
        )
    )
    if intersection_asphalt:
        intersection_asphalt["is_intersection"] = True
        variants[intersection_asphalt.name] = intersection_asphalt
        print(f"  Created: {intersection_asphalt.name}")

    # Create heavily worn markings
    for color in [MarkingColor.WHITE, MarkingColor.YELLOW]:
        worn_marking = create_road_marking_material(color, worn_amount=0.8)
        if worn_marking:
            worn_marking.name = f"marking_{color.value}_heavily_worn"
            variants[worn_marking.name] = worn_marking
            print(f"  Created: {worn_marking.name}")

    return variants


def assign_materials_to_scene() -> Dict[str, int]:
    """Assign appropriate materials to scene objects."""
    stats = {
        'roads': 0,
        'markings': 0,
        'curbs': 0,
        'sidewalks': 0,
        'terrain': 0,
        'furniture': 0,
        'errors': 0,
    }

    # Get or create materials
    road_mat = bpy.data.materials.get("asphalt_normal")
    marking_white = bpy.data.materials.get("marking_white")
    marking_yellow = bpy.data.materials.get("marking_yellow")
    curb_mat = bpy.data.materials.get("concrete_curb") or bpy.data.materials.get("sidewalk_concrete")
    sidewalk_mat = bpy.data.materials.get("sidewalk_concrete")
    terrain_mat = bpy.data.materials.get("terrain_grass")

    # Assign to road surfaces
    for obj in bpy.context.scene.objects:
        try:
            obj_type = obj.get('road_class', None)
            marking_type = obj.get('marking_type', None)
            material_zone = obj.get('material_zone', None)

            # Road surfaces
            if obj_type and road_mat:
                if 'road' in obj.name.lower() or 'surface' in obj.name.lower():
                    if len(obj.material_slots) == 0:
                        obj.data.materials.append(road_mat)
                    stats['roads'] += 1

            # Markings
            if marking_type:
                if 'center' in marking_type and marking_yellow:
                    mat = marking_yellow
                elif marking_white:
                    mat = marking_white
                else:
                    continue

                if len(obj.material_slots) == 0:
                    obj.data.materials.append(mat)
                stats['markings'] += 1

            # By material zone
            if material_zone is not None:
                zone = MaterialZone(material_zone) if isinstance(material_zone, int) else None

                if zone == MaterialZone.CURB and curb_mat:
                    if len(obj.material_slots) == 0:
                        obj.data.materials.append(curb_mat)
                    stats['curbs'] += 1

                elif zone == MaterialZone.SIDEWALK and sidewalk_mat:
                    if len(obj.material_slots) == 0:
                        obj.data.materials.append(sidewalk_mat)
                    stats['sidewalks'] += 1

                elif zone == MaterialZone.TERRAIN and terrain_mat:
                    if len(obj.material_slots) == 0:
                        obj.data.materials.append(terrain_mat)
                    stats['terrain'] += 1

        except Exception as e:
            stats['errors'] += 1

    return stats


def print_summary(materials: Dict, assignment_stats: Dict):
    """Print generation summary."""

    # Categorize materials
    asphalt_count = sum(1 for m in materials if 'asphalt' in m.lower())
    marking_count = sum(1 for m in materials if 'marking' in m.lower())
    concrete_count = sum(1 for m in materials if 'concrete' in m.lower() or 'sidewalk' in m.lower())
    weather_count = sum(1 for m in materials if 'wet' in m.lower() or 'rain' in m.lower() or 'puddle' in m.lower())

    print("\n" + "=" * 60)
    print("PBR Materials Summary")
    print("=" * 60)

    print(f"\nMaterials Created: {len(materials)}")
    print(f"  Asphalt variants: {asphalt_count}")
    print(f"  Marking variants: {marking_count}")
    print(f"  Concrete/sidewalk: {concrete_count}")
    print(f"  Weather variants: {weather_count}")

    print(f"\nMaterial Assignments:")
    print(f"  Roads: {assignment_stats.get('roads', 0)}")
    print(f"  Markings: {assignment_stats.get('markings', 0)}")
    print(f"  Curbs: {assignment_stats.get('curbs', 0)}")
    print(f"  Sidewalks: {assignment_stats.get('sidewalks', 0)}")
    print(f"  Terrain: {assignment_stats.get('terrain', 0)}")
    print(f"  Errors: {assignment_stats.get('errors', 0)}")

    # List all materials
    print(f"\nMaterial List:")
    for name in sorted(materials.keys()):
        mat = materials[name]
        # Get material properties
        props = []
        if mat.get('asphalt_type'):
            props.append(f"type={mat['asphalt_type']}")
        if mat.get('wetness'):
            props.append(f"wet={mat['wetness']:.1f}")
        if mat.get('weather_condition'):
            props.append(f"weather={mat['weather_condition']}")
        if mat.get('worn_amount'):
            props.append(f"worn={mat['worn_amount']:.1f}")
        if mat.get('crack_density'):
            props.append(f"cracks={mat['crack_density']:.1f}")

        prop_str = f" ({', '.join(props)})" if props else ""
        print(f"  {name}{prop_str}")


# =============================================================================
# WEATHER SYSTEM SWITCHER
# =============================================================================

class WeatherSystem:
    """
    System to switch between weather conditions.

    Controls which material variants are used and adjusts
    scene properties like lighting and reflections.
    """

    def __init__(self):
        self.current_weather = WeatherCondition.DRY
        self.wetness_factor = 0.0

    def set_weather(self, condition: WeatherCondition, intensity: float = 1.0):
        """
        Set weather condition for the scene.

        Args:
            condition: Weather condition to apply
            intensity: Intensity of the effect (0-1)
        """
        self.current_weather = condition

        # Set wetness based on condition
        wetness_map = {
            WeatherCondition.DRY: 0.0,
            WeatherCondition.WET: 0.7 * intensity,
            WeatherCondition.RAINING: 0.9 * intensity,
            WeatherCondition.SNOW: 0.3 * intensity,
            WeatherCondition.FROZEN: 0.5 * intensity,
        }
        self.wetness_factor = wetness_map.get(condition, 0.0)

        # Update all road materials
        self._update_road_materials()

        # Update scene lighting
        self._update_lighting(condition, intensity)

    def _update_road_materials(self):
        """Update road materials based on wetness."""
        for obj in bpy.context.scene.objects:
            if obj.get('road_class') or 'road' in obj.name.lower():
                # Get current material
                if obj.data.materials:
                    base_mat = obj.data.materials[0]

                    # Find wet variant
                    wet_name = f"{base_mat.name}_wet"
                    if wet_name in bpy.data.materials and self.wetness_factor > 0.5:
                        obj.data.materials[0] = bpy.data.materials[wet_name]

    def _update_lighting(self, condition: WeatherCondition, intensity: float):
        """Update scene lighting for weather."""
        # Adjust sun lamp
        sun = bpy.data.objects.get("Sun")
        if sun and sun.data:
            if condition == WeatherCondition.RAINING:
                sun.data.energy = 0.5  # Dimmer
            elif condition == WeatherCondition.SNOW:
                sun.data.energy = 0.7
            else:
                sun.data.energy = 1.0  # Normal

        # Adjust world background
        world = bpy.context.scene.world
        if world and world.use_nodes:
            bg_node = world.node_tree.nodes.get("Background")
            if bg_node:
                if condition == WeatherCondition.RAINING:
                    bg_node.inputs["Color"].default_value = (0.3, 0.35, 0.4, 1.0)
                elif condition == WeatherCondition.SNOW:
                    bg_node.inputs["Color"].default_value = (0.7, 0.75, 0.8, 1.0)
                else:
                    bg_node.inputs["Color"].default_value = (0.05, 0.05, 0.1, 1.0)


def set_scene_weather(condition: str = "dry", intensity: float = 1.0):
    """
    Convenience function to set scene weather.

    Args:
        condition: "dry", "wet", "raining", "snow", or "frozen"
        intensity: Effect intensity (0-1)
    """
    weather_map = {
        "dry": WeatherCondition.DRY,
        "wet": WeatherCondition.WET,
        "raining": WeatherCondition.RAINING,
        "rain": WeatherCondition.RAINING,
        "snow": WeatherCondition.SNOW,
        "frozen": WeatherCondition.FROZEN,
    }

    weather_enum = weather_map.get(condition.lower(), WeatherCondition.DRY)

    system = WeatherSystem()
    system.set_weather(weather_enum, intensity)

    print(f"Weather set to: {weather_enum.value} (intensity: {intensity})")


# =============================================================================
# ROAD WEAR SYSTEM
# =============================================================================

def apply_wear_to_roads(
    crack_intensity: float = 0.3,
    patch_coverage: float = 0.1,
    oil_stains: float = 0.2
):
    """
    Apply wear effects to all road materials.

    Args:
        crack_intensity: Intensity of crack patterns (0-1)
        patch_coverage: Coverage of repair patches (0-1)
        oil_stains: Intensity of oil stains (0-1)
    """
    print(f"\nApplying road wear effects...")
    print(f"  Crack intensity: {crack_intensity}")
    print(f"  Patch coverage: {patch_coverage}")
    print(f"  Oil stains: {oil_stains}")

    for name, mat in bpy.data.materials.items():
        if 'asphalt' in name.lower():
            if crack_intensity > 0:
                add_crack_pattern_to_material(mat, crack_intensity)
            if patch_coverage > 0:
                add_patch_overlay_to_material(mat, patch_coverage)

            mat["oil_stain_intensity"] = oil_stains

            print(f"  Updated: {name}")


# =============================================================================
# INTERSECTION WEAR
# =============================================================================

def apply_intersection_wear(intersection_objects: List[bpy.types.Object]):
    """
    Apply additional wear to intersection areas.

    Intersections have more:
    - Oil stains from stopped vehicles
    - Tire marks
    - Worn paint

    Args:
        intersection_objects: List of intersection marker objects
    """
    intersection_mat = bpy.data.materials.get("asphalt_intersection")

    if not intersection_mat:
        intersection_mat = create_asphalt_material(
            "asphalt_intersection",
            AsphaltType.NORMAL,
            AsphaltParams(
                condition=AsphaltType.NORMAL,
                oil_stain_intensity=0.4,
                crack_density=0.4,
            )
        )

    for obj in intersection_objects:
        # Check if object is near intersection
        if obj.get('is_intersection') or 'intersection' in obj.name.lower():
            if len(obj.material_slots) == 0 and intersection_mat:
                obj.data.materials.append(intersection_mat)
            elif intersection_mat:
                obj.material_slots[0].material = intersection_mat


# =============================================================================
# COMMAND LINE SUPPORT
# =============================================================================

def run_from_commandline():
    """Run via blender command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate Charlotte PBR materials")
    parser.add_argument('--blend', type=str, help="Input blend file")
    parser.add_argument('--output', type=str, default='output/charlotte_materials.blend',
                        help="Output blend file")
    parser.add_argument('--weather', type=str, default='dry',
                        choices=['dry', 'wet', 'raining', 'snow'],
                        help="Weather condition")
    parser.add_argument('--wear', type=float, default=0.3,
                        help="Wear intensity (0-1)")

    args = parser.parse_args()

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)

    main()

    # Apply weather and wear
    set_scene_weather(args.weather)
    apply_wear_to_roads(crack_intensity=args.wear)

    bpy.ops.wm.save_as_mainfile(filepath=args.output)


if __name__ == '__main__':
    main()
