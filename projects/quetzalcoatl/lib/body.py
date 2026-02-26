"""
Quetzalcoatl Body Generator

Procedural body mesh generation from spine curve with elliptical cross-sections.
"""

import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .types import BodyConfig
from .spine import SpineResult


class BodyRegion(Enum):
    """Body region identifiers."""
    HEAD = 0
    NECK = 1
    BODY = 2
    TAIL_BASE = 3
    TAIL_TIP = 4


@dataclass
class BodyResult:
    """Result of body mesh generation."""
    vertices: np.ndarray  # (N, 3) vertex positions
    faces: np.ndarray  # (M, 3) triangle faces (indices)
    uvs: np.ndarray  # (N, 2) UV coordinates
    vertex_normals: np.ndarray  # (N, 3) vertex normals
    spine_position: np.ndarray  # (N,) normalized spine position (0-1)
    body_region: np.ndarray  # (N,) region enum value
    radial_angle: np.ndarray  # (N,) radial angle around spine (0-2π)

    @property
    def vertex_count(self) -> int:
        """Number of vertices."""
        return len(self.vertices)

    @property
    def face_count(self) -> int:
        """Number of faces."""
        return len(self.faces)


class BodyGenerator:
    """Generate procedural body mesh from spine curve."""

    def __init__(
        self,
        spine_result: SpineResult,
        config: BodyConfig,
        body_length_ratio: float = 0.6,  # Where body region starts
        tail_start_ratio: float = 0.75,  # Where tail region starts
    ):
        """
        Initialize body generator.

        Args:
            spine_result: Generated spine curve data
            config: Body configuration
            body_length_ratio: Where neck ends and body begins (0-1)
            tail_start_ratio: Where tail begins (0-1)
        """
        self.spine = spine_result
        self.config = config
        self.body_length_ratio = body_length_ratio
        self.tail_start_ratio = tail_start_ratio

    def generate(self, radial_segments: int = 16) -> BodyResult:
        """
        Generate body mesh with elliptical cross-sections.

        Args:
            radial_segments: Number of vertices around each cross-section

        Returns:
            BodyResult with mesh data
        """
        n_spine = self.spine.point_count
        n_radial = max(3, radial_segments)

        # Calculate total vertex count
        n_vertices = n_spine * n_radial

        # Allocate arrays
        vertices = np.zeros((n_vertices, 3), dtype=np.float64)
        uvs = np.zeros((n_vertices, 2), dtype=np.float64)
        spine_positions = np.zeros(n_vertices, dtype=np.float64)
        body_regions = np.zeros(n_vertices, dtype=np.int32)
        radial_angles = np.zeros(n_vertices, dtype=np.float64)

        # Generate vertices for each spine point
        for i in range(n_spine):
            t = self.spine.spine_positions[i]
            radius = self.spine.radii[i] * self.config.radius

            # Apply compression for elliptical cross-section
            width = radius
            height = radius * self.config.compression

            # Apply dorsal flattening
            if self.config.dorsal_flat > 0:
                # Flatten the top of the ellipse
                pass  # Applied during cross-section generation

            # Get spine frame
            point = self.spine.points[i]
            tangent = self.spine.tangents[i]
            normal = self.spine.normals[i]
            binormal = self.spine.binormals[i]

            # Generate cross-section vertices
            for j in range(n_radial):
                angle = 2 * np.pi * j / n_radial

                # Elliptical cross-section
                local_x = width * np.cos(angle)
                local_y = height * np.sin(angle)

                # Apply dorsal flattening (compress top)
                if self.config.dorsal_flat > 0 and np.sin(angle) > 0:
                    local_y *= (1 - self.config.dorsal_flat * 0.5)

                # Transform to world space
                offset = local_x * normal + local_y * binormal
                world_pos = point + offset

                # Store vertex
                idx = i * n_radial + j
                vertices[idx] = world_pos

                # UV coordinates (spine position, radial angle)
                uvs[idx] = [t, angle / (2 * np.pi)]

                # Spine position
                spine_positions[idx] = t

                # Body region
                body_regions[idx] = self._get_region(t)

                # Radial angle
                radial_angles[idx] = angle

        # Generate faces
        faces = self._generate_faces(n_spine, n_radial)

        # Calculate vertex normals
        vertex_normals = self._calculate_normals(vertices, faces)

        return BodyResult(
            vertices=vertices,
            faces=faces,
            uvs=uvs,
            vertex_normals=vertex_normals,
            spine_position=spine_positions,
            body_region=body_regions,
            radial_angle=radial_angles,
        )

    def _get_region(self, t: float) -> int:
        """Determine body region based on spine position."""
        if t < 0.1:
            return BodyRegion.HEAD.value
        elif t < 0.2:
            return BodyRegion.NECK.value
        elif t < self.tail_start_ratio:
            return BodyRegion.BODY.value
        elif t < 0.9:
            return BodyRegion.TAIL_BASE.value
        else:
            return BodyRegion.TAIL_TIP.value

    def _generate_faces(
        self, n_spine: int, n_radial: int
    ) -> np.ndarray:
        """Generate triangle faces connecting cross-sections."""
        # Each quad between spine points becomes 2 triangles
        n_quads = (n_spine - 1) * n_radial
        faces = np.zeros((n_quads * 2, 3), dtype=np.int32)

        face_idx = 0
        for i in range(n_spine - 1):
            for j in range(n_radial):
                # Current and next radial indices (wrap around)
                j_next = (j + 1) % n_radial

                # Vertex indices
                v00 = i * n_radial + j
                v01 = i * n_radial + j_next
                v10 = (i + 1) * n_radial + j
                v11 = (i + 1) * n_radial + j_next

                # Two triangles for the quad
                faces[face_idx] = [v00, v10, v11]
                faces[face_idx + 1] = [v00, v11, v01]
                face_idx += 2

        return faces

    def _calculate_normals(
        self, vertices: np.ndarray, faces: np.ndarray
    ) -> np.ndarray:
        """Calculate vertex normals from face normals."""
        normals = np.zeros_like(vertices)

        # Calculate face normals and accumulate to vertices
        for face in faces:
            v0, v1, v2 = vertices[face]
            edge1 = v1 - v0
            edge2 = v2 - v0
            face_normal = np.cross(edge1, edge2)

            # Normalize face normal
            length = np.linalg.norm(face_normal)
            if length > 1e-8:
                face_normal /= length

            # Accumulate to vertices
            for vi in face:
                normals[vi] += face_normal

        # Normalize vertex normals
        lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        normals = normals / np.maximum(lengths, 1e-8)

        return normals


def generate_body(
    spine_result: SpineResult,
    radius: float = 0.5,
    compression: float = 0.8,
    dorsal_flat: float = 0.0,
    radial_segments: int = 16,
) -> BodyResult:
    """
    Convenience function to generate body mesh.

    Args:
        spine_result: Generated spine data
        radius: Body radius
        compression: Width/height ratio
        dorsal_flat: Dorsal flattening (0-1)
        radial_segments: Vertices per cross-section

    Returns:
        BodyResult with mesh data
    """
    config = BodyConfig(
        radius=radius,
        compression=compression,
        dorsal_flat=dorsal_flat,
    )
    generator = BodyGenerator(spine_result, config)
    return generator.generate(radial_segments)
