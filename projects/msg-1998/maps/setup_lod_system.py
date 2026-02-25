"""
MSG-1998 Road System - LOD (Level of Detail) System

Sets up LOD for roads:
- Hero roads (near MSG): Full detail with all geometry
- City-wide roads: Reduced detail, no furniture

Classifies roads based on distance from MSG center point.
"""

import bpy
from mathutils import Vector
from math import sqrt


# MSG center point (approximate)
MSG_CENTER = Vector((0, 0, 0))  # Update this to actual MSG coordinates

# Hero zone radius (roads within this distance get full detail)
HERO_RADIUS = 200.0  # meters


def get_road_curves():
    """Get all road curves from collections."""
    curves = []
    # Check all possible collections where roads might be
    for coll_name in ["Road_Objects", "Streets_Roads", "Roads_Hero", "Roads_City"]:
        if coll_name in bpy.data.collections:
            coll = bpy.data.collections[coll_name]
            for obj in coll.objects:
                if obj.type == 'CURVE' and obj not in curves:
                    curves.append(obj)

    # Also search all collections in scene
    for coll in bpy.data.collections:
        for obj in coll.objects:
            if obj.type == 'CURVE' and obj not in curves:
                curves.append(obj)

    return curves


def get_curve_center(curve_obj):
    """Get the center point of a curve."""
    curve = curve_obj.data

    all_points = []
    for spline in curve.splines:
        for pt in spline.points:
            co = curve_obj.matrix_world @ Vector((pt.co.x, pt.co.y, pt.co.z))
            all_points.append(co)

    if not all_points:
        return Vector((0, 0, 0))

    center = Vector((0, 0, 0))
    for pt in all_points:
        center += pt

    return center / len(all_points)


def classify_road(curve_obj, hero_center=MSG_CENTER, hero_radius=HERO_RADIUS):
    """
    Classify road as hero or city-wide based on distance from hero center.

    Returns:
        ('hero', distance) or ('city', distance)
    """
    center = get_curve_center(curve_obj)
    distance = (center - hero_center).length

    if distance <= hero_radius:
        return 'hero', distance
    else:
        return 'city', distance


def set_road_lod_settings(curve_obj, lod_level, road_width):
    """Configure road geometry nodes for specific LOD level."""

    # Get or create modifiers
    road_mod = None
    markings_mod = None

    for mod in curve_obj.modifiers:
        if mod.type == 'NODES':
            if mod.node_group and mod.node_group.name == "MSG_Road_Builder":
                road_mod = mod
            elif mod.node_group and mod.node_group.name == "MSG_Lane_Markings":
                markings_mod = mod

    if road_mod is None:
        road_mod = curve_obj.modifiers.new(name="Road", type='NODES')
        road_mod.node_group = bpy.data.node_groups.get("MSG_Road_Builder")

    if road_mod and road_mod.node_group:
        for item in road_mod.node_group.interface.items_tree:
            if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
                if lod_level == 'hero':
                    # Full detail
                    if item.name == "Road Width":
                        road_mod[item.identifier] = road_width
                    elif item.name == "Sidewalk Width":
                        road_mod[item.identifier] = 2.0
                    elif item.name == "Curb Height":
                        road_mod[item.identifier] = 0.15
                else:
                    # City-wide (reduced detail)
                    if item.name == "Road Width":
                        road_mod[item.identifier] = road_width
                    elif item.name == "Sidewalk Width":
                        road_mod[item.identifier] = 1.0  # Thinner sidewalks
                    elif item.name == "Curb Height":
                        road_mod[item.identifier] = 0.10  # Lower curbs

    # Disable lane markings for city-wide (performance)
    if markings_mod:
        markings_mod.show_viewport = (lod_level == 'hero')
        markings_mod.show_render = (lod_level == 'hero')

    return lod_level


def get_road_width(obj):
    """Get road width from name."""
    name_lower = obj.name.lower()
    if "avenue" in name_lower:
        return 20.0
    elif "broadway" in name_lower:
        return 22.0
    elif "plaza" in name_lower:
        return 25.0
    elif "street" in name_lower:
        return 12.0
    elif "lane" in name_lower:
        return 8.0
    return 10.0


