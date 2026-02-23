"""
Blender GSD Utility Library

This package provides safe, production-ready utilities for the Blender GSD pipeline:

- **safety**: Atomic writes, schema validation, data integrity
- **limits**: Performance limits with warnings
- **math_safe**: Quaternion interpolation, smooth falloff, safe math operations
- **drivers**: Safe driver creation with named variables

Quick Start:
    from lib.utils import (
        # Safety
        atomic_write,
        SafeYAML,
        validate_yaml,
        generate_unique_id,

        # Limits
        check_limit,
        LIMITS,
        timed,
        performance_block,

        # Math
        interpolate_rotation,
        smooth_falloff,
        safe_scale_blend,
        quaternion_slerp,

        # Drivers
        add_safe_driver,
        DriverBuilder,
        repair_drivers,
    )

    # Atomic write with validation
    SafeYAML.save('pose.yaml', pose_data, schema='pose')

    # Check limits
    if check_limit('max_particles', count):
        create_particles(count)

    # Safe rotation interpolation
    result = interpolate_rotation(rot_a, rot_b, t=0.5, mode='quaternion')

    # Safe driver creation
    add_safe_driver(
        wheel, "rotation_euler", 1,
        expression="dist / (2 * pi * r)",
        variables={'dist': (vehicle, "location[0]"), 'r': (None, "0.35")}
    )
"""

# Safety utilities
from .safety import (
    # Atomic operations
    atomic_write,

    # Validation
    validate_yaml,
    get_schema,
    SCHEMAS,

    # Safe YAML class
    SafeYAML,

    # ID generation
    generate_unique_id,
    id_exists,

    # Validation helpers
    validate_file_path,
    validate_range,

    # Dependencies check
    HAS_JSONSCHEMA,
)

# Limits and performance
from .limits import (
    # Limit checking
    check_limit,
    get_limit,
    set_limit,
    get_all_limits,
    get_limits_by_category,

    # Limit configuration
    LIMITS,
    LimitConfig,
    LimitWarning,
    LimitExceededError,

    # Performance timing
    timed,
    performance_block,
    get_performance_report,
    reset_performance_metrics,

    # Context managers
    limit_context,
)

# Safe math operations
from .math_safe import (
    # Quaternion operations
    euler_to_quaternion,
    quaternion_to_euler,
    quaternion_slerp,
    quaternion_multiply,
    quaternion_normalize,

    # Rotation interpolation
    interpolate_rotation,

    # Smooth functions
    smoothstep,
    smootherstep,
    smooth_falloff,
    exponential_falloff,

    # Scale blending
    safe_scale_blend,
    safe_scale_power,

    # Vector utilities
    clamp_vector,
    lerp_vector,
    vector_length,
    normalize_vector,
    vector_dot,
    vector_cross,

    # Angle utilities
    normalize_angle,
    angle_difference,
    degrees_to_radians,
    radians_to_degrees,
    euler_degrees_to_radians,
    euler_radians_to_degrees,

    # Validation
    validate_bone_chain,
    BoneInfo,

    # Types
    Vector3,
    Vector4,
    Euler,
    Quaternion,
)

# Driver utilities (may not be available outside Blender)
try:
    from .drivers import (
        # Driver creation
        add_safe_driver,
        remove_driver,

        # Builder
        DriverBuilder,

        # Inspection
        get_drivers,
        find_drivers_with_object,
        find_drivers_with_expression,
        DriverInfo,

        # Repair
        repair_drivers,
        fix_driver_expression,

        # Common patterns
        create_wheel_rotation_driver,
        create_ik_influence_driver,
        create_visibility_driver,

        # Validation
        validate_driver_expression,
        validate_all_drivers,

        # Blender check
        HAS_BLENDER,
    )
except ImportError:
    # Drivers module failed to import (likely no bpy)
    HAS_BLENDER = False
    add_safe_driver = None
    DriverBuilder = None
    repair_drivers = None


# ============================================================================
# VERSION
# ============================================================================

__version__ = "1.0.0"
__author__ = "Blender GSD Pipeline"


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def safe_save(path, data, schema=None):
    """
    Convenience function for safe YAML saving.

    Combines atomic write with optional schema validation.
    """
    return SafeYAML.save(path, data, schema=schema)


def safe_load(path, schema=None, default=None):
    """
    Convenience function for safe YAML loading.

    Combines validated loading with default fallback.
    """
    return SafeYAML.load(path, schema=schema, default=default)


def blend_values(a, b, t, mode='linear'):
    """
    Convenience function for blending two values.

    Args:
        a: Start value
        b: End value
        t: Blend factor (0-1)
        mode: 'linear', 'smooth', or 'smoother'

    Returns:
        Blended value
    """
    t = max(0.0, min(1.0, t))

    if mode == 'linear':
        return a + t * (b - a)
    elif mode == 'smooth':
        t = smoothstep(0, 1, t)
        return a + t * (b - a)
    elif mode == 'smoother':
        t = smootherstep(0, 1, t)
        return a + t * (b - a)
    else:
        return a + t * (b - a)


# ============================================================================
# ALL EXPORTS
# ============================================================================

__all__ = [
    # Version
    '__version__',

    # Safety
    'atomic_write',
    'validate_yaml',
    'get_schema',
    'SCHEMAS',
    'SafeYAML',
    'generate_unique_id',
    'id_exists',
    'validate_file_path',
    'validate_range',
    'HAS_JSONSCHEMA',

    # Limits
    'check_limit',
    'get_limit',
    'set_limit',
    'get_all_limits',
    'get_limits_by_category',
    'LIMITS',
    'LimitConfig',
    'LimitWarning',
    'LimitExceededError',
    'timed',
    'performance_block',
    'get_performance_report',
    'reset_performance_metrics',
    'limit_context',

    # Math
    'euler_to_quaternion',
    'quaternion_to_euler',
    'quaternion_slerp',
    'quaternion_multiply',
    'quaternion_normalize',
    'interpolate_rotation',
    'smoothstep',
    'smootherstep',
    'smooth_falloff',
    'exponential_falloff',
    'safe_scale_blend',
    'safe_scale_power',
    'clamp_vector',
    'lerp_vector',
    'vector_length',
    'normalize_vector',
    'vector_dot',
    'vector_cross',
    'normalize_angle',
    'angle_difference',
    'degrees_to_radians',
    'radians_to_degrees',
    'euler_degrees_to_radians',
    'euler_radians_to_degrees',
    'validate_bone_chain',
    'BoneInfo',
    'Vector3',
    'Vector4',
    'Euler',
    'Quaternion',

    # Drivers (may be None if no Blender)
    'add_safe_driver',
    'remove_driver',
    'DriverBuilder',
    'get_drivers',
    'find_drivers_with_object',
    'find_drivers_with_expression',
    'DriverInfo',
    'repair_drivers',
    'fix_driver_expression',
    'create_wheel_rotation_driver',
    'create_ik_influence_driver',
    'create_visibility_driver',
    'validate_driver_expression',
    'validate_all_drivers',
    'HAS_BLENDER',

    # Convenience
    'safe_save',
    'safe_load',
    'blend_values',
]
