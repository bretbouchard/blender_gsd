"""
MSG-1998 Road System - Street Furniture

Places street furniture along roads:
- Manhole covers (every 20-40m)
- Fire hydrants (every 60-100m on one side)
- Street signs at intersections
- Traffic signals at major intersections

Run this after roads and intersections are set up.
"""

import bpy
import random
from mathutils import Vector, Euler
from math import pi, floor


def get_road_curves():
    """Get all road curves from collections."""
    curves = []
    for coll_name in ["Road_Objects", "Streets_Roads"]:
        if coll_name in bpy.data.collections:
            coll = bpy.data.collections[coll_name]
            for obj in coll.objects:
                if obj.type == 'CURVE':
                    curves.append(obj)
    return curves


def get_intersections():
    """Get all intersection objects."""
    intersections = []
    if "Intersections" in bpy.data.collections:
        coll = bpy.data.collections["Intersections"]
        for obj in coll.objects:
            if obj.name.startswith("IX_"):
                intersections.append(obj)
    return intersections


def get_curve_points_along_length(curve_obj, spacing=5.0):
    """Get points along curve at regular intervals."""
    points = []
    curve = curve_obj.data

    for spline in curve.splines:
        if len(spline.points) < 2:
            continue

        # Get spline points
        spline_points = []
        for pt in spline.points:
            co = curve_obj.matrix_world @ Vector((pt.co.x, pt.co.y, pt.co.z))
            spline_points.append(co)

        # Calculate cumulative distances
        total_length = 0
        distances = [0]
        for i in range(1, len(spline_points)):
            seg_len = (spline_points[i] - spline_points[i-1]).length
            total_length += seg_len
            distances.append(total_length)

        # Sample at spacing intervals
        num_samples = max(1, int(total_length / spacing))

        for i in range(num_samples + 1):
            target_dist = i * spacing
            if target_dist > total_length:
                target_dist = total_length

            # Find segment
            seg_idx = 0
            for j in range(1, len(distances)):
                if distances[j] >= target_dist:
                    seg_idx = j - 1
                    break
            else:
                seg_idx = len(distances) - 2

            # Interpolate
            if seg_idx >= 0 and seg_idx < len(spline_points) - 1:
                seg_start = distances[seg_idx]
                seg_end = distances[seg_idx + 1]
                seg_len = seg_end - seg_start

                if seg_len > 0:
                    local_t = (target_dist - seg_start) / seg_len
                else:
                    local_t = 0

                p1 = spline_points[seg_idx]
                p2 = spline_points[seg_idx + 1]
                point = p1.lerp(p2, local_t)

                # Calculate tangent
                tangent = (p2 - p1).normalized() if seg_len > 0 else Vector((1, 0, 0))
                # Calculate normal (perpendicular in XY plane)
                normal = Vector((-tangent.y, tangent.x, 0)).normalized()

                points.append({
                    'position': point,
                    'tangent': tangent,
                    'normal': normal,
                    'distance': target_dist
                })

    return points


def create_manhole(location, collection):
    """Create a manhole cover at the given location."""
    # Create cylinder
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.35,  # 70cm diameter
        depth=0.05,
        location=location
    )
    obj = bpy.context.active_object
    obj.name = f"Manhole_{len(collection.objects):03d}"

    # Move to collection
    for c in obj.users_collection:
        c.objects.unlink(obj)
    collection.objects.link(obj)

    return obj


def create_fire_hydrant(location, normal, collection):
    """Create a fire hydrant at the given location."""
    # Create main body
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.12,  # 24cm diameter
        depth=0.75,   # 75cm tall
        location=location + normal * 0.5 + Vector((0, 0, 0.375))
    )
    body = bpy.context.active_object
    body.name = f"Hydrant_{len(collection.objects):03d}"

    # Rotate to align with normal
    angle = normal.angle(Vector((1, 0, 0)))
    body.rotation_euler = Euler((0, 0, angle), 'XYZ')

    # Move to collection
    for c in body.users_collection:
        c.objects.unlink(body)
    collection.objects.link(body)

    return body


