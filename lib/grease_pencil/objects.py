"""
Grease Pencil Object Creation Functions

Functions for creating GP objects, layers, strokes, and materials
from configuration dicts produced by the stage pipeline.

Phase 21.0: Core GP Module (REQ-GP-01)
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
import math

from .types import (
    GPStrokeConfig,
    GPMaterialConfig,
    GPLayerConfig,
    GPMaskConfig,
    GPAnimationConfig,
    DisplayMode,
    StrokeStyle,
    FillStyle,
    StrokeMode,
    BlendMode,
)


# =============================================================================
# OBJECT CREATION RESULT
# =============================================================================

@dataclass
class GPObjectResult:
    """Result from GP object creation."""
    success: bool
    object_name: str = ""
    layer_count: int = 0
    stroke_count: int = 0
    material_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'object_name': self.object_name,
            'layer_count': self.layer_count,
            'stroke_count': self.stroke_count,
            'material_count': self.material_count,
            'errors': self.errors,
            'warnings': self.warnings,
        }


# =============================================================================
# OBJECT CREATION FUNCTIONS (BLENDER-INDEPENDENT)
# =============================================================================

def create_gp_object_config(
    name: str,
    primary_result: Dict[str, Any],
    secondary_result: Dict[str, Any],
    detail_result: Optional[Dict[str, Any]] = None,
    output_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create GP object configuration from pipeline results.

    This function produces a complete configuration dict that can be
    applied in Blender via bpy operators or used for serialization.

    Args:
        name: Object name
        primary_result: Result from stage_primary_gp
        secondary_result: Result from stage_secondary_gp
        detail_result: Optional result from stage_detail_gp
        output_result: Optional result from stage_output_gp

    Returns:
        Complete GP object configuration dict
    """
    config = {
        'name': name,
        'type': 'GPENCIL',
        'layers': primary_result.get('layers', []),
        'strokes': secondary_result.get('strokes', []),
        'materials': secondary_result.get('materials', []),
        'modifiers': detail_result.get('modifiers', []) if detail_result else [],
        'mask': detail_result.get('mask') if detail_result else None,
        'animation': output_result.get('animation') if output_result else None,
        'render_settings': output_result.get('render_settings') if output_result else None,
    }
    return config


