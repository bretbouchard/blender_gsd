"""
Quetzalcoatl Limb Generator

Procedural limb (leg) generation with upper leg, lower leg, foot, and toes.
"""

import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from .types import LimbConfig
from .spine import SpineResult
from .body import BodyResult


class LimbSegment(Enum):
    """Limb segment identifiers."""
    UPPER_LEG = 0
    LOWER_LEG = 1
    FOOT = 2
    TOE = 3
    CLAW = 4


class LimbSide(Enum):
    """Limb side (left/right)."""
    LEFT = -1
    RIGHT = 1


@dataclass
class JointSocket:
    """Socket for joint attachment point."""
    joint_type: LimbSegment
    position: np.ndarray  # (3,) world position
    normal: np.ndarray  # (3,) joint axis
    rotation: float  # Joint rotation angle
    scale: float  # Socket scale


@dataclass
class LimbResult:
    """Result of limb generation for a single leg."""
    vertices: np.ndarray  # (N, 3) vertex positions
    faces: np.ndarray  # (M, 3) triangle faces
    uvs: np.ndarray  # (N, 2) UV coordinates
    normals: np.ndarray  # (N, 3) vertex normals
    sockets: List[JointSocket]  # Joint attachment points
    side: LimbSide  # Left or right
    spine_position: float  # Where on spine this limb attaches

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    @property
    def face_count(self) -> int:
        return len(self.faces)


@dataclass
class AllLimbsResult:
    """Result of all limbs generation."""
    limbs: List[LimbResult]  # One result per leg

    @property
    def limb_count(self) -> int:
        return len(self.limbs)

    @property
    def total_vertices(self) -> int:
        return sum(l.vertex_count for l in self.limbs)

    @property
    def total_faces(self) -> int:
        return sum(l.face_count for l in self.limbs)


