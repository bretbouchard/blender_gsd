"""
Proxy geometry generation for projection surfaces.

Creates UV-mapped proxy geometry optimized for projector projection.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .types import ProxyGeometryConfig, ProxyGeometryResult


def create_planar_proxy_vertices(
    points: List[Tuple[float, float, float]]
) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]:
    """
    Create vertices and faces for planar proxy from 3 calibration points.

    Computes the 4th corner of a rectangle from 3 points:
    - p1: bottom-left (point 0)
    - p2: bottom-right (point 1)
    - p3: top-left (point 2)
    - p4: top-right (computed as p1 + (p2-p1) + (p3-p1))

    Args:
        points: 3 calibration points in world space

    Returns:
        Tuple of (vertices, faces)
    """
    if len(points) != 3:
        raise ValueError("Planar proxy requires exactly 3 calibration points")

    p1 = points[0]
    p2 = points[1]
    p3 = points[2]

    # Compute vectors
    v1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])  # Bottom edge
    v2 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])  # Left edge

    # 4th corner = p1 + v1 + v2
    p4 = (
        p1[0] + v1[0] + v2[0],
        p1[1] + v1[1] + v2[1],
        p1[2] + v1[2] + v2[2]
    )

    # Vertices in quad order (counter-clockwise from front)
    vertices = [p1, p2, p4, p3]

    # Single quad face
    faces = [(0, 1, 2, 3)]

    return vertices, faces


def compute_uv_for_calibration_points(
    projector_uvs: List[Tuple[float, float]]
) -> List[Tuple[float, float]]:
    """
    Compute UV coordinates for proxy geometry vertices.

    Maps projector UV space to mesh UV coordinates:
    - Vertex 0 (BL): projector UV point 0
    - Vertex 1 (BR): projector UV point 1
    - Vertex 2 (TR): computed from points 1 and 2
    - Vertex 3 (TL): projector UV point 2

    Args:
        projector_uvs: 3 projector UV coordinates (0-1 range)

    Returns:
        List of 4 UV coordinates for mesh vertices
    """
    if len(projector_uvs) != 3:
        raise ValueError("Requires exactly 3 projector UV coordinates")

    uv0 = projector_uvs[0]  # Bottom-left
    uv1 = projector_uvs[1]  # Bottom-right
    uv2 = projector_uvs[2]  # Top-left

    # Compute top-right UV
    uv3 = (uv1[0], uv2[1])

    return [uv0, uv1, uv3, uv2]


def subdivide_quad(
    vertices: List[Tuple[float, float, float]],
    faces: List[Tuple[int, ...]],
    subdivisions: int
) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]:
    """
    Subdivide a quad face for better projection quality.

    Args:
        vertices: Original vertices
        faces: Original faces
        subdivisions: Number of subdivision levels (each level multiplies quads by 4)

    Returns:
        Tuple of (new_vertices, new_faces)
    """
    if subdivisions <= 0:
        return vertices, faces

    # Simple Catmull-Clark style subdivision for quads
    # For each subdivision level, split each quad into 4 quads
    current_verts = list(vertices)
    current_faces = list(faces)

    for level in range(subdivisions):
        new_verts = list(current_verts)
        new_faces = []

        # Edge midpoint cache
        edge_midpoints = {}

        for face in current_faces:
            if len(face) != 4:
                # Pass through non-quad faces
                new_faces.append(face)
                continue

            v0, v1, v2, v3 = face

            # Get or create edge midpoints
            def get_edge_midpoint(i, j):
                key = (min(i, j), max(i, j))
                if key not in edge_midpoints:
                    p0 = current_verts[i]
                    p1 = current_verts[j]
                    mid = (
                        (p0[0] + p1[0]) / 2,
                        (p0[1] + p1[1]) / 2,
                        (p0[2] + p1[2]) / 2
                    )
                    new_verts.append(mid)
                    edge_midpoints[key] = len(new_verts) - 1
                return edge_midpoints[key]

            # Get edge midpoints
            m01 = get_edge_midpoint(v0, v1)
            m12 = get_edge_midpoint(v1, v2)
            m23 = get_edge_midpoint(v2, v3)
            m30 = get_edge_midpoint(v3, v0)

            # Face center
            p0 = current_verts[v0]
            p1 = current_verts[v1]
            p2 = current_verts[v2]
            p3 = current_verts[v3]
            center = (
                (p0[0] + p1[0] + p2[0] + p3[0]) / 4,
                (p0[1] + p1[1] + p2[1] + p3[1]) / 4,
                (p0[2] + p1[2] + p2[2] + p3[2]) / 4
            )
            center_idx = len(new_verts)
            new_verts.append(center)

            # Create 4 sub-quads
            new_faces.append((v0, m01, center_idx, m30))
            new_faces.append((m01, v1, m12, center_idx))
            new_faces.append((center_idx, m12, v2, m23))
            new_faces.append((m30, center_idx, m23, v3))

        current_verts = new_verts
        current_faces = new_faces

    return current_verts, current_faces


def subdivide_uv(
    uvs: List[Tuple[float, float]],
    subdivisions: int
) -> List[Tuple[float, float]]:
    """
    Subdivide UV coordinates to match subdivided geometry.

    Args:
        uvs: Original 4 UV coordinates
        subdivisions: Number of subdivision levels

    Returns:
        Subdivided UV coordinates
    """
    if subdivisions <= 0:
        return uvs

    # For quad subdivision, interpolate UVs
    # Start with corner UVs
    uv0, uv1, uv2, uv3 = uvs

    current_uvs = [uv0, uv1, uv2, uv3]

    for level in range(subdivisions):
        # Calculate grid size at this level
        grid_size = 2 ** (level + 1)
        new_uvs = []

        # Generate interpolated UVs for the new grid
        for j in range(grid_size + 1):
            for i in range(grid_size + 1):
                u = i / grid_size
                v = j / grid_size

                # Bilinear interpolation
                # Bottom edge: uv0 to uv1
                bottom_u = uv0[0] + u * (uv1[0] - uv0[0])
                bottom_v = uv0[1] + u * (uv1[1] - uv0[1])

                # Top edge: uv3 to uv2
                top_u = uv3[0] + u * (uv2[0] - uv3[0])
                top_v = uv3[1] + u * (uv2[1] - uv3[1])

                # Interpolate vertically
                final_u = bottom_u + v * (top_u - bottom_u)
                final_v = bottom_v + v * (top_v - bottom_v)

                new_uvs.append((final_u, final_v))

        current_uvs = new_uvs

    return current_uvs


def create_proxy_geometry_for_surface(
    calibration_points: List[Tuple[float, float, float]],
    projector_uvs: List[Tuple[float, float]],
    config: ProxyGeometryConfig = ProxyGeometryConfig()
) -> ProxyGeometryResult:
    """
    Create UV-mapped proxy geometry for projection surface.

    The proxy geometry is a simplified mesh that matches the projection
    surface, optimized for UV projection from the projector.

    Args:
        calibration_points: World positions of calibration points
        projector_uvs: Corresponding projector UV coordinates
        config: Proxy geometry configuration

    Returns:
        ProxyGeometryResult with mesh data
    """
    errors = []

    try:
        # Validate inputs
        if len(calibration_points) != 3:
            errors.append("Planar proxy requires exactly 3 calibration points")
            return ProxyGeometryResult(success=False, errors=errors)

        if len(projector_uvs) != 3:
            errors.append("Requires exactly 3 projector UV coordinates")
            return ProxyGeometryResult(success=False, errors=errors)

        # Create base geometry
        vertices, faces = create_planar_proxy_vertices(calibration_points)

        # Subdivide if requested
        if config.subdivisions > 0:
            vertices, faces = subdivide_quad(vertices, faces, config.subdivisions)

        # Compute UV coordinates
        base_uvs = compute_uv_for_calibration_points(projector_uvs)

        if config.subdivisions > 0:
            uvs = subdivide_uv(base_uvs, config.subdivisions)
        else:
            uvs = base_uvs

        # Calculate UV bounds
        u_values = [uv[0] for uv in uvs]
        v_values = [uv[1] for uv in uvs]
        uv_bounds = (min(u_values), max(u_values), min(v_values), max(v_values))

        return ProxyGeometryResult(
            object_ref=None,  # Will be set when Blender object is created
            mesh_name="Projection_Proxy",
            vertex_count=len(vertices),
            face_count=len(faces),
            uv_bounds=uv_bounds,
            success=True,
            errors=[]
        )

    except Exception as e:
        errors.append(f"Error creating proxy geometry: {e}")
        return ProxyGeometryResult(success=False, errors=errors)


def create_proxy_mesh_blender(
    vertices: List[Tuple[float, float, float]],
    faces: List[Tuple[int, ...]],
    uvs: List[Tuple[float, float]],
    name: str = "Projection_Proxy"
):
    """
    Create Blender mesh object from geometry data.

    Args:
        vertices: Vertex positions
        faces: Face indices
        uvs: UV coordinates (one per vertex)
        name: Mesh name

    Returns:
        bpy.types.Object or None if Blender unavailable
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        return None

    # Create mesh
    mesh = bpy.data.meshes.new(name)

    # Create object
    obj = bpy.data.objects.new(name, mesh)

    # Link to scene
    bpy.context.collection.objects.link(obj)

    # Create geometry using bmesh
    bm = bmesh.new()

    # Add vertices
    vert_objs = []
    for v in vertices:
        vert_objs.append(bm.verts.new(v))

    # Add faces
    for f in faces:
        bm.faces.new([vert_objs[i] for i in f])

    # Update mesh
    bm.to_mesh(mesh)
    bm.free()

    # Add UV layer
    uv_layer = mesh.uv_layers.new(name="ProjectorUV")

    # Assign UV coordinates
    # Map vertex indices to UV indices
    for i, vert in enumerate(mesh.vertices):
        if i < len(uvs):
            # Find loops that reference this vertex
            for poly in mesh.polygons:
                for loop_idx in poly.loop_indices:
                    loop = mesh.loops[loop_idx]
                    if loop.vertex_index == i:
                        uv_layer.data[loop_idx].uv = uvs[i]

    return obj


