"""
Anamorphic Billboard System for Blender 5.x.

Implements 3D billboard/anamorphic screen effects as seen on curved LED
displays where content appears to pop out in 3D when viewed from the
correct angle.

Based on techniques from:
- Aryan's "How to Make 3D Billboards in Blender" tutorial
- Real-world anamorphic LED installations

Key Components:
- UV Project modifier wrapper for camera-based projection
- L-shaped and curved display geometry generators
- Viewing angle calculator for optimal effect
- Content preparation utilities

Example:
    >>> from lib.cinematic.anamorphic import (
    ...     create_anamorphic_setup,
    ...     ViewingAngleCalculator,
    ...     DisplayType,
    ... )
    ...
    >>> # Create complete anamorphic billboard
    >>> setup = create_anamorphic_setup(
    ...     name="TimesSquareBillboard",
    ...     display_type=DisplayType.L_SHAPED,
    ...     display_size=(10.0, 8.0),
    ...     viewing_distance=25.0,
    ... )
    >>> setup.create_display_mesh()
    >>> setup.position_viewing_camera()
    >>> setup.apply_uv_projection()
"""

__version__ = "0.1.0"
__author__ = "Blender GSD Team"

from .uv_project import (
    create_uv_project_setup,
    UVProjectConfig,
    UVProjectResult,
)
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
)
from .content import (
    prepare_anamorphic_content,
    ContentConfig,
    ContentType,
)
from .workflow import (
    AnamorphicWorkflow,
    create_anamorphic_setup,
)

__all__ = [
    # Version
    "__version__",
    # UV Project
    "create_uv_project_setup",
    "UVProjectConfig",
    "UVProjectResult",
    # Billboard Display
    "create_l_shaped_display",
    "create_curved_display",
    "create_flat_display",
    "DisplayType",
    "DisplayConfig",
    "DisplayResult",
    # Viewing
    "ViewingAngleCalculator",
    "ViewingPosition",
    "calculate_optimal_viewing_angle",
    # Content
    "prepare_anamorphic_content",
    "ContentConfig",
    "ContentType",
    # Workflow
    "AnamorphicWorkflow",
    "create_anamorphic_setup",
]