class LimbGenerator:
    """Generate procedural limb (leg) geometry."""

    # Anatomical ratios (relative to total leg length)
    UPPER_LEG_RATIO = 0.45
    LOWER_LEG_RATIO = 0.40
    FOOT_RATIO = 0.15

    def __init__(
        self,
        config: LimbConfig,
        spine_result: SpineResult,
        body_result: BodyResult,
    ):
        """
        Initialize limb generator.

        Args:
            config: Limb configuration
            spine_result: Generated spine data
            body_result: Generated body data (for attachment points)
        """
        self.config = config
        self.spine = spine_result
        self.body = body_result

    def generate_all(self, resolution: int = 8) -> AllLimbsResult:
        """
        Generate all limbs based on config.

        Args:
            resolution: Vertex resolution around limbs

        Returns:
            AllLimbsResult with all limb data
        """
        limbs = []

        for i in range(self.config.leg_pairs):
            # Get spine position for this leg pair
            if i < len(self.config.leg_positions):
                spine_t = self.config.leg_positions[i]
            else:
                # Default positions if not specified
                spine_t = 0.3 + 0.3 * i / max(1, self.config.leg_pairs - 1)

            # Generate left leg
            left_leg = self._generate_leg(
                spine_t=spine_t,
                side=LimbSide.LEFT,
                resolution=resolution,
            )
            limbs.append(left_leg)

            # Generate right leg
            right_leg = self._generate_leg(
                spine_t=spine_t,
                side=LimbSide.RIGHT,
                resolution=resolution,
            )
            limbs.append(right_leg)

        return AllLimbsResult(limbs=limbs)

    def _generate_leg(
        self,
        spine_t: float,
        side: LimbSide,
        resolution: int,
    ) -> LimbResult:
        """
        Generate a single leg.

        Args:
            spine_t: Spine position (0-1)
            side: Left or right
            resolution: Mesh resolution

        Returns:
            LimbResult for this leg
        """
        vertices_list = []
        faces_list = []
        sockets = []

        # Get spine frame at attachment point
        spine_idx = min(
            int(spine_t * (self.spine.point_count - 1)),
            self.spine.point_count - 1
        )

        spine_point = self.spine.points[spine_idx]
        spine_tangent = self.spine.tangents[spine_idx]
        spine_normal = self.spine.normals[spine_idx]
        spine_binormal = self.spine.binormals[spine_idx]
        spine_radius = self.spine.radii[spine_idx]

        # Calculate leg attachment position
        attach_offset = (spine_radius * 0.9) * side.value
        attach_pos = spine_point + attach_offset * spine_normal

        # Calculate leg length components
        total_length = self.config.leg_length
        upper_length = total_length * self.UPPER_LEG_RATIO
        lower_length = total_length * self.LOWER_LEG_RATIO
        foot_length = total_length * self.FOOT_RATIO

        # Generate segments
        offset = 0

        # Upper leg (femur)
        upper_verts, upper_faces, upper_sockets = self._generate_segment(
            start_pos=attach_pos,
            direction=-spine_binormal,  # Point downward
            lateral_dir=spine_normal * side.value,
            length=upper_length,
            base_radius=self.config.leg_girth,
            tip_radius=self.config.leg_girth * 0.7,
            resolution=resolution,
            segment_type=LimbSegment.UPPER_LEG,
        )
        vertices_list.append(upper_verts)
        faces_list.append(upper_faces)
        sockets.extend(upper_sockets)

        # Lower leg (tibia/fibula)
        knee_pos = attach_pos - upper_length * spine_binormal
        lower_verts, lower_faces, lower_sockets = self._generate_segment(
            start_pos=knee_pos,
            direction=-spine_binormal,
            lateral_dir=spine_normal * side.value,
            length=lower_length,
            base_radius=self.config.leg_girth * 0.7,
            tip_radius=self.config.leg_girth * 0.5,
            resolution=resolution,
            segment_type=LimbSegment.LOWER_LEG,
        )
        offset = len(upper_verts)
        vertices_list.append(lower_verts)
        faces_list.append(lower_faces + offset)
        sockets.extend(lower_sockets)

        # Foot
        ankle_pos = knee_pos - lower_length * spine_binormal
        foot_verts, foot_faces, foot_sockets = self._generate_foot(
            start_pos=ankle_pos,
            direction=-spine_binormal,
            forward_dir=-spine_tangent,
            lateral_dir=spine_normal * side.value,
            length=foot_length,
            radius=self.config.leg_girth * 0.4,
            resolution=resolution,
        )
        offset = len(upper_verts) + len(lower_verts)
        vertices_list.append(foot_verts)
        faces_list.append(foot_faces + offset)
        sockets.extend(foot_sockets)

        # Toes and claws
        foot_end = ankle_pos - foot_length * spine_binormal
        toe_verts, toe_faces, toe_sockets = self._generate_toes(
            foot_center=foot_end,
            forward_dir=-spine_tangent,
            lateral_dir=spine_normal * side.value,
            up_dir=spine_binormal,
            resolution=resolution,
        )
        offset = len(upper_verts) + len(lower_verts) + len(foot_verts)
        vertices_list.append(toe_verts)
        faces_list.append(toe_faces + offset)
        sockets.extend(toe_sockets)

        # Combine all geometry
        vertices = np.vstack(vertices_list) if vertices_list else np.zeros((0, 3))
        faces = np.vstack(faces_list) if faces_list else np.zeros((0, 3), dtype=int)

        # Generate UVs
        uvs = self._generate_uvs(vertices, side)

        # Calculate normals
        normals = self._calculate_normals(vertices, faces)

        return LimbResult(
            vertices=vertices,
            faces=faces,
            uvs=uvs,
            normals=normals,
            sockets=sockets,
            side=side,
            spine_position=spine_t,
        )

    def _generate_segment(
        self,
        start_pos: np.ndarray,
        direction: np.ndarray,
        lateral_dir: np.ndarray,
        length: float,
        base_radius: float,
        tip_radius: float,
        resolution: int,
        segment_type: LimbSegment,
    ) -> Tuple[np.ndarray, np.ndarray, List[JointSocket]]:
        """
        Generate a limb segment (cylindrical section).

        Args:
            start_pos: Starting position
            direction: Segment direction (normalized)
            lateral_dir: Lateral direction for orientation
            length: Segment length
            base_radius: Radius at start
            tip_radius: Radius at end
            resolution: Radial resolution
            segment_type: Type of segment

        Returns:
            Tuple of (vertices, faces, sockets)
        """
        sockets = []
        n_rings = 4

        # Normalize direction
        direction = direction / np.linalg.norm(direction)
        lateral_dir = lateral_dir / np.linalg.norm(lateral_dir)

        # Calculate perpendicular direction
        perp = np.cross(direction, lateral_dir)
        perp = perp / np.linalg.norm(perp)

        vertices = []
        faces = []

        for ring in range(n_rings + 1):
            t = ring / n_rings
            radius = base_radius * (1 - t) + tip_radius * t
            ring_pos = start_pos + direction * length * t

            for seg in range(resolution):
                angle = 2 * np.pi * seg / resolution

                # Elliptical cross-section (slightly wider than deep)
                offset = (
                    radius * 1.1 * np.cos(angle) * lateral_dir +
                    radius * 0.9 * np.sin(angle) * perp
                )
                vertices.append(ring_pos + offset)

        vertices = np.array(vertices)

        # Generate faces
        for ring in range(n_rings):
            for seg in range(resolution):
                seg_next = (seg + 1) % resolution

                v00 = ring * resolution + seg
                v01 = ring * resolution + seg_next
                v10 = (ring + 1) * resolution + seg
                v11 = (ring + 1) * resolution + seg_next

                faces.append([v00, v10, v11])
                faces.append([v00, v11, v01])

        faces = np.array(faces, dtype=np.int32)

        # Create joint socket at end
        end_pos = start_pos + direction * length
        sockets.append(JointSocket(
            joint_type=segment_type,
            position=end_pos,
            normal=direction.copy(),
            rotation=0.0,
            scale=tip_radius,
        ))

        return vertices, faces, sockets

    def _generate_foot(
        self,
        start_pos: np.ndarray,
        direction: np.ndarray,
        forward_dir: np.ndarray,
        lateral_dir: np.ndarray,
        length: float,
        radius: float,
        resolution: int,
    ) -> Tuple[np.ndarray, np.ndarray, List[JointSocket]]:
        """
        Generate foot segment.

        Args:
            start_pos: Ankle position
            direction: Downward direction
            forward_dir: Forward direction (toes point this way)
            lateral_dir: Lateral direction
            length: Foot length
            radius: Foot radius
            resolution: Mesh resolution

        Returns:
            Tuple of (vertices, faces, sockets)
        """
        sockets = []
        n_rings = 3

        # Normalize directions
        direction = direction / np.linalg.norm(direction)
        forward_dir = forward_dir / np.linalg.norm(forward_dir)
        lateral_dir = lateral_dir / np.linalg.norm(lateral_dir)

        vertices = []
        faces = []

        # Foot curves down then forward
        for ring in range(n_rings + 1):
            t = ring / n_rings

            # Curve: starts going down, transitions to forward
            down_amount = length * (1 - t) * 0.6
            forward_amount = length * t * 0.8

            ring_pos = (
                start_pos
                + direction * down_amount
                + forward_dir * forward_amount
            )

            # Foot gets wider toward toes, then tapers
            width_factor = 1.0 + 0.3 * np.sin(np.pi * t)

            for seg in range(resolution):
                angle = 2 * np.pi * seg / resolution

                # Foot is wider than tall
                offset = (
                    radius * width_factor * 1.3 * np.cos(angle) * lateral_dir +
                    radius * 0.6 * np.sin(angle) * direction
                )
                vertices.append(ring_pos + offset)

        vertices = np.array(vertices)

        # Generate faces
        for ring in range(n_rings):
            for seg in range(resolution):
                seg_next = (seg + 1) % resolution

                v00 = ring * resolution + seg
                v01 = ring * resolution + seg_next
                v10 = (ring + 1) * resolution + seg
                v11 = (ring + 1) * resolution + seg_next

                faces.append([v00, v10, v11])
                faces.append([v00, v11, v01])

        faces = np.array(faces, dtype=np.int32)

        # Foot socket at end
        end_pos = (
            start_pos
            + direction * length * 0.4
            + forward_dir * length * 0.6
        )
        sockets.append(JointSocket(
            joint_type=LimbSegment.FOOT,
            position=end_pos,
            normal=forward_dir.copy(),
            rotation=0.0,
            scale=radius * 0.5,
        ))

        return vertices, faces, sockets

    def _generate_toes(
        self,
        foot_center: np.ndarray,
        forward_dir: np.ndarray,
        lateral_dir: np.ndarray,
        up_dir: np.ndarray,
        resolution: int,
    ) -> Tuple[np.ndarray, np.ndarray, List[JointSocket]]:
        """
        Generate toes with claws.

        Args:
            foot_center: Center of foot end
            forward_dir: Forward direction
            lateral_dir: Lateral direction (outward)
            up_dir: Up direction
            resolution: Mesh resolution

        Returns:
            Tuple of (vertices, faces, sockets)
        """
        sockets = []
        vertices_list = []
        faces_list = []

        toe_count = self.config.toe_count
        claw_length = self.config.claw_length
        toe_length = 0.15  # Base toe length

        # Normalize directions
        forward_dir = forward_dir / np.linalg.norm(forward_dir)
        lateral_dir = lateral_dir / np.linalg.norm(lateral_dir)
        up_dir = up_dir / np.linalg.norm(up_dir)

        for toe_idx in range(toe_count):
            # Spread toes across foot
            spread = (toe_idx - (toe_count - 1) / 2) / max(1, toe_count - 1)

            # Toe position and direction
            toe_base = (
                foot_center
                + spread * 0.08 * lateral_dir
            )

            # Toe points forward and slightly outward
            toe_dir = (
                forward_dir * 0.9 +
                lateral_dir * spread * 0.3 +
                up_dir * (-0.1 - 0.1 * abs(spread))
            )
            toe_dir = toe_dir / np.linalg.norm(toe_dir)

            # Generate toe
            toe_verts, toe_faces = self._generate_single_toe(
                base_pos=toe_base,
                direction=toe_dir,
                length=toe_length * (1 - 0.2 * abs(spread)),
                base_radius=0.02,
                tip_radius=0.01,
                resolution=max(4, resolution // 2),
            )

            offset = sum(len(v) for v in vertices_list)
            vertices_list.append(toe_verts)
            faces_list.append(toe_faces + offset)

            # Generate claw
            claw_base = toe_base + toe_dir * toe_length * (1 - 0.2 * abs(spread))
            claw_verts, claw_faces = self._generate_claw(
                base_pos=claw_base,
                direction=toe_dir,
                length=claw_length,
                resolution=max(4, resolution // 2),
            )

            offset = sum(len(v) for v in vertices_list)
            vertices_list.append(claw_verts)
            faces_list.append(claw_faces + offset)

            # Claw socket
            sockets.append(JointSocket(
                joint_type=LimbSegment.CLAW,
                position=claw_base + claw_length * toe_dir,
                normal=toe_dir.copy(),
                rotation=0.0,
                scale=0.005,
            ))

        # Combine all toe geometry
        vertices = np.vstack(vertices_list) if vertices_list else np.zeros((0, 3))
        faces = np.vstack(faces_list) if faces_list else np.zeros((0, 3), dtype=int)

        return vertices, faces, sockets

    def _generate_single_toe(
        self,
        base_pos: np.ndarray,
        direction: np.ndarray,
        length: float,
        base_radius: float,
        tip_radius: float,
        resolution: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a single toe.

        Args:
            base_pos: Toe base position
            direction: Toe direction
            length: Toe length
            base_radius: Base radius
            tip_radius: Tip radius
            resolution: Radial resolution

        Returns:
            Tuple of (vertices, faces)
        """
        n_rings = 2

        direction = direction / np.linalg.norm(direction)

        # Create perpendicular vectors
        if abs(direction[2]) < 0.9:
            perp1 = np.cross(direction, np.array([0, 0, 1]))
        else:
            perp1 = np.cross(direction, np.array([1, 0, 0]))
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(direction, perp1)

        vertices = []
        faces = []

        for ring in range(n_rings + 1):
            t = ring / n_rings
            radius = base_radius * (1 - t) + tip_radius * t
            ring_pos = base_pos + direction * length * t

            for seg in range(resolution):
                angle = 2 * np.pi * seg / resolution
                offset = radius * np.cos(angle) * perp1 + radius * np.sin(angle) * perp2
                vertices.append(ring_pos + offset)

        vertices = np.array(vertices)

        for ring in range(n_rings):
            for seg in range(resolution):
                seg_next = (seg + 1) % resolution

                v00 = ring * resolution + seg
                v01 = ring * resolution + seg_next
                v10 = (ring + 1) * resolution + seg
                v11 = (ring + 1) * resolution + seg_next

                faces.append([v00, v10, v11])
                faces.append([v00, v11, v01])

        faces = np.array(faces, dtype=np.int32)

        return vertices, faces

    def _generate_claw(
        self,
        base_pos: np.ndarray,
        direction: np.ndarray,
        length: float,
        resolution: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a claw/talon.

        Args:
            base_pos: Claw base position
            direction: Claw direction
            length: Claw length
            resolution: Radial resolution

        Returns:
            Tuple of (vertices, faces)
        """
        base_radius = 0.008
        tip_radius = 0.001
        n_rings = 3

        direction = direction / np.linalg.norm(direction)

        # Create perpendicular vectors
        if abs(direction[2]) < 0.9:
            perp1 = np.cross(direction, np.array([0, 0, 1]))
        else:
            perp1 = np.cross(direction, np.array([1, 0, 0]))
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(direction, perp1)

        vertices = []
        faces = []

        for ring in range(n_rings + 1):
            t = ring / n_rings
            radius = base_radius * (1 - t) + tip_radius * t
            ring_pos = base_pos + direction * length * t

            for seg in range(resolution):
                angle = 2 * np.pi * seg / resolution
                offset = radius * np.cos(angle) * perp1 + radius * np.sin(angle) * perp2
                vertices.append(ring_pos + offset)

        # Add tip vertex
        tip_pos = base_pos + direction * length * 1.1
        vertices.append(tip_pos)
        tip_idx = len(vertices) - 1

        vertices = np.array(vertices)

        # Generate side faces
        for ring in range(n_rings):
            for seg in range(resolution):
                seg_next = (seg + 1) % resolution

                v00 = ring * resolution + seg
                v01 = ring * resolution + seg_next
                v10 = (ring + 1) * resolution + seg
                v11 = (ring + 1) * resolution + seg_next

                faces.append([v00, v10, v11])
                faces.append([v00, v11, v01])

        # Connect to tip
        last_ring_start = n_rings * resolution
        for seg in range(resolution):
            seg_next = (seg + 1) % resolution
            v0 = last_ring_start + seg
            v1 = last_ring_start + seg_next
            faces.append([v0, v1, tip_idx])

        faces = np.array(faces, dtype=np.int32)

        return vertices, faces

    def _generate_uvs(
        self,
        vertices: np.ndarray,
        side: LimbSide,
    ) -> np.ndarray:
        """Generate UV coordinates for limb."""
        if len(vertices) == 0:
            return np.zeros((0, 2))

        # Simple cylindrical UV projection
        center = np.mean(vertices, axis=0)
        rel = vertices - center

        # Calculate angles
        angles = np.arctan2(rel[:, 2], rel[:, 0])
        u = (angles + np.pi) / (2 * np.pi)

        # V based on height
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


def generate_limbs(
    config: LimbConfig,
    spine_result: SpineResult,
    body_result: BodyResult,
    resolution: int = 8,
) -> AllLimbsResult:
    """
    Convenience function to generate all limbs.

    Args:
        config: Limb configuration
        spine_result: Generated spine data
        body_result: Generated body data
        resolution: Mesh resolution

    Returns:
        AllLimbsResult with all limb data
    """
    generator = LimbGenerator(config, spine_result, body_result)
    return generator.generate_all(resolution)