def create_street_sign(location, normal, road_names, collection):
    """Create a street sign at intersection."""
    # Create pole
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.05,
        depth=3.5,
        location=location + normal * 0.5 + Vector((0, 0, 1.75))
    )
    pole = bpy.context.active_object
    pole.name = f"StreetSign_{len(collection.objects):03d}"

    # Move to collection
    for c in pole.users_collection:
        c.objects.unlink(pole)
    collection.objects.link(pole)

    return pole


def create_traffic_signal(location, normal, collection):
    """Create a traffic signal at intersection."""
    # Create pole
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.08,
        depth=4.0,
        location=location + normal * 1.0 + Vector((0, 0, 2.0))
    )
    pole = bpy.context.active_object
    pole.name = f"TrafficSignal_{len(collection.objects):03d}"

    # Move to collection
    for c in pole.users_collection:
        c.objects.unlink(pole)
    collection.objects.link(pole)

    return pole


def place_manholes(curves, collection, spacing=30.0):
    """Place manholes along all roads."""
    count = 0
    random.seed(42)  # Reproducible randomness

    for curve in curves:
        points = get_curve_points_along_length(curve, spacing=spacing)

        for pt in points:
            # Add some randomness to position
            offset = random.uniform(-2, 2)
            lateral = random.choice([-1, 1]) * random.uniform(1, 3)

            pos = pt['position'] + pt['normal'] * lateral + Vector((offset, offset, 0))
            pos.z = 0.01  # Just above ground

            create_manhole(pos, collection)
            count += 1

    return count


def place_fire_hydrants(curves, collection, spacing=80.0):
    """Place fire hydrants along roads."""
    count = 0
    random.seed(43)

    for curve in curves:
        points = get_curve_points_along_length(curve, spacing=spacing)

        # Only on one side (positive normal)
        side = random.choice([-1, 1])

        for i, pt in enumerate(points):
            if i % 2 == 0:  # Every other point
                lateral = side * random.uniform(2, 4)
                pos = pt['position'] + pt['normal'] * lateral
                pos.z = 0.0

                create_fire_hydrant(pos, pt['normal'] * side, collection)
                count += 1

    return count


def place_intersection_furniture(intersections, collection):
    """Place street signs and traffic signals at intersections."""
    signs = 0
    signals = 0

    for ix in intersections:
        pos = ix.location
        roads = ix.get('roads', '').split(', ')

        # Determine if major intersection (avenue x avenue)
        is_major = any('avenue' in r.lower() or 'broadway' in r.lower() for r in roads)

        # Street signs at all intersections
        normal = Vector((1, 0, 0))
        create_street_sign(pos, normal, roads, collection)
        signs += 1

        # Traffic signals at major intersections
        if is_major:
            for angle in [0, pi/2]:
                normal = Vector((cos(angle), sin(angle), 0))
                create_traffic_signal(pos, normal, collection)
                signals += 1

    return signs, signals


def create_street_furniture():
    """Main function to create all street furniture."""

    print("\n" + "=" * 50)
    print("Creating Street Furniture")
    print("=" * 50)

    # Create collection
    if "Street_Furniture" not in bpy.data.collections:
        furniture_coll = bpy.data.collections.new("Street_Furniture")
        bpy.context.scene.collection.children.link(furniture_coll)
    else:
        furniture_coll = bpy.data.collections["Street_Furniture"]

    # Get roads and intersections
    curves = get_road_curves()
    intersections = get_intersections()

    print(f"Found {len(curves)} roads, {len(intersections)} intersections")

    # Place manholes
    print("\nPlacing manholes...")
    manholes = place_manholes(curves, furniture_coll, spacing=30.0)
    print(f"  Created {manholes} manhole covers")

    # Place fire hydrants
    print("\nPlacing fire hydrants...")
    hydrants = place_fire_hydrants(curves, furniture_coll, spacing=80.0)
    print(f"  Created {hydrants} fire hydrants")

    # Place intersection furniture
    print("\nPlacing intersection furniture...")
    signs, signals = place_intersection_furniture(intersections, furniture_coll)
    print(f"  Created {signs} street signs")
    print(f"  Created {signals} traffic signals")

    print("\n" + "=" * 50)
    print("Street Furniture Complete!")
    print(f"  Total objects: {manholes + hydrants + signs + signals}")
    print(f"  Collection: Street_Furniture")
    print("=" * 50)

    return furniture_coll


# Run in Blender
if __name__ == "__main__":
    create_street_furniture()
