"""
Detail Features Generator (Phase 20.7)

Generates detail features: teeth, whiskers, and claws.

Universal Stage Order:
- Stage 0: Normalize (parameter validation)
- Stage 1: Primary (teeth generation)
- Stage 2: Secondary (whiskers, claws)
- Stage 3: Detail (variations, surface details)
- Stage 4: Output Prep (UVs, normals)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple
import numpy as np


class ToothType(Enum):
    """Types of teeth for different creature types."""
    CONICAL = 0      # Serpent-like, simple cone teeth
    SERRATED = 1     # Dragon-like, saw-tooth edge
    FANG = 2         # Venomous fangs
    TUSK = 3         # Boar-like tusks


class WhiskerType(Enum):
    """Types of whiskers."""
    THIN = 0         # Thin, flexible whiskers
    THICK = 1        # Thick, stiff whiskers
    FEATHERED = 2    # Feather-like whiskers (catfish style)
    TENDRIL = 3      # Tendril-like whiskers


class ClawType(Enum):
    """Types of claws/talons."""
    SHARP = 0        # Sharp, curved talons
    BLUNT = 1        # Blunt claws
    HOOVED = 2       # Hoof-like
    WEBBED = 3       # Webbed feet


@dataclass
class ToothData:
    """Data for a single tooth."""
    position: np.ndarray
    direction: np.ndarray
    length: float
    width: float
    tooth_type: ToothType
    is_fang: bool = False


@dataclass
class WhiskerData:
    """Data for a single whisker."""
    position: np.ndarray
    direction: np.ndarray
    length: float
    thickness: float
    curve_amount: float
    whisker_type: WhiskerType


@dataclass
class ClawData:
    """Data for a single claw."""
    position: np.ndarray
    direction: np.ndarray
    length: float
    width: float
    curve_amount: float
    claw_type: ClawType


@dataclass
class TeethResult:
    """Result from teeth generation."""
    teeth: List[ToothData]
    vertices: np.ndarray
    faces: np.ndarray
    uvs: np.ndarray
    normals: np.ndarray

    @property
    def tooth_count(self) -> int:
        return len(self.teeth)

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)


@dataclass
class WhiskerResult:
    """Result from whisker generation."""
    whiskers: List[WhiskerData]
    vertices: np.ndarray
    faces: np.ndarray
    uvs: np.ndarray
    normals: np.ndarray

    @property
    def whisker_count(self) -> int:
        return len(self.whiskers)

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)


@dataclass
class ClawResult:
    """Result from claw generation."""
    claws: List[ClawData]
    vertices: np.ndarray
    faces: np.ndarray
    uvs: np.ndarray
    normals: np.ndarray

    @property
    def claw_count(self) -> int:
        return len(self.claws)

    @property
    def vertex_count(self) -> int:
        return len(self.vertices)


@dataclass
class DetailResult:
    """Combined result from all detail features."""
    teeth_result: TeethResult
    whisker_result: WhiskerResult
    claw_result: ClawResult

    @property
    def vertices(self) -> np.ndarray:
        return np.vstack([
            self.teeth_result.vertices,
            self.whisker_result.vertices,
            self.claw_result.vertices,
        ]) if self.total_vertex_count > 0 else np.zeros((0, 3))

    @property
    def faces(self) -> np.ndarray:
        teeth_count = self.teeth_result.vertex_count
        whisker_count = self.whisker_result.vertex_count

        teeth_faces = self.teeth_result.faces
        whisker_faces = self.whisker_result.faces + teeth_count
        claw_faces = self.claw_result.faces + teeth_count + whisker_count

        return np.vstack([
            teeth_faces,
            whisker_faces,
            claw_faces,
        ]) if self.total_face_count > 0 else np.zeros((0, 3), dtype=int)

    @property
    def uvs(self) -> np.ndarray:
        return np.vstack([
            self.teeth_result.uvs,
            self.whisker_result.uvs,
            self.claw_result.uvs,
        ]) if self.total_vertex_count > 0 else np.zeros((0, 2))

    @property
    def normals(self) -> np.ndarray:
        return np.vstack([
            self.teeth_result.normals,
            self.whisker_result.normals,
            self.claw_result.normals,
        ]) if self.total_vertex_count > 0 else np.zeros((0, 3))

    @property
    def total_vertex_count(self) -> int:
        return (
            self.teeth_result.vertex_count +
            self.whisker_result.vertex_count +
            self.claw_result.vertex_count
        )

    @property
    def total_face_count(self) -> int:
        return (
            len(self.teeth_result.faces) +
            len(self.whisker_result.faces) +
            len(self.claw_result.faces)
        )


class TeethGenerator:
    """Generates teeth for the creature's mouth."""

    def __init__(
        self,
        tooth_type: ToothType,
        count: int = 20,
        length: float = 0.05,
        width: float = 0.015,
        fang_count: int = 2,
        fang_length_multiplier: float = 2.0,
    ):
        """Initialize teeth generator.

        Args:
            tooth_type: Type of teeth to generate
            count: Number of regular teeth
            length: Base length of teeth
            width: Base width of teeth
            fang_count: Number of fangs (0, 2, or 4)
            fang_length_multiplier: How much longer fangs are
        """
        self.tooth_type = tooth_type
        self.count = max(0, count)
        self.length = max(0.01, length)
        self.width = max(0.005, width)
        self.fang_count = min(fang_count, 4)
        self.fang_length_multiplier = max(1.0, fang_length_multiplier)

    def generate(
        self,
        mouth_positions: Optional[List[Tuple[np.ndarray, np.ndarray]]] = None,
        seed: Optional[int] = None,
    ) -> TeethResult:
        """Generate teeth geometry.

        Args:
            mouth_positions: List of (position, normal) tuples for mouth edge
            seed: Random seed for variation

        Returns:
            TeethResult with teeth data and geometry
        """
        if seed is not None:
            np.random.seed(seed)

        teeth: List[ToothData] = []
        all_vertices: List[np.ndarray] = []
        all_faces: List[np.ndarray] = []
        all_uvs: List[np.ndarray] = []
        all_normals: List[np.ndarray] = []

        # Generate default mouth line if none provided
        if mouth_positions is None:
            mouth_positions = self._generate_default_mouth_line()

        if len(mouth_positions) == 0:
            return TeethResult(
                teeth=[],
                vertices=np.zeros((0, 3)),
                faces=np.zeros((0, 3), dtype=int),
                uvs=np.zeros((0, 2)),
                normals=np.zeros((0, 3)),
            )

        # Distribute teeth along mouth
        tooth_indices = np.linspace(0, len(mouth_positions) - 1, self.count, dtype=int)

        vertex_offset = 0
        for i, idx in enumerate(tooth_indices):
            pos, normal = mouth_positions[idx]

            # Determine if this is a fang position
            is_fang = self._is_fang_position(i, len(tooth_indices))

            # Calculate tooth properties
            tooth_length = self.length
            if is_fang:
                tooth_length *= self.fang_length_multiplier

            # Add slight variation
            variation = 1.0 + np.random.uniform(-0.1, 0.1)
            tooth_length *= variation
            tooth_width = self.width * variation

            # Generate tooth geometry
            vertices, faces, uvs, normals = self._generate_tooth_geometry(
                pos, normal, tooth_length, tooth_width, vertex_offset
            )

            tooth = ToothData(
                position=pos.copy(),
                direction=normal.copy(),
                length=tooth_length,
                width=tooth_width,
                tooth_type=self.tooth_type,
                is_fang=is_fang,
            )
            teeth.append(tooth)

            all_vertices.append(vertices)
            all_faces.append(faces)
            all_uvs.append(uvs)
            all_normals.append(normals)

            vertex_offset += len(vertices)

        if len(all_vertices) == 0:
            return TeethResult(
                teeth=teeth,
                vertices=np.zeros((0, 3)),
                faces=np.zeros((0, 3), dtype=int),
                uvs=np.zeros((0, 2)),
                normals=np.zeros((0, 3)),
            )

        return TeethResult(
            teeth=teeth,
            vertices=np.vstack(all_vertices),
            faces=np.vstack(all_faces),
            uvs=np.vstack(all_uvs),
            normals=np.vstack(all_normals),
        )

    def _generate_default_mouth_line(self) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Generate a default mouth line for testing."""
        positions = []
        for i in range(20):
            t = i / 19.0
            # Semi-circular mouth line
            angle = np.pi * 0.3 * (t - 0.5)
            x = np.sin(angle) * 0.3
            y = 0.0
            z = -np.cos(angle) * 0.1 + 0.1
            pos = np.array([x, y, z])

            # Normal pointing outward/down
            normal = np.array([np.sin(angle), 0.0, -np.cos(angle)])
            normal = normal / np.linalg.norm(normal)

            positions.append((pos, normal))

        return positions

    def _is_fang_position(self, index: int, total: int) -> bool:
        """Check if this position should be a fang."""
        if self.fang_count == 0:
            return False

        # Fangs go at front positions
        if self.fang_count == 2:
            return index == total // 4 or index == (3 * total) // 4
        elif self.fang_count == 4:
            return index in [total // 6, total // 3, (2 * total) // 3, (5 * total) // 6]

        return False

    def _generate_tooth_geometry(
        self,
        position: np.ndarray,
        direction: np.ndarray,
        length: float,
        width: float,
        vertex_offset: int,
        segments: int = 6,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Generate geometry for a single tooth."""
        vertices = []
        faces = []
        uvs = []
        normals = []

        # Create coordinate frame
        direction = direction / np.linalg.norm(direction)

        # Find perpendicular vectors
        if abs(direction[2]) < 0.9:
            perp1 = np.cross(direction, np.array([0, 0, 1]))
        else:
            perp1 = np.cross(direction, np.array([1, 0, 0]))
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(direction, perp1)

        # Generate conical tooth
        rings = 4
        for ring in range(rings + 1):
            t = ring / rings
            ring_radius = width * (1.0 - t * 0.9)  # Taper to tip
            ring_height = t * length

            for seg in range(segments):
                angle = 2 * np.pi * seg / segments
                local_pos = (
                    ring_radius * np.cos(angle) * perp1 +
                    ring_radius * np.sin(angle) * perp2 +
                    ring_height * direction
                )

                vertices.append(position + local_pos)

                # UV
                u = seg / segments
                v = t
                uvs.append(np.array([u, v]))

                # Normal
                normal = local_pos
                if np.linalg.norm(normal) > 0.001:
                    normal = normal / np.linalg.norm(normal)
                else:
                    normal = direction
                normals.append(normal)

        # Generate faces
        for ring in range(rings):
            for seg in range(segments):
                next_seg = (seg + 1) % segments

                i0 = vertex_offset + ring * segments + seg
                i1 = vertex_offset + ring * segments + next_seg
                i2 = vertex_offset + (ring + 1) * segments + next_seg
                i3 = vertex_offset + (ring + 1) * segments + seg

                faces.append(np.array([i0, i1, i2]))
                faces.append(np.array([i0, i2, i3]))

        return (
            np.array(vertices),
            np.array(faces, dtype=int),
            np.array(uvs),
            np.array(normals),
        )


