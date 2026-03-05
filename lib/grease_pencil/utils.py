"""
Grease Pencil Utility Functions

Provides seed generation, validation, and helper functions
for deterministic GP generation.

Phase 21.0: Core GP Module (REQ-GP-02)
"""

from __future__ import annotations
from typing import Any, Dict, Optional, List
import hashlib


def generate_seed_from_params(params: Dict[str, Any]) -> int:
    """
    Generate deterministic seed from parameter dictionary.

    Uses SHA-256 hash of sorted params for reproducibility.
    Same params always produce same seed.

    Args:
        params: Dictionary of generation parameters

    Returns:
        Integer seed in range [0, 2^31)

    Example:
        >>> seed1 = generate_seed_from_params({'stroke_count': 10, 'width': 5.0})
        >>> seed2 = generate_seed_from_params({'stroke_count': 10, 'width': 5.0})
        >>> assert seed1 == seed2
    """
    # If seed already provided, use it
    if 'seed' in params and params['seed'] is not None:
        return int(params['seed']) % (2**31)

    # Hash sorted params for consistency
    param_str = str(sorted(params.items(), key=lambda x: x[0]))
    hash_bytes = hashlib.sha256(param_str.encode()).digest()

    # Convert first 4 bytes to integer
    seed = int.from_bytes(hash_bytes[:4], byteorder='big')
    return seed % (2**31)


def validate_gp_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize GP parameters.

    Ensures required fields exist with sensible defaults.

    Args:
        params: Raw parameter dictionary

    Returns:
        Validated parameter dictionary

    Raises:
        ValueError: If validation fails
    """
    validated = dict(params)

    # Set defaults
    validated.setdefault('stroke_count', 10)
    validated.setdefault('layer_count', 3)
    validated.setdefault('stroke_width', 5.0)
    validated.setdefault('material_config', {})
    validated.setdefault('animation_config', {})
    validated.setdefault('mask_config', {})
    validated.setdefault('seed', None)

    validated.setdefault('name', 'GP_Object')
    validated.setdefault('frame_start', 1)
    validated.setdefault('frame_end', 100)
    validated.setdefault('frame_rate', 24.0)

    # Validate ranges
    if validated['stroke_count'] < 1:
        raise ValueError(f"stroke_count must be >= 1, got {validated['stroke_count']}")
    if validated['layer_count'] < 1:
        raise ValueError(f"layer_count must be >= 1, got {validated['layer_count']}")
    if validated['stroke_width'] <= 0:
        raise ValueError(f"stroke_width must be > 0, got {validated['stroke_width']}")
    if validated['frame_start'] >= validated['frame_end']:
        raise ValueError(f"frame_start ({validated['frame_start']}) must be < frame_end ({validated['frame_end']})")
    if validated['frame_rate'] <= 0:
        raise ValueError(f"frame_rate must be > 0, got {validated['frame_rate']}")

    return validated


def validate_stroke_points(points: List[tuple]) -> List[tuple]:
    """
    Validate stroke points list.

    Args:
        points: List of (x, y, z, pressure, strength) tuples

    Returns:
        Validated points list
    """
    if not points:
        return [(0.0, 0.0, 0.0, 1.0, 1.0)]

    validated = []
    for point in points:
        if len(point) != 5:
            raise ValueError(f"Point must have 5 elements (x, y, z, pressure, strength), got {len(point)}")
        x, y, z, pressure, strength = point
        validated.append((float(x), float(y), float(z), float(pressure), float(strength)))

    return validated


def validate_layer_config(layer_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate layer configuration.

    Args:
        layer_config: Layer configuration dict

    Returns:
        Validated layer configuration
    """
    validated = dict(layer_config)

    # Required fields
    validated.setdefault('name', 'Layer')
    validated.setdefault('opacity', 1.0)
    validated.setdefault('blend_mode', 'REGULAR')
    validated.setdefault('use_lights', False)
    validated.setdefault('stroke_configs', [])
    validated.setdefault('mask_config', {})

    validated.setdefault('lock', False)
    validated.setdefault('hide', False)

    # Clamp values
    validated['opacity'] = max(0.0, min(1.0, validated['opacity']))
    validated['blend_mode'] = validated['blend_mode'].upper()

    return validated


def blend_colors(base_color: tuple, blend_color: tuple, factor: float) -> tuple:
    """
    Blend two colors based on factor.

    Args:
        base_color: Base color (RGBA tuple)
        blend_color: Blend color (RGBA tuple)
        factor: Blend factor (0.0 to 1.0)

    Returns:
        Blended color (RGBA tuple)
    """
    result = tuple(
        base_color[i] * (1 - factor) + blend_color[i] * factor
        for i in range(4)
    )
    return result
