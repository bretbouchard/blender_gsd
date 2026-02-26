"""
Quetzalcoatl Head Generator

Procedural head generation with snout, jaw, eyes, nostrils, and crest options.
"""

import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from .types import HeadConfig, CrestType
from .spine import SpineResult
from .body import BodyResult


class HeadFeature(Enum):
    """Head feature identifiers for socket system."""
    SNOUT = 0
    JAW = 1
    LEFT_EYE = 2
    RIGHT_EYE = 3
    LEFT_NOSTRIL = 4
    RIGHT_NOSTRIL = 5
    CREST = 6
    LEFT_HORN = 7
    RIGHT_HORN = 8


@dataclass
class FeatureSocket:
    """Socket for attaching features to head."""
    feature_type: HeadFeature
    position: np.ndarray  # (3,) world position
    normal: np.ndarray  # (3,) surface normal
    scale: float  # Socket scale factor
    rotation: float  # Rotation around normal


@dataclass
class HeadResult:
    """Result of head generation."""
    vertices: np.ndarray  # (N, 3) vertex positions
    faces: np.ndarray  # (M, 3) triangle faces
    uvs: np.ndarray  # (N, 2) UV coordinates
    normals: np.ndarray  # (N, 3) vertex normals
    sockets: List[FeatureSocket]  # Feature attachment points

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    @property
    def face_count(self) -> int:
        return len(self.faces)