def create_multi_surface_proxy(
    calibration_points: List[Tuple[float, float, float]],
    projector_uvs: List[Tuple[float, float]],
    config: ProxyGeometryConfig = ProxyGeometryConfig()
) -> ProxyGeometryResult:
    """
    Create multi-surface proxy geometry from 4+ point DLT calibration.

    Creates more complex geometry for non-planar or multi-surface targets.

    Args:
        calibration_points: World positions of calibration points
        projector_uvs: Corresponding projector UV coordinates
        config: Proxy geometry configuration

    Returns:
        ProxyGeometryResult with mesh data
    """
    errors = []

    if len(calibration_points) < 4:
        errors.append("Multi-surface proxy requires at least 4 calibration points")
        return ProxyGeometryResult(success=False, errors=errors)

    # For multi-surface, create convex hull triangulation
    # This is a simplified implementation - full version would use
    # Delaunay triangulation or similar

    try:
        # Create vertices from calibration points
        vertices = list(calibration_points)

        # Simple fan triangulation from first point
        faces = []
        for i in range(1, len(vertices) - 1):
            faces.append((0, i, i + 1))

        # UVs from projector coordinates
        uvs = list(projector_uvs)

        # Calculate UV bounds
        u_values = [uv[0] for uv in uvs]
        v_values = [uv[1] for uv in uvs]
        uv_bounds = (min(u_values), max(u_values), min(v_values), max(v_values))

        return ProxyGeometryResult(
            object_ref=None,
            mesh_name="MultiSurface_Proxy",
            vertex_count=len(vertices),
            face_count=len(faces),
            uv_bounds=uv_bounds,
            success=True,
            errors=[]
        )

    except Exception as e:
        errors.append(f"Error creating multi-surface proxy: {e}")
        return ProxyGeometryResult(success=False, errors=errors)
