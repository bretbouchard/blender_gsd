"""
Quetzalcoatl Wing Generator

Procedural wing generation supporting feathered and membrane wing types.
"""

import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from .types import WingConfig, WingType
from .spine import SpineResult
from .body import BodyResult


class WingSegment(Enum):
    """Wing segment identifiers."""
    SHOULDER = 0
    ARM = 1
    FOREARM = 2
    HAND = 3
    FINGER = 4
    FEATHER = 5


class WingSide(Enum):
    """Wing side (left/right)."""
    LEFT = -1
    RIGHT = 1


@dataclass
class WingSocket:
    """Socket for wing attachment point."""
    segment_type: WingSegment
    position: np.ndarray  # (3,) world position
    normal: np.ndarray  # (3,) surface normal
    rotation: float  # Rotation angle
    scale: float  # Socket scale


@dataclass
class FeatherData:
    """Data for a single feather."""
    position: np.ndarray  # (3,) base position
    direction: np.ndarray  # (3,) feather direction
    length: float
    width: float
    barb_density: int
    rotation: float  # Rotation around direction axis


@dataclass
class WingResult:
    """Result of wing generation for a single wing."""
    vertices: np.ndarray  # (N, 3) vertex positions
    faces: np.ndarray  # (M, 3) triangle faces
    uvs: np.ndarray  # (N, 2) UV coordinates
    normals: np.ndarray  # (N, 3) vertex normals
    sockets: List[WingSocket]  # Attachment points
    feathers: List[FeatherData]  # Feather data (for feathered wings)
    side: WingSide
    wing_type: WingType

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)

    @property
    def face_count(self) -> int:
        return len(self.faces)


@dataclass
class AllWingsResult:
    """Result of all wings generation."""
    wings: List[WingResult]

    @property
    def wing_count(self) -> int:
        return len(self.wings)

    @property
    def total_vertices(self) -> int:
        return sum(w.vertex_count for w in self.wings)

    @property
    def total_faces(self) -> int:
        return sum(w.face_count for w in self.wings)


