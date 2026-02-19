"""
Composition Guides Module - Viewport Overlay System

Provides composition guide overlays for cinematography composition rules
rendered as viewport annotations (grease pencil/annotations).

Usage:
    from lib.cinematic.composition import setup_composition_guides, show_rule_of_thirds, clear_guides

    # Show rule of thirds
    show_rule_of_thirds(opacity=0.5)

    # Show golden ratio
    show_golden_ratio(opacity=0.6, color=(1.0, 0.8, 0.0))

    # Setup from config
    setup_composition_guides(config)

    # Clear all guides
    clear_guides()
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple

from .types import CompositionGuide
from .enums import CompositionGuideType

# Blender availability check
try:
    import bpy
    import bmesh
    from mathutils import Vector
    BLENDER_AVAILABLE = True
except ImportError:
    bpy = None
    bmesh = None
    Vector = None
    BLENDER_AVAILABLE = False

# Constants for guide naming
GUIDE_COLLECTION_NAME = "CompositionGuides"
GUIDE_PREFIX = "guide_"

# Golden ratio (phi)
PHI = 1.618033988749895


def setup_composition_guides(config: CompositionGuide) -> bool:
    """
    Setup composition guide overlays from configuration.

    Creates viewport annotation layers based on the guide type.

    Args:
        config: CompositionGuide with guide settings

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Clear existing guides first
        clear_guides()

        if not config.enabled:
            return True

        # Setup based on guide type
        guide_type = config.guide_type if hasattr(config, 'guide_type') else 'rule_of_thirds'

        if guide_type == 'rule_of_thirds' or (hasattr(config, 'rule_of_thirds') and config.rule_of_thirds):
            show_rule_of_thirds(opacity=config.guide_opacity, color=tuple(config.guide_color[:3]))

        if guide_type == 'golden_ratio' or (hasattr(config, 'golden_ratio') and config.golden_ratio):
            show_golden_ratio(opacity=config.guide_opacity, color=tuple(config.guide_color[:3]))

        if guide_type == 'golden_spiral':
            show_golden_spiral(opacity=config.guide_opacity, color=tuple(config.guide_color[:3]))

        if guide_type == 'center_cross' or (hasattr(config, 'center_cross') and config.center_cross):
            show_center_cross(opacity=config.guide_opacity, color=tuple(config.guide_color[:3]))

        if guide_type == 'diagonal' or (hasattr(config, 'diagonal') and config.diagonal):
            show_diagonal_overlay(opacity=config.guide_opacity, color=tuple(config.guide_color[:3]))

        return True

    except Exception:
        return False


def create_guide_overlay(config: CompositionGuide) -> bool:
    """
    Create viewport annotation for composition guide.

    Args:
        config: CompositionGuide with settings

    Returns:
        True if successful
    """
    return setup_composition_guides(config)


def _get_or_create_guide_collection() -> Optional[Any]:
    """
    Get or create the composition guides collection.

    Returns:
        Collection or None if failed
    """
    if not BLENDER_AVAILABLE:
        return None

    try:
        # Check if collection exists
        if GUIDE_COLLECTION_NAME in bpy.data.collections:
            return bpy.data.collections[GUIDE_COLLECTION_NAME]

        # Create new collection
        collection = bpy.data.collections.new(GUIDE_COLLECTION_NAME)

        # Link to scene
        if bpy.context.scene:
            bpy.context.scene.collection.children.link(collection)

        # Hide from render
        collection.hide_render = True

        return collection

    except Exception:
        return None


