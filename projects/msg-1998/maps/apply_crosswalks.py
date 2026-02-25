"""
MSG-1998 Road System - Crosswalks

Creates crosswalk markings at intersections:
- Zebra stripe pattern (white stripes)
- Proper width based on road width
- Aligned with road direction

Run this after intersections are detected.
"""

import bpy
from mathutils import Vector, Matrix
from math import pi, cos, sin, floor


def get_intersections():
    """Get all intersection objects."""
    intersections = []
    if "Intersections" in bpy.data.collections:
        coll = bpy.data.collections["Intersections"]
        for obj in coll.objects:
            if obj.name.startswith("IX_"):
                intersections.append(obj)
    return intersections


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


def find_road_direction_at_point(curves, point, search_radius=20.0):
    """Find the direction of the nearest road at a point."""
    best_dir = None
    best_dist = float('inf')

    for curve in curves:
        curve_data = curve.data

        for spline in curve_data.splines:
            if len(spline.points) < 2:
                continue

            points = []
            for pt in spline.points:
                co = curve.matrix_world @ Vector((pt.co.x, pt.co.y, pt.co.z))
                points.append(co)

            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i + 1]

                # Check distance to segment
                seg_dir = (p2 - p1).normalized()
                seg_len = (p2 - p1).length

                to_point = point - p1
                proj_len = to_point.dot(seg_dir)

                if 0 <= proj_len <= seg_len:
                    closest = p1 + seg_dir * proj_len
                    dist = (point - closest).length

                    if dist < best_dist:
                        best_dist = dist
                        best_dir = seg_dir

    return best_dir, best_dist


def create_crosswalk_mesh(location, direction, width=6.0, length=4.0, stripe_width=0.4, gap_width=0.6):
    """Create a crosswalk mesh with zebra stripes."""

    # Calculate rotation from direction
    angle = atan2(direction.y, direction.x)
    rot_matrix = Matrix.Rotation(angle, 4, 'Z')

    # Create mesh
    mesh = bpy.data.meshes.new("CrosswalkMesh")

    # Generate stripe vertices
    vertices = []
    faces = []

    stripe_total = stripe_width + gap_width
    num_stripes = int(length / stripe_total)

    half_width = width / 2
    half_length = length / 2

    for i in range(num_stripes):
        # Stripe position along length
        stripe_start = -half_length + i * stripe_total
        stripe_end = stripe_start + stripe_width

        # Create quad for stripe
        v_base = len(vertices)

        # Four corners of stripe
        corners = [
            (stripe_start, -half_width, 0.02),
            (stripe_end, -half_width, 0.02),
            (stripe_end, half_width, 0.02),
            (stripe_start, half_width, 0.02)
        ]

        for corner in corners:
            # Transform by rotation and translate
            local_pos = Vector(corner)
            world_pos = rot_matrix @ local_pos + location
            vertices.append(world_pos)

        faces.append([v_base, v_base + 1, v_base + 2, v_base + 3])

    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    return mesh


def create_crosswalk(location, direction, road_width=12.0, collection=None):
    """Create a crosswalk object at the given location."""

    # Crosswalk width is slightly less than road width
    crosswalk_width = road_width * 0.8

    # Create mesh
    mesh = create_crosswalk_mesh(
        location,
        direction,
        width=crosswalk_width,
        length=4.0,
        stripe_width=0.4,
        gap_width=0.6
    )

    # Create object
    obj = bpy.data.objects.new("Crosswalk", mesh)
    obj.location = location

    # Link to collection
    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def get_road_width_at_intersection(intersection_name, curves):
    """Estimate road width at intersection from road names."""
    # Parse intersection name to get road names
    parts = intersection_name.replace("IX_", "").split("_")

    for curve in curves:
        curve_name = curve.name.lower()

        # Check for avenue (20m)
        if "avenue" in curve_name:
            for part in parts:
                if part.lower() in curve_name:
                    return 20.0

        # Check for broadway (22m)
        if "broadway" in curve_name:
            return 22.0

        # Check for plaza (25m)
        if "plaza" in curve_name:
            return 25.0

    # Default street width
    return 12.0


def create_all_crosswalks():
    """Main function to create crosswalks at all intersections."""

    print("\n" + "=" * 50)
    print("Creating Crosswalks")
    print("=" * 50)

    # Create collection
    if "Crosswalks" not in bpy.data.collections:
        crosswalk_coll = bpy.data.collections.new("Crosswalks")
        bpy.context.scene.collection.children.link(crosswalk_coll)
    else:
        crosswalk_coll = bpy.data.collections["Crosswalks"]

    # Get data
    intersections = get_intersections()
    curves = get_road_curves()

    print(f"Found {len(intersections)} intersections")

    created = 0
    skipped = 0

    for ix in intersections:
        pos = ix.location
        ix_name = ix.name

        # Find road direction at this intersection
        direction, dist = find_road_direction_at_point(curves, pos)

        if direction is None:
            skipped += 1
            continue

        # Get road width
        road_width = get_road_width_at_intersection(ix_name, curves)

        # Create crosswalks on both sides of intersection
        # (offset along normal to direction)
        normal = Vector((-direction.y, direction.x, 0))

        offset_distance = road_width / 2 + 2.0  # 2m from road edge

        for side in [-1, 1]:
            crosswalk_pos = pos + normal * side * offset_distance
            crosswalk_pos.z = 0.02  # Slightly above ground

            crosswalk = create_crosswalk(
                crosswalk_pos,
                direction,
                road_width=road_width,
                collection=crosswalk_coll
            )
            crosswalk.name = f"Crosswalk_{ix_name}_{side:+d}"
            created += 1

    print(f"\nCreated {created} crosswalks")
    if skipped > 0:
        print(f"Skipped {skipped} intersections (no road direction found)")

    print("\n" + "=" * 50)
    print("Crosswalks Complete!")
    print(f"  Collection: Crosswalks")
    print("=" * 50)

    return crosswalk_coll


# Run in Blender
if __name__ == "__main__":
    create_all_crosswalks()