class WhiskerGenerator:
    """Generates whiskers for the creature's face."""

    def __init__(
        self,
        whisker_type: WhiskerType,
        count: int = 6,
        length: float = 0.3,
        thickness: float = 0.003,
        curve_amount: float = 0.3,
    ):
        """Initialize whisker generator.

        Args:
            whisker_type: Type of whiskers
            count: Number of whiskers per side
            length: Base whisker length
            thickness: Base whisker thickness
            curve_amount: How much whiskers curve
        """
        self.whisker_type = whisker_type
        self.count = max(0, count)
        self.length = max(0.01, length)
        self.thickness = max(0.001, thickness)
        self.curve_amount = max(0.0, curve_amount)

    def generate(
        self,
        snout_position: Optional[np.ndarray] = None,
        snout_direction: Optional[np.ndarray] = None,
        seed: Optional[int] = None,
    ) -> WhiskerResult:
        """Generate whisker geometry.

        Args:
            snout_position: Position of snout base
            snout_direction: Direction snout is facing
            seed: Random seed for variation

        Returns:
            WhiskerResult with whisker data and geometry
        """
        if seed is not None:
            np.random.seed(seed)

        # Default snout position
        if snout_position is None:
            snout_position = np.array([0.0, 0.0, 0.0])
        if snout_direction is None:
            snout_direction = np.array([0.0, 1.0, 0.0])

        whiskers: List[WhiskerData] = []
        all_vertices: List[np.ndarray] = []
        all_faces: List[np.ndarray] = []
        all_uvs: List[np.ndarray] = []
        all_normals: List[np.ndarray] = []

        # Generate whiskers on both sides
        vertex_offset = 0
        for side in [-1, 1]:  # Left and right
            for i in range(self.count):
                # Calculate whisker position on snout
                t = (i + 0.5) / self.count  # Distribute along snout

                # Position along snout side
                lateral_offset = side * 0.1  # Side of snout
                forward_offset = t * 0.2  # Forward on snout

                pos = snout_position + (
                    lateral_offset * np.array([1, 0, 0]) +
                    forward_offset * snout_direction
                )

                # Direction: mostly outward with slight forward curve
                base_direction = np.array([side * 0.7, 0.3, 0.0])
                base_direction = base_direction / np.linalg.norm(base_direction)

                # Add variation
                length_var = self.length * (1.0 + np.random.uniform(-0.2, 0.2))
                thick_var = self.thickness * (1.0 + np.random.uniform(-0.1, 0.1))
                curve_var = self.curve_amount * (1.0 + np.random.uniform(-0.3, 0.3))

                # Generate whisker geometry
                vertices, faces, uvs, normals = self._generate_whisker_geometry(
                    pos, base_direction, length_var, thick_var, curve_var, vertex_offset
                )

                whisker = WhiskerData(
                    position=pos.copy(),
                    direction=base_direction.copy(),
                    length=length_var,
                    thickness=thick_var,
                    curve_amount=curve_var,
                    whisker_type=self.whisker_type,
                )
                whiskers.append(whisker)

                all_vertices.append(vertices)
                all_faces.append(faces)
                all_uvs.append(uvs)
                all_normals.append(normals)

                vertex_offset += len(vertices)

        if len(all_vertices) == 0:
            return WhiskerResult(
                whiskers=[],
                vertices=np.zeros((0, 3)),
                faces=np.zeros((0, 3), dtype=int),
                uvs=np.zeros((0, 2)),
                normals=np.zeros((0, 3)),
            )

        return WhiskerResult(
            whiskers=whiskers,
            vertices=np.vstack(all_vertices),
            faces=np.vstack(all_faces),
            uvs=np.vstack(all_uvs),
            normals=np.vstack(all_normals),
        )

    def _generate_whisker_geometry(
        self,
        position: np.ndarray,
        direction: np.ndarray,
        length: float,
        thickness: float,
        curve_amount: float,
        vertex_offset: int,
        segments: int = 8,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Generate geometry for a single whisker."""
        vertices = []
        faces = []
        uvs = []
        normals = []

        # Create coordinate frame
        direction = direction / np.linalg.norm(direction)

        if abs(direction[2]) < 0.9:
            perp1 = np.cross(direction, np.array([0, 0, 1]))
        else:
            perp1 = np.cross(direction, np.array([1, 0, 0]))
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(direction, perp1)

        # Generate curved whisker
        rings = 6
        sides = 4  # Square cross-section for whiskers

        for ring in range(rings + 1):
            t = ring / rings

            # Curved position along whisker
            curve_offset = curve_amount * np.sin(t * np.pi) * perp2
            ring_length = t * length
            base_pos = position + ring_length * direction + curve_offset

            # Taper thickness
            ring_thickness = thickness * (1.0 - t * 0.8)

            for side in range(sides):
                angle = 2 * np.pi * side / sides + np.pi / 4
                local_pos = (
                    ring_thickness * np.cos(angle) * perp1 +
                    ring_thickness * np.sin(angle) * perp2
                )

                vertices.append(base_pos + local_pos)

                # UV
                u = side / sides
                v = t
                uvs.append(np.array([u, v]))

                # Normal (approximate)
                normal = local_pos
                if np.linalg.norm(normal) > 0.001:
                    normal = normal / np.linalg.norm(normal)
                normals.append(normal)

        # Generate faces
        for ring in range(rings):
            for side in range(sides):
                next_side = (side + 1) % sides

                i0 = vertex_offset + ring * sides + side
                i1 = vertex_offset + ring * sides + next_side
                i2 = vertex_offset + (ring + 1) * sides + next_side
                i3 = vertex_offset + (ring + 1) * sides + side

                faces.append(np.array([i0, i1, i2]))
                faces.append(np.array([i0, i2, i3]))

        return (
            np.array(vertices),
            np.array(faces, dtype=int),
            np.array(uvs),
            np.array(normals),
        )


class ClawGenerator:
    """Generates claws/talons for the creature's limbs."""

    def __init__(
        self,
        claw_type: ClawType,
        count_per_foot: int = 4,
        length: float = 0.08,
        width: float = 0.015,
        curve_amount: float = 0.4,
    ):
        """Initialize claw generator.

        Args:
            claw_type: Type of claws
            count_per_foot: Number of claws per foot
            length: Base claw length
            width: Base claw width
            curve_amount: How much claws curve
        """
        self.claw_type = claw_type
        self.count_per_foot = max(0, count_per_foot)
        self.length = max(0.01, length)
        self.width = max(0.005, width)
        self.curve_amount = max(0.0, curve_amount)

    def generate(
        self,
        foot_positions: Optional[List[Tuple[np.ndarray, np.ndarray]]] = None,
        seed: Optional[int] = None,
    ) -> ClawResult:
        """Generate claw geometry.

        Args:
            foot_positions: List of (position, direction) for each foot
            seed: Random seed for variation

        Returns:
            ClawResult with claw data and geometry
        """
        if seed is not None:
            np.random.seed(seed)

        # Default foot positions
        if foot_positions is None:
            foot_positions = self._generate_default_foot_positions()

        claws: List[ClawData] = []
        all_vertices: List[np.ndarray] = []
        all_faces: List[np.ndarray] = []
        all_uvs: List[np.ndarray] = []
        all_normals: List[np.ndarray] = []

        vertex_offset = 0
        for foot_pos, foot_dir in foot_positions:
            for i in range(self.count_per_foot):
                # Distribute claws across foot
                spread = (i - (self.count_per_foot - 1) / 2) / self.count_per_foot

                # Claw position on foot
                if abs(foot_dir[0]) > abs(foot_dir[1]):
                    lateral = np.array([0, spread * 0.03, 0])
                else:
                    lateral = np.array([spread * 0.03, 0, 0])

                claw_pos = foot_pos + lateral

                # Claw direction: down and slightly forward with curve
                base_direction = foot_dir.copy()
                base_direction = base_direction / np.linalg.norm(base_direction)

                # Add variation
                length_var = self.length * (1.0 + np.random.uniform(-0.15, 0.15))
                width_var = self.width * (1.0 + np.random.uniform(-0.1, 0.1))
                curve_var = self.curve_amount * (1.0 + np.random.uniform(-0.2, 0.2))

                # Center claw is usually larger
                if i == self.count_per_foot // 2:
                    length_var *= 1.2

                # Generate claw geometry
                vertices, faces, uvs, normals = self._generate_claw_geometry(
                    claw_pos, base_direction, length_var, width_var, curve_var, vertex_offset
                )

                claw = ClawData(
                    position=claw_pos.copy(),
                    direction=base_direction.copy(),
                    length=length_var,
                    width=width_var,
                    curve_amount=curve_var,
                    claw_type=self.claw_type,
                )
                claws.append(claw)

                all_vertices.append(vertices)
                all_faces.append(faces)
                all_uvs.append(uvs)
                all_normals.append(normals)

                vertex_offset += len(vertices)

        if len(all_vertices) == 0:
            return ClawResult(
                claws=[],
                vertices=np.zeros((0, 3)),
                faces=np.zeros((0, 3), dtype=int),
                uvs=np.zeros((0, 2)),
                normals=np.zeros((0, 3)),
            )

        return ClawResult(
            claws=claws,
            vertices=np.vstack(all_vertices),
            faces=np.vstack(all_faces),
            uvs=np.vstack(all_uvs),
            normals=np.vstack(all_normals),
        )

    def _generate_default_foot_positions(self) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Generate default foot positions for testing."""
        positions = []
        # 4 feet (front left, front right, back left, back right)
        for x in [-0.5, 0.5]:
            for y in [-0.5, 0.5]:
                pos = np.array([x, y, 0.0])
                direction = np.array([0, 0, -1])  # Pointing down
                positions.append((pos, direction))
        return positions

    def _generate_claw_geometry(
        self,
        position: np.ndarray,
        direction: np.ndarray,
        length: float,
        width: float,
        curve_amount: float,
        vertex_offset: int,
        segments: int = 6,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Generate geometry for a single claw."""
        vertices = []
        faces = []
        uvs = []
        normals = []

        # Create coordinate frame
        direction = direction / np.linalg.norm(direction)

        if abs(direction[2]) < 0.9:
            perp1 = np.cross(direction, np.array([0, 0, 1]))
        else:
            perp1 = np.cross(direction, np.array([1, 0, 0]))
        perp1 = perp1 / np.linalg.norm(perp1)
        perp2 = np.cross(direction, perp1)

        # Generate curved claw
        rings = 5
        for ring in range(rings + 1):
            t = ring / rings

            # Curved position along claw
            curve_offset = curve_amount * t * t * perp2  # Parabolic curve
            ring_length = t * length
            base_pos = position + ring_length * direction + curve_offset

            # Taper width
            ring_width = width * (1.0 - t * 0.85)

            for seg in range(segments):
                angle = 2 * np.pi * seg / segments
                local_pos = (
                    ring_width * np.cos(angle) * perp1 +
                    ring_width * np.sin(angle) * perp2
                )

                vertices.append(base_pos + local_pos)

                # UV
                u = seg / segments
                v = t
                uvs.append(np.array([u, v]))

                # Normal
                normal = local_pos
                if np.linalg.norm(normal) > 0.001:
                    normal = normal / np.linalg.norm(normal)
                normals.append(normal)

        # Generate faces
        for ring in range(rings):
            for seg in range(segments):
                next_seg = (seg + 1) % segments

                i0 = vertex_offset + ring * segments + seg
                i1 = vertex_offset + ring * segments + next_seg
                i2 = vertex_offset + (ring + 1) * segments + next_seg
                i3 = vertex_offset + (ring + 1) * segments + seg

                faces.append(np.array([i0, i1, i2]))
                faces.append(np.array([i0, i2, i3]))

        return (
            np.array(vertices),
            np.array(faces, dtype=int),
            np.array(uvs),
            np.array(normals),
        )


class DetailGenerator:
    """Combined generator for all detail features."""

    def __init__(
        self,
        tooth_type: ToothType = ToothType.CONICAL,
        whisker_type: WhiskerType = WhiskerType.THIN,
        claw_type: ClawType = ClawType.SHARP,
        tooth_count: int = 20,
        whisker_count: int = 6,
        claw_count_per_foot: int = 4,
    ):
        """Initialize detail generator.

        Args:
            tooth_type: Type of teeth
            whisker_type: Type of whiskers
            claw_type: Type of claws
            tooth_count: Number of teeth
            whisker_count: Whiskers per side
            claw_count_per_foot: Claws per foot
        """
        self.teeth_gen = TeethGenerator(tooth_type, count=tooth_count)
        self.whisker_gen = WhiskerGenerator(whisker_type, count=whisker_count)
        self.claw_gen = ClawGenerator(claw_type, count_per_foot=claw_count_per_foot)

    def generate(
        self,
        mouth_positions: Optional[List[Tuple[np.ndarray, np.ndarray]]] = None,
        snout_position: Optional[np.ndarray] = None,
        snout_direction: Optional[np.ndarray] = None,
        foot_positions: Optional[List[Tuple[np.ndarray, np.ndarray]]] = None,
        seed: Optional[int] = None,
    ) -> DetailResult:
        """Generate all detail features.

        Args:
            mouth_positions: Positions for teeth along mouth
            snout_position: Position for whisker base
            snout_direction: Direction snout faces
            foot_positions: Positions for claw attachment
            seed: Random seed

        Returns:
            DetailResult with all feature geometry
        """
        teeth_result = self.teeth_gen.generate(mouth_positions, seed)
        whisker_result = self.whisker_gen.generate(
            snout_position, snout_direction,
            seed + 1 if seed is not None else None
        )
        claw_result = self.claw_gen.generate(
            foot_positions,
            seed + 2 if seed is not None else None
        )

        return DetailResult(
            teeth_result=teeth_result,
            whisker_result=whisker_result,
            claw_result=claw_result,
        )


# Convenience functions
def generate_teeth(
    tooth_type: ToothType = ToothType.CONICAL,
    count: int = 20,
    mouth_positions: Optional[List[Tuple[np.ndarray, np.ndarray]]] = None,
    seed: Optional[int] = None,
) -> TeethResult:
    """Generate teeth with default settings."""
    gen = TeethGenerator(tooth_type, count=count)
    return gen.generate(mouth_positions, seed)


def generate_whiskers(
    whisker_type: WhiskerType = WhiskerType.THIN,
    count: int = 6,
    snout_position: Optional[np.ndarray] = None,
    snout_direction: Optional[np.ndarray] = None,
    seed: Optional[int] = None,
) -> WhiskerResult:
    """Generate whiskers with default settings."""
    gen = WhiskerGenerator(whisker_type, count=count)
    return gen.generate(snout_position, snout_direction, seed)


def generate_claws(
    claw_type: ClawType = ClawType.SHARP,
    count_per_foot: int = 4,
    foot_positions: Optional[List[Tuple[np.ndarray, np.ndarray]]] = None,
    seed: Optional[int] = None,
) -> ClawResult:
    """Generate claws with default settings."""
    gen = ClawGenerator(claw_type, count_per_foot=count_per_foot)
    return gen.generate(foot_positions, seed)


def generate_details(
    tooth_type: ToothType = ToothType.CONICAL,
    whisker_type: WhiskerType = WhiskerType.THIN,
    claw_type: ClawType = ClawType.SHARP,
    seed: Optional[int] = None,
) -> DetailResult:
    """Generate all detail features with default settings."""
    gen = DetailGenerator(tooth_type, whisker_type, claw_type)
    return gen.generate(seed=seed)
