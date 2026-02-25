"""
Charlotte Digital Twin - LOD System

Provides Level of Detail organization for efficient rendering
of the Charlotte digital twin.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import bpy


class LODLevel(Enum):
    """Level of Detail levels."""
    LOD0 = 0  # Hero - Full detail
    LOD1 = 1  # High - Simplified
    LOD2 = 2  # Medium - Box geometry
    LOD3 = 3  # Low - Flat footprint


@dataclass
class LODSpec:
    """Specifications for a LOD level."""
    level: LODLevel
    max_distance: float
    geometry_detail: str
    material_type: str
    has_windows: bool
    has_details: bool


LOD_SPECS = {
    LODLevel.LOD0: LODSpec(
        level=LODLevel.LOD0,
        max_distance=100.0,
        geometry_detail="full",
        material_type="pbr_textured",
        has_windows=True,
        has_details=True,
    ),
    LODLevel.LOD1: LODSpec(
        level=LODLevel.LOD1,
        max_distance=500.0,
        geometry_detail="simplified",
        material_type="single_texture",
        has_windows=True,
        has_details=False,
    ),
    LODLevel.LOD2: LODSpec(
        level=LODLevel.LOD2,
        max_distance=2000.0,
        geometry_detail="box",
        material_type="single_color",
        has_windows=False,
        has_details=False,
    ),
    LODLevel.LOD3: LODSpec(
        level=LODLevel.LOD3,
        max_distance=float('inf'),
        geometry_detail="footprint",
        material_type="flat",
        has_windows=False,
        has_details=False,
    ),
}


class LODAssigner:
    """Assigns LOD levels to objects."""

    def __init__(self):
        self.building_priority = {
            'commercial': 10,
            'retail': 9,
            'office': 9,
            'apartments': 7,
            'house': 5,
            'yes': 3,
            'garage': 2,
            'shed': 1,
            'roof': 1,
            'parking': 1,
        }

    def assign_building_lod(self, building_obj: bpy.types.Object) -> LODLevel:
        """
        Determine appropriate LOD level for a building.

        Priority factors:
        1. Named buildings -> LOD0
        2. Buildings with addresses -> LOD1
        3. Commercial/retail -> LOD1
        4. Type-based priority
        5. Location (Uptown gets higher detail)
        """
        # Named buildings are always hero
        if building_obj.get('building_name'):
            return LODLevel.LOD0

        # Buildings with addresses
        if building_obj.get('addr_housenumber') and building_obj.get('addr_street'):
            return LODLevel.LOD1

        # Type-based priority
        building_type = building_obj.get('building_type', 'yes')
        priority = self.building_priority.get(building_type, 3)

        # Uptown buildings get higher priority
        neighborhood = building_obj.get('neighborhood', '')
        if neighborhood == 'Uptown':
            priority += 2

        if priority >= 9:
            return LODLevel.LOD0
        elif priority >= 5:
            return LODLevel.LOD1
        else:
            return LODLevel.LOD2

    def assign_road_lod(self, road_obj: bpy.types.Object) -> LODLevel:
        """Determine LOD level for a road."""
        road_class = road_obj.get('road_class', 'local')

        if road_class == 'highway':
            return LODLevel.LOD1
        elif road_class == 'arterial':
            return LODLevel.LOD1
        elif road_class == 'collector':
            return LODLevel.LOD2
        else:
            return LODLevel.LOD3


class LODOrganizer:
    """Organizes objects into LOD collections."""

    def __init__(self):
        self.collections: Dict[str, bpy.types.Collection] = {}
        self._create_lod_collections()

    def _create_lod_collections(self):
        """Create LOD collection hierarchy."""
        # Main LOD collection
        lod_root = bpy.data.collections.get("LOD")
        if not lod_root:
            lod_root = bpy.data.collections.new("LOD")
            bpy.context.scene.collection.children.link(lod_root)

        # Buildings LOD
        for level in LODLevel:
            name = f"Buildings_{level.name}"
            coll = bpy.data.collections.get(name)
            if not coll:
                coll = bpy.data.collections.new(name)
                lod_root.children.link(coll)
            self.collections[f"buildings_{level.name}"] = coll

        # Roads LOD
        for level in LODLevel:
            name = f"Roads_{level.name}"
            coll = bpy.data.collections.get(name)
            if not coll:
                coll = bpy.data.collections.new(name)
                lod_root.children.link(coll)
            self.collections[f"roads_{level.name}"] = coll

    def add_to_lod(self, obj: bpy.types.Object, lod_level: LODLevel, obj_type: str):
        """Add object to appropriate LOD collection."""
        if obj_type == 'building':
            key = f"buildings_{lod_level.name}"
        elif obj_type == 'road':
            key = f"roads_{lod_level.name}"
        else:
            return

        coll = self.collections.get(key)
        if coll:
            # Remove from other collections first
            for c in list(obj.users_collection):
                c.objects.unlink(obj)
            coll.objects.link(obj)

            # Store LOD level on object
            obj['lod_level'] = lod_level.value

    def organize_all(self):
        """Organize all objects in scene into LOD collections."""
        assigner = LODAssigner()

        building_count = 0
        road_count = 0

        for obj in bpy.context.scene.objects:
            if obj.get('building_type'):
                lod = assigner.assign_building_lod(obj)
                self.add_to_lod(obj, lod, 'building')
                building_count += 1

            elif obj.get('road_class'):
                lod = assigner.assign_road_lod(obj)
                self.add_to_lod(obj, lod, 'road')
                road_count += 1

        print(f"Organized {building_count} buildings into LOD collections")
        print(f"Organized {road_count} roads into LOD collections")

        self._report_stats()

    def _report_stats(self):
        """Report LOD distribution statistics."""
        print("\n=== LOD Distribution ===")

        for key, coll in self.collections.items():
            count = len(coll.objects)
            if count > 0:
                print(f"  {key}: {count} objects")


def setup_visibility_toggles():
    """Create custom properties for easy LOD visibility toggling."""
    scene = bpy.context.scene

    # Add LOD visibility properties
    scene['lod_show_lod0'] = True
    scene['lod_show_lod1'] = True
    scene['lod_show_lod2'] = True
    scene['lod_show_lod3'] = True

    print("LOD visibility toggles added to scene properties")


def main():
    """Setup LOD system for Charlotte scene."""
    print("\n=== Setting up LOD System ===")

    # Create LOD organization
    organizer = LODOrganizer()
    organizer.organize_all()

    # Setup visibility toggles
    setup_visibility_toggles()

    print("\nLOD setup complete!")


if __name__ == '__main__':
    main()
