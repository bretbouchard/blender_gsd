"""
MSG-1998 Road System - Create Mesh Roads

Instead of geometry nodes, create actual mesh objects from curves.
This is more reliable and gives us full control.

Creates:
- Road surface mesh (asphalt)
- Curb meshes (both sides)
- Sidewalk meshes (both sides)
"""

import bpy
import bmesh
from mathutils import Vector, Matrix
from math import pi, cos, sin


def get_or_create_material(name, color, roughness=0.8):
    """Get or create material."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness

    output = nodes.new('ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def get_road_curves():
    """Get all road curves."""
    curves = []
    for coll in bpy.data.collections:
        for obj in coll.objects:
            if obj.type == 'CURVE' and obj not in curves:
                curves.append(obj)
    return curves


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


def curve_to_road_mesh(curve_obj, road_width, sidewalk_width, curb_height):
    """
    Convert a curve to a road mesh with sidewalks and curbs.

    Returns dict with mesh objects.
    """
    curve = curve_obj.data
    matrix = curve_obj.matrix_world

    # Collect all spline points
    all_points = []
    for spline in curve.splines:
        points = []
        for pt in spline.points:
            co = matrix @ Vector((pt.co.x, pt.co.y, pt.co.z))
            points.append(co)
        if len(points) >= 2:
            all_points.append(points)

    if not all_points:
        return None

    results = {}

    # Materials
    asphalt = get_or_create_material("M_Road_Asphalt", (0.08, 0.08, 0.09, 1.0), 0.85)
    concrete = get_or_create_material("M_Road_Concrete", (0.5, 0.48, 0.45, 1.0), 0.9)
    curb_mat = get_or_create_material("M_Road_Curb", (0.4, 0.38, 0.36, 1.0), 0.8)

    half_road = road_width / 2
    total_half = half_road + 0.3 + sidewalk_width  # road + curb + sidewalk

    # Create road surface
    road_mesh = bpy.data.meshes.new(f"{curve_obj.name}_road")
    road_obj = bpy.data.objects.new(f"{curve_obj.name}_Road", road_mesh)
    road_obj.data.materials.append(asphalt)

    bm = bmesh.new()

    for points in all_points:
        # Create road surface as quad strip
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            direction = (p2 - p1).normalized()
            normal = Vector((-direction.y, direction.x, 0))

            # Four corners of road segment
            v1 = bm.verts.new(p1 + normal * half_road + Vector((0, 0, 0.01)))
            v2 = bm.verts.new(p1 - normal * half_road + Vector((0, 0, 0.01)))
            v3 = bm.verts.new(p2 - normal * half_road + Vector((0, 0, 0.01)))
            v4 = bm.verts.new(p2 + normal * half_road + Vector((0, 0, 0.01)))

            bm.faces.new([v1, v2, v3, v4])

    bm.to_mesh(road_mesh)
    bm.free()
    results['road'] = road_obj

    # Create curbs
    curb_mesh = bpy.data.meshes.new(f"{curve_obj.name}_curb")
    curb_obj = bpy.data.objects.new(f"{curve_obj.name}_Curb", curb_mesh)
    curb_obj.data.materials.append(curb_mat)

    bm = bmesh.new()

    for points in all_points:
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            direction = (p2 - p1).normalized()
            normal = Vector((-direction.y, direction.x, 0))

            # Left curb (4 verts: bottom-inner, top-inner, top-outer, bottom-outer)
            bi_l = bm.verts.new(p1 + normal * half_road + Vector((0, 0, 0.01)))
            ti_l = bm.verts.new(p1 + normal * half_road + Vector((0, 0, 0.01 + curb_height)))
            to_l = bm.verts.new(p1 + normal * (half_road + 0.3) + Vector((0, 0, 0.01 + curb_height)))
            bo_l = bm.verts.new(p1 + normal * (half_road + 0.3) + Vector((0, 0, 0.01)))

            bi_l2 = bm.verts.new(p2 + normal * half_road + Vector((0, 0, 0.01)))
            ti_l2 = bm.verts.new(p2 + normal * half_road + Vector((0, 0, 0.01 + curb_height)))
            to_l2 = bm.verts.new(p2 + normal * (half_road + 0.3) + Vector((0, 0, 0.01 + curb_height)))
            bo_l2 = bm.verts.new(p2 + normal * (half_road + 0.3) + Vector((0, 0, 0.01)))

            # Front face
            bm.faces.new([bi_l, ti_l, to_l, bo_l])
            bm.faces.new([bi_l2, ti_l2, to_l2, bo_l2])
            # Top face
            bm.faces.new([ti_l, ti_l2, to_l2, to_l])
            # Side faces
            bm.faces.new([bi_l, bi_l2, ti_l2, ti_l])
            bm.faces.new([bo_l, bo_l2, to_l2, to_l])

            # Right curb
            bi_r = bm.verts.new(p1 - normal * half_road + Vector((0, 0, 0.01)))
            ti_r = bm.verts.new(p1 - normal * half_road + Vector((0, 0, 0.01 + curb_height)))
            to_r = bm.verts.new(p1 - normal * (half_road + 0.3) + Vector((0, 0, 0.01 + curb_height)))
            bo_r = bm.verts.new(p1 - normal * (half_road + 0.3) + Vector((0, 0, 0.01)))

            bi_r2 = bm.verts.new(p2 - normal * half_road + Vector((0, 0, 0.01)))
            ti_r2 = bm.verts.new(p2 - normal * half_road + Vector((0, 0, 0.01 + curb_height)))
            to_r2 = bm.verts.new(p2 - normal * (half_road + 0.3) + Vector((0, 0, 0.01 + curb_height)))
            bo_r2 = bm.verts.new(p2 - normal * (half_road + 0.3) + Vector((0, 0, 0.01)))

            bm.faces.new([bi_r, ti_r, to_r, bo_r])
            bm.faces.new([bi_r2, ti_r2, to_r2, bo_r2])
            bm.faces.new([ti_r, ti_r2, to_r2, to_r])
            bm.faces.new([bi_r, bi_r2, ti_r2, ti_r])
            bm.faces.new([bo_r, bo_r2, to_r2, to_r])

    bm.to_mesh(curb_mesh)
    bm.free()
    results['curb'] = curb_obj

    # Create sidewalks
    sw_mesh = bpy.data.meshes.new(f"{curve_obj.name}_sw")
    sw_obj = bpy.data.objects.new(f"{curve_obj.name}_Sidewalk", sw_mesh)
    sw_obj.data.materials.append(concrete)

    bm = bmesh.new()

    for points in all_points:
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            direction = (p2 - p1).normalized()
            normal = Vector((-direction.y, direction.x, 0))

            inner = half_road + 0.3
            outer = inner + sidewalk_width
            z = 0.01 + curb_height

            # Left sidewalk
            v1 = bm.verts.new(p1 + normal * inner + Vector((0, 0, z)))
            v2 = bm.verts.new(p1 + normal * outer + Vector((0, 0, z + 0.1)))
            v3 = bm.verts.new(p2 + normal * outer + Vector((0, 0, z + 0.1)))
            v4 = bm.verts.new(p2 + normal * inner + Vector((0, 0, z)))
            bm.faces.new([v1, v2, v3, v4])

            # Right sidewalk
            v5 = bm.verts.new(p1 - normal * inner + Vector((0, 0, z)))
            v6 = bm.verts.new(p1 - normal * outer + Vector((0, 0, z + 0.1)))
            v7 = bm.verts.new(p2 - normal * outer + Vector((0, 0, z + 0.1)))
            v8 = bm.verts.new(p2 - normal * inner + Vector((0, 0, z)))
            bm.faces.new([v5, v6, v7, v8])

    bm.to_mesh(sw_mesh)
    bm.free()
    results['sidewalk'] = sw_obj

    return results


def create_mesh_roads():
    """Convert all road curves to mesh roads."""

    print("\n" + "=" * 50)
    print("Creating Mesh Roads")
    print("=" * 50)

    # Create collection
    if "Road_Meshes" not in bpy.data.collections:
        mesh_coll = bpy.data.collections.new("Road_Meshes")
        bpy.context.scene.collection.children.link(mesh_coll)
    else:
        mesh_coll = bpy.data.collections["Road_Meshes"]

    curves = get_road_curves()
    print(f"Found {len(curves)} road curves")

    road_count = 0
    curb_count = 0
    sw_count = 0

    for curve in curves:
        road_width = get_road_width(curve)
        sidewalk_width = 2.0
        curb_height = 0.15

        print(f"  Processing: {curve.name} (width={road_width}m)")

        results = curve_to_road_mesh(curve, road_width, sidewalk_width, curb_height)

        if results:
            for key, obj in results.items():
                mesh_coll.objects.link(obj)
                if key == 'road':
                    road_count += 1
                elif key == 'curb':
                    curb_count += 1
                elif key == 'sidewalk':
                    sw_count += 1

    print(f"\nCreated:")
    print(f"  Roads: {road_count}")
    print(f"  Curbs: {curb_count}")
    print(f"  Sidewalks: {sw_count}")

    print("\n" + "=" * 50)
    print("Mesh Roads Complete!")
    print("Collection: Road_Meshes")
    print("=" * 50)

    return mesh_coll


# Run in Blender
if __name__ == "__main__":
    create_mesh_roads()