class WingGenerator:
    """Generate procedural wing geometry."""

    # Anatomical ratios for membrane wings (relative to arm length)
    ARM_RATIO = 0.35
    FOREARM_RATIO = 0.35
    HAND_RATIO = 0.30

    def __init__(
        self,
        config: WingConfig,
        spine_result: SpineResult,
        body_result: BodyResult,
    ):
        """
        Initialize wing generator.

        Args:
            config: Wing configuration
            spine_result: Generated spine data
            body_result: Generated body data
        """
        self.config = config
        self.spine = spine_result
        self.body = body_result

    def generate_all(self, resolution: int = 8) -> AllWingsResult:
        """
        Generate all wings based on config.

        Args:
            resolution: Vertex resolution

        Returns:
            AllWingsResult with all wing data
        """
        wings = []

        if self.config.wing_type == WingType.NONE:
            return AllWingsResult(wings=[])

        # Wings attach near the front of the creature
        spine_t = 0.15  # Attachment position on spine

        # Generate left wing
        left_wing = self._generate_wing(
            spine_t=spine_t,
            side=WingSide.LEFT,
            resolution=resolution,
        )
        wings.append(left_wing)

        # Generate right wing
        right_wing = self._generate_wing(
            spine_t=spine_t,
            side=WingSide.RIGHT,
            resolution=resolution,
        )
        wings.append(right_wing)

        return AllWingsResult(wings=wings)

    def _generate_wing(
        self,
        spine_t: float,
        side: WingSide,
        resolution: int,
    ) -> WingResult:
        """
        Generate a single wing.

        Args:
            spine_t: Spine attachment position
            side: Left or right
            resolution: Mesh resolution

        Returns:
            WingResult for this wing
        """
        if self.config.wing_type == WingType.FEATHERED:
            return self._generate_feathered_wing(spine_t, side, resolution)
        elif self.config.wing_type == WingType.MEMBRANE:
            return self._generate_membrane_wing(spine_t, side, resolution)
        else:
            # Return empty result for NONE type
            return WingResult(
                vertices=np.zeros((0, 3)),
                faces=np.zeros((0, 3), dtype=int),
                uvs=np.zeros((0, 2)),
                normals=np.zeros((0, 3)),
                sockets=[],
                feathers=[],
                side=side,
                wing_type=self.config.wing_type,
            )

    def _generate_feathered_wing(
        self,
        spine_t: float,
        side: WingSide,
        resolution: int,
    ) -> WingResult:
        """
        Generate a feathered (bird-like) wing.

        Args:
            spine_t: Spine attachment position
            side: Left or right
            resolution: Mesh resolution

        Returns:
            WingResult for feathered wing
        """
        vertices_list = []
        faces_list = []
        sockets = []
        feathers = []

        # Get attachment point from body
        spine_idx = min(
            int(spine_t * (self.spine.point_count - 1)),
            self.spine.point_count - 1
        )

        attach_pos = self.spine.points[spine_idx]
        spine_tangent = self.spine.tangents[spine_idx]
        spine_normal = self.spine.normals[spine_idx]
        spine_binormal = self.spine.binormals[spine_idx]
        spine_radius = self.spine.radii[spine_idx]

        # Wing extends outward and slightly back
        outward_dir = spine_normal * side.value
        outward_dir = outward_dir / np.linalg.norm(outward_dir)

        # Wing attachment position (on side of body)
        wing_attach = attach_pos + spine_radius * 0.9 * outward_dir

        # Calculate wing arm direction (mostly outward, slightly back and up)
        arm_length = self.config.wing_arm_length
        arm_dir = (
            outward_dir * 0.8 +
            spine_tangent * 0.3 +
            spine_binormal * 0.2
        )
        arm_dir = arm_dir / np.linalg.norm(arm_dir)

        # Generate wing arm bones (simplified as thin cylinders)
        arm_verts, arm_faces, arm_sockets = self._generate_wing_arm(
            base_pos=wing_attach,
            direction=arm_dir,
            outward_dir=outward_dir,
            length=arm_length,
            resolution=resolution,
        )
        vertices_list.append(arm_verts)
        faces_list.append(arm_faces)
        sockets.extend(arm_sockets)

        # Generate feather layers
        arm_tip = wing_attach + arm_dir * arm_length
        for layer_idx in range(self.config.feather_layers):
            layer_feathers = self._generate_feather_layer(
                base_pos=wing_attach,
                arm_tip=arm_tip,
                arm_dir=arm_dir,
                outward_dir=outward_dir,
                back_dir=-spine_tangent,
                layer_index=layer_idx,
                total_layers=self.config.feather_layers,
                resolution=resolution,
            )

            offset = sum(len(v) for v in vertices_list)
            vertices_list.append(layer_feathers[0])
            faces_list.append(layer_feathers[1] + offset)
            feathers.extend(layer_feathers[2])

        # Combine all geometry
        vertices = np.vstack(vertices_list) if vertices_list else np.zeros((0, 3))
        faces = np.vstack(faces_list) if faces_list else np.zeros((0, 3), dtype=int)

        # Generate UVs
        uvs = self._generate_uvs(vertices, side)

        # Calculate normals
        normals = self._calculate_normals(vertices, faces)

        return WingResult(
            vertices=vertices,
            faces=faces,
            uvs=uvs,
            normals=normals,
            sockets=sockets,
            feathers=feathers,
            side=side,
            wing_type=WingType.FEATHERED,
        )

    def _generate_wing_arm(
        self,
        base_pos: np.ndarray,
        direction: np.ndarray,
        outward_dir: np.ndarray,
        length: float,
        resolution: int,
    ) -> Tuple[np.ndarray, np.ndarray, List[WingSocket]]:
        """
        Generate wing arm bones.

        Args:
            base_pos: Base position
            direction: Arm direction
            outward_dir: Outward direction
            length: Arm length
            resolution: Mesh resolution

        Returns:
            Tuple of (vertices, faces, sockets)
        """
        sockets = []
        n_segments = 4
        base_radius = 0.08
        tip_radius = 0.03

        direction = direction / np.linalg.norm(direction)

        # Create perpendicular vectors
        perp1 = np.cross(direction, outward_dir)
        if np.linalg.norm(perp1) < 0.01:
            perp1 = np.cross(direction, np.array([0, 0, 1]))
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(direction, perp1)

        vertices = []
        faces = []

        for seg in range(n_segments + 1):
            t = seg / n_segments
            radius = base_radius * (1 - t) + tip_radius * t
            seg_pos = base_pos + direction * length * t

            for i in range(resolution):
                angle = 2 * np.pi * i / resolution
                offset = (
                    radius * np.cos(angle) * perp1 +
                    radius * np.sin(angle) * perp2
                )
                vertices.append(seg_pos + offset)

        vertices = np.array(vertices)

        # Generate faces
        for seg in range(n_segments):
            for i in range(resolution):
                i_next = (i + 1) % resolution

                v00 = seg * resolution + i
                v01 = seg * resolution + i_next
                v10 = (seg + 1) * resolution + i
                v11 = (seg + 1) * resolution + i_next

                faces.append([v00, v10, v11])
                faces.append([v00, v11, v01])

        faces = np.array(faces, dtype=np.int32)

        # Tip socket
        sockets.append(WingSocket(
            segment_type=WingSegment.ARM,
            position=base_pos + direction * length,
            normal=direction.copy(),
            rotation=0.0,
            scale=tip_radius,
        ))

        return vertices, faces, sockets

    def _generate_feather_layer(
        self,
        base_pos: np.ndarray,
        arm_tip: np.ndarray,
        arm_dir: np.ndarray,
        outward_dir: np.ndarray,
        back_dir: np.ndarray,
        layer_index: int,
        total_layers: int,
        resolution: int,
    ) -> Tuple[np.ndarray, np.ndarray, List[FeatherData]]:
        """
        Generate a layer of feathers.

        Args:
            base_pos: Wing base position
            arm_tip: Arm tip position
            arm_dir: Arm direction
            outward_dir: Outward direction
            back_dir: Backward direction
            layer_index: Layer index (0 = innermost)
            total_layers: Total number of layers
            resolution: Mesh resolution

        Returns:
            Tuple of (vertices, faces, feathers)
        """
        feathers = []
        vertices_list = []
        faces_list = []

        # Number of feathers per layer
        feather_count = 12 - layer_index * 2  # Fewer feathers in outer layers
        feather_count = max(4, feather_count)

        # Layer parameters
        layer_offset = layer_index / total_layers
        feather_length = 0.3 + 0.2 * layer_offset  # Longer feathers in outer layers
        feather_width = 0.03 + 0.01 * layer_offset

        for f_idx in range(feather_count):
            # Feather position along wing
            t = f_idx / (feather_count - 1) if feather_count > 1 else 0.5

            # Position: from base toward tip
            feather_base = (
                base_pos * (1 - t) +
                arm_tip * t +
                outward_dir * layer_offset * 0.3
            )

            # Feather direction: mostly outward/backward
            feather_dir = (
                outward_dir * 0.5 +
                back_dir * (0.3 + 0.4 * layer_offset) +
                np.array([0, 0, -0.2])  # Slight downward
            )
            feather_dir = feather_dir / np.linalg.norm(feather_dir)

            # Generate feather geometry
            f_verts, f_faces = self._generate_single_feather(
                base_pos=feather_base,
                direction=feather_dir,
                length=feather_length * (1 - 0.3 * t),  # Shorter toward tip
                width=feather_width * (1 - 0.2 * t),
                resolution=max(4, resolution // 2),
            )

            offset = sum(len(v) for v in vertices_list)
            vertices_list.append(f_verts)
            faces_list.append(f_faces + offset)

            feathers.append(FeatherData(
                position=feather_base.copy(),
                direction=feather_dir.copy(),
                length=feather_length * (1 - 0.3 * t),
                width=feather_width * (1 - 0.2 * t),
                barb_density=15,
                rotation=0.0,
            ))

        vertices = np.vstack(vertices_list) if vertices_list else np.zeros((0, 3))
        faces = np.vstack(faces_list) if faces_list else np.zeros((0, 3), dtype=int)

        return vertices, faces, feathers

    def _generate_single_feather(
        self,
        base_pos: np.ndarray,
        direction: np.ndarray,
        length: float,
        width: float,
        resolution: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a single feather.

        Args:
            base_pos: Feather base position
            direction: Feather direction
            length: Feather length
            width: Feather width
            resolution: Mesh resolution

        Returns:
            Tuple of (vertices, faces)
        """
        n_segments = 3

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

        for seg in range(n_segments + 1):
            t = seg / n_segments
            # Feather tapers
            seg_width = width * (1 - t * 0.8)
            seg_pos = base_pos + direction * length * t

            for i in range(resolution):
                angle = 2 * np.pi * i / resolution
                offset = (
                    seg_width * np.cos(angle) * perp1 +
                    seg_width * 0.3 * np.sin(angle) * perp2
                )
                vertices.append(seg_pos + offset)

        vertices = np.array(vertices)

        for seg in range(n_segments):
            for i in range(resolution):
                i_next = (i + 1) % resolution

                v00 = seg * resolution + i
                v01 = seg * resolution + i_next
                v10 = (seg + 1) * resolution + i
                v11 = (seg + 1) * resolution + i_next

                faces.append([v00, v10, v11])
                faces.append([v00, v11, v01])

        faces = np.array(faces, dtype=np.int32)

        return vertices, faces

    def _generate_membrane_wing(
        self,
        spine_t: float,
        side: WingSide,
        resolution: int,
    ) -> WingResult:
        """
        Generate a membrane (bat/dragon-like) wing.

        Args:
            spine_t: Spine attachment position
            side: Left or right
            resolution: Mesh resolution

        Returns:
            WingResult for membrane wing
        """
        vertices_list = []
        faces_list = []
        sockets = []

        # Get attachment point
        spine_idx = min(
            int(spine_t * (self.spine.point_count - 1)),
            self.spine.point_count - 1
        )

        attach_pos = self.spine.points[spine_idx]
        spine_tangent = self.spine.tangents[spine_idx]
        spine_normal = self.spine.normals[spine_idx]
        spine_binormal = self.spine.binormals[spine_idx]
        spine_radius = self.spine.radii[spine_idx]

        outward_dir = spine_normal * side.value
        outward_dir = outward_dir / np.linalg.norm(outward_dir)

        wing_attach = attach_pos + spine_radius * 0.9 * outward_dir

        # Wing span
        span = self.config.wing_span
        arm_length = self.config.wing_arm_length

        # Generate finger bones that support the membrane
        finger_count = self.config.finger_count
        all_finger_pos = []

        for f_idx in range(finger_count):
            # Spread fingers from front to back
            spread = (f_idx - (finger_count - 1) / 2) / max(1, finger_count - 1)

            finger_dir = (
                outward_dir * 0.7 +
                spine_tangent * (0.2 + 0.3 * spread) +
                spine_binormal * (0.2 - 0.2 * abs(spread))
            )
            finger_dir = finger_dir / np.linalg.norm(finger_dir)

            finger_length = span * (0.6 + 0.4 * (1 - abs(spread)))

            # Generate finger bone
            f_verts, f_faces, f_sockets = self._generate_finger_bone(
                base_pos=wing_attach,
                direction=finger_dir,
                length=finger_length,
                resolution=resolution,
            )

            offset = sum(len(v) for v in vertices_list)
            vertices_list.append(f_verts)
            faces_list.append(f_faces + offset)
            sockets.extend(f_sockets)

            # Store finger tip for membrane
            all_finger_pos.append(wing_attach + finger_dir * finger_length)

        # Generate membrane between fingers
        if len(all_finger_pos) >= 2:
            mem_verts, mem_faces = self._generate_membrane(
                body_attach=wing_attach,
                finger_tips=all_finger_pos,
                resolution=resolution,
            )

            offset = sum(len(v) for v in vertices_list)
            vertices_list.append(mem_verts)
            faces_list.append(mem_faces + offset)

        # Combine all geometry
        vertices = np.vstack(vertices_list) if vertices_list else np.zeros((0, 3))
        faces = np.vstack(faces_list) if faces_list else np.zeros((0, 3), dtype=int)

        # Generate UVs
        uvs = self._generate_uvs(vertices, side)

        # Calculate normals
        normals = self._calculate_normals(vertices, faces)

        return WingResult(
            vertices=vertices,
            faces=faces,
            uvs=uvs,
            normals=normals,
            sockets=sockets,
            feathers=[],  # No feathers for membrane wings
            side=side,
            wing_type=WingType.MEMBRANE,
        )

    def _generate_finger_bone(
        self,
        base_pos: np.ndarray,
        direction: np.ndarray,
        length: float,
        resolution: int,
    ) -> Tuple[np.ndarray, np.ndarray, List[WingSocket]]:
        """
        Generate a finger bone for membrane wing.

        Args:
            base_pos: Base position
            direction: Finger direction
            length: Finger length
            resolution: Mesh resolution

        Returns:
            Tuple of (vertices, faces, sockets)
        """
        sockets = []
        n_segments = 4
        base_radius = 0.04
        tip_radius = 0.01

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

        for seg in range(n_segments + 1):
            t = seg / n_segments
            radius = base_radius * (1 - t) + tip_radius * t
            seg_pos = base_pos + direction * length * t

            for i in range(resolution):
                angle = 2 * np.pi * i / resolution
                offset = (
                    radius * np.cos(angle) * perp1 +
                    radius * np.sin(angle) * perp2
                )
                vertices.append(seg_pos + offset)

        vertices = np.array(vertices)

        for seg in range(n_segments):
            for i in range(resolution):
                i_next = (i + 1) % resolution

                v00 = seg * resolution + i
                v01 = seg * resolution + i_next
                v10 = (seg + 1) * resolution + i
                v11 = (seg + 1) * resolution + i_next

                faces.append([v00, v10, v11])
                faces.append([v00, v11, v01])

        faces = np.array(faces, dtype=np.int32)

        sockets.append(WingSocket(
            segment_type=WingSegment.FINGER,
            position=base_pos + direction * length,
            normal=direction.copy(),
            rotation=0.0,
            scale=tip_radius,
        ))

        return vertices, faces, sockets

    def _generate_membrane(
        self,
        body_attach: np.ndarray,
        finger_tips: List[np.ndarray],
        resolution: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate membrane between finger bones.

        Args:
            body_attach: Body attachment point
            finger_tips: List of finger tip positions
            resolution: Mesh resolution

        Returns:
            Tuple of (vertices, faces)
        """
        vertices = [body_attach]
        faces = []

        # Create membrane panels between each pair of adjacent fingers
        for i in range(len(finger_tips) - 1):
            tip1 = finger_tips[i]
            tip2 = finger_tips[i + 1]

            # Create a quad between body, tip1, tip2
            v0 = 0  # body_attach is always vertex 0

            # Add intermediate vertices for smoother membrane
            mid1 = (body_attach + tip1) / 2
            mid2 = (body_attach + tip2) / 2
            edge_mid = (tip1 + tip2) / 2

            v1 = len(vertices)
            vertices.append(mid1)

            v2 = len(vertices)
            vertices.append(tip1)

            v3 = len(vertices)
            vertices.append(edge_mid)

            v4 = len(vertices)
            vertices.append(tip2)

            v5 = len(vertices)
            vertices.append(mid2)

            # Triangulate the membrane panel
            faces.append([v0, v1, v3])
            faces.append([v1, v2, v3])
            faces.append([v0, v3, v5])
            faces.append([v3, v4, v5])

        vertices = np.array(vertices)
        faces = np.array(faces, dtype=np.int32)

        return vertices, faces

    def _generate_uvs(
        self,
        vertices: np.ndarray,
        side: WingSide,
    ) -> np.ndarray:
        """Generate UV coordinates for wing."""
        if len(vertices) == 0:
            return np.zeros((0, 2))

        # Simple projection based on position
        center = np.mean(vertices, axis=0)
        rel = vertices - center

        # UV from planar projection
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


def generate_wings(
    config: WingConfig,
    spine_result: SpineResult,
    body_result: BodyResult,
    resolution: int = 8,
) -> AllWingsResult:
    """
    Convenience function to generate all wings.

    Args:
        config: Wing configuration
        spine_result: Generated spine data
        body_result: Generated body data
        resolution: Mesh resolution

    Returns:
        AllWingsResult with all wing data
    """
    generator = WingGenerator(config, spine_result, body_result)
    return generator.generate_all(resolution)
