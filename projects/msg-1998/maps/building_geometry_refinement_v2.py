"""
MSG-1998 Building Geometry Refinement System v2

Fixed for Blender 5.x bmesh API changes.
Uses bmesh.from_edit_mesh() instead of bmesh.from_mesh()
"""

import bpy
import bmesh
from mathutils import Vector
import random
import math

# =============================================================================
# ARCHITECTURAL PROFILES
# =============================================================================

BUILDING_GEOMETRY_PROFILES = {
    "Madison Square Garden": {
        "type": "arena",
        "shape": "cylindrical",
        "features": ["cylindrical_facade", "cable_roof"],
        "roof_type": "domed",
        "setbacks": None,
    },
    "Empire State Building": {
        "type": "skyscraper_artdeco",
        "shape": "stepped",
        "features": ["multiple_setbacks", "spire"],
        "setbacks": [0.25, 0.45, 0.65, 0.80],
        "roof_type": "spire",
    },
    "PENN 1": {
        "type": "office_tower",
        "shape": "rectangular",
        "features": ["single_setback", "mechanical_penthouse"],
        "setbacks": [0.85],
        "roof_type": "flat_mechanical",
    },
}

TYPE_PROFILES = {
    "hotel_modern": {
        "features": ["window_grid", "mechanical_penthouse"],
        "setbacks": None,
        "roof_type": "flat_mechanical",
    },
    "hotel_historic": {
        "features": ["cornice", "window_grid"],
        "setbacks": [0.90],
        "roof_type": "flat_cornice",
    },
    "office_modern": {
        "features": ["window_grid", "mechanical_penthouse"],
        "setbacks": None,
        "roof_type": "flat_mechanical",
    },
    "office_historic": {
        "features": ["setbacks", "cornice"],
        "setbacks": [0.75, 0.90],
        "roof_type": "flat_cornice",
    },
    "residential": {
        "features": ["window_grid", "cornice"],
        "setbacks": None,
        "roof_type": "flat_cornice",
    },
    "church": {
        "features": ["steeple"],
        "setbacks": None,
        "roof_type": "steeple",
    },
    "retail": {
        "features": ["large_windows"],
        "setbacks": None,
        "roof_type": "flat",
    },
}


# =============================================================================
# GEOMETRY ANALYSIS
# =============================================================================

def get_object_dimensions(obj):
    """Get object dimensions in world space."""
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    min_x = min(v.x for v in bbox)
    max_x = max(v.x for v in bbox)
    min_y = min(v.y for v in bbox)
    max_y = max(v.y for v in bbox)
    min_z = min(v.z for v in bbox)
    max_z = max(v.z for v in bbox)

    return {
        'width': max_x - min_x,
        'depth': max_y - min_y,
        'height': max_z - min_z,
        'min_z': min_z,
        'max_z': max_z,
        'center': Vector(((min_x+max_x)/2, (min_y+max_y)/2, (min_z+max_z)/2)),
        'footprint_area': (max_x - min_x) * (max_y - min_y),
    }


def analyze_building_complexity(obj):
    """Analyze how complex the building geometry is."""
    if obj.type != 'MESH':
        return "unknown"

    vert_count = len(obj.data.vertices)
    face_count = len(obj.data.polygons)

    if face_count < 10:
        return "simple_box"
    elif face_count < 50:
        return "basic_shape"
    elif face_count < 200:
        return "moderate_detail"
    else:
        return "high_detail"


