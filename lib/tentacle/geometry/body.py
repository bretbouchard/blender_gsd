"""Tentacle body generation from curves."""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np

try:
    import bpy
    from bpy.types import Object, Curve, Mesh
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    Object = None
    Curve = None
    Mesh = None

from ..types import TentacleConfig
from .taper import calculate_taper_radii, TaperProfile
from .segments import distribute_segment_points


@dataclass
class TentacleResult:
    """Result of tentacle generation."""

    object: Optional["Object"] = None     # Blender mesh object
    curve: Optional["Object"] = None      # Base curve (for animation)
    mesh: Optional["Mesh"] = None         # Mesh data

    # Metadata
    vertex_count: int = 0
    face_count: int = 0
    length: float = 0.0
    base_radius: float = 0.0
    tip_radius: float = 0.0

    # For testing without Blender
    vertices: Optional[np.ndarray] = None
    faces: Optional[np.ndarray] = None


class TentacleBodyGenerator:
    """Generate procedural tentacle bodies from curves."""

    def __init__(self, config: TentacleConfig):
        """
        Initialize generator with configuration.

        Args:
            config: Tentacle geometry configuration
        """
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not 0.1 <= self.config.length <= 3.0:
            raise ValueError(f"Length must be 0.1-3.0m, got {self.config.length}")
        if not 10 <= self.config.segments <= 50:
            raise ValueError(f"Segments must be 10-50, got {self.config.segments}")
        if self.config.tip_diameter >= self.config.base_diameter:
            raise ValueError("Tip diameter must be smaller than base diameter")

    def generate(self, name: Optional[str] = None) -> TentacleResult:
        """
        Generate tentacle mesh.

        Args:
            name: Override object name

        Returns:
            TentacleResult with mesh and metadata
        """
        name = name or self.config.name

        if BLENDER_AVAILABLE:
            return self._generate_blender(name)
        else:
            return self._generate_numpy(name)

    def _generate_blender(self, name: str) -> TentacleResult:
        """Generate tentacle using Blender API."""
        curve_obj = None
        mesh_obj = None

        try:
            # Create curve
            curve_obj = self._create_base_curve(name)
            curve = curve_obj.data

            # Apply taper profile
            self._apply_taper_to_curve(curve)

            # Apply twist if specified
            if self.config.twist != 0.0:
                self._apply_twist_to_curve(curve)

            # Resample for segments
            self._resample_curve(curve)

            # Convert to mesh
            mesh_obj = self._curve_to_mesh(curve_obj, f"{name}_mesh")

            # Apply subdivision
            if self.config.subdivision_levels > 0:
                self._apply_subdivision(mesh_obj)

            # Calculate metadata
            mesh = mesh_obj.data
            result = TentacleResult(
                object=mesh_obj,
                curve=curve_obj,
                mesh=mesh,
                vertex_count=len(mesh.vertices),
                face_count=len(mesh.polygons),
                length=self.config.length,
                base_radius=self.config.base_diameter / 2,
                tip_radius=self.config.tip_diameter / 2,
            )

            return result

        except Exception as e:
            # Clean up created objects on failure
            if curve_obj is not None:
                bpy.data.objects.remove(curve_obj)
            if mesh_obj is not None:
                bpy.data.objects.remove(mesh_obj)
            raise RuntimeError(f"Failed to generate tentacle '{name}': {e}") from e

    def _generate_numpy(self, name: str) -> TentacleResult:
        """Generate tentacle geometry as numpy arrays (for testing)."""
        # Calculate taper radii
        radii = calculate_taper_radii(
            self.config.segments + 1,
            self.config.base_diameter / 2,
            self.config.tip_diameter / 2,
            self.config.taper_profile,
        )

        # Generate curve points
        t = np.linspace(0, 1, self.config.segments + 1)
        z = t * self.config.length

        # Create circle vertices at each point
        resolution = self.config.curve_resolution
        angles = np.linspace(0, 2 * np.pi, resolution, endpoint=False)

        # Calculate twist per segment
        twist_radians = np.radians(self.config.twist)

        vertices = []
        faces = []

        for i, (zi, ri) in enumerate(zip(z, radii)):
            # Apply twist along length
            twist_at_point = twist_radians * t[i]
            for angle in angles:
                twisted_angle = angle + twist_at_point
                x = ri * np.cos(twisted_angle)
                y = ri * np.sin(twisted_angle)
                vertices.append([x, y, zi])

        vertices = np.array(vertices)

        # Create faces (quad strips)
        for i in range(self.config.segments):
            for j in range(resolution):
                j_next = (j + 1) % resolution
                v1 = i * resolution + j
                v2 = i * resolution + j_next
                v3 = (i + 1) * resolution + j_next
                v4 = (i + 1) * resolution + j
                faces.append([v1, v2, v3, v4])

        faces = np.array(faces)

        return TentacleResult(
            vertices=vertices,
            faces=faces,
            vertex_count=len(vertices),
            face_count=len(faces),
            length=self.config.length,
            base_radius=self.config.base_diameter / 2,
            tip_radius=self.config.tip_diameter / 2,
        )

    def _create_base_curve(self, name: str) -> "Object":
        """Create base Bézier curve for tentacle."""
        curve_data = bpy.data.curves.new(name=f"{name}_curve", type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = self.config.curve_resolution

        # Create spline
        spline = curve_data.splines.new('BEZIER')

        # Add control points (start, middle, end)
        spline.bezier_points.add(2)  # 3 points total

        # Set point positions
        spline.bezier_points[0].co = (0, 0, 0)
        spline.bezier_points[1].co = (0, 0, self.config.length * 0.5)
        spline.bezier_points[2].co = (0, 0, self.config.length)

        # Set handles for smooth curve
        for point in spline.bezier_points:
            point.handle_left_type = 'AUTO'
            point.handle_right_type = 'AUTO'

        # Create object
        curve_obj = bpy.data.objects.new(name, curve_data)
        bpy.context.collection.objects.link(curve_obj)

        return curve_obj

    def _apply_taper_to_curve(self, curve: "Curve") -> None:
        """Apply taper profile to curve radii."""
        spline = curve.splines[0]
        point_count = len(spline.bezier_points)

        radii = calculate_taper_radii(
            point_count,
            self.config.base_diameter / 2,
            self.config.tip_diameter / 2,
            self.config.taper_profile,
        )

        for i, point in enumerate(spline.bezier_points):
            point.radius = radii[i]

    def _apply_twist_to_curve(self, curve: "Curve") -> None:
        """Apply twist rotation along the curve length.

        Uses Blender's built-in twist smoothing for natural-looking results.
        Twist is applied as a linear interpolation from base (0°) to tip (twist°).
        """
        spline = curve.splines[0]
        point_count = len(spline.bezier_points)
        twist_radians = np.radians(self.config.twist)

        for i, point in enumerate(spline.bezier_points):
            # Linear interpolation of twist along length
            t = i / (point_count - 1) if point_count > 1 else 0.0
            point.tilt = twist_radians * t

    def _resample_curve(self, curve: "Curve") -> None:
        """Resample curve to match segment count."""
        # Use path conversion for segment distribution
        curve.resolution_u = self.config.segments

    # Ratio of curve_resolution used for bevel (quarter resolution provides good
    # balance between smoothness and vertex count for procedural geometry)
    BEVEL_RESOLUTION_RATIO = 4

    def _curve_to_mesh(self, curve_obj: "Object", name: str) -> "Object":
        """Convert curve to mesh.

        Bevel resolution is set to curve_resolution // BEVEL_RESOLUTION_RATIO
        to balance smoothness with vertex count. For a curve_resolution of 64,
        this yields a bevel_resolution of 16 segments around the circumference.
        """
        # Add bevel depth for tube shape
        curve = curve_obj.data
        curve.bevel_depth = 1.0  # Full radius
        curve.bevel_resolution = self.config.curve_resolution // self.BEVEL_RESOLUTION_RATIO

        # Convert to mesh
        bpy.context.view_layer.objects.active = curve_obj
        curve_obj.select_set(True)
        bpy.ops.object.convert(target='MESH')

        mesh_obj = bpy.context.active_object
        mesh_obj.name = name

        return mesh_obj

    def _apply_subdivision(self, mesh_obj: "Object") -> None:
        """Apply subdivision surface modifier."""
        mod = mesh_obj.modifiers.new(name="Subdivision", type='SUBSURF')
        mod.levels = self.config.subdivision_levels
        mod.render_levels = self.config.subdivision_levels


def create_tentacle(config: TentacleConfig, name: Optional[str] = None) -> TentacleResult:
    """
    Convenience function to create a tentacle.

    Args:
        config: Tentacle configuration
        name: Optional object name

    Returns:
        TentacleResult with mesh and metadata
    """
    generator = TentacleBodyGenerator(config)
    return generator.generate(name)
