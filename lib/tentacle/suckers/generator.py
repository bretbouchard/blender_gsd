"""Sucker geometry generation."""

from typing import Optional, List, Tuple
import numpy as np

try:
    import bpy
    from bpy.types import Object, Mesh
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = None
    Mesh = None

from .types import SuckerConfig, SuckerInstance, SuckerResult
from .placement import calculate_sucker_positions, calculate_sucker_mesh_size


class SuckerGenerator:
    """Generate procedural sucker geometry."""

    def __init__(self, config: SuckerConfig):
        """
        Initialize generator with configuration.

        Args:
            config: Sucker configuration
        """
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not 2 <= self.config.rows <= 8:
            raise ValueError(f"Rows must be 2-8, got {self.config.rows}")
        if not 4 <= self.config.columns <= 12:
            raise ValueError(f"Columns must be 4-12, got {self.config.columns}")

    def generate_for_tentacle(
        self,
        tentacle_length: float,
        tentacle_radius_func,
        name: str = "Suckers",
    ) -> SuckerResult:
        """
        Generate suckers for a tentacle.

        Args:
            tentacle_length: Total tentacle length
            tentacle_radius_func: Function(t) -> radius at position t
            name: Base name for generated objects

        Returns:
            SuckerResult with sucker data
        """
        if not self.config.enabled:
            return SuckerResult()

        # Calculate positions
        suckers = calculate_sucker_positions(
            self.config,
            tentacle_length,
            tentacle_radius_func,
        )

        result = SuckerResult(suckers=suckers, total_count=len(suckers))

        if BLENDER_AVAILABLE and hasattr(bpy, 'data'):
            return self._generate_blender(result, name)
        else:
            return self._generate_numpy(result)

    def _generate_blender(self, result: SuckerResult, name: str) -> SuckerResult:
        """Generate sucker meshes using Blender API."""
        # Create collection for suckers
        collection = bpy.data.collections.new(f"{name}_Collection")
        bpy.context.collection.children.link(collection)

        total_vertices = 0
        total_faces = 0

        for i, sucker in enumerate(result.suckers):
            mesh_obj = self._create_single_sucker(sucker, f"{name}_{i:03d}")
            if mesh_obj:
                collection.objects.link(mesh_obj)
                total_vertices += len(mesh_obj.data.vertices)
                total_faces += len(mesh_obj.data.polygons)

        result.vertex_count = total_vertices
        result.face_count = total_faces

        return result

    def _generate_numpy(self, result: SuckerResult) -> SuckerResult:
        """Generate sucker geometry as numpy arrays (for testing)."""
        all_vertices = []
        all_faces = []
        vertex_offset = 0

        for sucker in result.suckers:
            vertices, faces = self._create_sucker_mesh_numpy(sucker)
            all_vertices.extend(vertices)

            # Offset face indices
            for face in faces:
                all_faces.append([v + vertex_offset for v in face])

            vertex_offset += len(vertices)

        result.vertices = np.array(all_vertices) if all_vertices else np.array([])
        # Keep faces as list since they may have varying sizes (triangles vs quads)
        result.faces = all_faces
        result.vertex_count = len(all_vertices)
        result.face_count = len(all_faces)

        return result

    def _create_single_sucker(
        self,
        sucker: SuckerInstance,
        name: str,
    ) -> Optional["Object"]:
        """Create a single sucker mesh object in Blender."""
        if not BLENDER_AVAILABLE or not hasattr(bpy, 'data'):
            return None

        # Create mesh
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        # Generate cup geometry using config resolution
        vertices, faces = self._create_sucker_mesh_geometry(
            sucker.size,
            self.config.cup_depth,
            self.config.rim_width,
            self.config.mesh_resolution,
        )

        # Create mesh data
        mesh.from_pydata(vertices, [], faces)

        # Position and rotate
        obj.location = sucker.position

        # Simple rotation - set to identity for now (will be handled in Blender)
        obj.rotation_euler = (0, 0, 0)

        return obj

    def _create_sucker_mesh_numpy(
        self,
        sucker: SuckerInstance,
    ) -> Tuple[List, List]:
        """Create sucker mesh as numpy-compatible data."""
        # Use config resolution for consistency
        return self._create_sucker_mesh_geometry(
            sucker.size,
            self.config.cup_depth,
            self.config.rim_width,
            self.config.mesh_resolution,
        )

    def _create_sucker_mesh_geometry(
        self,
        size: float,
        cup_depth: float,
        rim_width: float,
        resolution: int,
    ) -> Tuple[List[List[float]], List[List[int]]]:
        """
        Create cup-shaped mesh geometry.

        Args:
            size: Sucker diameter
            cup_depth: Depth of cup
            rim_width: Width of rim
            resolution: Number of vertices around circumference

        Returns:
            (vertices, faces) tuple
        """
        vertices = []
        faces = []

        radius = size / 2
        inner_radius = radius - rim_width

        # Create cup rings (from rim to center)
        num_rings = max(4, resolution // 4)

        for ring in range(num_rings):
            t = ring / (num_rings - 1)  # 0 at rim, 1 at center

            # Radius decreases toward center
            ring_radius = inner_radius * (1 - t)

            # Depth curve (hemisphere-like)
            if t < 0.5:
                # Outer half - goes down
                depth = cup_depth * (1 - (1 - 2*t) ** 2)
            else:
                # Inner half - comes back up slightly
                depth = cup_depth * (1 - (2*t - 1) ** 2 * 0.2)

            # Create ring vertices
            for i in range(resolution):
                angle = 2 * np.pi * i / resolution
                x = ring_radius * np.cos(angle)
                y = ring_radius * np.sin(angle)
                z = -depth  # Negative = into surface

                vertices.append([x, y, z])

        # Add center vertex
        center_idx = len(vertices)
        vertices.append([0, 0, -cup_depth])

        # Create faces (quad strips + center fan)
        for ring in range(num_rings - 1):
            for i in range(resolution):
                next_i = (i + 1) % resolution

                v1 = ring * resolution + i
                v2 = ring * resolution + next_i
                v3 = (ring + 1) * resolution + next_i
                v4 = (ring + 1) * resolution + i

                faces.append([v1, v2, v3, v4])

        # Center fan (last ring to center)
        last_ring_start = (num_rings - 1) * resolution
        for i in range(resolution):
            next_i = (i + 1) % resolution
            v1 = last_ring_start + i
            v2 = last_ring_start + next_i
            faces.append([v1, v2, center_idx])

        # Add rim ring (outermost, at z=0)
        rim_start = len(vertices)
        for i in range(resolution):
            angle = 2 * np.pi * i / resolution
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = 0
            vertices.append([x, y, z])

        # Connect rim to first ring
        for i in range(resolution):
            next_i = (i + 1) % resolution
            v1 = rim_start + i
            v2 = rim_start + next_i
            v3 = next_i
            v4 = i
            faces.append([v1, v2, v3, v4])

        return vertices, faces


def generate_suckers(
    config: SuckerConfig,
    tentacle_length: float,
    tentacle_radius_func,
    name: str = "Suckers",
) -> SuckerResult:
    """
    Convenience function to generate suckers for a tentacle.

    Args:
        config: Sucker configuration
        tentacle_length: Total tentacle length
        tentacle_radius_func: Function(t) -> radius at position t
        name: Base name for generated objects

    Returns:
        SuckerResult with sucker data
    """
    generator = SuckerGenerator(config)
    return generator.generate_for_tentacle(tentacle_length, tentacle_radius_func, name)
