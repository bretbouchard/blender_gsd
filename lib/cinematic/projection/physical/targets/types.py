"""
Target types and dataclasses for projection surface presets.

Provides types for defining projection targets (planar, multi-surface, curved)
with material properties and calibration metadata.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class TargetType(Enum):
    """Type of projection target."""
    PLANAR = "planar"              # Single flat surface
    MULTI_SURFACE = "multi_surface"  # Multiple connected surfaces
    CURVED = "curved"              # Curved surface (cylinder, dome)
    IRREGULAR = "irregular"        # Complex geometry


class SurfaceMaterial(Enum):
    """Surface material type for brightness/color compensation."""
    WHITE_PAINT = "white_paint"    # Standard white (albedo ~0.85)
    GRAY_PAINT = "gray_paint"      # Gray (albedo ~0.5)
    DARK_PAINT = "dark_paint"      # Dark (albedo ~0.2)
    PROJECTOR_SCREEN = "screen"    # Specialized screen (albedo ~0.95)
    FABRIC = "fabric"              # Fabric surface
    METAL = "metal"                # Metallic surface
    WOOD = "wood"                  # Wood surface
    GLASS = "glass"                # Glass surface
    CONCRETE = "concrete"          # Concrete surface
    BRICK = "brick"                # Brick surface


@dataclass
class ProjectionSurface:
    """
    Single projection surface within a target.

    Attributes:
        name: Surface identifier
        surface_type: Type of surface geometry
        position: 3D position offset (x, y, z) in meters
        dimensions: (width, height) in meters
        bounding_box: ((min_x, min_y, min_z), (max_x, max_y, max_z))
        surface_normal: Normal vector (nx, ny, nz)
        area_m2: Surface area in square meters
        material: Surface material type
        albedo: Surface reflectivity (0-1)
        glossiness: Surface glossiness (0-1)
        calibration_points: List of 3D calibration points
        is_calibrated: Whether surface has been calibrated
        calibration_error_mm: Calibration error in millimeters
    """
    name: str
    surface_type: TargetType

    # Geometry
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    dimensions: Tuple[float, float] = (1.0, 1.0)  # (width, height)
    bounding_box: Tuple[Tuple[float, float, float], Tuple[float, float, float]] = (
        (-0.5, 0.0, -0.5), (0.5, 0.0, 0.5)
    )
    surface_normal: Tuple[float, float, float] = (0.0, 1.0, 0.0)
    area_m2: float = 1.0

    # Material properties
    material: SurfaceMaterial = SurfaceMaterial.WHITE_PAINT
    albedo: float = 0.85
    glossiness: float = 0.1

    # Calibration
    calibration_points: List[Tuple[float, float, float]] = field(default_factory=list)
    is_calibrated: bool = False
    calibration_error_mm: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'surface_type': self.surface_type.value,
            'position': list(self.position),
            'dimensions': list(self.dimensions),
            'bounding_box': [list(self.bounding_box[0]), list(self.bounding_box[1])],
            'surface_normal': list(self.surface_normal),
            'area_m2': self.area_m2,
            'material': self.material.value,
            'albedo': self.albedo,
            'glossiness': self.glossiness,
            'calibration_points': [list(p) for p in self.calibration_points],
            'is_calibrated': self.is_calibrated,
            'calibration_error_mm': self.calibration_error_mm,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectionSurface':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            surface_type=TargetType(data['surface_type']),
            position=tuple(data.get('position', (0.0, 0.0, 0.0))),
            dimensions=tuple(data.get('dimensions', (1.0, 1.0))),
            bounding_box=(
                tuple(data.get('bounding_box', ((-0.5, 0.0, -0.5),))[0]),
                tuple(data.get('bounding_box', (None, (0.5, 0.0, 0.5)))[1])
            ) if isinstance(data.get('bounding_box'), list) else (
                tuple(data.get('bounding_box', ((-0.5, 0.0, -0.5), (0.5, 0.0, 0.5)))[0]),
                tuple(data.get('bounding_box', ((-0.5, 0.0, -0.5), (0.5, 0.0, 0.5)))[1])
            ),
            surface_normal=tuple(data.get('surface_normal', (0.0, 1.0, 0.0))),
            area_m2=data.get('area_m2', 1.0),
            material=SurfaceMaterial(data.get('material', 'white_paint')),
            albedo=data.get('albedo', 0.85),
            glossiness=data.get('glossiness', 0.1),
            calibration_points=[tuple(p) for p in data.get('calibration_points', [])],
            is_calibrated=data.get('is_calibrated', False),
            calibration_error_mm=data.get('calibration_error_mm', 0.0),
        )

    def compute_default_calibration_points(self) -> List[Tuple[float, float, float]]:
        """Compute default 3-point calibration points for this surface."""
        x, y, z = self.position
        w, h = self.dimensions

        # Default: bottom-left, bottom-right, top-left
        return [
            (x - w/2, y, z - h/2),  # Bottom-left
            (x + w/2, y, z - h/2),  # Bottom-right
            (x - w/2, y, z + h/2),  # Top-left
        ]


@dataclass
class ProjectionTarget:
    """
    Complete projection target configuration.

    A target represents a real-world projection surface or set of surfaces
    (e.g., garage door, room walls, building facade).

    Attributes:
        name: Target identifier
        description: Human-readable description
        target_type: Type of target (planar, multi-surface, etc.)
        surfaces: List of projection surfaces
        width_m: Overall width in meters
        height_m: Overall height in meters
        depth_m: Overall depth in meters (0 for planar)
        recommended_calibration: Recommended calibration method
        preset_measurements: Named measurements for quick reference
    """
    name: str
    description: str
    target_type: TargetType

    # Surfaces
    surfaces: List[ProjectionSurface] = field(default_factory=list)

    # Overall dimensions
    width_m: float = 1.0
    height_m: float = 1.0
    depth_m: float = 0.0  # 0 for planar

    # Recommended calibration type
    recommended_calibration: str = "three_point"

    # Preset measurements (for common targets)
    preset_measurements: Dict[str, float] = field(default_factory=dict)

    def get_total_area(self) -> float:
        """Get total projection area in square meters."""
        return sum(s.area_m2 for s in self.surfaces)

    def get_primary_surface(self) -> Optional[ProjectionSurface]:
        """Get the primary (largest) surface."""
        if not self.surfaces:
            return None
        return max(self.surfaces, key=lambda s: s.area_m2)

    def get_all_calibration_points(self) -> List[Tuple[float, float, float]]:
        """Get all calibration points from all surfaces."""
        points = []
        for surface in self.surfaces:
            if surface.calibration_points:
                points.extend(surface.calibration_points)
            else:
                points.extend(surface.compute_default_calibration_points())
        return points

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'target_type': self.target_type.value,
            'surfaces': [s.to_dict() for s in self.surfaces],
            'dimensions': {
                'width_m': self.width_m,
                'height_m': self.height_m,
                'depth_m': self.depth_m,
            },
            'recommended_calibration': self.recommended_calibration,
            'preset_measurements': self.preset_measurements,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectionTarget':
        """Create from dictionary."""
        dims = data.get('dimensions', {})
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            target_type=TargetType(data['target_type']),
            surfaces=[ProjectionSurface.from_dict(s) for s in data.get('surfaces', [])],
            width_m=dims.get('width_m', 1.0),
            height_m=dims.get('height_m', 1.0),
            depth_m=dims.get('depth_m', 0.0),
            recommended_calibration=data.get('recommended_calibration', 'three_point'),
            preset_measurements=data.get('preset_measurements', {}),
        )


@dataclass
class TargetGeometryResult:
    """
    Result of target geometry generation.

    Contains the generated Blender objects and UV layers.

    Attributes:
        object: Main Blender object (or parent empty for multi-surface)
        surfaces: Dict mapping surface names to Blender objects
        uv_layers: Dict mapping UV layer names to UV layer data
        errors: List of errors encountered during generation
        warnings: List of warnings
    """
    object: Any = None  # bpy.types.Object when in Blender
    surfaces: Dict[str, Any] = field(default_factory=dict)
    uv_layers: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if geometry was generated successfully."""
        return len(self.errors) == 0 and self.object is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (without Blender objects)."""
        return {
            'success': self.success,
            'surface_names': list(self.surfaces.keys()),
            'uv_layer_names': list(self.uv_layers.keys()),
            'errors': self.errors,
            'warnings': self.warnings,
        }


# Preset targets for common use cases

PLANAR_2X2M = ProjectionTarget(
    name="planar_2x2m",
    description="Standard 2m x 2m planar projection surface",
    target_type=TargetType.PLANAR,
    surfaces=[
        ProjectionSurface(
            name="main",
            surface_type=TargetType.PLANAR,
            dimensions=(2.0, 2.0),
            area_m2=4.0,
        )
    ],
    width_m=2.0,
    height_m=2.0,
    recommended_calibration="three_point",
)

GARAGE_DOOR_STANDARD = ProjectionTarget(
    name="garage_door_standard",
    description="Standard US garage door (7ft x 16ft)",
    target_type=TargetType.PLANAR,
    surfaces=[
        ProjectionSurface(
            name="door_panel",
            surface_type=TargetType.PLANAR,
            position=(0, 0, 1.065),
            dimensions=(4.88, 2.13),  # 16ft x 7ft
            area_m2=10.40,
            material=SurfaceMaterial.WHITE_PAINT,
        )
    ],
    width_m=4.88,
    height_m=2.13,
    recommended_calibration="three_point",
    preset_measurements={
        'frame_width': 0.05,
        'panel_gap': 0.02,
        'handle_height': 1.0,
    },
)
