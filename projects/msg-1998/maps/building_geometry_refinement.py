"""
MSG-1998 Building Geometry Refinement System

Analyzes and refines building geometries to make them more architecturally accurate:
1. Add setbacks to tall buildings (1916 Zoning Resolution style)
2. Add rooftop details (mechanical penthouses, water tanks)
3. Add window grid patterns via UV mapping or geometry
4. Special handling for landmark buildings (MSG, Empire State, etc.)

Key architectural features for NYC buildings:
- Setbacks: Stepped profiles allowing light to streets
- Rooftop mechanical: Elevator penthouses, water tanks, HVAC
- Window patterns: Grid layouts typical of each era
- Base/Tower distinction: Wider base, narrower tower
"""

import bpy
import bmesh
from mathutils import Vector, Matrix
import random
import math

# =============================================================================
# ARCHITECTURAL PROFILES
# =============================================================================

# Building-specific geometry instructions
BUILDING_GEOMETRY_PROFILES = {
    "Madison Square Garden": {
        "type": "arena",
        "shape": "cylindrical",
        "features": ["cylindrical_facade", "cable_roof", "low_profile"],
        "roof_type": "domed",
        "setbacks": None,
    },
    "Empire State Building": {
        "type": "skyscraper_artdeco",
        "shape": "stepped",
        "features": ["multiple_setbacks", "spire", "art_deco_massing"],
        "setbacks": [0.25, 0.45, 0.65, 0.80],  # Fraction of height
        "roof_type": "spire",
    },
    "PENN 1": {
        "type": "office_tower",
        "shape": "rectangular",
        "features": ["single_setback", "mechanical_penthouse"],
        "setbacks": [0.85],
        "roof_type": "flat_mechanical",
    },
    "PENN 2": {
        "type": "office_tower",
        "shape": "rectangular",
        "features": ["mechanical_penthouse"],
        "setbacks": None,
        "roof_type": "flat_mechanical",
    },
    "New Yorker by Lotte Hotels": {
        "type": "hotel_historic",
        "shape": "setback",
        "features": ["art_deco_setbacks", "signage_top"],
        "setbacks": [0.70, 0.85],
        "roof_type": "flat_signage",
    },
    "Macy's": {
        "type": "department_store",
        "shape": "block",
        "features": ["large_floorplate", "cornice", "display_windows"],
        "setbacks": None,
        "roof_type": "flat",
    },
}

