"""
Shot YAML integration for physical projection system.

Provides tools for building complete projection setups from YAML configuration,
integrating projector profiles, calibration, targets, content mapping, and output.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path


@dataclass
class ProjectionShotConfig:
    """
    Configuration for projection shot from YAML.

    Encapsulates all settings needed to build a complete projection setup.

    Attributes:
        name: Shot name
        description: Shot description
        projector_profile: Name of projector profile to load
        calibration_type: "three_point" or "four_point_dlt"
        calibration_points: List of calibration point dictionaries
        target_preset: Optional target preset name to load
        content_source: Path to content (image/video)
        blend_mode: Blend mode for content ("mix", "add", "multiply")
        intensity: Content intensity (0-1)
        resolution: Optional output resolution override
        output_format: "video", "image_sequence", "exr"
        output_path: Output directory path
        color_space: Output color space
    """
    name: str
    description: str = ""

    # Projector configuration
    projector_profile: str = ""
    calibration_type: str = "three_point"
    calibration_points: List[Dict[str, Any]] = field(default_factory=list)
    target_preset: Optional[str] = None

    # Content
    content_source: str = ""
    blend_mode: str = "mix"
    intensity: float = 1.0

    # Output
    resolution: Optional[Tuple[int, int]] = None
    output_format: str = "video"
    output_path: str = "//output/"
    color_space: str = "sRGB"
    frame_start: int = 1
    frame_end: int = 250

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'camera': {
                'type': 'projection',
                'projector_profile': self.projector_profile,
                'calibration': {
                    'type': self.calibration_type,
                    'points': self.calibration_points,
                },
                'target_preset': self.target_preset,
            },
            'content': {
                'source': self.content_source,
                'blend_mode': self.blend_mode,
                'intensity': self.intensity,
            },
            'output': {
                'resolution': list(self.resolution) if self.resolution else None,
                'format': self.output_format,
                'output_path': self.output_path,
                'color_space': self.color_space,
                'frame_start': self.frame_start,
                'frame_end': self.frame_end,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectionShotConfig':
        """Create from dictionary (YAML data)."""
        camera = data.get('camera', {})
        calibration = camera.get('calibration', {})
        content = data.get('content', {})
        output = data.get('output', {})

        resolution_data = output.get('resolution')
        resolution = tuple(resolution_data) if resolution_data else None

        return cls(
            name=data.get('name', 'Projection Shot'),
            description=data.get('description', ''),
            projector_profile=camera.get('projector_profile', ''),
            calibration_type=calibration.get('type', 'three_point'),
            calibration_points=calibration.get('points', []),
            target_preset=camera.get('target_preset'),
            content_source=content.get('source', ''),
            blend_mode=content.get('blend_mode', 'mix'),
            intensity=content.get('intensity', 1.0),
            resolution=resolution,
            output_format=output.get('format', 'video'),
            output_path=output.get('output_path', '//output/'),
            color_space=output.get('color_space', 'sRGB'),
            frame_start=output.get('frame_start', 1),
            frame_end=output.get('frame_end', 250),
        )


@dataclass
class ProjectionShotResult:
    """
    Result of building a projection shot.

    Attributes:
        success: Whether the build succeeded
        config: The configuration used
        profile: Loaded projector profile (if any)
        calibration: Created calibration (if any)
        target: Loaded target preset (if any)
        projector_camera: Created projector camera object
        content_material: Created content material
        output_config: Output configuration
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    config: Optional[ProjectionShotConfig] = None
    profile: Any = None
    calibration: Any = None
    target: Any = None
    projector_camera: Any = None
    content_material: Any = None
    output_config: Any = None
    output_files: List[Path] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class ProjectionShotBuilder:
    """
    Build complete projection setup from YAML configuration.

    Provides fluent API for building projection shots step by step,
    or all at once with the build() method.

    Example:
        >>> builder = ProjectionShotBuilder(config)
        >>> builder.load_profile().setup_calibration().create_projector_camera()
        >>> result = builder.build()
        >>> if result.success:
        ...     output_files = builder.render()
    """

    def __init__(self, config: ProjectionShotConfig):
        self.config = config
        self.profile: Any = None
        self.calibration: Any = None
        self.target: Any = None
        self.projector_camera: Any = None
        self.content_material: Any = None
        self.output_config: Any = None
        self._errors: List[str] = []
        self._warnings: List[str] = []

    def load_profile(self) -> 'ProjectionShotBuilder':
        """Load projector profile from configuration."""
        if self._errors:
            return self

        if not self.config.projector_profile:
            self._errors.append("No projector profile specified")
            return self

        try:
            from ..projector import load_profile
            self.profile = load_profile(self.config.projector_profile)
        except KeyError as e:
            self._errors.append(f"Projector profile not found: {e}")
        except Exception as e:
            self._errors.append(f"Error loading projector profile: {e}")

        return self

    def setup_calibration(self) -> 'ProjectionShotBuilder':
        """Setup calibration from points or preset."""
        if self._errors:
            return self

        try:
            # Load target preset if specified
            if self.config.target_preset:
                from ..targets import load_target_preset
                self.target = load_target_preset(self.config.target_preset)

                # Extract calibration from target surfaces
                if self.target and self.target.surfaces:
                    from ..calibration import (
                        CalibrationPoint,
                        CalibrationType,
                        SurfaceCalibration,
                    )

                    # Get calibration type from target recommendation
                    cal_type = (
                        CalibrationType.THREE_POINT
                        if self.target.recommended_calibration == "three_point"
                        else CalibrationType.FOUR_POINT_DLT
                    )

                    # Get calibration points from target surfaces
                    points = []
                    for surface in self.target.surfaces:
                        for i, pos in enumerate(surface.calibration_points[:3]):
                            # Map corner positions to UV coordinates
                            uvs = [(0, 0), (1, 0), (0, 1)]
                            if i < len(uvs):
                                points.append(CalibrationPoint(
                                    world_position=pos,
                                    projector_uv=uvs[i],
                                    label=f"{surface.name}_point_{i+1}"
                                ))

                    if points:
                        self.calibration = SurfaceCalibration(
                            name=f"{self.config.name}_calibration",
                            calibration_type=cal_type,
                            points=points
                        )

            # Or use manual calibration points
            elif self.config.calibration_points:
                from ..calibration import (
                    CalibrationPoint,
                    CalibrationType,
                    SurfaceCalibration,
                )

                cal_type = (
                    CalibrationType.THREE_POINT
                    if self.config.calibration_type == "three_point"
                    else CalibrationType.FOUR_POINT_DLT
                )

                points = [
                    CalibrationPoint(
                        world_position=tuple(p['world_position']),
                        projector_uv=tuple(p['projector_uv']),
                        label=p.get('label', f"Point {i+1}")
                    )
                    for i, p in enumerate(self.config.calibration_points)
                ]

                self.calibration = SurfaceCalibration(
                    name=f"{self.config.name}_calibration",
                    calibration_type=cal_type,
                    points=points
                )

        except FileNotFoundError as e:
            self._errors.append(f"Target preset not found: {e}")
        except Exception as e:
            self._errors.append(f"Error setting up calibration: {e}")

        return self

    def create_projector_camera(self) -> 'ProjectionShotBuilder':
        """Create projector camera from profile and calibration."""
        if self._errors:
            return self

        if not self.profile:
            self._errors.append("No projector profile loaded")
            return self

        try:
            import bpy
            from ..projector import create_projector_camera

            self.projector_camera = create_projector_camera(
                self.profile,
                name=f"{self.config.name}_Projector"
            )

            # Apply calibration transform if available
            if self.calibration and self.projector_camera:
                from ..calibration import compute_alignment_transform
                import mathutils

                world_points = [p.world_position for p in self.calibration.points]
                projector_uvs = [p.projector_uv for p in self.calibration.points]

                result = compute_alignment_transform(world_points, projector_uvs)

                # Apply transform to camera
                matrix = mathutils.Matrix(result.transform)
                self.projector_camera.matrix_world = matrix

        except ImportError:
            self._warnings.append("Blender (bpy) not available - camera not created")
        except Exception as e:
            self._errors.append(f"Error creating projector camera: {e}")

        return self

    def map_content(self) -> 'ProjectionShotBuilder':
        """Map content to projection surface."""
        if self._errors:
            return self

        if not self.config.content_source:
            self._warnings.append("No content source specified")
            return self

        try:
            from ..shaders import ContentMapper

            mapper = ContentMapper(self.profile)

            # Create target geometry if target is loaded
            if self.target:
                from ..targets import create_builder
                builder = create_builder(self.target)
                result = builder.create_geometry()

                if result.success and result.object:
                    target_obj = result.object
                else:
                    self._warnings.append("Could not create target geometry")
                    return self
            else:
                # Create simple calibration geometry
                target_obj = self._create_calibration_geometry()

            if target_obj and self.projector_camera:
                self.content_material = mapper.map_content_to_surface(
                    content_path=self.config.content_source,
                    surface_object=target_obj,
                    projector_object=self.projector_camera,
                    calibration=self.calibration
                )

        except Exception as e:
            self._warnings.append(f"Content mapping not available: {e}")

        return self

    def _create_calibration_geometry(self) -> Any:
        """Create simple geometry from calibration points."""
        try:
            import bpy

            # Create mesh from calibration points
            mesh = bpy.data.meshes.new(f"{self.config.name}_cal_mesh")
            obj = bpy.data.objects.new(f"{self.config.name}_Surface", mesh)

            if self.calibration and len(self.calibration.points) >= 3:
                # Create quad from first 3-4 points
                points = self.calibration.points
                verts = [p.world_position for p in points[:4]]

                if len(verts) == 3:
                    # Triangle
                    faces = [(0, 1, 2)]
                else:
                    # Quad
                    verts.append(verts[3])  # Close the quad
                    faces = [(0, 1, 2, 3)]

                mesh.from_pydata(verts, [], faces)

            bpy.context.collection.objects.link(obj)
            return obj

        except Exception:
            return None

    def configure_output(self) -> 'ProjectionShotBuilder':
        """Configure output settings."""
        if self._errors:
            return self

        try:
            from ..output import ProjectionOutputConfig, OutputFormat, ColorSpace

            resolution = self.config.resolution
            if not resolution and self.profile:
                resolution = self.profile.native_resolution
            if not resolution:
                resolution = (1920, 1080)

            # Map format string to enum
            format_map = {
                'video': OutputFormat.VIDEO,
                'image_sequence': OutputFormat.IMAGE_SEQUENCE,
                'exr': OutputFormat.EXR,
            }

            # Map color space string to enum
            colorspace_map = {
                'srgb': ColorSpace.SRGB,
                'rec709': ColorSpace.REC709,
                'rec2020': ColorSpace.REC2020,
            }

            self.output_config = ProjectionOutputConfig(
                resolution=resolution,
                output_format=format_map.get(
                    self.config.output_format.lower(),
                    OutputFormat.IMAGE_SEQUENCE
                ),
                color_space=colorspace_map.get(
                    self.config.color_space.lower(),
                    ColorSpace.SRGB
                ),
                output_path=Path(self.config.output_path),
            )

        except Exception as e:
            self._warnings.append(f"Output configuration issue: {e}")
            # Create minimal config
            from ..output import ProjectionOutputConfig
            self.output_config = ProjectionOutputConfig(
                resolution=(1920, 1080),
                output_path=Path(self.config.output_path),
            )

        return self

    def build(self) -> ProjectionShotResult:
        """
        Execute complete build pipeline.

        Returns:
            ProjectionShotResult with build status and created objects
        """
        # Execute build pipeline
        (self
         .load_profile()
         .setup_calibration()
         .create_projector_camera()
         .map_content()
         .configure_output())

        # Create result
        result = ProjectionShotResult(
            success=len(self._errors) == 0,
            config=self.config,
            profile=self.profile,
            calibration=self.calibration,
            target=self.target,
            projector_camera=self.projector_camera,
            content_material=self.content_material,
            output_config=self.output_config,
            errors=self._errors.copy(),
            warnings=self._warnings.copy(),
        )

        return result

    def render(self, frame_start: int = None, frame_end: int = None) -> List[Path]:
        """
        Render projection output.

        Args:
            frame_start: Optional frame start override
            frame_end: Optional frame end override

        Returns:
            List of output file paths
        """
        if not self.output_config:
            self._errors.append("Output not configured")
            return []

        # Update frame range if specified
        if frame_start is not None:
            self.output_config.frame_start = frame_start
        else:
            self.output_config.frame_start = self.config.frame_start

        if frame_end is not None:
            self.output_config.frame_end = frame_end
        else:
            self.output_config.frame_end = self.config.frame_end

        try:
            import bpy
            from ..output import ProjectionOutputRenderer

            renderer = ProjectionOutputRenderer(self.output_config)
            return renderer.render_animation(bpy.context.scene, self.output_config)

        except ImportError:
            self._warnings.append("Blender (bpy) not available - cannot render")
            return []
        except Exception as e:
            self._errors.append(f"Render error: {e}")
            return []


def build_projection_shot(yaml_path: str) -> ProjectionShotResult:
    """
    Build projection shot from YAML file.

    This is the main convenience function for loading and building
    a complete projection setup from a YAML configuration file.

    Args:
        yaml_path: Path to YAML configuration file

    Returns:
        ProjectionShotResult with build status and created objects

    Example:
        >>> result = build_projection_shot("shots/reading_room_shot.yaml")
        >>> if result.success:
        ...     print(f"Built shot: {result.config.name}")
        ...     print(f"Projector: {result.profile.name}")
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML required: pip install pyyaml")

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    config = ProjectionShotConfig.from_dict(data)
    builder = ProjectionShotBuilder(config)

    return builder.build()


def build_projection_shot_from_dict(data: Dict[str, Any]) -> ProjectionShotResult:
    """
    Build projection shot from dictionary data.

    Args:
        data: Dictionary with shot configuration

    Returns:
        ProjectionShotResult with build status
    """
    config = ProjectionShotConfig.from_dict(data)
    builder = ProjectionShotBuilder(config)
    return builder.build()