def organize_by_lod():
    """Organize roads into Hero and City collections based on LOD."""

    print("\n" + "=" * 50)
    print("Setting up LOD System")
    print("=" * 50)

    # Create LOD collections
    if "Roads_Hero" not in bpy.data.collections:
        hero_coll = bpy.data.collections.new("Roads_Hero")
        bpy.context.scene.collection.children.link(hero_coll)
    else:
        hero_coll = bpy.data.collections["Roads_Hero"]

    if "Roads_City" not in bpy.data.collections:
        city_coll = bpy.data.collections.new("Roads_City")
        bpy.context.scene.collection.children.link(city_coll)
    else:
        city_coll = bpy.data.collections["Roads_City"]

    # Get all curves
    curves = get_road_curves()
    print(f"Found {len(curves)} road curves")

    hero_count = 0
    city_count = 0

    for curve in curves:
        # Classify road
        lod_level, distance = classify_road(curve)

        # Get road width
        road_width = get_road_width(curve)

        # Set LOD settings
        set_road_lod_settings(curve, lod_level, road_width)

        # Move to appropriate collection
        target_coll = hero_coll if lod_level == 'hero' else city_coll

        # Unlink from current collections
        for coll in list(curve.users_collection):
            if coll not in [hero_coll, city_coll]:
                coll.objects.unlink(curve)

        # Link to target collection
        if target_coll not in curve.users_collection:
            target_coll.objects.link(curve)

        if lod_level == 'hero':
            hero_count += 1
            print(f"  HERO: {curve.name} (dist={distance:.1f}m)")
        else:
            city_count += 1

    print(f"\nHero roads: {hero_count}")
    print(f"City roads: {city_count}")

    print("\n" + "=" * 50)
    print("LOD System Complete!")
    print(f"  Hero collection: Roads_Hero")
    print(f"  City collection: Roads_City")
    print("=" * 50)

    return hero_count, city_count


def mark_hero_roads_manual(road_names):
    """
    Manually mark specific roads as hero roads.
    Use this to override automatic classification.

    Args:
        road_names: List of road names to mark as hero
    """
    curves = get_road_curves()

    hero_coll = bpy.data.collections.get("Roads_Hero")
    if not hero_coll:
        hero_coll = bpy.data.collections.new("Roads_Hero")
        bpy.context.scene.collection.children.link(hero_coll)

    for curve in curves:
        for name in road_names:
            if name.lower() in curve.name.lower():
                road_width = get_road_width(curve)
                set_road_lod_settings(curve, 'hero', road_width)

                # Move to hero collection
                for coll in list(curve.users_collection):
                    coll.objects.unlink(curve)
                hero_coll.objects.link(curve)

                print(f"Marked as hero: {curve.name}")


# Default hero roads near MSG (these are the key roads around the arena)
DEFAULT_HERO_ROADS = [
    "31st Street",
    "32nd Street",
    "33rd Street",
    "34th Street",
    "7th Avenue",
    "8th Avenue",
    "Pennsylvania Plaza",
    "Dyer Avenue",
]


def setup_lod_with_defaults():
    """Setup LOD with default hero roads near MSG."""

    print("\n" + "=" * 50)
    print("Setting up LOD System (with defaults)")
    print("=" * 50)

    # Create collections first
    if "Roads_Hero" not in bpy.data.collections:
        hero_coll = bpy.data.collections.new("Roads_Hero")
        bpy.context.scene.collection.children.link(hero_coll)
    else:
        hero_coll = bpy.data.collections["Roads_Hero"]

    if "Roads_City" not in bpy.data.collections:
        city_coll = bpy.data.collections.new("Roads_City")
        bpy.context.scene.collection.children.link(city_coll)
    else:
        city_coll = bpy.data.collections["Roads_City"]

    # Get all curves
    curves = get_road_curves()
    print(f"Found {len(curves)} road curves")

    hero_count = 0
    city_count = 0

    for curve in curves:
        # Check if road name matches hero list
        is_hero = False
        curve_name_lower = curve.name.lower()

        for hero_name in DEFAULT_HERO_ROADS:
            if hero_name.lower() in curve_name_lower:
                is_hero = True
                break

        # Get road width
        road_width = get_road_width(curve)

        # Set LOD level
        lod_level = 'hero' if is_hero else 'city'
        set_road_lod_settings(curve, lod_level, road_width)

        # Move to appropriate collection
        target_coll = hero_coll if is_hero else city_coll

        # Unlink from current collections
        for coll in list(curve.users_collection):
            if coll not in [hero_coll, city_coll]:
                coll.objects.unlink(curve)

        # Link to target collection
        if target_coll not in curve.users_collection:
            target_coll.objects.link(curve)

        if is_hero:
            hero_count += 1
            print(f"  HERO: {curve.name}")
        else:
            city_count += 1

    print(f"\nHero roads: {hero_count}")
    print(f"City roads: {city_count}")

    print("\n" + "=" * 50)
    print("LOD System Complete!")
    print(f"  Hero collection: Roads_Hero")
    print(f"  City collection: Roads_City")
    print("=" * 50)

    return hero_count, city_count


# Run in Blender
if __name__ == "__main__":
    setup_lod_with_defaults()