def _create_guide_line(
    start: Tuple[float, float, float],
    end: Tuple[float, float, float],
    name: str,
    color: Tuple[float, float, float] = (1.0, 0.5, 0.0),
    opacity: float = 0.5
) -> bool:
    """
    Create a single guide line as a mesh object.

    Args:
        start: Start position (x, y, z)
        end: End position (x, y, z)
        name: Object name
        color: RGB color
        opacity: Line opacity

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        collection = _get_or_create_guide_collection()
        if collection is None:
            return False

        # Create mesh
        mesh = bpy.data.meshes.new(name)

        # Create line vertices
        verts = [start, end]
        edges = [(0, 1)]

        mesh.from_pydata(verts, edges, [])

        # Create object
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)

        # Set display properties
        obj.display_type = 'WIRE'
        obj.hide_render = True
        obj.show_in_front = True  # Always visible in front

        # Create material
        mat = bpy.data.materials.new(f"{name}_mat")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes

        # Setup emission for visibility
        emission = nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = (*color, opacity)
        emission.inputs['Strength'].default_value = 1.0

        output = nodes.get('Material Output')
        if output:
            mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

        obj.data.materials.append(mat)

        return True

    except Exception:
        return False


def show_rule_of_thirds(
    opacity: float = 0.5,
    color: Tuple[float, float, float] = (1.0, 0.5, 0.0)
) -> bool:
    """
    Display rule of thirds grid overlay.

    Creates 2 vertical + 2 horizontal lines at 1/3 intervals.

    Args:
        opacity: Line opacity (0-1)
        color: RGB color tuple

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Get render resolution for aspect ratio
        render = bpy.context.scene.render
        aspect = render.resolution_x / render.resolution_y if render.resolution_y > 0 else 16/9

        # Scale factor for guide size
        scale = 10.0

        # Calculate thirds
        third_h = scale / 3
        third_w = scale * aspect / 3

        # Create 4 lines (2 vertical, 2 horizontal)
        # Vertical lines at 1/3 and 2/3
        _create_guide_line(
            (-scale * aspect / 3, 0, -scale / 2),
            (-scale * aspect / 3, 0, scale / 2),
            f"{GUIDE_PREFIX}rot_v1",
            color, opacity
        )
        _create_guide_line(
            (scale * aspect / 3, 0, -scale / 2),
            (scale * aspect / 3, 0, scale / 2),
            f"{GUIDE_PREFIX}rot_v2",
            color, opacity
        )

        # Horizontal lines at 1/3 and 2/3
        _create_guide_line(
            (-scale * aspect / 2, 0, -scale / 3),
            (scale * aspect / 2, 0, -scale / 3),
            f"{GUIDE_PREFIX}rot_h1",
            color, opacity
        )
        _create_guide_line(
            (-scale * aspect / 2, 0, scale / 3),
            (scale * aspect / 2, 0, scale / 3),
            f"{GUIDE_PREFIX}rot_h2",
            color, opacity
        )

        return True

    except Exception:
        return False


def create_rule_of_thirds_overlay(
    opacity: float = 0.5,
    color: Tuple[float, float, float] = (1.0, 0.5, 0.0)
) -> bool:
    """Alias for show_rule_of_thirds() for backward compatibility."""
    return show_rule_of_thirds(opacity, color)