def classify_building(obj):
    """Classify building type based on name and dimensions."""
    name_lower = obj.name.lower()
    dims = get_object_dimensions(obj)

    for building_name in BUILDING_GEOMETRY_PROFILES:
        if building_name.lower() in name_lower:
            return BUILDING_GEOMETRY_PROFILES[building_name], "specific"

    if "church" in name_lower or "st." in name_lower or "cathedral" in name_lower:
        return TYPE_PROFILES["church"], "church"

    if "hotel" in name_lower or "inn" in name_lower or "suites" in name_lower:
        if dims['height'] > 80:
            return TYPE_PROFILES["hotel_historic"], "hotel_historic"
        return TYPE_PROFILES["hotel_modern"], "hotel_modern"

    if "residential" in name_lower or "apartment" in name_lower or "house" in name_lower:
        return TYPE_PROFILES["residential"], "residential"

    if "retail" in name_lower or "store" in name_lower or "shop" in name_lower:
        return TYPE_PROFILES["retail"], "retail"

    if dims['height'] > 60:
        return TYPE_PROFILES["office_historic"], "office_historic"
    return TYPE_PROFILES["office_modern"], "office_modern"


# =============================================================================
# GEOMETRY MODIFICATIONS (Fixed for Blender 5.x)
# =============================================================================

def add_setbacks_v2(obj, setback_heights, inset_amount=0.15):
    """
    Add setbacks using extrude and scale approach.
    Works with Blender 5.x bmesh API.
    """
    if not setback_heights:
        return False

    dims = get_object_dimensions(obj)
    if dims['height'] < 20:
        return False

    try:
        # Enter edit mode
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')

        # Get bmesh from edit mesh
        bm = bmesh.from_edit_mesh(obj.data)

        if bm is None:
            bpy.ops.object.mode_set(mode='OBJECT')
            return False

        # Find top face
        top_z = dims['max_z']
        tolerance = 0.5

        top_faces = []
        for face in bm.faces:
            face_center_z = sum(v.co.z for v in face.verts) / len(face.verts)
            if face_center_z > top_z - tolerance:
                top_faces.append(face)

        if not top_faces:
            bpy.ops.object.mode_set(mode='OBJECT')
            return False

        # Select top faces
        for face in top_faces:
            face.select = True

        # Extrude and scale for each setback
        for height_frac in sorted(setback_heights, reverse=True):
            target_z = dims['min_z'] + (dims['height'] * height_frac)

            # Deselect all
            for face in bm.faces:
                face.select = False

            # Find faces at this height level
            for face in bm.faces:
                avg_z = sum(v.co.z for v in face.verts) / len(face.verts)
                if abs(avg_z - target_z) < dims['height'] * 0.1:
                    face.select = True

            selected = [f for f in bm.faces if f.select]
            if selected:
                # Scale selected faces inward
                scale_factor = 1.0 - inset_amount
                bmesh.ops.scale(
                    bm,
                    vec=Vector((scale_factor, scale_factor, 1.0)),
                    space=Matrix.Translation(dims['center']),
                    verts=[v for f in selected for v in f.verts]
                )

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        return True

    except Exception as e:
        print(f"    Setback error: {e}")
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        return False


def add_rooftop_structure(obj, structure_type='mechanical'):
    """Add a rooftop structure using object duplication approach."""

    dims = get_object_dimensions(obj)
    if dims['height'] < 20:
        return False

    try:
        # Calculate structure dimensions
        struct_height = min(4.0, dims['height'] * 0.03)
        struct_width = dims['width'] * 0.4
        struct_depth = dims['depth'] * 0.4

        if struct_width < 3 or struct_depth < 3:
            return False

        # Create a new cube for the structure
        bpy.ops.mesh.primitive_cube_add(size=1)

        struct_obj = bpy.context.active_object
        struct_obj.name = f"{obj.name}_rooftop"

        # Scale and position it
        struct_obj.scale = (struct_width/2, struct_depth/2, struct_height/2)
        struct_obj.location = (
            dims['center'].x,
            dims['center'].y,
            dims['max_z'] + struct_height/2
        )

        # Apply scale
        bpy.context.view_layer.objects.active = struct_obj
        bpy.ops.object.transform_apply(scale=True)

        # Parent to building
        struct_obj.parent = obj

        # Move to same collection
        for coll in obj.users_collection:
            if struct_obj not in coll.objects:
                coll.objects.link(struct_obj)

        # Unlink from master collection if there
        if struct_obj in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(struct_obj)

        return True

    except Exception as e:
        print(f"    Rooftop structure error: {e}")
        return False