class HeadGenerator:
    """Generate procedural head geometry."""

    def __init__(
        self,
        config: HeadConfig,
        head_position: np.ndarray,
        head_direction: np.ndarray,
        head_scale: float = 1.0,
    ):
        """
        Initialize head generator.

        Args:
            config: Head configuration
            head_position: Center position of head base
            head_direction: Forward direction (normalized)
            head_scale: Base scale factor
        """
        self.config = config
        self.position = head_position
        self.direction = head_direction / np.linalg.norm(head_direction)
        self.scale = head_scale

        # Calculate coordinate frame
        self._setup_frame()

    def _setup_frame(self):
        """Set up local coordinate frame."""
        # Use up vector to create frame
        up = np.array([0.0, 0.0, 1.0])

        # Handle case where direction is parallel to up
        if abs(np.dot(self.direction, up)) > 0.99:
            up = np.array([0.0, 1.0, 0.0])

        self.right = np.cross(self.direction, up)
        self.right = self.right / np.linalg.norm(self.right)

        self.up = np.cross(self.right, self.direction)
        self.up = self.up / np.linalg.norm(self.up)

    def generate(self, resolution: int = 16) -> HeadResult:
        """
        Generate head mesh.

        Args:
            resolution: Vertex resolution for curves

        Returns:
            HeadResult with mesh data and feature sockets
        """
        vertices_list = []
        faces_list = []
        sockets = []

        # Generate base head sphere/ellipsoid
        head_verts, head_faces = self._generate_head_base(resolution)
        vertices_list.append(head_verts)
        faces_list.append(head_faces)

        # Generate snout
        snout_verts, snout_faces, snout_socket = self._generate_snout(
            resolution, head_verts
        )
        if snout_verts is not None:
            offset = len(head_verts)
            vertices_list.append(snout_verts)
            faces_list.append(snout_faces + offset)
            sockets.append(snout_socket)

        # Generate jaw
        jaw_verts, jaw_faces = self._generate_jaw(resolution, head_verts)
        if jaw_verts is not None:
            offset = sum(len(v) for v in vertices_list)
            vertices_list.append(jaw_verts)
            faces_list.append(jaw_faces + offset)

        # Generate crest if configured
        if self.config.crest_type != CrestType.NONE:
            crest_verts, crest_faces, crest_sockets = self._generate_crest(
                resolution
            )
            if crest_verts is not None:
                offset = sum(len(v) for v in vertices_list)
                vertices_list.append(crest_verts)
                faces_list.append(crest_faces + offset)
                sockets.extend(crest_sockets)

        # Add eye sockets
        sockets.extend(self._generate_eye_sockets(head_verts))

        # Add nostril sockets
        sockets.extend(self._generate_nostril_sockets(head_verts))

        # Combine all geometry
        vertices = np.vstack(vertices_list) if vertices_list else np.zeros((0, 3))
        faces = np.vstack(faces_list) if faces_list else np.zeros((0, 3), dtype=int)

        # Generate UVs (simple projection)
        uvs = self._generate_uvs(vertices)

        # Calculate normals
        normals = self._calculate_normals(vertices, faces)

        return HeadResult(
            vertices=vertices,
            faces=faces,
            uvs=uvs,
            normals=normals,
            sockets=sockets,
        )

    def _generate_head_base(
        self, resolution: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate base head ellipsoid."""
        # Create ellipsoid
        n_u = resolution  # Around
        n_v = resolution // 2  # Top to bottom

        vertices = []
        faces = []

        # Generate vertices
        for i in range(n_v + 1):
            v = i / n_v  # 0 to 1
            phi = np.pi * v  # 0 to π

            for j in range(n_u):
                u = j / n_u  # 0 to 1
                theta = 2 * np.pi * u

                # Ellipsoid with head proportions
                rx = 0.3 * self.scale  # Width
                ry = 0.35 * self.scale  # Depth (snout direction)
                rz = 0.25 * self.scale  # Height

                x = rx * np.sin(phi) * np.cos(theta)
                y = ry * np.sin(phi) * np.sin(theta)
                z = rz * np.cos(phi)

                # Transform to world space
                local_pos = np.array([x, y, z])
                world_pos = (
                    self.position
                    + local_pos[0] * self.right
                    + local_pos[1] * self.direction
                    + local_pos[2] * self.up
                )
                vertices.append(world_pos)

        vertices = np.array(vertices)

        # Generate faces
        for i in range(n_v):
            for j in range(n_u):
                j_next = (j + 1) % n_u

                v00 = i * n_u + j
                v01 = i * n_u + j_next
                v10 = (i + 1) * n_u + j
                v11 = (i + 1) * n_u + j_next

                # Skip degenerate faces at poles
                if i > 0:
                    faces.append([v00, v10, v11])
                if i < n_v - 1:
                    faces.append([v00, v11, v01])

        faces = np.array(faces, dtype=np.int32)

        return vertices, faces

    def _generate_snout(
        self, resolution: int, head_verts: np.ndarray
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[FeatureSocket]]:
        """Generate snout extension."""
        snout_length = self.config.snout_length * self.scale

        if snout_length < 0.01:
            return None, None, None

        # Create tapered cone for snout
        n_segments = resolution
        n_rings = 4

        vertices = []
        faces = []

        # Snout extends in forward direction
        base_radius = 0.15 * self.scale
        tip_radius = 0.02 * self.scale

        snout_start = self.position + 0.35 * self.scale * self.direction

        for ring in range(n_rings + 1):
            t = ring / n_rings
            radius = base_radius * (1 - t) + tip_radius * t
            z = snout_length * t

            ring_center = snout_start + z * self.direction

            for seg in range(n_segments):
                angle = 2 * np.pi * seg / n_segments

                # Elliptical cross-section (wider than tall)
                rx = radius * 1.2
                rz = radius * 0.8

                offset = (
                    rx * np.cos(angle) * self.right
                    + rz * np.sin(angle) * self.up
                )
                vertices.append(ring_center + offset)

        vertices = np.array(vertices)

        # Generate faces
        for ring in range(n_rings):
            for seg in range(n_segments):
                seg_next = (seg + 1) % n_segments

                v00 = ring * n_segments + seg
                v01 = ring * n_segments + seg_next
                v10 = (ring + 1) * n_segments + seg
                v11 = (ring + 1) * n_segments + seg_next

                faces.append([v00, v10, v11])
                faces.append([v00, v11, v01])

        faces = np.array(faces, dtype=np.int32)

        # Create snout tip socket
        socket = FeatureSocket(
            feature_type=HeadFeature.SNOUT,
            position=snout_start + snout_length * self.direction,
            normal=self.direction.copy(),
            scale=tip_radius,
            rotation=0.0,
        )

        return vertices, faces, socket

    def _generate_jaw(
        self, resolution: int, head_verts: np.ndarray
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Generate lower jaw."""
        jaw_depth = self.config.jaw_depth * self.scale

        if jaw_depth < 0.01:
            return None, None

        # Create lower jaw as a curved shape
        n_segments = resolution // 2
        n_rings = 3

        vertices = []
        faces = []

        jaw_start = self.position - 0.1 * self.scale * self.up
        jaw_length = 0.3 * self.scale

        for ring in range(n_rings + 1):
            t = ring / n_rings
            # Jaw curves down then forward
            z = jaw_length * t
            y = -jaw_depth * np.sin(np.pi * t / 2)

            ring_center = jaw_start + y * self.up + z * self.direction
            radius = 0.1 * self.scale * (1 - t * 0.7)

            for seg in range(n_segments):
                angle = np.pi * seg / (n_segments - 1) - np.pi / 2

                offset = radius * np.cos(angle) * self.right
                offset += radius * 0.5 * np.sin(angle) * self.up
                vertices.append(ring_center + offset)

        vertices = np.array(vertices)

        # Generate faces
        for ring in range(n_rings):
            for seg in range(n_segments - 1):
                v00 = ring * n_segments + seg
                v01 = ring * n_segments + seg + 1
                v10 = (ring + 1) * n_segments + seg
                v11 = (ring + 1) * n_segments + seg + 1

                faces.append([v00, v10, v11])
                faces.append([v00, v11, v01])

        faces = np.array(faces, dtype=np.int32)

        return vertices, faces

    def _generate_crest(
        self, resolution: int
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], List[FeatureSocket]]:
        """Generate head crest/horns."""
        sockets = []

        if self.config.crest_type == CrestType.NONE:
            return None, None, sockets

        crest_size = self.config.crest_size * self.scale
        vertices = []
        faces = []

        if self.config.crest_type == CrestType.RIDGE:
            # Simple dorsal ridge
            n_points = 8
            for i in range(n_points):
                t = i / (n_points - 1)
                height = crest_size * np.sin(np.pi * t)
                pos = (
                    self.position
                    + 0.1 * self.scale * self.up
                    + (0.2 * t - 0.1) * self.scale * self.direction
                    + height * self.up
                )
                vertices.append(pos)

            # Create faces for ridge (simplified as line of quads)
            # ... (simplified for now)

        elif self.config.crest_type == CrestType.HORNS:
            # Two horns on sides
            for side in [-1, 1]:
                horn_base = (
                    self.position
                    + 0.15 * self.scale * self.up
                    + 0.1 * side * self.scale * self.right
                    + 0.1 * self.scale * self.direction
                )

                # Horn socket
                feature = (
                    HeadFeature.LEFT_HORN if side == -1 else HeadFeature.RIGHT_HORN
                )
                sockets.append(FeatureSocket(
                    feature_type=feature,
                    position=horn_base,
                    normal=self.up.copy() + 0.3 * side * self.right,
                    scale=crest_size * 0.2,
                    rotation=0.0,
                ))

        vertices = np.array(vertices) if vertices else np.zeros((0, 3))
        faces = np.array(faces, dtype=np.int32) if faces else np.zeros((0, 3), dtype=int)

        return vertices, faces, sockets

    def _generate_eye_sockets(
        self, head_verts: np.ndarray
    ) -> List[FeatureSocket]:
        """Generate eye socket positions."""
        sockets = []

        eye_offset = 0.2 * self.scale
        eye_forward = 0.15 * self.scale
        eye_up = 0.1 * self.scale
        eye_scale = 0.08 * self.scale

        for side in [-1, 1]:
            eye_pos = (
                self.position
                + eye_offset * side * self.right
                + eye_forward * self.direction
                + eye_up * self.up
            )

            feature = HeadFeature.LEFT_EYE if side == -1 else HeadFeature.RIGHT_EYE
            sockets.append(FeatureSocket(
                feature_type=feature,
                position=eye_pos,
                normal=self.right * side * 0.5 + self.direction * 0.5,
                scale=eye_scale,
                rotation=0.0,
            ))

        return sockets

    def _generate_nostril_sockets(
        self, head_verts: np.ndarray
    ) -> List[FeatureSocket]:
        """Generate nostril socket positions."""
        sockets = []

        # Nostrils on snout
        nostril_offset = 0.05 * self.scale
        nostril_forward = (
            0.35 + self.config.snout_length * 0.8
        ) * self.scale
        nostril_up = -0.05 * self.scale
        nostril_scale = 0.02 * self.scale

        for side in [-1, 1]:
            nostril_pos = (
                self.position
                + nostril_offset * side * self.right
                + nostril_forward * self.direction
                + nostril_up * self.up
            )

            feature = (
                HeadFeature.LEFT_NOSTRIL if side == -1 else HeadFeature.RIGHT_NOSTRIL
            )
            sockets.append(FeatureSocket(
                feature_type=feature,
                position=nostril_pos,
                normal=self.direction.copy() - 0.5 * self.up,
                scale=nostril_scale,
                rotation=0.0,
            ))

        return sockets

    def _generate_uvs(self, vertices: np.ndarray) -> np.ndarray:
        """Generate UV coordinates using spherical projection."""
        if len(vertices) == 0:
            return np.zeros((0, 2))

        # Calculate relative positions
        rel = vertices - self.position

        # Project to spherical coordinates
        r = np.linalg.norm(rel, axis=1, keepdims=True)
        r = np.maximum(r, 1e-8)

        # Normalized direction
        d = rel / r

        # UV from spherical coordinates
        u = 0.5 + np.arctan2(d[:, 0], d[:, 1]) / (2 * np.pi)
        v = 0.5 - np.arcsin(np.clip(d[:, 2], -1, 1)) / np.pi

        return np.column_stack([u, v])

    def _calculate_normals(
        self, vertices: np.ndarray, faces: np.ndarray
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


def generate_head(
    config: HeadConfig,
    position: Tuple[float, float, float] = (0, 0, 0),
    direction: Tuple[float, float, float] = (0, 1, 0),
    scale: float = 1.0,
    resolution: int = 16,
) -> HeadResult:
    """
    Convenience function to generate head geometry.

    Args:
        config: Head configuration
        position: Head center position
        direction: Forward direction
        scale: Base scale factor
        resolution: Mesh resolution

    Returns:
        HeadResult with mesh and sockets
    """
    generator = HeadGenerator(
        config,
        np.array(position),
        np.array(direction),
        scale,
    )
    return generator.generate(resolution)
