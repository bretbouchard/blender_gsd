"""
MSG-1998 Road System - Intersection Detection

Detects where roads intersect by:
1. Finding where road endpoints are near other roads (T-intersections)
2. Finding where roads cross each other (X-intersections)
3. Creating intersection geometry with appropriate radii

Run this in Blender after roads are set up.
"""

import bpy
import bmesh
from mathutils import Vector
from math import sqrt


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


def get_curve_points(curve_obj, sample_distance=5.0):
    """
    Get sampled points along a curve.
    Returns list of (point, tangent, distance_along_curve) tuples.
    """
    points = []

    # Get the curve data
    curve = curve_obj.data

    # Sample points along each spline
    for spline in curve.splines:
        if len(spline.points) < 2:
            continue

        # Get total length approximation
        spline_points = []
        for i, pt in enumerate(spline.points):
            co = curve_obj.matrix_world @ Vector((pt.co.x, pt.co.y, pt.co.z))
            spline_points.append(co)

        # Calculate cumulative distances
        total_length = 0
        distances = [0]
        for i in range(1, len(spline_points)):
            seg_len = (spline_points[i] - spline_points[i-1]).length
            total_length += seg_len
            distances.append(total_length)

        # Sample at regular intervals
        num_samples = max(2, int(total_length / sample_distance) + 1)

        for i in range(num_samples):
            t = i / (num_samples - 1) if num_samples > 1 else 0
            target_dist = t * total_length

            # Find segment
            seg_idx = 0
            for j in range(1, len(distances)):
                if distances[j] >= target_dist:
                    seg_idx = j - 1
                    break
            else:
                seg_idx = len(distances) - 2

            # Interpolate point
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

                points.append((point, tangent, target_dist))

    return points


def point_to_segment_distance(p, a, b):
    """Calculate minimum distance from point p to line segment a-b."""
    ab = b - a
    ap = p - a

    ab_len_sq = ab.length_squared
    if ab_len_sq == 0:
        return (p - a).length, a

    t = max(0, min(1, ap.dot(ab) / ab_len_sq))
    closest = a + t * ab

    return (p - closest).length, closest


def find_intersections(curves, merge_distance=3.0):
    """
    Find all intersection points between roads.

    Returns list of:
    - ('endpoint', point, road_name, connecting_road_name)
    - ('crossing', point, road1_name, road2_name)
    """
    intersections = []

    # Get all sampled points for each curve
    curve_data = {}
    for curve in curves:
        points = get_curve_points(curve, sample_distance=2.0)
        curve_data[curve.name] = {
            'curve': curve,
            'points': points,
            'raw_points': [(p[0], p[1]) for p in points]  # Just position and tangent
        }

    # 1. Find endpoint intersections (T-junctions)
    print("\nFinding endpoint intersections...")
    for curve in curves:
        points = curve_data[curve.name]['points']
        if not points:
            continue

        # Check start and end points
        endpoints = [
            (points[0][0], 'start'),
            (points[-1][0], 'end')
        ]

        for ep, ep_type in endpoints:
            # Check distance to all other curves
            for other_curve in curves:
                if other_curve.name == curve.name:
                    continue

                other_points = curve_data[other_curve.name]['points']
                if not other_points:
                    continue

                # Find closest point on other curve
                min_dist = float('inf')
                closest_point = None

                for i in range(len(other_points) - 1):
                    p1 = other_points[i][0]
                    p2 = other_points[i + 1][0]

                    dist, closest = point_to_segment_distance(ep, p1, p2)
                    if dist < min_dist:
                        min_dist = dist
                        closest_point = closest

                if min_dist < merge_distance:
                    intersections.append({
                        'type': 'endpoint',
                        'point': ep,
                        'road': curve.name,
                        'crossing_road': other_curve.name,
                        'distance': min_dist
                    })

    # 2. Find crossing intersections (X-junctions)
    print("Finding crossing intersections...")
    curve_names = list(curve_data.keys())
    for i, name1 in enumerate(curve_names):
        data1 = curve_data[name1]
        points1 = data1['points']

        for name2 in curve_names[i+1:]:
            data2 = curve_data[name2]
            points2 = data2['points']

            if not points1 or not points2:
                continue

            # Check for segment crossings
            for j in range(len(points1) - 1):
                p1_start = points1[j][0]
                p1_end = points1[j + 1][0]

                for k in range(len(points2) - 1):
                    p2_start = points2[k][0]
                    p2_end = points2[k + 1][0]

                    # 2D crossing check (ignore Z)
                    crossing = line_segments_cross_2d(
                        (p1_start.x, p1_start.y),
                        (p1_end.x, p1_end.y),
                        (p2_start.x, p2_start.y),
                        (p2_end.x, p2_end.y)
                    )

                    if crossing:
                        # Calculate intersection point
                        cross_point = Vector((crossing[0], crossing[1], (p1_start.z + p2_start.z) / 2))
                        intersections.append({
                            'type': 'crossing',
                            'point': cross_point,
                            'road': name1,
                            'crossing_road': name2,
                            'distance': 0
                        })

    return intersections


