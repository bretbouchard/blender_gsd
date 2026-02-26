"""
Decimate wrapper for retopology workflow.

Provides clean decimate operations optimized for game-ready pipelines.
"""

from dataclasses import dataclass
from typing import Optional, Any
from enum import Enum


class DecimateMode(Enum):
    """Decimate modifier modes."""
    COLLAPSE = "collapse"
    UN_SUBDIVIDE = "un_subdivide"
    PLANAR = "planar"
    DISSOLVE = "dissolve"


@dataclass
class DecimateConfig:
    """
    Configuration for decimate operation.

    Attributes:
        mode: Decimate mode
        ratio: Collapse ratio (0-1)
        angle_limit: Planar angle limit (degrees)
        vertex_group: Optional vertex group mask
        invert_vertex_group: Invert vertex group mask
        delimit: Delimit boundary vertices
    """
    mode: DecimateMode = DecimateMode.PLANAR
    ratio: float = 0.5
    angle_limit: float = 5.0
    vertex_group: Optional[str] = None
    invert_vertex_group: bool = False
    delimit: bool = True


@dataclass
class DecimateResult:
    """
    Result of decimate operation.

    Attributes:
        success: Whether operation succeeded
        modifier: Created/applied modifier
        original_face_count: Original face count
        final_face_count: Final face count
        reduction_ratio: Reduction ratio
    """
    success: bool = False
    modifier: Any = None
    original_face_count: int = 0
    final_face_count: int = 0
    reduction_ratio: float = 1.0


def apply_decimate(
    obj: Any,
    config: Optional[DecimateConfig] = None,
) -> DecimateResult:
    """
    Apply decimate modifier to object.

    Args:
        obj: Object to decimate
        config: Decimate configuration

    Returns:
        DecimateResult with operation status
    """
    result = DecimateResult()

    if config is None:
        config = DecimateConfig()

    try:
        import bpy
    except ImportError:
        return result

    if obj is None or obj.type != 'MESH':
        return result

    try:
        # Get original face count
        result.original_face_count = len(obj.data.polygons)

        # Create or get modifier
        decimate = obj.modifiers.new(name="Decimate_Retopo", type='DECIMATE')

        # Configure mode
        mode_map = {
            DecimateMode.COLLAPSE: 'COLLAPSE',
            DecimateMode.UN_SUBDIVIDE: 'UN_SUBDIVIDE',
            DecimateMode.PLANAR: 'PLANAR',
            DecimateMode.DISSOLVE: 'DISSOLVE',
        }
        decimate.decimate_mode = mode_map[config.mode]

        # Set parameters based on mode
        if config.mode == DecimateMode.COLLAPSE:
            decimate.ratio = config.ratio
        elif config.mode == DecimateMode.PLANAR:
            decimate.angle_limit = config.angle_limit

        # Vertex group
        if config.vertex_group:
            decimate.vertex_group = config.vertex_group
            decimate.invert_vertex_group = config.invert_vertex_group

        # Delimit
        decimate.delimit = config.delimit

        # Apply modifier
        bpy.context.view_layer.objects.active = {obj}
        bpy.ops.object.modifier_apply(modifier="Decimate_Retopo")

        # Get final face count
        result.final_face_count = len(obj.data.polygons)
        result.reduction_ratio = (
            result.final_face_count / result.original_face_count
            if result.original_face_count > 0 else 1.0
        )
        result.modifier = decimate
        result.success = True

        return result

    except Exception as e:
        return result


def planar_decimate(
    obj: Any,
    angle: float = 5.0,
) -> DecimateResult:
    """
    Convenience function for planar decimate (most common for retopology).

    Args:
        obj: Object to decimate
        angle: Angle limit in degrees

    Returns:
        DecimateResult
    """
    config = DecimateConfig(
        mode=DecimateMode.PLANAR,
        angle_limit=angle,
    )
    return apply_decimate(obj, config)


def collapse_decimate(
    obj: Any,
    ratio: float = 0.5,
) -> DecimateResult:
    """
    Convenience function for collapse decimate.

    Args:
        obj: Object to decimate
        ratio: Target ratio (0-1)

    Returns:
        DecimateResult
    """
    config = DecimateConfig(
        mode=DecimateMode.COLLAPSE,
        ratio=ratio,
    )
    return apply_decimate(obj, config)