def create_layer_config(
    name: str,
    opacity: float = 1.0,
    blend_mode: str = "REGULAR",
    use_lights: bool = False,
    stroke_configs: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Create GP layer configuration.

    Args:
        name: Layer name
        opacity: Layer opacity (0.0 to 1.0)
        blend_mode: Blend mode (REGULAR, MULTIPLY, ADD, etc.)
        use_lights: Whether layer responds to scene lights
        stroke_configs: List of stroke configuration dicts

    Returns:
        Layer configuration dict
    """
    return {
        'id': f"layer_{name.lower().replace(' ', '_')}",
        'name': name,
        'opacity': max(0.0, min(1.0, opacity)),
        'blend_mode': blend_mode,
        'use_lights': use_lights,
        'use_mask_layer': False,
        'stroke_configs': stroke_configs or [],
    }


def create_stroke_config(
    points: List[Tuple[float, float, float, float, float]],
    stroke_width: float = 5.0,
    hardness: float = 1.0,
    material_index: int = 0,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create GP stroke configuration.

    Args:
        points: List of (x, y, z, pressure, strength) tuples
        stroke_width: Stroke line width
        hardness: Stroke hardness (0.0 to 1.0)
        material_index: Material slot index
        seed: Optional seed for procedural variation

    Returns:
        Stroke configuration dict
    """
    return {
        'id': f"stroke_{id(points) % 10000:04d}",
        'points': points,
        'stroke_width': max(0.1, stroke_width),
        'hardness': max(0.0, min(1.0, hardness)),
        'material_index': material_index,
        'seed': seed,
    }


def create_material_config(
    name: str,
    color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
    fill_color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    stroke_style: str = "SOLID",
    fill_style: str = "SOLID",
    use_stroke_holdout: bool = False,
    use_fill_holdout: bool = False,
    pass_index: int = 0,
) -> Dict[str, Any]:
    """
    Create GP material configuration.

    Args:
        name: Material name
        color: Stroke color (RGBA tuple)
        fill_color: Fill color (RGBA tuple)
        stroke_style: Stroke style (SOLID, DOTS, TEXTURE)
        fill_style: Fill style (SOLID, GRADIENT, TEXTURE, CHECKER)
        use_stroke_holdout: Whether stroke is transparent in render
        use_fill_holdout: Whether fill is transparent in render
        pass_index: Render pass index

    Returns:
        Material configuration dict
    """
    return {
        'id': f"material_{name.lower().replace(' ', '_')}",
        'name': name,
        'color': list(color),
        'fill_color': list(fill_color),
        'stroke_style': stroke_style,
        'fill_style': fill_style,
        'use_stroke_holdout': use_stroke_holdout,
        'use_fill_holdout': use_fill_holdout,
        'pass_index': pass_index,
    }


def create_mask_config(
    enabled: bool = False,
    mask_layer: str = "",
    invert: bool = False,
    feather: float = 0.0,
    mask_type: str = "procedural",
) -> Dict[str, Any]:
    """
    Create GP mask configuration.

    Args:
        enabled: Whether mask is active
        mask_layer: Layer to use as mask
        invert: Invert mask
        feather: Mask edge feather amount
        mask_type: Mask type (layer, stroke_weight, procedural, texture)

    Returns:
        Mask configuration dict
    """
    return {
        'enabled': enabled,
        'mask_layer': mask_layer,
        'invert': invert,
        'feather': max(0.0, feather),
        'type': mask_type,
    }


# =============================================================================
# STROKE GENERATION UTILITIES
# =============================================================================

def generate_line_stroke(
    start: Tuple[float, float, float],
    end: Tuple[float, float, float],
    stroke_width: float = 5.0,
    pressure: float = 1.0,
    strength: float = 1.0,
) -> Dict[str, Any]:
    """
    Generate a simple line stroke from start to end point.

    Args:
        start: Start point (x, y, z)
        end: End point (x, y, z)
        stroke_width: Stroke width
        pressure: Pressure for all points
        strength: Strength for all points

    Returns:
        Stroke configuration dict
    """
    points = [
        (start[0], start[1], start[2], pressure, strength),
        (end[0], end[1], end[2], pressure, strength),
    ]
    return create_stroke_config(points, stroke_width=stroke_width)


def generate_circle_stroke(
    center: Tuple[float, float, float],
    radius: float,
    segments: int = 32,
    stroke_width: float = 5.0,
    pressure: float = 1.0,
    strength: float = 1.0,
) -> Dict[str, Any]:
    """
    Generate a circular stroke.

    Args:
        center: Circle center (x, y, z)
        radius: Circle radius
        segments: Number of segments
        stroke_width: Stroke width
        pressure: Pressure for all points
        strength: Strength for all points

    Returns:
        Stroke configuration dict
    """
    points = []
    for i in range(segments + 1):
        angle = (2 * math.pi * i) / segments
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        z = center[2]
        points.append((x, y, z, pressure, strength))

    return create_stroke_config(points, stroke_width=stroke_width)


def generate_rect_stroke(
    corner1: Tuple[float, float, float],
    corner2: Tuple[float, float, float],
    stroke_width: float = 5.0,
    pressure: float = 1.0,
    strength: float = 1.0,
) -> Dict[str, Any]:
    """
    Generate a rectangular stroke from two corner points.

    Args:
        corner1: First corner (x, y, z)
        corner2: Opposite corner (x, y, z)
        stroke_width: Stroke width
        pressure: Pressure for all points
        strength: Strength for all points

    Returns:
        Stroke configuration dict
    """
    x1, y1, z1 = corner1
    x2, y2, z2 = corner2

    # Create 4 corners + close
    points = [
        (x1, y1, z1, pressure, strength),  # Top-left
        (x2, y1, z1, pressure, strength),  # Top-right
        (x2, y2, z1, pressure, strength),  # Bottom-right
        (x1, y2, z1, pressure, strength),  # Bottom-left
        (x1, y1, z1, pressure, strength),  # Close
    ]
    return create_stroke_config(points, stroke_width=stroke_width)


def generate_arc_stroke(
    center: Tuple[float, float, float],
    radius: float,
    start_angle: float,
    end_angle: float,
    segments: int = 16,
    stroke_width: float = 5.0,
    pressure: float = 1.0,
    strength: float = 1.0,
) -> Dict[str, Any]:
    """
    Generate an arc stroke.

    Args:
        center: Arc center (x, y, z)
        radius: Arc radius
        start_angle: Start angle in radians
        end_angle: End angle in radians
        segments: Number of segments
        stroke_width: Stroke width
        pressure: Pressure for all points
        strength: Strength for all points

    Returns:
        Stroke configuration dict
    """
    points = []
    angle_range = end_angle - start_angle

    for i in range(segments + 1):
        t = i / segments
        angle = start_angle + t * angle_range
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        z = center[2]
        points.append((x, y, z, pressure, strength))

    return create_stroke_config(points, stroke_width=stroke_width)


# =============================================================================
# BLENDER OBJECT CREATION (OPTIONAL - REQUIRES BPY)
# =============================================================================

def create_gp_object_in_blender(
    config: Dict[str, Any],
    collection_name: Optional[str] = None,
) -> GPObjectResult:
    """
    Create GP object in Blender from configuration.

    This function requires bpy and should only be called
    within Blender's Python environment.

    Args:
        config: GP object configuration from create_gp_object_config
        collection_name: Optional collection to link object to

    Returns:
        GPObjectResult with creation status
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Check for bpy availability
    try:
        import bpy
    except ImportError:
        return GPObjectResult(
            success=False,
            errors=["bpy module not available - must run in Blender"],
        )

    try:
        # Create GP data block
        gp_data = bpy.data.grease_pencils.new(config['name'])

        # Create object
        gp_obj = bpy.data.objects.new(config['name'], gp_data)

        # Link to collection
        if collection_name:
            collection = bpy.data.collections.get(collection_name)
            if collection:
                collection.objects.link(gp_obj)
            else:
                warnings.append(f"Collection '{collection_name}' not found, using scene collection")
                bpy.context.scene.collection.objects.link(gp_obj)
        else:
            bpy.context.scene.collection.objects.link(gp_obj)

        # Create layers
        layer_count = 0
        for layer_config in config.get('layers', []):
            layer = gp_data.layers.new(layer_config['name'])
            layer.opacity = layer_config.get('opacity', 1.0)
            # Note: Additional layer properties depend on Blender API version
            layer_count += 1

        # Create materials
        material_count = 0
        for mat_config in config.get('materials', []):
            mat = bpy.data.materials.new(mat_config['name'])
            mat.use_nodes = True

            # Configure GP material (simplified for now)
            # Full material setup would involve node tree manipulation
            gp_mat = bpy.data.materials.create_gp_material_config(mat)
            material_count += 1

        return GPObjectResult(
            success=True,
            object_name=config['name'],
            layer_count=layer_count,
            stroke_count=len(config.get('strokes', [])),
            material_count=material_count,
            warnings=warnings,
        )

    except Exception as e:
        return GPObjectResult(
            success=False,
            errors=[f"Blender object creation failed: {str(e)}"],
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_simple_gp_object(
    name: str,
    stroke_count: int = 10,
    layer_count: int = 1,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a simple GP object configuration with random strokes.

    Convenience function that runs the full pipeline.

    Args:
        name: Object name
        stroke_count: Number of strokes to generate
        layer_count: Number of layers
        seed: Random seed for deterministic output

    Returns:
        Complete GP object configuration
    """
    from .stages import run_gp_pipeline

    params = {
        'name': name,
        'stroke_count': stroke_count,
        'layer_count': layer_count,
        'seed': seed,
    }

    result = run_gp_pipeline(params)

    return create_gp_object_config(
        name=name,
        primary_result=result['primary'],
        secondary_result=result['secondary'],
        detail_result=result['detail'],
        output_result=result['output'],
    )