# Generic profiles by building type
TYPE_PROFILES = {
    "hotel_modern": {
        "features": ["window_grid", "mechanical_penthouse"],
        "setbacks": None,
        "roof_type": "flat_mechanical",
    },
    "hotel_historic": {
        "features": ["cornice", "window_grid", "small_setback"],
        "setbacks": [0.90],
        "roof_type": "flat_cornice",
    },
    "office_modern": {
        "features": ["window_grid", "mechanical_penthouse"],
        "setbacks": None,
        "roof_type": "flat_mechanical",
    },
    "office_historic": {
        "features": ["setbacks", "cornice", "window_grid"],
        "setbacks": [0.75, 0.90],
        "roof_type": "flat_cornice",
    },
    "residential": {
        "features": ["window_grid", "cornice"],
        "setbacks": None,
        "roof_type": "flat_cornice",
    },
    "church": {
        "features": ["steeple", "gothic_windows", "buttresses"],
        "setbacks": None,
        "roof_type": "steeple",
    },
    "retail": {
        "features": ["large_windows", "awning", "signage"],
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
        'center': Vector(( (min_x+max_x)/2, (min_y+max_y)/2, (min_z+max_z)/2 )),
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

    # Check for specific buildings first
    for building_name in BUILDING_GEOMETRY_PROFILES:
        if building_name.lower() in name_lower:
            return BUILDING_GEOMETRY_PROFILES[building_name], "specific"

    # Classify by keywords
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

    # Default to office
    if dims['height'] > 60:
        return TYPE_PROFILES["office_historic"], "office_historic"
    return TYPE_PROFILES["office_modern"], "office_modern"


# =============================================================================
# GEOMETRY MODIFICATIONS
# =============================================================================

def add_setbacks(obj, setback_heights, inset_amount=0.15):
    """
    Add setbacks to a building at specified height fractions.

    Args:
        obj: Blender mesh object
        setback_heights: List of height fractions (0.0-1.0) where setbacks occur
        inset_amount: How much to inset the setback (fraction of footprint)
    """
    if not setback_heights:
        return False

    dims = get_object_dimensions(obj)
    if dims['height'] < 20:  # Don't add setbacks to short buildings
        return False

    # Enter edit mode
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')

    # Get bmesh
    bm = bmesh.from_mesh(obj.data)
    bmesh.ops.transform(bm, matrix=obj.matrix_world, verts=bm.verts)

    # Find vertices at each setback level and move them inward
    for height_frac in sorted(setback_heights):
        target_z = dims['min_z'] + (dims['height'] * height_frac)
        tolerance = dims['height'] * 0.05  # 5% tolerance

        # Find verts near this height on the perimeter
        for vert in bm.verts:
            if abs(vert.co.z - target_z) < tolerance:
                # Check if this is an edge vert (not interior)
                is_edge = False
                for edge in vert.link_edges:
                    other = edge.other_vert(vert)
                    if abs(other.co.z - vert.co.z) > tolerance:
                        is_edge = True
                        break

                if is_edge:
                    # Move vert toward center
                    direction = dims['center'].xy - vert.co.xy
                    if direction.length > 0:
                        direction.normalize()
                        move_dist = min(dims['width'], dims['depth']) * inset_amount
                        vert.co.xy += direction * move_dist * 0.3

    # Apply changes
    bmesh.ops.transform(bm, matrix=obj.matrix_world.inverted(), verts=bm.verts)
    bmesh.update_edit_mesh(obj.data)

    bpy.ops.object.mode_set(mode='OBJECT')
    return True


def add_mechanical_penthouse(obj, height_fraction=0.03, inset_fraction=0.1):
    """Add a mechanical penthouse/rooftop structure to a building."""

    dims = get_object_dimensions(obj)
    if dims['height'] < 15:  # Skip short buildings
        return False

    # Calculate penthouse dimensions
    penthouse_height = dims['height'] * height_fraction
    if penthouse_height < 2:
        penthouse_height = 2
    if penthouse_height > 8:
        penthouse_height = 8

    # Create penthouse mesh
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_mesh(obj.data)
    bmesh.ops.transform(bm, matrix=obj.matrix_world, verts=bm.verts)

    # Find the top face
    top_z = dims['max_z']
    top_verts = [v for v in bm.verts if abs(v.co.z - top_z) < 0.1]

    if len(top_verts) < 4:
        bpy.ops.object.mode_set(mode='OBJECT')
        return False

    # Get the center of the top
    center_xy = Vector((
        sum(v.co.x for v in top_verts) / len(top_verts),
        sum(v.co.y for v in top_verts) / len(top_verts),
        top_z
    ))

    # Create inset rectangle for penthouse base
    inset_dist = min(dims['width'], dims['depth']) * inset_fraction

    # Find corners and inset them
    new_z = top_z + penthouse_height

    # Create new face for penthouse top
    # Get bounding box of top
    min_x = min(v.co.x for v in top_verts)
    max_x = max(v.co.x for v in top_verts)
    min_y = min(v.co.y for v in top_verts)
    max_y = max(v.co.y for v in top_verts)

    # Create inset corners
    corners = [
        (min_x + inset_dist, min_y + inset_dist),
        (max_x - inset_dist, min_y + inset_dist),
        (max_x - inset_dist, max_y - inset_dist),
        (min_x + inset_dist, max_y - inset_dist),
    ]

    # Create new vertices for penthouse
    new_verts = []
    for x, y in corners:
        vert = bm.verts.new((x, y, new_z))
        new_verts.append(vert)

    # Create new face
    bm.faces.new(new_verts)

    # Create side faces (extrude up from inset)
    # This is simplified - proper implementation would need edge detection

    bmesh.ops.transform(bm, matrix=obj.matrix_world.inverted(), verts=bm.verts)
    bmesh.update_edit_mesh(obj.data)

    bpy.ops.object.mode_set(mode='OBJECT')
    return True


def add_cornice(obj, depth=0.5, height=0.8):
    """Add a cornice (decorative overhang) at the top of a building."""

    dims = get_object_dimensions(obj)
    if dims['height'] < 10:
        return False

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    bm = bmesh.from_mesh(obj.data)
    bmesh.ops.transform(bm, matrix=obj.matrix_world, verts=bm.verts)

    top_z = dims['max_z']
    tolerance = 0.5

    # Find top edge vertices and extrude them outward
    top_verts = [v for v in bm.verts if v.co.z > top_z - tolerance]

    for vert in top_verts:
        # Push outward from center
        direction = vert.co.xy - dims['center'].xy
        if direction.length > 0:
            direction.normalize()
            vert.co.xy += direction * depth
            vert.co.z += height * 0.5

    bmesh.ops.transform(bm, matrix=obj.matrix_world.inverted(), verts=bm.verts)
    bmesh.update_edit_mesh(obj.data)

    bpy.ops.object.mode_set(mode='OBJECT')
    return True


def subdivide_for_windows(obj, target_face_size=15.0):
    """
    Subdivide building faces to create window grid pattern.
    Uses subdivision surface modifier for cleaner results.
    """
    dims = get_object_dimensions(obj)

    # Calculate how many subdivisions needed
    width_subdivs = max(1, int(dims['width'] / target_face_size))
    depth_subdivs = max(1, int(dims['depth'] / target_face_size))
    height_subdivs = max(2, int(dims['height'] / 4.0))  # ~4m per floor

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')

    # Simple subdivision approach
    bm = bmesh.from_mesh(obj.data)
    bmesh.ops.transform(bm, matrix=obj.matrix_world, verts=bm.verts)

    # Subdivide edges
    edges_to_subdivide = []

    # Find vertical edges and subdivide
    for edge in bm.edges:
        v1, v2 = edge.verts
        if abs(v1.co.z - v2.co.z) > dims['height'] * 0.5:
            edges_to_subdivide.append(edge)

    if edges_to_subdivide:
        bmesh.ops.subdivide_edges(bm, edges=edges_to_subdivide, cuts=height_subdivs)

    bmesh.ops.transform(bm, matrix=obj.matrix_world.inverted(), verts=bm.verts)
    bmesh.update_edit_mesh(obj.data)

    bpy.ops.object.mode_set(mode='OBJECT')
    return True


def add_roof_water_tank(obj):
    """Add a water tank structure on the roof (classic NYC feature)."""
    dims = get_object_dimensions(obj)

    if dims['height'] < 30:  # Only taller buildings
        return False

    # Water tank dimensions
    tank_radius = min(dims['width'], dims['depth']) * 0.08
    if tank_radius < 2:
        tank_radius = 2
    if tank_radius > 5:
        tank_radius = 5

    tank_height = tank_radius * 1.5

    # Create cylinder for water tank
    bpy.context.view_layer.objects.active = obj

    # Store original location
    orig_loc = obj.location.copy()

    # Create water tank mesh
    bpy.ops.mesh.primitive_cylinder_add(
        radius=tank_radius,
        depth=tank_height,
        location=(dims['center'].x, dims['center'].y, dims['max_z'] + tank_height/2)
    )
    tank = bpy.context.active_object
    tank.name = f"{obj.name}_watertank"

    # Parent to building
    tank.parent = obj

    # Move to same collection
    for coll in obj.users_collection:
        coll.objects.link(tank)

    return True


# =============================================================================
# SPECIAL BUILDING HANDLERS
# =============================================================================

def refine_msg_arena(obj):
    """Special refinement for Madison Square Garden - cylindrical arena."""
    dims = get_object_dimensions(obj)

    # MSG is cylindrical with a domed roof
    # If the current mesh is boxy, we should make it more cylindrical

    complexity = analyze_building_complexity(obj)

    if complexity == "simple_box":
        print(f"  MSG is currently a box - would need major geometry replacement")
        print(f"    Recommended: Create cylindrical mesh with {dims['width']:.0f}m diameter")
        return "needs_replacement"

    # Add subtle details if already roughly correct shape
    return "refined"


def refine_empire_state(obj):
    """Special refinement for Empire State Building - Art Deco setbacks."""
    dims = get_object_dimensions(obj)

    # ESB has multiple setbacks creating the classic stepped profile
    # Height: 443m to tip, ~380m to roof

    profile = BUILDING_GEOMETRY_PROFILES.get("Empire State Building")

    # Check if setbacks already exist
    complexity = analyze_building_complexity(obj)

    if complexity in ["simple_box", "basic_shape"]:
        print(f"  Empire State needs setback geometry added")
        added = add_setbacks(obj, profile['setbacks'], inset_amount=0.12)
        if added:
            return "setbacks_added"

    return "already_detailed"


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

    # Print summary
    print(f"\nTotal buildings analyzed: {len(buildings)}")
    print(f"\nComplexity breakdown:")
    print(f"  Simple boxes (need major work): {len(analysis['simple_box'])}")
    print(f"  Basic shapes (need refinement): {len(analysis['basic_shape'])}")
    print(f"  Moderate detail: {len(analysis['moderate_detail'])}")
    print(f"  High detail: {len(analysis['high_detail'])}")
    print(f"  Special buildings: {len(analysis['special_buildings'])}")

    # List simple boxes that need most work
    if analysis['simple_box']:
        print("\n" + "-" * 80)
        print("Buildings needing geometry replacement (simple boxes):")
        print("-" * 80)
        for info in sorted(analysis['simple_box'], key=lambda x: -x['dimensions']['height'])[:20]:
            d = info['dimensions']
            print(f"  {info['name'][:45]:<45} {d['height']:>6.1f}m x {d['width']:>6.1f}m")

    # List special buildings
    if analysis['special_buildings']:
        print("\n" + "-" * 80)
        print("Special buildings requiring custom handling:")
        print("-" * 80)
        for info in analysis['special_buildings']:
            d = info['dimensions']
            print(f"  {info['name'][:45]:<45} {d['height']:>6.1f}m - {info['type']}")

    return analysis


def refine_all_buildings(max_complexity='basic_shape'):
    """
    Apply geometry refinements to buildings.

    Args:
        max_complexity: Only refine buildings up to this complexity level
                       ('simple_box', 'basic_shape', 'moderate_detail')
    """

    print("\n" + "=" * 80)
    print("MSG-1998 Building Geometry Refinement")
    print("=" * 80)

    analysis = analyze_all_buildings()
    if not analysis:
        return

    complexity_order = ['simple_box', 'basic_shape', 'moderate_detail']
    max_idx = complexity_order.index(max_complexity) if max_complexity in complexity_order else 1

    refined_count = 0
    skipped_count = 0

    for complexity in complexity_order[:max_idx + 1]:
        for info in analysis[complexity]:
            obj = info['object']
            profile = info['profile']
            dims = info['dimensions']

            print(f"\n  Refining: {obj.name[:50]}")

            try:
                # Add setbacks if specified
                if profile.get('setbacks'):
                    if add_setbacks(obj, profile['setbacks']):
                        print(f"    Added setbacks at: {profile['setbacks']}")

                # Add mechanical penthouse for taller buildings
                if dims['height'] > 40 and profile.get('roof_type') == 'flat_mechanical':
                    if add_mechanical_penthouse(obj):
                        print(f"    Added mechanical penthouse")

                # Add cornice for historic buildings
                if profile.get('roof_type') == 'flat_cornice':
                    if add_cornice(obj):
                        print(f"    Added cornice")

                # Subdivide for window pattern on simple buildings
                if complexity == 'simple_box':
                    if subdivide_for_windows(obj):
                        print(f"    Subdivided for window grid")

                # Add water tank to very tall buildings
                if dims['height'] > 60:
                    if add_roof_water_tank(obj):
                        print(f"    Added rooftop water tank")

                refined_count += 1

            except Exception as e:
                print(f"    ERROR: {e}")
                skipped_count += 1

    print("\n" + "=" * 80)
    print(f"Refinement Complete: {refined_count} refined, {skipped_count} skipped")
    print("=" * 80)


def create_refinement_plan():
    """Create a detailed plan for geometry refinement."""

    print("\n" + "=" * 80)
    print("MSG-1998 Geometry Refinement Plan")
    print("=" * 80)

    analysis = analyze_all_buildings()
    if not analysis:
        return

    plan = {
        'replace_geometry': [],
        'add_setbacks': [],
        'add_rooftop_details': [],
        'add_window_grid': [],
        'special_handling': [],
    }

    for info in analysis['simple_box']:
        dims = info['dimensions']
        if dims['height'] > 80:
            plan['replace_geometry'].append(info)
        elif dims['height'] > 40:
            plan['add_setbacks'].append(info)
        else:
            plan['add_window_grid'].append(info)

    for info in analysis['basic_shape']:
        dims = info['dimensions']
        if dims['height'] > 60:
            plan['add_rooftop_details'].append(info)

    for info in analysis['special_buildings']:
        plan['special_handling'].append(info)

    print("\n" + "-" * 80)
    print("RECOMMENDED ACTIONS:")
    print("-" * 80)

    if plan['replace_geometry']:
        print(f"\n1. GEOMETRY REPLACEMENT ({len(plan['replace_geometry'])} tall buildings)")
        print("   These simple boxes should be replaced with proper geometry:")
        for info in plan['replace_geometry'][:10]:
            print(f"     - {info['name']}: {info['dimensions']['height']:.0f}m")

    if plan['add_setbacks']:
        print(f"\n2. ADD SETBACKS ({len(plan['add_setbacks'])} mid-rise buildings)")
        print("   Run: refine_all_buildings(max_complexity='basic_shape')")

    if plan['add_rooftop_details']:
        print(f"\n3. ADD ROOFTOP DETAILS ({len(plan['add_rooftop_details'])} buildings)")

    if plan['special_handling']:
        print(f"\n4. SPECIAL HANDLING ({len(plan['special_handling'])} landmark buildings)")
        for info in plan['special_handling']:
            print(f"     - {info['name']}")

    print("\n" + "=" * 80)

    return plan


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("MSG-1998 Building Geometry Refinement System")
    print("=" * 80)

    # Step 1: Analyze
    analysis = analyze_all_buildings()

    # Step 2: Create plan
    plan = create_refinement_plan()

    print("\n" + "=" * 80)
    print("To apply refinements, run:")
    print("  refine_all_buildings()  # For basic refinements")
    print("  refine_all_buildings(max_complexity='moderate_detail')  # For more")
    print("=" * 80)


if __name__ == "__main__":
    main()