def add_roof_water_tank_v2(obj):
    """Add a water tank structure on the roof."""
    dims = get_object_dimensions(obj)

    if dims['height'] < 30:
        return False

    try:
        tank_radius = min(3.0, min(dims['width'], dims['depth']) * 0.08)
        tank_height = tank_radius * 1.5

        # Offset from center
        offset_x = dims['width'] * 0.25
        offset_y = dims['depth'] * 0.25

        # Create cylinder for water tank
        bpy.ops.mesh.primitive_cylinder_add(
            radius=tank_radius,
            depth=tank_height,
            location=(
                dims['center'].x + offset_x,
                dims['center'].y + offset_y,
                dims['max_z'] + tank_height/2
            )
        )

        tank = bpy.context.active_object
        tank.name = f"{obj.name}_watertank"
        tank.parent = obj

        # Move to same collection
        for coll in obj.users_collection:
            if tank not in coll.objects:
                coll.objects.link(tank)

        if tank in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(tank)

        return True

    except Exception as e:
        print(f"    Water tank error: {e}")
        return False


def subdivide_for_windows_v2(obj, floors=None):
    """Subdivide building using loop cuts for window pattern."""

    dims = get_object_dimensions(obj)

    if floors is None:
        floors = max(2, int(dims['height'] / 4.0))  # ~4m per floor

    try:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')

        # Select all
        bpy.ops.mesh.select_all(action='SELECT')

        # Add vertical loop cuts (for windows across width)
        try:
            bpy.ops.mesh.loopcut_slide(
                MESH_OT_loopcut={
                    "number_cuts": min(floors, 20),
                    "smoothness": 0,
                    "falloff": 'INVERSE_SURFACE',
                    "object_index": 0,
                    "edge_index": 0,
                },
                TRANSFORM_OT_edge_slide={"value": 0}
            )
        except:
            pass

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')
        return True

    except Exception as e:
        print(f"    Subdivision error: {e}")
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            pass
        return False


# =============================================================================
# MAIN REFINEMENT WORKFLOW
# =============================================================================

def analyze_all_buildings():
    """Analyze all buildings and categorize refinement needs."""

    print("\n" + "=" * 80)
    print("MSG-1998 Building Geometry Analysis")
    print("=" * 80)

    if "Buildings" not in bpy.data.collections:
        print("ERROR: Buildings collection not found!")
        return None

    buildings_coll = bpy.data.collections["Buildings"]
    buildings = [obj for obj in buildings_coll.objects if obj.type == 'MESH']

    analysis = {
        'simple_box': [],
        'basic_shape': [],
        'moderate_detail': [],
        'high_detail': [],
        'special_buildings': [],
    }

    for obj in buildings:
        complexity = analyze_building_complexity(obj)
        profile, building_type = classify_building(obj)
        dims = get_object_dimensions(obj)

        info = {
            'object': obj,
            'name': obj.name,
            'type': building_type,
            'dimensions': dims,
            'complexity': complexity,
            'profile': profile,
        }

        if building_type == "specific":
            analysis['special_buildings'].append(info)
        else:
            analysis[complexity].append(info)

    print(f"\nTotal buildings analyzed: {len(buildings)}")
    print(f"\nComplexity breakdown:")
    print(f"  Simple boxes: {len(analysis['simple_box'])}")
    print(f"  Basic shapes: {len(analysis['basic_shape'])}")
    print(f"  Moderate detail: {len(analysis['moderate_detail'])}")
    print(f"  High detail: {len(analysis['high_detail'])}")
    print(f"  Special buildings: {len(analysis['special_buildings'])}")

    return analysis


