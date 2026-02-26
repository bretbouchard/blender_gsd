"""
Complete anamorphic workflow orchestration.

Provides a unified workflow for creating anamorphic billboard setups
from configuration to render.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from pathlib import Path

from .billboard import (
    create_l_shaped_display,
    create_curved_display,
    create_flat_display,
    DisplayType,
    DisplayConfig,
    DisplayResult,
)
from .viewing import (
    ViewingAngleCalculator,
    ViewingPosition,
    calculate_optimal_viewing_angle,
    create_viewing_camera,
)
from .uv_project import (
    create_uv_project_setup,
    UVProjectConfig,
    UVProjectResult,
)
from .content import (
    prepare_anamorphic_content,
    ContentConfig,
    ContentResult,
)


@dataclass
class AnamorphicSetupResult:
    """
    Complete result of anamorphic setup creation.

    Attributes:
        success: Whether setup succeeded
        display: Display creation result
        viewing_position: Calculated viewing position
        viewing_camera: Created viewing camera
        uv_project: UV projection result
        content: Content preparation result
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    display: Optional[DisplayResult] = None
    viewing_position: Optional[ViewingPosition] = None
    viewing_camera: Any = None
    uv_project: Optional[UVProjectResult] = None
    content: Optional[ContentResult] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class AnamorphicWorkflow:
    """
    Complete workflow for anamorphic billboard creation.

    Orchestrates all steps: display creation, viewing calculation,
    camera setup, UV projection, and content preparation.

    Example:
        >>> workflow = AnamorphicWorkflow(
        ...     name="TimesSquareAd",
        ...     display_type=DisplayType.L_SHAPED,
        ...     display_width=12.0,
        ...     display_height=9.0,
        ... )
        >>> result = workflow.create_complete_setup()
        >>> if result.success:
        ...     workflow.render_content("output/")
    """

    def __init__(
        self,
        name: str = "AnamorphicBillboard",
        display_type: DisplayType = DisplayType.L_SHAPED,
        display_width: float = 10.0,
        display_height: float = 8.0,
        display_depth: float = 3.0,
        curve_angle: float = 90.0,
        content_path: Optional[str] = None,
        output_resolution: tuple = (1920, 1080),
    ):
        """
        Initialize workflow with display parameters.

        Args:
            name: Setup name (used for object naming)
            display_type: Type of display geometry
            display_width: Display width in meters
            display_height: Display height in meters
            display_depth: Depth for L-shaped displays
            curve_angle: Arc angle for curved displays
            content_path: Optional path to content file
            output_resolution: Render resolution (width, height)
        """
        self.name = name
        self.display_type = display_type
        self.display_width = display_width
        self.display_height = display_height
        self.display_depth = display_depth
        self.curve_angle = curve_angle
        self.content_path = content_path
        self.output_resolution = output_resolution

        # Results storage
        self._result: Optional[AnamorphicSetupResult] = None

    def create_display(self) -> DisplayResult:
        """Create display geometry."""
        config = DisplayConfig(
            name=f"{self.name}_Display",
            display_type=self.display_type,
            width=self.display_width,
            height=self.display_height,
            depth=self.display_depth,
            curve_angle=self.curve_angle,
        )

        if self.display_type == DisplayType.L_SHAPED:
            return create_l_shaped_display(config)
        elif self.display_type == DisplayType.CURVED:
            return create_curved_display(config)
        else:
            return create_flat_display(config)

    def calculate_viewing(self) -> ViewingPosition:
        """Calculate optimal viewing position."""
        display_type_str = {
            DisplayType.FLAT: "flat",
            DisplayType.L_SHAPED: "l_shaped",
            DisplayType.CURVED: "curved",
            DisplayType.CYLINDRICAL: "curved",
        }.get(self.display_type, "l_shaped")

        return calculate_optimal_viewing_angle(
            display_width=self.display_width,
            display_height=self.display_height,
            display_type=display_type_str,
            display_depth=self.display_depth,
            curve_angle=self.curve_angle,
        )

    def create_camera(
        self,
        viewing_position: ViewingPosition,
    ) -> Any:
        """Create viewing camera at optimal position."""
        return create_viewing_camera(
            position=viewing_position,
            name=f"{self.name}_ViewCamera",
        )

    def setup_uv_projection(
        self,
        display_object: Any,
        viewing_camera: Any,
    ) -> UVProjectResult:
        """Set up UV projection from viewing camera."""
        config = UVProjectConfig(
            name=f"{self.name}_UVProject",
            viewing_camera=viewing_camera,
            aspect_x=self.output_resolution[0],
            aspect_y=self.output_resolution[1],
        )
        return create_uv_project_setup(display_object, viewing_camera, config)

    def prepare_content(
        self,
        display_object: Any,
        viewing_camera: Any,
    ) -> ContentResult:
        """Prepare content for display."""
        config = ContentConfig(
            name=f"{self.name}_Content",
            source_path=self.content_path,
        )
        return prepare_anamorphic_content(config, display_object, viewing_camera)

    def create_complete_setup(self) -> AnamorphicSetupResult:
        """
        Execute complete setup workflow.

        Creates display, calculates viewing, sets up camera,
        configures UV projection, and prepares content.

        Returns:
            AnamorphicSetupResult with all created objects
        """
        errors = []
        warnings = []

        # Step 1: Create display
        display_result = self.create_display()
        if not display_result.success:
            errors.extend(display_result.errors)
            return AnamorphicSetupResult(
                success=False,
                display=display_result,
                errors=errors,
            )
        warnings.extend(display_result.warnings)

        # Step 2: Calculate viewing position
        viewing_position = self.calculate_viewing()

        # Step 3: Create viewing camera
        viewing_camera = self.create_camera(viewing_position)
        if viewing_camera is None:
            warnings.append("Could not create viewing camera")

        # Step 4: Set up UV projection
        uv_result = None
        if viewing_camera:
            uv_result = self.setup_uv_projection(
                display_result.display_object,
                viewing_camera,
            )
            if not uv_result.success:
                warnings.extend(uv_result.errors)
            warnings.extend(uv_result.warnings)

        # Step 5: Prepare content
        content_result = None
        if viewing_camera:
            content_result = self.prepare_content(
                display_result.display_object,
                viewing_camera,
            )
            if not content_result.success:
                warnings.extend(content_result.errors)
            warnings.extend(content_result.warnings)

        # Store result
        self._result = AnamorphicSetupResult(
            success=True,
            display=display_result,
            viewing_position=viewing_position,
            viewing_camera=viewing_camera,
            uv_project=uv_result,
            content=content_result,
            warnings=warnings,
        )

        return self._result

    def render_content(
        self,
        output_path: str,
        frame_start: int = 1,
        frame_end: int = 250,
    ) -> List[str]:
        """
        Render anamorphic content.

        Args:
            output_path: Output directory
            frame_start: Start frame
            frame_end: End frame

        Returns:
            List of rendered file paths
        """
        if self._result is None or not self._result.success:
            return []

        from .content import render_anamorphic_content

        return render_anamorphic_content(
            display_object=self._result.display.display_object,
            viewing_camera=self._result.viewing_camera,
            output_path=output_path,
            frame_start=frame_start,
            frame_end=frame_end,
        )

    def export_setup_config(self, path: str) -> bool:
        """
        Export setup configuration to YAML.

        Args:
            path: Output file path

        Returns:
            True if export succeeded
        """
        try:
            import yaml

            config = {
                'name': self.name,
                'display': {
                    'type': self.display_type.value,
                    'width': self.display_width,
                    'height': self.display_height,
                    'depth': self.display_depth,
                    'curve_angle': self.curve_angle,
                },
                'output': {
                    'resolution': list(self.output_resolution),
                },
            }

            if self.content_path:
                config['content'] = {'source': self.content_path}

            if self._result and self._result.viewing_position:
                config['viewing'] = {
                    'distance': self._result.viewing_position.distance,
                    'camera_location': list(self._result.viewing_position.camera_location),
                    'camera_rotation': list(self._result.viewing_position.camera_rotation),
                    'fov': self._result.viewing_position.fov,
                }

            with open(path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            return True

        except ImportError:
            return False
        except Exception:
            return False


def create_anamorphic_setup(
    name: str = "AnamorphicBillboard",
    display_type: DisplayType = DisplayType.L_SHAPED,
    display_width: float = 10.0,
    display_height: float = 8.0,
    **kwargs,
) -> AnamorphicSetupResult:
    """
    Convenience function to create complete anamorphic setup.

    Args:
        name: Setup name
        display_type: Type of display
        display_width: Display width in meters
        display_height: Display height in meters
        **kwargs: Additional arguments passed to AnamorphicWorkflow

    Returns:
        AnamorphicSetupResult with all created objects

    Example:
        >>> result = create_anamorphic_setup(
        ...     name="TimesSquare",
        ...     display_type=DisplayType.L_SHAPED,
        ...     display_width=15.0,
        ...     display_height=10.0,
        ...     display_depth=5.0,
        ... )
        >>> print(f"Created display: {result.display.surface_area}m²")
    """
    workflow = AnamorphicWorkflow(
        name=name,
        display_type=display_type,
        display_width=display_width,
        display_height=display_height,
        **kwargs,
    )
    return workflow.create_complete_setup()
