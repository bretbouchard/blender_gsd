"""
Quetzalcoatl Scale Layer Generator

Procedural scale generation for body surface detail.
"""

import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from .types import ScaleConfig, ScaleShape
from .body import BodyResult


class ScaleRegion(Enum):
    """Scale region on body."""
    HEAD = 0
    NECK = 1
    BACK = 2
    BELLY = 3
    TAIL = 4


@dataclass
class ScaleData:
    """Data for a single scale."""
    position: np.ndarray  # (3,) center position
    normal: np.ndarray  # (3,) surface normal
    size: float
    shape: ScaleShape
    rotation: float
    overlap: float
    region: ScaleRegion


@dataclass
class ScaleLayerResult:
    """Result of scale layer generation."""
    scales: List[ScaleData]
    vertices: np.ndarray  # Combined scale vertices
    faces: np.ndarray  # Combined scale faces
    uvs: np.ndarray
    normals: np.ndarray

    @property
    def scale_count(self) -> int:
        return len(self.scales)

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)


class ScaleGenerator:
    """Generate procedural scale layer."""

    def __init__(
        self,
        config: ScaleConfig,
        body_result: BodyResult,
    ):
        """
        Initialize scale generator.

        Args:
            config: Scale configuration
            body_result: Generated body data (for surface placement)
        """
        self.config = config
        self.body = body_result

    def generate(self, seed: Optional[int] = None) -> ScaleLayerResult:
        """
        Generate scale layer on body surface.

        Args:
            seed: Random seed for variation

        Returns:
            ScaleLayerResult with scale data and geometry
        """
        rng = np.random.default_rng(seed)

        scales = []
        vertices_list = []
        faces_list = []

        # Calculate scale distribution based on body surface
        body_vertex_count = self.body.vertex_count

        if body_vertex_count == 0:
            return ScaleLayerResult(
                scales=[],
                vertices=np.zeros((0, 3)),
                faces=np.zeros((0, 3), dtype=int),
                uvs=np.zeros((0, 2)),
                normals=np.zeros((0, 3)),
            )

        # Determine scale density
        # Higher density = more scales per body vertex
        density_factor = self.config.density * 0.5  # Adjust for reasonable count
        target_scales = max(10, int(body_vertex_count * density_factor))

        # Distribute scales across body surface
        scale_positions = self._distribute_scales(target_scales, rng)

        for i, pos_data in enumerate(scale_positions):
            vertex_idx = pos_data['vertex_idx']
            t = pos_data['t']
            angle = pos_data['angle']

            # Get body vertex data
            position = self.body.vertices[vertex_idx]
            normal = self.body.vertex_normals[vertex_idx]

            # Determine region
            region = self._get_region(t)

            # Calculate scale size with variation
            base_size = self.config.size
            variation = self.config.variation
            size = base_size * (1 + variation * (rng.random() - 0.5))

            # Scale rotation follows body curvature
            rotation = angle + variation * rng.random() * 0.2

            # Create scale geometry
            scale_verts, scale_faces = self._generate_single_scale(
                position=position,
                normal=normal,
                size=size,
                rotation=rotation,
            )

            offset = sum(len(v) for v in vertices_list)
            vertices_list.append(scale_verts)
            faces_list.append(scale_faces + offset)

            scales.append(ScaleData(
                position=position.copy(),
                normal=normal.copy(),
                size=size,
                shape=self.config.shape,
                rotation=rotation,
                overlap=self.config.overlap,
                region=region,
            ))

        # Combine all geometry
        vertices = np.vstack(vertices_list) if vertices_list else np.zeros((0, 3))
        faces = np.vstack(faces_list) if faces_list else np.zeros((0, 3), dtype=int)

        # Generate UVs
        uvs = self._generate_uvs(vertices)

        # Calculate normals
        normals = self._calculate_normals(vertices, faces)

        return ScaleLayerResult(
            scales=scales,
            vertices=vertices,
            faces=faces,
            uvs=uvs,
            normals=normals,
        )

    def _distribute_scales(
        self,
        target_count: int,
        rng: np.random.Generator,
    ) -> List[dict]:
        """
        Distribute scales across body surface.

        Args:
            target_count: Target number of scales
            rng: Random number generator

        Returns:
            List of scale position data
        """
        positions = []
        n_body = self.body.vertex_count

        # Use body vertices as candidate positions
        # Sample based on density and avoid clustering

        # Simple approach: sample vertices with probability based on spacing
        indices = np.arange(n_body)
        rng.shuffle(indices)

        # Take first target_count (or all if fewer)
        sample_count = min(target_count, n_body)
        sampled = indices[:sample_count]

        for idx in sampled:
            t = self.body.spine_position[idx]
            angle = self.body.radial_angle[idx]

            positions.append({
                'vertex_idx': idx,
                't': t,
                'angle': angle,
            })

        return positions

    def _get_region(self, t: float) -> ScaleRegion:
        """Determine scale region based on spine position."""
        if t < 0.1:
            return ScaleRegion.HEAD
        elif t < 0.2:
            return ScaleRegion.NECK
        elif t < 0.7:
            return ScaleRegion.BACK
        elif t < 0.85:
            return ScaleRegion.BELLY
        else:
            return ScaleRegion.TAIL

    def _generate_single_scale(
        self,
        position: np.ndarray,
        normal: np.ndarray,
        size: float,
        rotation: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a single scale mesh.

        Args:
            position: Center position on body surface
            normal: Surface normal
            size: Scale size
            rotation: Rotation angle

        Returns:
            Tuple of (vertices, faces)
        """
        # Create local coordinate frame
        normal = normal / np.linalg.norm(normal)

        # Find perpendicular vectors
        if abs(normal[2]) < 0.9:
            tangent = np.cross(normal, np.array([0, 0, 1]))
        else:
            tangent = np.cross(normal, np.array([1, 0, 0]))
        tangent = tangent / np.linalg.norm(tangent)
        bitangent = np.cross(normal, tangent)

        # Apply rotation
        cos_r = np.cos(rotation)
        sin_r = np.sin(rotation)
        u = tangent * cos_r + bitangent * sin_r
        v = -tangent * sin_r + bitangent * cos_r

        vertices = []
        faces = []

        # Generate scale based on shape
        if self.config.shape == ScaleShape.ROUND:
            verts, fcs = self._generate_round_scale(
                position, normal, u, v, size
            )
        elif self.config.shape == ScaleShape.OVAL:
            verts, fcs = self._generate_oval_scale(
                position, normal, u, v, size
            )
        elif self.config.shape == ScaleShape.HEXAGONAL:
            verts, fcs = self._generate_hexagonal_scale(
                position, normal, u, v, size
            )
        elif self.config.shape == ScaleShape.DIAMOND:
            verts, fcs = self._generate_diamond_scale(
                position, normal, u, v, size
            )
        else:
            verts, fcs = self._generate_oval_scale(
                position, normal, u, v, size
            )

        return verts, fcs

    def _generate_round_scale(
        self,
        position: np.ndarray,
        normal: np.ndarray,
        u: np.ndarray,
        v: np.ndarray,
        size: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate round/circular scale."""
        n_segments = 8
        height = size * 0.3 * self.config.overlap

        vertices = []
        faces = []

        # Base ring
        for i in range(n_segments):
            angle = 2 * np.pi * i / n_segments
            offset = size * 0.5 * (np.cos(angle) * u + np.sin(angle) * v)
            vertices.append(position + offset)

        # Top ring (smaller, raised)
        for i in range(n_segments):
            angle = 2 * np.pi * i / n_segments
            offset = size * 0.3 * (np.cos(angle) * u + np.sin(angle) * v)
            vertices.append(position + offset + normal * height)

        # Center vertex
        vertices.append(position + normal * height * 1.2)
        center_idx = len(vertices) - 1

        vertices = np.array(vertices)

        # Side faces
        for i in range(n_segments):
            i_next = (i + 1) % n_segments
            v00 = i
            v01 = i_next
            v10 = n_segments + i
            v11 = n_segments + i_next

            faces.append([v00, v10, v11])
            faces.append([v00, v11, v01])

        # Top faces (fan)
        for i in range(n_segments):
            i_next = (i + 1) % n_segments
            faces.append([n_segments + i, center_idx, n_segments + i_next])

        faces = np.array(faces, dtype=np.int32)

        return vertices, faces

    def _generate_oval_scale(
        self,
        position: np.ndarray,
        normal: np.ndarray,
        u: np.ndarray,
        v: np.ndarray,
        size: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate oval/elliptical scale."""
        n_segments = 8
        height = size * 0.25 * self.config.overlap

        # Oval ratio (wider along u)
        width_u = size * 0.6
        width_v = size * 0.35

        vertices = []
        faces = []

        # Base ring
        for i in range(n_segments):
            angle = 2 * np.pi * i / n_segments
            offset = width_u * np.cos(angle) * u + width_v * np.sin(angle) * v
            vertices.append(position + offset)

        # Top ring
        for i in range(n_segments):
            angle = 2 * np.pi * i / n_segments
            offset = width_u * 0.6 * np.cos(angle) * u + width_v * 0.6 * np.sin(angle) * v
            vertices.append(position + offset + normal * height)

        # Center vertex
        vertices.append(position + normal * height * 1.3)
        center_idx = len(vertices) - 1

        vertices = np.array(vertices)

        for i in range(n_segments):
            i_next = (i + 1) % n_segments
            v00 = i
            v01 = i_next
            v10 = n_segments + i
            v11 = n_segments + i_next

            faces.append([v00, v10, v11])
            faces.append([v00, v11, v01])

        for i in range(n_segments):
            i_next = (i + 1) % n_segments
            faces.append([n_segments + i, center_idx, n_segments + i_next])

        faces = np.array(faces, dtype=np.int32)

        return vertices, faces

    def _generate_hexagonal_scale(
        self,
        position: np.ndarray,
        normal: np.ndarray,
        u: np.ndarray,
        v: np.ndarray,
        size: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate hexagonal scale."""
        n_sides = 6
        height = size * 0.2 * self.config.overlap

        vertices = []
        faces = []

        # Hexagon vertices
        for i in range(n_sides):
            angle = np.pi / 6 + 2 * np.pi * i / n_sides
            offset = size * 0.5 * (np.cos(angle) * u + np.sin(angle) * v)
            vertices.append(position + offset)

        # Inner vertices (raised)
        for i in range(n_sides):
            angle = np.pi / 6 + 2 * np.pi * i / n_sides
            offset = size * 0.3 * (np.cos(angle) * u + np.sin(angle) * v)
            vertices.append(position + offset + normal * height)

        # Center
        vertices.append(position + normal * height * 1.2)
        center_idx = len(vertices) - 1

        vertices = np.array(vertices)

        # Side faces
        for i in range(n_sides):
            i_next = (i + 1) % n_sides
            faces.append([i, n_sides + i, n_sides + i_next])
            faces.append([i, n_sides + i_next, i_next])

        # Top faces
        for i in range(n_sides):
            i_next = (i + 1) % n_sides
            faces.append([n_sides + i, center_idx, n_sides + i_next])

        faces = np.array(faces, dtype=np.int32)

        return vertices, faces

    def _generate_diamond_scale(
        self,
        position: np.ndarray,
        normal: np.ndarray,
        u: np.ndarray,
        v: np.ndarray,
        size: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate diamond-shaped scale."""
        height = size * 0.35 * self.config.overlap

        vertices = []
        faces = []

        # Diamond has 4 base corners + 1 top
        half_size = size * 0.5

        # Base corners
        vertices.append(position + half_size * u)  # Front
        vertices.append(position + half_size * 0.6 * v)  # Right
        vertices.append(position - half_size * u * 0.3)  # Back
        vertices.append(position - half_size * 0.6 * v)  # Left

        # Top point
        vertices.append(position + normal * height + u * half_size * 0.3)

        vertices = np.array(vertices)

        # Four triangular faces meeting at top
        faces = np.array([
            [0, 1, 4],
            [1, 2, 4],
            [2, 3, 4],
            [3, 0, 4],
        ], dtype=np.int32)

        return vertices, faces

    def _generate_uvs(self, vertices: np.ndarray) -> np.ndarray:
        """Generate UV coordinates for scales."""
        if len(vertices) == 0:
            return np.zeros((0, 2))

        # Simple planar projection
        center = np.mean(vertices, axis=0)
        rel = vertices - center

        u = (rel[:, 0] - rel[:, 0].min()) / max(0.01, rel[:, 0].max() - rel[:, 0].min())
        v = (rel[:, 1] - rel[:, 1].min()) / max(0.01, rel[:, 1].max() - rel[:, 1].min())

        return np.column_stack([u, v])

    def _calculate_normals(
        self,
        vertices: np.ndarray,
        faces: np.ndarray,
    ) -> np.ndarray:
        """Calculate vertex normals."""
        if len(vertices) == 0:
            return np.zeros((0, 3))

        normals = np.zeros_like(vertices)

        for face in faces:
            v0, v1, v2 = vertices[face]
            edge1 = v1 - v0
            edge2 = v2 - v0
            face_normal = np.cross(edge1, edge2)

            length = np.linalg.norm(face_normal)
            if length > 1e-8:
                face_normal /= length

            for vi in face:
                normals[vi] += face_normal

        lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        normals = normals / np.maximum(lengths, 1e-8)

        return normals


def generate_scales(
    config: ScaleConfig,
    body_result: BodyResult,
    seed: Optional[int] = None,
) -> ScaleLayerResult:
    """
    Convenience function to generate scale layer.

    Args:
        config: Scale configuration
        body_result: Generated body data
        seed: Random seed

    Returns:
        ScaleLayerResult with scale data
    """
    generator = ScaleGenerator(config, body_result)
    return generator.generate(seed)