def show_golden_ratio(
    opacity: float = 0.5,
    color: Tuple[float, float, float] = (1.0, 0.8, 0.0)
) -> bool:
    """
    Display golden ratio (phi) composition overlay.

    Creates divisions at golden ratio intervals (1/phi and 1/phi^2).

    Args:
        opacity: Line opacity (0-1)
        color: RGB color tuple

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        render = bpy.context.scene.render
        aspect = render.resolution_x / render.resolution_y if render.resolution_y > 0 else 16/9

        scale = 10.0

        # Golden ratio positions
        golden_pos = scale / PHI
        golden_neg = scale - golden_pos

        golden_w = scale * aspect / PHI
        golden_w_neg = scale * aspect - golden_w

        # Vertical lines at golden ratio
        _create_guide_line(
            (-golden_w, 0, -scale / 2),
            (-golden_w, 0, scale / 2),
            f"{GUIDE_PREFIX}phi_v1",
            color, opacity
        )
        _create_guide_line(
            (golden_w_neg - scale * aspect / 2, 0, -scale / 2),
            (golden_w_neg - scale * aspect / 2, 0, scale / 2),
            f"{GUIDE_PREFIX}phi_v2",
            color, opacity
        )

        # Horizontal lines at golden ratio
        _create_guide_line(
            (-scale * aspect / 2, 0, -golden_pos),
            (scale * aspect / 2, 0, -golden_pos),
            f"{GUIDE_PREFIX}phi_h1",
            color, opacity
        )
        _create_guide_line(
            (-scale * aspect / 2, 0, golden_neg - scale / 2),
            (scale * aspect / 2, 0, golden_neg - scale / 2),
            f"{GUIDE_PREFIX}phi_h2",
            color, opacity
        )

        return True

    except Exception:
        return False


def create_golden_ratio_overlay(
    opacity: float = 0.5,
    color: Tuple[float, float, float] = (1.0, 0.8, 0.0)
) -> bool:
    """Alias for show_golden_ratio() for backward compatibility."""
    return show_golden_ratio(opacity, color)


def show_golden_spiral(
    opacity: float = 0.4,
    color: Tuple[float, float, float] = (0.0, 0.8, 1.0)
) -> bool:
    """
    Display golden spiral overlay.

    Approximates the Fibonacci spiral with arc segments.

    Args:
        opacity: Line opacity (0-1)
        color: RGB color tuple

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # For now, create a simplified version with corner arcs
        # A full implementation would use curve objects

        scale = 5.0

        # Create corner markers representing spiral focus points
        corners = [
            (scale / PHI, scale / PHI),
            (-scale / PHI, scale / PHI),
            (-scale / PHI, -scale / PHI),
            (scale / PHI, -scale / PHI),
        ]

        for i, (cx, cy) in enumerate(corners):
            # Create small cross at each focus point
            _create_guide_line(
                (cx - 0.3, 0, cy),
                (cx + 0.3, 0, cy),
                f"{GUIDE_PREFIX}spiral_h{i}",
                color, opacity
            )
            _create_guide_line(
                (cx, 0, cy - 0.3),
                (cx, 0, cy + 0.3),
                f"{GUIDE_PREFIX}spiral_v{i}",
                color, opacity
            )

        return True

    except Exception:
        return False


def show_center_cross(
    opacity: float = 0.3,
    color: Tuple[float, float, float] = (1.0, 0.0, 0.0)
) -> bool:
    """
    Display center crosshair overlay.

    Single vertical + horizontal through center.

    Args:
        opacity: Line opacity (0-1)
        color: RGB color tuple

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        render = bpy.context.scene.render
        aspect = render.resolution_x / render.resolution_y if render.resolution_y > 0 else 16/9

        scale = 10.0

        # Vertical center line
        _create_guide_line(
            (0, 0, -scale / 2),
            (0, 0, scale / 2),
            f"{GUIDE_PREFIX}center_v",
            color, opacity
        )

        # Horizontal center line
        _create_guide_line(
            (-scale * aspect / 2, 0, 0),
            (scale * aspect / 2, 0, 0),
            f"{GUIDE_PREFIX}center_h",
            color, opacity
        )

        return True

    except Exception:
        return False


def show_diagonal_overlay(
    opacity: float = 0.4,
    color: Tuple[float, float, float] = (0.5, 0.5, 0.5)
) -> bool:
    """
    Display diagonal composition overlay.

    Creates diagonal lines from corners.

    Args:
        opacity: Line opacity (0-1)
        color: RGB color tuple

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        render = bpy.context.scene.render
        aspect = render.resolution_x / render.resolution_y if render.resolution_y > 0 else 16/9

        scale = 10.0
        half_w = scale * aspect / 2
        half_h = scale / 2

        # Diagonal from top-left to bottom-right
        _create_guide_line(
            (-half_w, 0, half_h),
            (half_w, 0, -half_h),
            f"{GUIDE_PREFIX}diag_1",
            color, opacity
        )

        # Diagonal from top-right to bottom-left
        _create_guide_line(
            (half_w, 0, half_h),
            (-half_w, 0, -half_h),
            f"{GUIDE_PREFIX}diag_2",
            color, opacity
        )

        return True

    except Exception:
        return False


