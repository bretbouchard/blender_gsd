"""
Tile geometry generation for the tile platform system.

This module provides procedural tile geometry generation that is
Blender-independent for maximum testability.

All geometry is generated centered at origin with CCW winding order.
"""

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class TileGeometry:
    """Procedural geometry data for a tile.

    Attributes:
        vertices: List of (x, y, z) vertex positions
        faces: List of vertex index tuples defining faces
        normals: List of (x, y, z) normal vectors per vertex
        uvs: Optional list of (u, v) texture coordinates per vertex
    """
    vertices: List[Tuple[float, float, float]]
    faces: List[Tuple[int, ...]]
    normals: List[Tuple[float, float, float]]
    uvs: Optional[List[Tuple[float, float]]] = None


class Tile:
    """Tile geometry generator for different tile shapes.

    This class provides static methods for generating procedural geometry
    for various tile shapes. All shapes are:
    - Centered at origin (0, 0, 0)
    - Generated with CCW winding order
    - Include UV coordinates for texturing
    - Independent of Blender for testability
    """

    @staticmethod
    def generate_square(size: float) -> TileGeometry:
        """Generate a square tile geometry.

        Creates a square in the XY plane centered at origin.

        Args:
            size: The size (width and height) of the square

        Returns:
            TileGeometry with 4 vertices, 1 face, normals, and UVs
        """
        half = size / 2.0

        # 4 vertices, CCW winding starting from bottom-left
        vertices = [
            (-half, -half, 0.0),  # 0: bottom-left
            (half, -half, 0.0),   # 1: bottom-right
            (half, half, 0.0),    # 2: top-right
            (-half, half, 0.0),   # 3: top-left
        ]

        # 1 face with 4 vertices (CCW when viewed from above)
        faces = [(0, 1, 2, 3)]

        # All vertices have the same normal (pointing up in +Z)
        normals = [
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0),
        ]

        # UV coordinates for texturing
        uvs = [
            (0.0, 0.0),  # bottom-left
            (1.0, 0.0),  # bottom-right
            (1.0, 1.0),  # top-right
            (0.0, 1.0),  # top-left
        ]

        return TileGeometry(vertices=vertices, faces=faces, normals=normals, uvs=uvs)

    @staticmethod
    def generate_octagon(size: float) -> TileGeometry:
        """Generate an octagonal tile geometry.

        Creates a regular octagon in the XY plane centered at origin.

        Args:
            size: The diameter (corner-to-corner) of the octagon

        Returns:
            TileGeometry with 8 vertices, 1 face, normals, and UVs
        """
        # For a regular octagon, vertices are at 22.5°, 67.5°, etc.
        # Using corner-to-corner diameter
        radius = size / 2.0
        vertices = []

        # Generate 8 vertices, starting at angle 0 (right), CCW
        for i in range(8):
            angle = i * math.pi / 4.0  # 45° increments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertices.append((x, y, 0.0))

        # 1 face with 8 vertices (fan from vertex 0)
        faces = [(0, 1, 2, 3, 4, 5, 6, 7)]

        # All vertices have the same normal (pointing up in +Z)
        normals = [(0.0, 0.0, 1.0) for _ in range(8)]

        # UV coordinates mapped to bounding square
        # Map octagon vertices to square UV space
        uvs = []
        for i in range(8):
            angle = i * math.pi / 4.0
            # Map from [-1, 1] to [0, 1]
            u = (math.cos(angle) + 1.0) / 2.0
            v = (math.sin(angle) + 1.0) / 2.0
            uvs.append((u, v))

        return TileGeometry(vertices=vertices, faces=faces, normals=normals, uvs=uvs)

    @staticmethod
    def generate_hexagon(size: float) -> TileGeometry:
        """Generate a hexagonal tile geometry.

        Creates a regular hexagon in the XY plane centered at origin.

        Args:
            size: The diameter (flat-to-flat or point-to-point) of the hexagon

        Returns:
            TileGeometry with 6 vertices, 1 face, normals, and UVs
        """
        # Using point-to-point diameter
        radius = size / 2.0
        vertices = []

        # Generate 6 vertices, starting at angle 0 (right), CCW
        for i in range(6):
            angle = i * math.pi / 3.0  # 60° increments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            vertices.append((x, y, 0.0))

        # 1 face with 6 vertices (fan from vertex 0)
        faces = [(0, 1, 2, 3, 4, 5)]

        # All vertices have the same normal (pointing up in +Z)
        normals = [(0.0, 0.0, 1.0) for _ in range(6)]

        # UV coordinates mapped to bounding square
        uvs = []
        for i in range(6):
            angle = i * math.pi / 3.0
            # Map from [-1, 1] to [0, 1]
            u = (math.cos(angle) + 1.0) / 2.0
            v = (math.sin(angle) + 1.0) / 2.0
            uvs.append((u, v))

        return TileGeometry(vertices=vertices, faces=faces, normals=normals, uvs=uvs)
