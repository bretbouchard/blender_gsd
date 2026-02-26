"""
UV Project modifier wrapper for anamorphic billboard projection.

Implements camera-based UV projection for creating anamorphic illusions
where content appears 3D from a specific viewing angle.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Any
from enum import Enum


class UVProjectMode(Enum):
    """UV projection mode."""
    CAMERA = "camera"
    OBJECT = "object"


@dataclass
class UVProjectConfig:
    """
    Configuration for UV Project modifier setup.

    Attributes:
        name: Modifier name
        viewing_camera: Camera object for projection
        aspect_x: Horizontal aspect ratio
        aspect_y: Vertical aspect ratio
        scale_x: Horizontal UV scale
        scale_y: Vertical UV scale
        uv_layer: Target UV layer name
        mode: Projection mode (camera or object)
    """
    name: str = "UVProject_Anamorphic"
    viewing_camera: Any = None
    aspect_x: int = 1920
    aspect_y: int = 1080
    scale_x: float = 1.0
    scale_y: float = 1.0
    uv_layer: str = "UVMap"
    mode: UVProjectMode = UVProjectMode.CAMERA

    # Projector settings (up to 10 projectors supported)
    projectors: List[Any] = field(default_factory=list)


@dataclass
class UVProjectResult:
    """
    Result of UV Project modifier creation.

    Attributes:
        success: Whether the operation succeeded
        modifier: Created modifier (if any)
        display_object: Display mesh object
        viewing_camera: Viewing camera object
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool = False
    modifier: Any = None
    display_object: Any = None
    viewing_camera: Any = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def create_uv_project_setup(
    display_mesh: Any,
    viewing_camera: Any,
    config: Optional[UVProjectConfig] = None,
) -> UVProjectResult:
    """
    Create UV Project modifier for anamorphic billboard.

    This sets up the UV Project modifier to project content from
    the viewing camera's perspective, creating the anamorphic illusion.

    Args:
        display_mesh: The display surface mesh object
        viewing_camera: Camera at the optimal viewing position
        config: Optional configuration (uses defaults if not provided)

    Returns:
        UVProjectResult with modifier and status

    Example:
        >>> import bpy
        >>> display = bpy.data.objects["BillboardDisplay"]
        >>> camera = bpy.data.objects["ViewingCamera"]
        >>> result = create_uv_project_setup(display, camera)
        >>> if result.success:
        ...     print(f"Created modifier: {result.modifier.name}")
    """
    if config is None:
        config = UVProjectConfig(viewing_camera=viewing_camera)
    else:
        config.viewing_camera = viewing_camera

    errors = []
    warnings = []

    try:
        import bpy
    except ImportError:
        return UVProjectResult(
            success=False,
            errors=["Blender (bpy) not available"],
        )

    # Validate inputs
    if display_mesh is None:
        errors.append("Display mesh is required")
        return UVProjectResult(success=False, errors=errors)

    if viewing_camera is None:
        errors.append("Viewing camera is required")
        return UVProjectResult(success=False, errors=errors)

    try:
        # Create UV Project modifier
        modifier = display_mesh.modifiers.new(
            name=config.name,
            type='UV_PROJECT'
        )

        # Configure projector
        # UV Project modifier has 10 projector slots
        modifier.projectors[0].object = viewing_camera

        # Set aspect ratio
        modifier.aspect_x = config.aspect_x
        modifier.aspect_y = config.aspect_y

        # Set UV layer
        if config.uv_layer in display_mesh.data.uv_layers:
            modifier.uv_layer = config.uv_layer
        else:
            warnings.append(
                f"UV layer '{config.uv_layer}' not found, using default"
            )

        return UVProjectResult(
            success=True,
            modifier=modifier,
            display_object=display_mesh,
            viewing_camera=viewing_camera,
            warnings=warnings,
        )

    except Exception as e:
        errors.append(f"Error creating UV Project modifier: {e}")
        return UVProjectResult(success=False, errors=errors)


def create_multi_projector_setup(
    display_mesh: Any,
    projectors: List[Any],
    blend_factor: float = 0.5,
) -> UVProjectResult:
    """
    Create multi-projector UV setup for large displays.

    For very large billboards, multiple projectors may be needed
    to cover the entire surface without distortion.

    Args:
        display_mesh: The display surface mesh object
        projectors: List of camera objects for projection
        blend_factor: Blend factor between overlapping projectors

    Returns:
        UVProjectResult with modifier and status
    """
    errors = []

    try:
        import bpy
    except ImportError:
        return UVProjectResult(
            success=False,
            errors=["Blender (bpy) not available"],
        )

    if len(projectors) > 10:
        errors.append("Maximum 10 projectors supported")
        return UVProjectResult(success=False, errors=errors)

    try:
        modifier = display_mesh.modifiers.new(
            name="UVProject_Multi",
            type='UV_PROJECT'
        )

        # Assign each projector
        for i, projector in enumerate(projectors[:10]):
            modifier.projectors[i].object = projector

        modifier.aspect_x = 1920
        modifier.aspect_y = 1080

        return UVProjectResult(
            success=True,
            modifier=modifier,
            display_object=display_mesh,
            warnings=[f"Using {len(projectors)} projectors"],
        )

    except Exception as e:
        errors.append(f"Error creating multi-projector setup: {e}")
        return UVProjectResult(success=False, errors=errors)


def update_uv_projection(
    modifier: Any,
    viewing_camera: Any,
) -> bool:
    """
    Update UV projection for animated camera.

    Call this each frame if the viewing camera is animated
    to maintain the anamorphic effect.

    Args:
        modifier: UV Project modifier
        viewing_camera: Updated camera object

    Returns:
        True if update succeeded
    """
    try:
        modifier.projectors[0].object = viewing_camera
        return True
    except Exception:
        return False


def calculate_uv_bounds(
    display_mesh: Any,
    viewing_camera: Any,
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Calculate UV bounds for the projection.

    Returns the min and max UV coordinates that the camera
    can see on the display mesh.

    Args:
        display_mesh: Display surface mesh
        viewing_camera: Viewing camera

    Returns:
        Tuple of (min_uv, max_uv) where each is (u, v)
    """
    try:
        import bpy
        import mathutils

        # Get camera view vectors
        camera_matrix = viewing_camera.matrix_world
        camera_location = camera_matrix.translation

        # Raycast from camera to mesh
        min_u, min_v = float('inf'), float('inf')
        max_u, max_v = float('-inf'), float('-inf')

        # Sample mesh vertices
        mesh = display_mesh.data
        for vertex in mesh.vertices:
            world_pos = display_mesh.matrix_world @ vertex.co

            # Transform to camera space
            camera_space = camera_matrix.inverted() @ world_pos

            # Project to UV (simplified)
            if camera_space.z < 0:  # In front of camera
                u = -camera_space.x / abs(camera_space.z)
                v = -camera_space.y / abs(camera_space.z)

                min_u = min(min_u, u)
                max_u = max(max_u, u)
                min_v = min(min_v, v)
                max_v = max(max_v, v)

        # Normalize to 0-1 range
        if min_u != float('inf'):
            range_u = max_u - min_u
            range_v = max_v - min_v
            if range_u > 0 and range_v > 0:
                return ((min_u, min_v), (max_u, max_v))

        return ((0.0, 0.0), (1.0, 1.0))

    except Exception:
        return ((0.0, 0.0), (1.0, 1.0))
