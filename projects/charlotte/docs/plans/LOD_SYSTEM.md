# Charlotte - LOD System Plan

## Goal
Implement a Level of Detail (LOD) system for the Charlotte digital twin that enables efficient rendering and viewport performance for 3,739 buildings and 5,500+ road segments.

## Requirements
- Support 4 LOD levels (LOD0-Hero through LOD3-Low)
- Group objects by LOD for easy visibility toggling
- Enable distance-based switching for rendering
- Maintain attribute access across all LOD levels
- Support neighborhood/block-based LOD batching

## LOD Levels

### Buildings

| LOD | Distance | Features | Target Count |
|-----|----------|----------|--------------|
| LOD0 (Hero) | 0-100m | Full detail, windows, textures | ~100-200 |
| LOD1 (High) | 100-500m | Simplified geometry, implied windows | ~500-800 |
| LOD2 (Medium) | 500m-2km | Box geometry, single material | ~1500-2000 |
| LOD3 (Low) | 2km+ | Flat footprint only | ~1000-1500 |

### Roads

| LOD | Features | Target |
|-----|----------|--------|
| LOD0 | Lane markings, cracks, manholes | Hero roads |
| LOD1 | Lane markings only | Arterials |
| LOD2 | Textured surface | Collectors |
| LOD3 | Flat colored surface | Local, service |

## Implementation

### File: `scripts/lib/lod_system.py`

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import bpy
import math

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
        if building_obj.get('name') or building_obj.get('building_name'):
            return LODLevel.LOD0

        # Buildings with addresses
        if building_obj.get('addr_housenumber') and building_obj.get('addr_street'):
            return LODLevel.LOD1

        # Type-based priority
        building_type = building_obj.get('building_type', 'yes')
        priority = self.building_priority.get(building_type, 3)

        if priority >= 9:
            return LODLevel.LOD1
        elif priority >= 5:
            return LODLevel.LOD2
        else:
            return LODLevel.LOD3

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
        self.collections = {}
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
            for c in obj.users_collection:
                c.objects.unlink(obj)
            coll.objects.link(obj)

            # Store LOD level on object
            obj['lod_level'] = lod_level.value

    def organize_all(self):
        """Organize all objects in scene into LOD collections."""
        assigner = LODAssigner()

        for obj in bpy.context.scene.objects:
            if obj.get('building_type'):
                lod = assigner.assign_building_lod(obj)
                self.add_to_lod(obj, lod, 'building')
            elif obj.get('road_class'):
                lod = assigner.assign_road_lod(obj)
                self.add_to_lod(obj, lod, 'road')

        self._report_stats()

    def _report_stats(self):
        """Report LOD distribution statistics."""
        print("\n=== LOD Distribution ===")

        for key, coll in self.collections.items():
            count = len(coll.objects)
            if count > 0:
                print(f"{key}: {count} objects")

class LODSwitcher:
    """Handles runtime LOD switching based on camera distance."""

    def __init__(self, camera: bpy.types.Object = None):
        self.camera = camera or bpy.context.scene.camera
        self.enabled = False

    def setup_driver(self):
        """Setup Blender drivers for automatic LOD switching."""
        # This would setup drivers on collection visibility
        # based on camera distance to collection center
        pass

    def update_visibility(self, max_distance: float = 2000.0):
        """
        Update collection visibility based on camera position.

        Note: For production, use Blender's built-in LOD system
        or geometry nodes for distance-based switching.
        """
        if not self.camera:
            return

        cam_loc = self.camera.location

        for level in LODLevel:
            spec = LOD_SPECS[level]

            # Check each LOD collection
            for obj_type in ['buildings', 'roads']:
                key = f"{obj_type}_{level.name}"
                coll = bpy.data.collections.get(key)
                if not coll:
                    continue

                # Simple distance check to collection center
                # In production, would use more sophisticated culling
                coll.hide_viewport = spec.max_distance < 1.0  # Placeholder logic

