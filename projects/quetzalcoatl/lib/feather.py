"""
Quetzalcoatl Feather Layer Generator

Procedural feather generation for body surface detail (distinct from wing feathers).
"""

import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from .types import FeatherConfig
from .body import BodyResult


class FeatherRegion(Enum):
    """Feather region on body."""
    HEAD_CREST = 0
    NECK_MANE = 1
    BACK_RIDGE = 2
    TAIL_TUFT = 3
    BODY_PLUMAGE = 4


@dataclass
class FeatherData:
    """Data for a single feather."""
    position: np.ndarray  # (3,) base position
    direction: np.ndarray  # (3,) feather direction (points outward)
    length: float
    width: float
    barb_density: int
    rotation: float  # Rotation around direction axis
    iridescence: float
    region: FeatherRegion


@dataclass
class FeatherLayerResult:
    """Result of feather layer generation."""
    feathers: List[FeatherData]
    vertices: np.ndarray  # Combined feather vertices
    faces: np.ndarray  # Combined feather faces
    uvs: np.ndarray
    normals: np.ndarray

    @property
    def feather_count(self) -> int:
        return len(self.feathers)

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)


class FeatherGenerator:
    """Generate procedural feather layer."""

    def __init__(
        self,
        config: FeatherConfig,
        body_result: BodyResult,
    ):
        """
        Initialize feather generator.

        Args:
            config: Feather configuration
            body_result: Generated body data
        """
        self.config = config
        self.body = body_result

    def generate(
        self,
        seed: Optional[int] = None,
        coverage: float = 0.3,  # Fraction of body to cover with feathers
    ) -> FeatherLayerResult:
        """
        Generate feather layer on body surface.

        Args:
            seed: Random seed for variation
            coverage: Fraction of body vertices to add feathers to (0-1)

        Returns:
            FeatherLayerResult with feather data and geometry
        """
        rng = np.random.default_rng(seed)

        feathers = []
        vertices_list = []
        faces_list = []

        body_vertex_count = self.body.vertex_count

        if body_vertex_count == 0:
            return FeatherLayerResult(
                feathers=[],
                vertices=np.zeros((0, 3)),
                faces=np.zeros((0, 3), dtype=int),
                uvs=np.zeros((0, 2)),
                normals=np.zeros((0, 3)),
            )

        # Determine which body vertices get feathers
        # Focus on upper body (positive radial angle = top)
        feather_positions = self._select_feather_positions(coverage, rng)

        for pos_data in feather_positions:
            vertex_idx = pos_data['vertex_idx']
            t = pos_data['t']
            angle = pos_data['angle']

            # Get body vertex data
            position = self.body.vertices[vertex_idx]
            normal = self.body.vertex_normals[vertex_idx]

            # Determine region
            region = self._get_region(t, angle)

            # Calculate feather parameters with variation
            base_length = self.config.length
            base_width = self.config.width

            # Add variation
            length = base_length * (1 + 0.2 * (rng.random() - 0.5))
            width = base_width * (1 + 0.2 * (rng.random() - 0.5))

            # Feather direction: mostly along normal with some backward lean
            direction = normal * 0.7 + np.array([0, -0.3, 0])
            direction = direction / np.linalg.norm(direction)

            # Rotation based on body position
            rotation = angle * 0.3 + rng.random() * 0.1

            # Generate feather geometry
            f_verts, f_faces = self._generate_single_feather(
                position=position,
                direction=direction,
                length=length,
                width=width,
                rotation=rotation,
            )

            offset = sum(len(v) for v in vertices_list)
            vertices_list.append(f_verts)
            faces_list.append(f_faces + offset)

            feathers.append(FeatherData(
                position=position.copy(),
                direction=direction.copy(),
                length=length,
                width=width,
                barb_density=self.config.barb_density,
                rotation=rotation,
                iridescence=self.config.iridescence,
                region=region,
            ))

        # Combine all geometry
        vertices = np.vstack(vertices_list) if vertices_list else np.zeros((0, 3))
        faces = np.vstack(faces_list) if faces_list else np.zeros((0, 3), dtype=int)

        # Generate UVs
        uvs = self._generate_uvs(vertices)

        # Calculate normals
        normals = self._calculate_normals(vertices, faces)

        return FeatherLayerResult(
            feathers=feathers,
            vertices=vertices,
            faces=faces,
            uvs=uvs,
            normals=normals,
        )

    def _select_feather_positions(
        self,
        coverage: float,
        rng: np.random.Generator,
    ) -> List[dict]:
        """
        Select body positions for feather placement.

        Args:
            coverage: Coverage fraction
            rng: Random number generator

        Returns:
            List of position data dictionaries
        """
        positions = []
        n_body = self.body.vertex_count

        # Sample based on coverage
        sample_count = max(1, int(n_body * coverage))
        indices = np.arange(n_body)
        rng.shuffle(indices)
        sampled = indices[:sample_count]

        for idx in sampled:
            t = self.body.spine_position[idx]
            angle = self.body.radial_angle[idx]

            # Bias toward top of body (positive Z direction in local frame)
            # angle is 0-2π, top is around π/2 and 3π/2
            z_component = np.sin(angle)

            # Prefer top half (positive z_component)
            if z_component < 0 and rng.random() > 0.3:
                continue  # Skip most bottom positions

            positions.append({
                'vertex_idx': idx,
                't': t,
                'angle': angle,
            })

        return positions

    def _get_region(self, t: float, angle: float) -> FeatherRegion:
        """Determine feather region based on position."""
        # Top of body
        is_top = np.sin(angle) > 0

        if t < 0.1:
            return FeatherRegion.HEAD_CREST
        elif t < 0.2:
            return FeatherRegion.NECK_MANE
        elif t < 0.7:
            if is_top:
                return FeatherRegion.BACK_RIDGE
            else:
                return FeatherRegion.BODY_PLUMAGE
        else:
            return FeatherRegion.TAIL_TUFT

    def _generate_single_feather(
        self,
        position: np.ndarray,
        direction: np.ndarray,
        length: float,
        width: float,
        rotation: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a single feather mesh.

        Args:
            position: Base position on body
            direction: Feather growth direction
            length: Feather length
            width: Feather width
            rotation: Rotation around direction

        Returns:
            Tuple of (vertices, faces)
        """
        direction = direction / np.linalg.norm(direction)

        # Create local coordinate frame
        if abs(direction[2]) < 0.9:
            tangent = np.cross(direction, np.array([0, 0, 1]))
        else:
            tangent = np.cross(direction, np.array([1, 0, 0]))
        tangent = tangent / np.linalg.norm(tangent)
        bitangent = np.cross(direction, tangent)

        # Apply rotation
        cos_r = np.cos(rotation)
        sin_r = np.sin(rotation)
        u = tangent * cos_r + bitangent * sin_r
        v = -tangent * sin_r + bitangent * cos_r

        vertices = []
        faces = []

        # Feather is a tapered shape with a central shaft
        n_segments = 4

        # Central shaft vertices
        for seg in range(n_segments + 1):
            t = seg / n_segments
            # Shaft tapers
            shaft_width = width * 0.2 * (1 - t * 0.5)
            shaft_pos = position + direction * length * t

            # Two vertices for shaft edges
            vertices.append(shaft_pos + shaft_width * u)
            vertices.append(shaft_pos - shaft_width * u)

        # Add barbs (simplified as side extensions)
        for seg in range(1, n_segments):
            t = seg / n_segments
            barb_length = width * (1 - t * 0.5) * 2
            barb_pos = position + direction * length * t

            # Left barb tip
            vertices.append(barb_pos + barb_length * u)
            # Right barb tip
            vertices.append(barb_pos - barb_length * u)

        vertices = np.array(vertices)

        # Generate faces for shaft
        for seg in range(n_segments):
            v00 = seg * 2
            v01 = seg * 2 + 1
            v10 = (seg + 1) * 2
            v11 = (seg + 1) * 2 + 1

            faces.append([v00, v10, v11])
            faces.append([v00, v11, v01])

        # Generate faces for barbs
        shaft_vertex_count = (n_segments + 1) * 2
        for seg in range(1, n_segments):
            shaft_idx = seg * 2
            barb_idx = shaft_vertex_count + (seg - 1) * 2

            # Left barb
            faces.append([shaft_idx, shaft_idx + 2, barb_idx])
            # Right barb
            faces.append([shaft_idx + 1, barb_idx + 1, shaft_idx + 3])

        faces = np.array(faces, dtype=np.int32)

        return vertices, faces

    def _generate_uvs(self, vertices: np.ndarray) -> np.ndarray:
        """Generate UV coordinates for feathers."""
        if len(vertices) == 0:
            return np.zeros((0, 2))

        center = np.mean(vertices, axis=0)
        rel = vertices - center

        u = (rel[:, 0] - rel[:, 0].min()) / max(0.01, rel[:, 0].max() - rel[:, 0].min())
        v = (rel[:, 2] - rel[:, 2].min()) / max(0.01, rel[:, 2].max() - rel[:, 2].min())

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


def generate_feathers(
    config: FeatherConfig,
    body_result: BodyResult,
    seed: Optional[int] = None,
    coverage: float = 0.3,
) -> FeatherLayerResult:
    """
    Convenience function to generate feather layer.

    Args:
        config: Feather configuration
        body_result: Generated body data
        seed: Random seed
        coverage: Coverage fraction

    Returns:
        FeatherLayerResult with feather data
    """
    generator = FeatherGenerator(config, body_result)
    return generator.generate(seed, coverage)
