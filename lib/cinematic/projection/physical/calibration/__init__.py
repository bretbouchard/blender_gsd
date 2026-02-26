"""
Surface calibration package for physical projector mapping.

Provides 3-point alignment for planar surfaces and 4-point DLT
for non-planar/multi-surface targets.
"""

from .types import (
    CalibrationPoint,
    CalibrationType,
    SurfaceCalibration,
    CalibrationPattern,
    PatternType,
)
from .alignment import AlignmentResult
from .alignment import (
    compute_alignment_transform,
    build_orthonormal_basis,
    are_collinear,
)
from .dlt import (
    four_point_dlt_alignment,
    build_dlt_matrix,
    solve_dlt,
    decompose_projection_matrix,
)
from .patterns import (
    generate_checkerboard_pattern,
    generate_color_bars_pattern,
    generate_grid_pattern,
    generate_crosshair_pattern,
    generate_gradient_pattern,
    generate_pattern,
    save_pattern,
)
from .keystone import (
    compute_keystone_correction,
    apply_keystone_to_camera,
)
from .surface_transform import (
    SurfaceTransform,
    calculate_surface_transform,
)
from .manager import CalibrationManager

__all__ = [
    # Types
    'CalibrationPoint',
    'CalibrationType',
    'SurfaceCalibration',
    'CalibrationPattern',
    'PatternType',
    'AlignmentResult',

    # 3-point alignment
    'compute_alignment_transform',
    'build_orthonormal_basis',
    'are_collinear',

    # 4-point DLT
    'four_point_dlt_alignment',
    'build_dlt_matrix',
    'solve_dlt',
    'decompose_projection_matrix',

    # Patterns
    'generate_checkerboard_pattern',
    'generate_color_bars_pattern',
    'generate_grid_pattern',
    'generate_crosshair_pattern',
    'generate_gradient_pattern',
    'generate_pattern',
    'save_pattern',

    # Keystone
    'compute_keystone_correction',
    'apply_keystone_to_camera',

    # Transform
    'SurfaceTransform',
    'calculate_surface_transform',

    # Manager
    'CalibrationManager',
]