def line_segments_cross_2d(p1, p2, p3, p4):
    """
    Check if line segments (p1-p2) and (p3-p4) cross in 2D.
    Returns intersection point (x, y) or None.
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

    if abs(denom) < 0.0001:
        return None  # Parallel

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if 0 < t < 1 and 0 < u < 1:
        ix = x1 + t * (x2 - x1)
        iy = y1 + t * (y2 - y1)
        return (ix, iy)

    return None


def merge_nearby_points(points, distance=5.0):
    """Merge points that are within distance of each other."""
    merged = []
    used = set()

    for i, p1 in enumerate(points):
        if i in used:
            continue

        cluster = [p1]
        used.add(i)

        for j, p2 in enumerate(points):
            if j in used:
                continue

            if (p1['point'] - p2['point']).length < distance:
                cluster.append(p2)
                used.add(j)

        # Average position for merged point
        avg_pos = Vector((0, 0, 0))
        for p in cluster:
            avg_pos += p['point']
        avg_pos /= len(cluster)

        merged.append({
            'point': avg_pos,
            'roads': list(set([p['road'] for p in cluster] + [p.get('crossing_road') for p in cluster if p.get('crossing_road')])),
            'type': cluster[0]['type'],
            'count': len(cluster)
        })

    return merged


def create_intersection_objects(intersections, collection_name="Intersections"):
    """Create Blender objects at intersection points."""

    # Create collection
    if collection_name not in bpy.data.collections:
        coll = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(coll)
    else:
        coll = bpy.data.collections[collection_name]

    created = 0

    for ix in intersections:
        # Create a small sphere to mark the intersection
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=2.0,
            location=ix['point']
        )
        obj = bpy.context.active_object
        obj.name = f"IX_{ix['roads'][0]}_{ix['roads'][1] if len(ix['roads']) > 1 else 'end'}"

        # Link to collection
        for c in obj.users_collection:
            c.objects.unlink(obj)
        coll.objects.link(obj)

        # Store metadata
        obj['intersection_type'] = ix['type']
        obj['roads'] = ', '.join(ix['roads'])

        created += 1

    return created


def detect_and_create_intersections():
    """Main function to detect and create intersections."""

    print("\n" + "=" * 50)
    print("Detecting Road Intersections")
    print("=" * 50)

    # Get curves
    curves = get_road_curves()
    print(f"Found {len(curves)} road curves")

    if not curves:
        print("ERROR: No road curves found")
        return

    # Find intersections
    print("\nSearching for intersections...")
    intersections = find_intersections(curves, merge_distance=3.0)
    print(f"Found {len(intersections)} raw intersections")

    # Merge nearby intersections
    print("\nMerging nearby intersections...")
    merged = merge_nearby_points(intersections, distance=8.0)
    print(f"Merged to {len(merged)} unique intersections")

    # Create objects
    print("\nCreating intersection objects...")
    created = create_intersection_objects(merged)
    print(f"Created {created} intersection markers")

    # Summary
    endpoint_count = sum(1 for ix in merged if ix['type'] == 'endpoint')
    crossing_count = sum(1 for ix in merged if ix['type'] == 'crossing')

    print("\n" + "=" * 50)
    print("Intersection Detection Complete!")
    print(f"  T-junctions (endpoints): {endpoint_count}")
    print(f"  X-intersections (crossings): {crossing_count}")
    print(f"  Total: {len(merged)}")
    print(f"  Collection: Intersections")
    print("=" * 50)

    return merged


# Run in Blender
if __name__ == "__main__":
    detect_and_create_intersections()