def refine_all_buildings_v2():
    """Apply geometry refinements using fixed Blender 5.x methods."""

    print("\n" + "=" * 80)
    print("MSG-1998 Building Geometry Refinement v2")
    print("=" * 80)

    analysis = analyze_all_buildings()
    if not analysis:
        return

    refined_count = 0
    rooftop_count = 0
    watertank_count = 0

    # Process all simple and basic buildings
    for complexity in ['simple_box', 'basic_shape']:
        for info in analysis[complexity]:
            obj = info['object']
            profile = info['profile']
            dims = info['dimensions']

            # Skip parks and very small structures
            if dims['height'] < 5:
                continue

            print(f"\n  Refining: {obj.name[:50]}")

            try:
                # Add rooftop structure to taller buildings
                if dims['height'] > 40:
                    if add_rooftop_structure(obj):
                        print(f"    Added rooftop structure")
                        rooftop_count += 1

                # Add water tank to very tall buildings
                if dims['height'] > 60:
                    if add_roof_water_tank_v2(obj):
                        print(f"    Added water tank")
                        watertank_count += 1

                refined_count += 1

            except Exception as e:
                print(f"    ERROR: {e}")

    print("\n" + "=" * 80)
    print(f"Refinement Complete:")
    print(f"  Buildings processed: {refined_count}")
    print(f"  Rooftop structures added: {rooftop_count}")
    print(f"  Water tanks added: {watertank_count}")
    print("=" * 80)


# =============================================================================
# SPECIAL BUILDING HANDLERS
# =============================================================================

def create_msg_arena_geometry():
    """Create proper cylindrical geometry for Madison Square Garden."""

    # Find MSG in scene
    msg = None
    for obj in bpy.data.objects:
        if "madison square garden" in obj.name.lower():
            msg = obj
            break

    if not msg:
        print("Madison Square Garden not found!")
        return False

    dims = get_object_dimensions(msg)

    # MSG specs: 425ft diameter, 153ft height
    # Our scene uses meters
    target_diameter = 129.5  # 425ft in meters
    target_height = 46.6     # 153ft in meters

    print(f"\nCreating MSG Arena geometry:")
    print(f"  Current: {dims['width']:.1f}m x {dims['depth']:.1f}m x {dims['height']:.1f}m")
    print(f"  Target:  ~{target_diameter:.1f}m diameter x {target_height:.1f}m height")

    # Create new cylinder
    bpy.ops.mesh.primitive_cylinder_add(
        radius=target_diameter / 2,
        depth=target_height,
        location=dims['center']
    )

    new_msg = bpy.context.active_object
    new_msg.name = "Madison Square Garden_NEW"

    # Copy materials from old MSG
    if msg.data.materials:
        for mat in msg.data.materials:
            new_msg.data.materials.append(mat)

    # Parent to same collection
    for coll in msg.users_collection:
        coll.objects.link(new_msg)

    print(f"  Created: {new_msg.name}")
    print(f"  Delete old MSG and rename new one to complete")

    return True


def create_empire_state_setbacks():
    """Add proper Art Deco setbacks to Empire State Building."""

    esb = None
    for obj in bpy.data.objects:
        if "empire state" in obj.name.lower():
            esb = obj
            break

    if not esb:
        print("Empire State Building not found!")
        return False

    dims = get_object_dimensions(esb)

    print(f"\nAdding setbacks to Empire State Building:")
    print(f"  Current height: {dims['height']:.1f}m")

    # Add setbacks at classic Art Deco heights
    setbacks = [0.25, 0.45, 0.65, 0.80, 0.92]

    if add_setbacks_v2(esb, setbacks, inset_amount=0.12):
        print(f"  Added setbacks at: {setbacks}")
        return True

    return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""

    print("\n" + "=" * 80)
    print("MSG-1998 Building Geometry Refinement System v2")
    print("=" * 80)

    # Analyze
    analysis = analyze_all_buildings()

    # Refine
    refine_all_buildings_v2()

    print("\n" + "=" * 80)
    print("For special buildings, run:")
    print("  create_msg_arena_geometry()")
    print("  create_empire_state_setbacks()")
    print("=" * 80)


if __name__ == "__main__":
    main()