class LODGenerator:
    """Generates simplified geometry for lower LOD levels."""

    def generate_lod_geometry(self, obj: bpy.types.Object, target_lod: LODLevel):
        """
        Generate simplified geometry for an object.

        For LOD1-LOD3, creates simplified versions.
        """
        if target_lod == LODLevel.LOD0:
            return obj  # No simplification

        # Create simplified copy
        simplified = obj.copy()
        simplified.data = obj.data.copy()
        simplified.name = f"{obj.name}_{target_lod.name}"

        if target_lod == LODLevel.LOD2:
            # Box geometry - use bounding box
            self._simplify_to_box(simplified)
        elif target_lod == LODLevel.LOD3:
            # Flat footprint - project to Z=0
            self._flatten_to_footprint(simplified)

        return simplified

    def _simplify_to_box(self, obj):
        """Simplify object to bounding box."""
        # Get bounding box
        bbox = obj.bound_box

        # Create new simple box mesh
        # ... implementation

    def _flatten_to_footprint(self, obj):
        """Flatten object to 2D footprint."""
        # Project all vertices to Z=0
        for v in obj.data.vertices:
            v.co.z = 0
```

### File: `scripts/6_setup_lod.py`

```python
import bpy
from lib.lod_system import LODAssigner, LODOrganizer, LODLevel

def main():
    """Setup LOD system for Charlotte scene."""
    print("Setting up LOD system...")

    # Create LOD organization
    organizer = LODOrganizer()

    # Assign and organize all buildings
    assigner = LODAssigner()

    building_count = 0
    road_count = 0

    for obj in bpy.context.scene.objects:
        if obj.get('building_type'):
            lod = assigner.assign_building_lod(obj)
            organizer.add_to_lod(obj, lod, 'building')
            building_count += 1

        elif obj.get('road_class'):
            lod = assigner.assign_road_lod(obj)
            organizer.add_to_lod(obj, lod, 'road')
            road_count += 1

    print(f"Organized {building_count} buildings into LOD collections")
    print(f"Organized {road_count} roads into LOD collections")

    # Report distribution
    organizer._report_stats()

    # Setup visibility toggles
    setup_visibility_toggles()

    print("LOD setup complete!")

def setup_visibility_toggles():
    """Create custom properties for easy LOD visibility toggling."""
    scene = bpy.context.scene

    # Add LOD visibility properties
    if not hasattr(scene, 'lod_show_lod0'):
        scene['lod_show_lod0'] = True
        scene['lod_show_lod1'] = True
        scene['lod_show_lod2'] = True
        scene['lod_show_lod3'] = True

    print("LOD visibility toggles added to scene properties")

if __name__ == '__main__':
    main()
```

## Collection Structure

```
LOD/
├── Buildings_LOD0/    # Hero buildings (~200)
├── Buildings_LOD1/    # High detail (~800)
├── Buildings_LOD2/    # Medium detail (~1500)
├── Buildings_LOD3/    # Low detail (~1200)
├── Roads_LOD0/        # Hero roads
├── Roads_LOD1/        # Arterials + highways
├── Roads_LOD2/        # Collectors
└── Roads_LOD3/        # Local + service
```

## LOD Assignment Rules

### Buildings
```
IF has name OR in Uptown → LOD0
ELSE IF has address → LOD1
ELSE IF commercial/retail/office → LOD1
ELSE IF apartments → LOD2
ELSE IF house → LOD2
ELSE → LOD3
```

### Roads
```
IF highway → LOD1
ELSE IF arterial → LOD1
ELSE IF collector → LOD2
ELSE → LOD3
```

## Scene Properties

After running LOD setup, these custom properties are available:

```python
# Toggle LOD visibility
bpy.context.scene['lod_show_lod0'] = True   # Show hero detail
bpy.context.scene['lod_show_lod1'] = True   # Show high detail
bpy.context.scene['lod_show_lod2'] = True   # Show medium detail
bpy.context.scene['lod_show_lod3'] = True   # Show low detail
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Viewport with LOD0-LOD1 only | 30+ FPS |
| Viewport with all LODs | 15+ FPS |
| Render time (single frame) | < 5 min |
| Memory usage | < 8 GB |

## Success Criteria
- [ ] All buildings assigned to LOD collections
- [ ] All roads assigned to LOD collections
- [ ] LOD distribution matches targets
- [ ] Visibility toggles work
- [ ] Viewport performance acceptable

## Estimated Effort
- LOD assignment logic: 1 hour
- Collection organization: 1 hour
- Visibility system: 1 hour
- Testing and tuning: 1 hour
