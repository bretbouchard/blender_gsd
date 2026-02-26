"""
Content mapping workflow for physical projector mapping.

Orchestrates the complete pipeline from calibration to final output:
1. Setup projector camera from profile
2. Apply calibration data
3. Create UV-mapped proxy geometry
4. Map content via projection shader
5. Render output for projector
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path


@dataclass
class ContentMappingWorkflow:
    """
    Complete workflow for mapping content to physical projection surface.

    Orchestrates: calibration -> proxy geometry -> shader -> output

    Usage:
        from lib.cinematic.projection.physical import (
            ContentMappingWorkflow,
            load_profile,
            SurfaceCalibration,
        )

        # Load profile and create calibration
        profile = load_profile("epson_home_cinema_2150")
        calibration = SurfaceCalibration(...)

        # Create and execute workflow
        workflow = ContentMappingWorkflow(
            name="reading_room_projection",
            projector_profile=profile,
            calibration=calibration,
        )

        output_files = workflow.execute(
            content_path="//content/animation.mp4",
            output_dir="//projector_output/"
        )
    """
    name: str
    projector_profile: Any  # ProjectorProfile
    calibration: Any  # SurfaceCalibration

    # Blender objects (set during execution)
    projector_camera: Optional[Any] = None
    proxy_geometry: Optional[Any] = None
    content_material: Optional[Any] = None

    # Configuration
    shader_config: Optional[Any] = None  # ProjectionShaderConfig
    output_config: Optional[Any] = None  # ProjectionOutputConfig

    # State
    _calibration_error: float = 0.0
    _errors: List[str] = field(default_factory=list)

    def setup(self) -> 'ContentMappingWorkflow':
        """
        Step 1: Setup projector camera from profile.

        Creates a Blender camera object configured with projector parameters.

        Returns:
            self for method chaining
        """
        try:
            from .projector.calibration import create_projector_camera
            self.projector_camera = create_projector_camera(
                self.projector_profile,
                name=f"{self.name}_Projector"
            )
        except ImportError:
            self._errors.append("Blender (bpy) not available")
        except Exception as e:
            self._errors.append(f"Error setting up projector: {e}")

        return self

    def calibrate(self) -> 'ContentMappingWorkflow':
        """
        Step 2: Apply calibration to projector camera.

        Transforms the projector camera to align with the calibrated surface.

        Returns:
            self for method chaining
        """
        if self._errors:
            return self

        try:
            from .calibration import compute_alignment_transform

            # Get calibration points
            world_points = [p.world_position for p in self.calibration.points]
            projector_uvs = [p.projector_uv for p in self.calibration.points]

            # Compute alignment transform
            result = compute_alignment_transform(world_points, projector_uvs)

            if self.projector_camera:
                # Apply transform to camera
                import bpy
                import mathutils
                matrix = mathutils.Matrix(result.transform)
                self.projector_camera.matrix_world = matrix

            self._calibration_error = result.error

        except ImportError:
            self._errors.append("Blender (bpy) not available")
        except Exception as e:
            self._errors.append(f"Error calibrating: {e}")

        return self

    def create_proxy(self) -> 'ContentMappingWorkflow':
        """
        Step 3: Create UV-mapped proxy geometry.

        Generates a proxy mesh with UV coordinates matching projector UV space.

        Returns:
            self for method chaining
        """
        if self._errors:
            return self

        try:
            from .shaders.proxy_geometry import (
                create_proxy_geometry_for_surface,
                create_proxy_mesh_blender,
                ProxyGeometryConfig,
            )
            from .shaders import compute_uv_for_calibration_points

            # Get calibration data
            calibration_points = [p.world_position for p in self.calibration.points]
            projector_uvs = [p.projector_uv for p in self.calibration.points]

            # Create proxy geometry data
            proxy_config = ProxyGeometryConfig(subdivisions=2)
            proxy_result = create_proxy_geometry_for_surface(
                calibration_points,
                projector_uvs,
                proxy_config
            )

            if not proxy_result.success:
                self._errors.extend(proxy_result.errors)
                return self

            # Create Blender mesh
            uvs = compute_uv_for_calibration_points(projector_uvs)
            self.proxy_geometry = create_proxy_mesh_blender(
                proxy_result.vertices if hasattr(proxy_result, 'vertices') else [],
                proxy_result.faces if hasattr(proxy_result, 'faces') else [],
                uvs,
                name=f"{self.name}_Proxy"
            )

        except ImportError:
            self._errors.append("Blender (bpy) not available")
        except Exception as e:
            self._errors.append(f"Error creating proxy: {e}")

        return self

    def map_content(self, content_path: str) -> 'ContentMappingWorkflow':
        """
        Step 4: Map content to surface via projection shader.

        Creates a material with camera projection shader and applies to proxy.

        Args:
            content_path: Path to content image/video

        Returns:
            self for method chaining
        """
        if self._errors:
            return self

        try:
            from .shaders import ContentMapper, ProjectionShaderConfig

            mapper = ContentMapper(self.projector_profile)

            result = mapper.map_content_to_surface(
                content_path=content_path,
                surface_object=self.proxy_geometry,
                projector_object=self.projector_camera,
                calibration=self.calibration
            )

            if not result.success:
                self._errors.extend(result.errors)
                return self

            self.content_material = result.material
            self.shader_config = mapper.shader_config

        except ImportError:
            self._errors.append("Blender (bpy) not available")
        except Exception as e:
            self._errors.append(f"Error mapping content: {e}")

        return self

    def configure_output(self, config: Any) -> 'ContentMappingWorkflow':
        """
        Step 5: Configure output rendering.

        Args:
            config: ProjectionOutputConfig instance

        Returns:
            self for method chaining
        """
        self.output_config = config
        return self

    def render(self, output_dir: str) -> List[Path]:
        """
        Step 6: Render final output for projector.

        Renders from projector camera perspective at native resolution.

        Args:
            output_dir: Directory for output files

        Returns:
            List of output file paths
        """
        if self._errors:
            return []

        if not self.output_config:
            self._errors.append("Output config not set. Call configure_output() first.")
            return []

        try:
            import bpy
            from .output import ProjectionOutputRenderer

            renderer = ProjectionOutputRenderer(self.projector_profile)

            # Set output path
            self.output_config.output_path = output_dir

            # Set scene camera to projector camera
            bpy.context.scene.camera = self.projector_camera

            # Render
            result = renderer.render_animation(bpy.context.scene, self.output_config)

            if not result.success:
                self._errors.extend(result.errors)
                return []

            return result.output_files

        except ImportError:
            self._errors.append("Blender (bpy) not available")
            return []
        except Exception as e:
            self._errors.append(f"Error rendering: {e}")
            return []

    def execute(self, content_path: str, output_dir: str) -> List[Path]:
        """
        Execute complete workflow in one call.

        setup -> calibrate -> create_proxy -> map_content -> render

        Args:
            content_path: Path to content image/video
            output_dir: Output directory for rendered files

        Returns:
            List of output file paths
        """
        return (
            self.setup()
            .calibrate()
            .create_proxy()
            .map_content(content_path)
            .configure_output(self._create_default_output_config(output_dir))
            .render(output_dir)
        )

    def _create_default_output_config(self, output_dir: str) -> Any:
        """Create default output configuration."""
        from .output import ProjectionOutputConfig
        return ProjectionOutputConfig(
            resolution=self.projector_profile.native_resolution,
            output_path=output_dir,
        )

    def get_errors(self) -> List[str]:
        """Get all errors from workflow execution."""
        return self._errors.copy()

    def get_calibration_error(self) -> float:
        """Get calibration alignment error (lower is better)."""
        return self._calibration_error


def render_for_projector(
    content_path: str,
    projector_profile_name: str,
    calibration_points: List[Tuple],
    output_dir: str = "//projector_output/"
) -> List[Path]:
    """
    Render content for physical projector in one function call.

    This is a convenience function that handles the complete workflow:
    - Load projector profile
    - Create calibration from points
    - Execute content mapping workflow
    - Render output

    Args:
        content_path: Path to content image/video
        projector_profile_name: Name of projector profile
            (e.g., "epson_home_cinema_2150")
        calibration_points: List of (world_pos, projector_uv) tuples
            world_pos: (x, y, z) world coordinates
            projector_uv: (u, v) projector UV coordinates (0-1 range)
        output_dir: Output directory for rendered files

    Returns:
        List of output file paths

    Example:
        >>> files = render_for_projector(
        ...     content_path="//content/animation.mp4",
        ...     projector_profile_name="epson_home_cinema_2150",
        ...     calibration_points=[
        ...         ((0, 0, 0), (0, 0)),       # Bottom-left
        ...         ((2, 0, 0), (1, 0)),       # Bottom-right
        ...         ((0, 1.5, 0), (0, 1)),     # Top-left
        ...     ],
        ...     output_dir="//projector_output/"
        ... )
    """
    from .projector.profile_database import load_profile
    from .calibration import CalibrationPoint, CalibrationType, SurfaceCalibration

    # Load profile
    profile = load_profile(projector_profile_name)

    # Create calibration from points
    points = [
        CalibrationPoint(
            world_position=wp,
            projector_uv=puv,
            label=f"Point {i+1}"
        )
        for i, (wp, puv) in enumerate(calibration_points)
    ]

    # Determine calibration type from point count
    cal_type = CalibrationType.THREE_POINT if len(points) == 3 else CalibrationType.DLT

    calibration = SurfaceCalibration(
        name="auto_calibration",
        calibration_type=cal_type,
        points=points
    )

    # Create and execute workflow
    workflow = ContentMappingWorkflow(
        name="projection",
        projector_profile=profile,
        calibration=calibration
    )

    return workflow.execute(content_path, output_dir)


def create_multi_surface_workflow(
    name: str,
    projector_profile_name: str,
    surface_calibrations: Dict[str, Any],
    content_paths: Dict[str, str],
    output_dir: str = "//projector_output/"
) -> Any:
    """
    Create workflow for multi-surface projection setup.

    Args:
        name: Workflow name
        projector_profile_name: Projector profile name
        surface_calibrations: Dict mapping surface_name -> SurfaceCalibration
        content_paths: Dict mapping surface_name -> content_path
        output_dir: Output directory

    Returns:
        Dict mapping surface_name -> output_files
    """
    from .projector.profile_database import load_profile
    from .output import MultiSurfaceOutput, MultiSurfaceRenderer, ProjectionOutputRenderer

    profile = load_profile(projector_profile_name)
    renderer = ProjectionOutputRenderer(profile)

    # Create proxy objects dict (would need actual execution)
    surfaces = {}
    for surface_name, calibration in surface_calibrations.items():
        workflow = ContentMappingWorkflow(
            name=f"{name}_{surface_name}",
            projector_profile=profile,
            calibration=calibration,
        )
        workflow.setup().calibrate().create_proxy()
        if workflow.proxy_geometry:
            surfaces[surface_name] = workflow.proxy_geometry

    return surfaces