def show_safe_areas(
    opacity: float = 0.3,
    color: Tuple[float, float, float] = (0.5, 0.5, 0.5)
) -> bool:
    """
    Display title safe (90%) and action safe (93%) areas.

    Standard broadcast safe zones for TV/film.

    Args:
        opacity: Line opacity (0-1)
        color: RGB color tuple

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        render = bpy.context.scene.render
        aspect = render.resolution_x / render.resolution_y if render.resolution_y > 0 else 16/9

        scale = 10.0
        half_w = scale * aspect / 2
        half_h = scale / 2

        # Action safe (93%)
        action_scale = 0.93
        action_w = half_w * action_scale
        action_h = half_h * action_scale

        # Create action safe rectangle
        _create_guide_line((-action_w, 0, action_h), (action_w, 0, action_h), f"{GUIDE_PREFIX}safe_action_top", color, opacity)
        _create_guide_line((-action_w, 0, -action_h), (action_w, 0, -action_h), f"{GUIDE_PREFIX}safe_action_bottom", color, opacity)
        _create_guide_line((-action_w, 0, -action_h), (-action_w, 0, action_h), f"{GUIDE_PREFIX}safe_action_left", color, opacity)
        _create_guide_line((action_w, 0, -action_h), (action_w, 0, action_h), f"{GUIDE_PREFIX}safe_action_right", color, opacity)

        # Title safe (90%)
        title_scale = 0.90
        title_w = half_w * title_scale
        title_h = half_h * title_scale

        # Create title safe rectangle
        _create_guide_line((-title_w, 0, title_h), (title_w, 0, title_h), f"{GUIDE_PREFIX}safe_title_top", color, opacity * 0.7)
        _create_guide_line((-title_w, 0, -title_h), (title_w, 0, -title_h), f"{GUIDE_PREFIX}safe_title_bottom", color, opacity * 0.7)
        _create_guide_line((-title_w, 0, -title_h), (-title_w, 0, title_h), f"{GUIDE_PREFIX}safe_title_left", color, opacity * 0.7)
        _create_guide_line((title_w, 0, -title_h), (title_w, 0, title_h), f"{GUIDE_PREFIX}safe_title_right", color, opacity * 0.7)

        return True

    except Exception:
        return False


def clear_guides() -> bool:
    """
    Remove all composition guide overlays.

    Returns:
        True if successful
    """
    if not BLENDER_AVAILABLE:
        return False

    try:
        # Remove guide collection and all its objects
        if GUIDE_COLLECTION_NAME in bpy.data.collections:
            collection = bpy.data.collections[GUIDE_COLLECTION_NAME]

            # Unlink from scene
            for scene in bpy.data.scenes:
                if collection.name in scene.collection.children:
                    scene.collection.children.unlink(collection)

            # Remove objects
            for obj in collection.objects:
                if obj.data:
                    bpy.data.meshes.remove(obj.data)
                bpy.data.objects.remove(obj)

            # Remove collection
            bpy.data.collections.remove(collection)

        # Also remove any orphaned guide objects
        for obj in bpy.data.objects:
            if obj.name.startswith(GUIDE_PREFIX):
                if obj.data:
                    mesh = obj.data
                    bpy.data.objects.remove(obj)
                    if mesh.users == 0:
                        bpy.data.meshes.remove(mesh)

        return True

    except Exception:
        return False


def remove_composition_guides() -> bool:
    """Alias for clear_guides() for backward compatibility."""
    return clear_guides()


def get_active_guides() -> List[str]:
    """
    Return list of currently active guide types.

    Returns:
        List of guide type names
    """
    if not BLENDER_AVAILABLE:
        return []

    active = []

    try:
        if GUIDE_COLLECTION_NAME in bpy.data.collections:
            collection = bpy.data.collections[GUIDE_COLLECTION_NAME]

            for obj in collection.objects:
                name = obj.name
                if "rot" in name and "rule_of_thirds" not in active:
                    active.append("rule_of_thirds")
                elif "phi" in name and "golden_ratio" not in active:
                    active.append("golden_ratio")
                elif "spiral" in name and "golden_spiral" not in active:
                    active.append("golden_spiral")
                elif "center" in name and "center_cross" not in active:
                    active.append("center_cross")
                elif "diag" in name and "diagonal" not in active:
                    active.append("diagonal")
                elif "safe" in name and "safe_areas" not in active:
                    active.append("safe_areas")

    except Exception:
        pass

    return active
