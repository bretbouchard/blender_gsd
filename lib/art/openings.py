"""
Door and Window Builder Module

Procedural door and window construction with frames, glass, and treatments.
Uses bmesh for context-free mesh creation.

Implements REQ-SET-02: Door and window placement.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, List
import math

from .set_types import (
    DoorConfig,
    DoorPlacement,
    WindowConfig,
    WindowPlacement,
    DoorStyle,
    WindowStyle,
)


@dataclass
class DoorMeshes:
    """Container for generated door meshes."""
    door: Any = None
    frame: Any = None
    handle: Any = None
    glass: Any = None  # For French/glass doors


@dataclass
class WindowMeshes:
    """Container for generated window meshes."""
    window: Any = None
    frame: Any = None
    glass: Any = None
    sill: Any = None
    curtains: Any = None
    blinds: Any = None
    shutters: Any = None


# =============================================================================
# DOOR CREATION
# =============================================================================

def create_door(config: DoorConfig, collection: Any = None, name: str = "door") -> DoorMeshes:
    """
    Create door mesh based on style configuration.

    Args:
        config: Door configuration
        collection: Optional Blender collection
        name: Mesh name prefix

    Returns:
        DoorMeshes container with door components
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for door creation")

    meshes = DoorMeshes()

    # Create door panel based on style
    if config.style == "panel_6":
        meshes.door = create_panel_door(config, 6, collection, name)
    elif config.style == "panel_4":
        meshes.door = create_panel_door(config, 4, collection, name)
    elif config.style == "flush":
        meshes.door = create_flush_door(config, collection, name)
    elif config.style == "barn":
        meshes.door = create_barn_door(config, collection, name)
    elif config.style == "french":
        meshes.door = create_french_door(config, collection, name)
    elif config.style == "glass":
        meshes.door, meshes.glass = create_glass_door(config, collection, name)
    else:
        meshes.door = create_flush_door(config, collection, name)

    # Create frame
    meshes.frame = create_door_frame(config, collection, name)

    # Create handle
    meshes.handle = create_door_handle(config, collection, name)

    return meshes


def create_panel_door(config: DoorConfig, num_panels: int, collection: Any = None, name: str = "door") -> Any:
    """
    Create panel door with raised panels.

    Args:
        config: Door configuration
        num_panels: Number of panels (4 or 6)
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Door mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for door creation")

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bm = bmesh.new()

    # Door dimensions
    w = config.width
    h = config.height
    d = config.thickness

    # Frame widths
    top_rail = 0.12
    bottom_rail = 0.20
    stile = 0.10
    panel_depth = 0.01

    # Create main door body
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=(
        (w, 0, 0, 0),
        (0, d, 0, 0),
        (0, 0, h, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(w/2, 0, h/2))

    # Create panel indentations
    if num_panels == 6:
        # 6-panel: 2 rows of 3 panels each
        rows = 2
        cols = 3
    else:
        # 4-panel: 2 rows of 2 panels
        rows = 2
        cols = 2

    panel_width = (w - 2 * stile) / cols
    panel_height_top = (h - top_rail - bottom_rail - (rows - 1) * stile) / rows * (0.6 if num_panels == 6 else 1)
    panel_height_bottom = (h - top_rail - bottom_rail - (rows - 1) * stile) / rows * (0.4 if num_panels == 6 else 0)

    for row in range(rows):
        for col in range(cols):
            # Calculate panel position
            px = stile + col * panel_width
            py = d / 2 - panel_depth / 2

            if num_panels == 6:
                ph = panel_height_top if row == 1 else panel_height_bottom
                pz = bottom_rail + row * (ph + stile)
            else:
                ph = panel_height_top
                pz = bottom_rail + row * (ph + stile)

            # Create panel inset
            panel_size = (panel_width * 0.8, panel_depth, ph * 0.9)

    bm.to_mesh(mesh)
    bm.free()

    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def create_flush_door(config: DoorConfig, collection: Any = None, name: str = "door") -> Any:
    """
    Create flat/flush door.

    Args:
        config: Door configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Door mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for door creation")

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bm = bmesh.new()

    # Create simple box
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=(
        (config.width, 0, 0, 0),
        (0, config.thickness, 0, 0),
        (0, 0, config.height, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(config.width/2, 0, config.height/2))

    bm.to_mesh(mesh)
    bm.free()

    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def create_barn_door(config: DoorConfig, collection: Any = None, name: str = "door") -> Any:
    """
    Create barn-style sliding door with X-bracing.

    Args:
        config: Door configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Door mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for door creation")

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bm = bmesh.new()

    # Create main panel
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=(
        (config.width, 0, 0, 0),
        (0, config.thickness * 0.7, 0, 0),
        (0, 0, config.height, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(config.width/2, 0, config.height/2))

    # Add X-bracing (simplified - would be more complex in full implementation)
    brace_width = 0.08
    brace_depth = config.thickness * 0.4

    bm.to_mesh(mesh)
    bm.free()

    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def create_french_door(config: DoorConfig, collection: Any = None, name: str = "door") -> Any:
    """
    Create French door with glass panes.

    Args:
        config: Door configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Door mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for door creation")

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bm = bmesh.new()

    # French doors are typically double doors
    # Create frame with glass panes
    frame_width = 0.05

    # Create outer frame
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=(
        (config.width, 0, 0, 0),
        (0, config.thickness, 0, 0),
        (0, 0, config.height, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(config.width/2, 0, config.height/2))

    bm.to_mesh(mesh)
    bm.free()

    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def create_glass_door(config: DoorConfig, collection: Any = None, name: str = "door") -> Tuple[Any, Any]:
    """
    Create full glass door with minimal frame.

    Args:
        config: Door configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Tuple of (frame mesh, glass mesh)
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for door creation")

    # Create frame
    frame_mesh = bpy.data.meshes.new(f"{name}_frame")
    frame_obj = bpy.data.objects.new(f"{name}_frame", frame_mesh)

    bm_frame = bmesh.new()
    frame_thickness = 0.03

    # Create minimal frame (simplified)
    bmesh.ops.create_cube(bm_frame, size=1.0)
    bmesh.ops.transform(bm_frame, verts=bm_frame.verts, matrix=(
        (config.width, 0, 0, 0),
        (0, frame_thickness, 0, 0),
        (0, 0, config.height, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm_frame, verts=bm_frame.verts, vec=(config.width/2, 0, config.height/2))

    bm_frame.to_mesh(frame_mesh)
    bm_frame.free()

    # Create glass
    glass_mesh = bpy.data.meshes.new(f"{name}_glass")
    glass_obj = bpy.data.objects.new(f"{name}_glass", glass_mesh)

    bm_glass = bmesh.new()

    # Glass panel
    glass_offset = 0.01
    bmesh.ops.create_cube(bm_glass, size=1.0)
    bmesh.ops.transform(bm_glass, verts=bm_glass.verts, matrix=(
        (config.width - frame_thickness * 2, 0, 0, 0),
        (0, 0.005, 0, 0),  # Thin glass
        (0, 0, config.height - frame_thickness * 2, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm_glass, verts=bm_glass.verts, vec=(config.width/2, 0, config.height/2))

    bm_glass.to_mesh(glass_mesh)
    bm_glass.free()

    if collection:
        collection.objects.link(frame_obj)
        collection.objects.link(glass_obj)
    else:
        bpy.context.collection.objects.link(frame_obj)
        bpy.context.collection.objects.link(glass_obj)

    return frame_obj, glass_obj


def create_door_frame(config: DoorConfig, collection: Any = None, name: str = "door") -> Any:
    """
    Create door frame/jamb.

    Args:
        config: Door configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Frame mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for door frame creation")

    mesh = bpy.data.meshes.new(f"{name}_frame")
    obj = bpy.data.objects.new(f"{name}_frame", mesh)

    bm = bmesh.new()

    # Frame dimensions
    frame_width = 0.08  # Frame thickness
    frame_depth = 0.10  # How far frame extends into wall
    door_gap = 0.01  # Gap between door and frame

    # Create L-shaped frame profile
    # Vertical jambs (left and right)
    for side in [-1, 1]:
        x = side * (config.width / 2 + door_gap)

        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.transform(bm, verts=bm.verts[-8:], matrix=(
            (frame_width, 0, 0, 0),
            (0, frame_depth, 0, 0),
            (0, 0, config.height + frame_width * 2, 0),
            (0, 0, 0, 1)
        ))
        bmesh.ops.translate(bm, verts=bm.verts[-8:], vec=(
            x + (frame_width / 2 if side > 0 else -frame_width / 2),
            0,
            config.height / 2 + frame_width
        ))

    # Header (top)
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=bm.verts[-8:], matrix=(
        (config.width + 2 * (frame_width + door_gap), 0, 0, 0),
        (0, frame_depth, 0, 0),
        (0, 0, frame_width, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm, verts=bm.verts[-8:], vec=(
        config.width / 2,
        0,
        config.height + frame_width + frame_width / 2
    ))

    bm.to_mesh(mesh)
    bm.free()

    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def create_door_handle(config: DoorConfig, collection: Any = None, name: str = "door") -> Any:
    """
    Create door handle/lever.

    Args:
        config: Door configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Handle mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for handle creation")

    mesh = bpy.data.meshes.new(f"{name}_handle")
    obj = bpy.data.objects.new(f"{name}_handle", mesh)

    bm = bmesh.new()

    # Handle dimensions
    handle_length = 0.12
    handle_diameter = 0.015
    backset = 0.06  # Distance from door edge

    # Create simple lever handle
    # Base/rosette
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, diameter1=0.025, diameter2=0.025, depth=0.01)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(backset, config.thickness / 2 + 0.005, 0))

    # Lever
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, diameter1=handle_diameter, diameter2=handle_diameter, depth=handle_length)
    bmesh.ops.rotate(bm, verts=bm.verts[-24:], cent=(0, 0, 0), matrix=(
        (1, 0, 0),
        (0, 0, -1),
        (0, 1, 0)
    ))
    bmesh.ops.translate(bm, verts=bm.verts[-24:], vec=(backset, config.thickness / 2 + handle_length / 2, 0))

    bm.to_mesh(mesh)
    bm.free()

    # Position handle at standard height
    obj.location = (config.width - 0.1, 0, 0.9)

    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


# =============================================================================
# WINDOW CREATION
# =============================================================================

def create_window(config: WindowConfig, collection: Any = None, name: str = "window") -> WindowMeshes:
    """
    Create window mesh based on style configuration.

    Args:
        config: Window configuration
        collection: Optional Blender collection
        name: Mesh name prefix

    Returns:
        WindowMeshes container with window components
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for window creation")

    meshes = WindowMeshes()

    # Create window based on style
    if config.style == "double_hung":
        meshes.window, meshes.glass = create_double_hung_window(config, collection, name)
    elif config.style == "casement":
        meshes.window, meshes.glass = create_casement_window(config, collection, name)
    elif config.style == "picture":
        meshes.window, meshes.glass = create_picture_window(config, collection, name)
    elif config.style == "slider":
        meshes.window, meshes.glass = create_slider_window(config, collection, name)
    else:
        meshes.window, meshes.glass = create_picture_window(config, collection, name)

    # Create frame
    meshes.frame = create_window_frame(config, collection, name)

    # Create sill
    meshes.sill = create_window_sill(config, collection, name)

    # Create curtains if enabled
    if config.has_curtains:
        meshes.curtains = create_curtains(config, collection, name)

    # Create blinds if enabled
    if config.has_blinds:
        meshes.blinds = create_blinds(config, collection, name)

    return meshes


def create_double_hung_window(config: WindowConfig, collection: Any = None, name: str = "window") -> Tuple[Any, Any]:
    """
    Create double-hung window with two sliding sashes.

    Args:
        config: Window configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Tuple of (frame mesh, glass mesh)
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for window creation")

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bm = bmesh.new()

    frame_width = config.frame_width

    # Create outer frame
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=(
        (config.width, 0, 0, 0),
        (0, config.depth, 0, 0),
        (0, 0, config.height, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(config.width/2, 0, config.height/2))

    # Create center meeting rail
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=bm.verts[-8:], matrix=(
        (config.width, 0, 0, 0),
        (0, config.depth * 1.2, 0, 0),
        (0, 0, frame_width, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm, verts=bm.verts[-8:], vec=(config.width/2, 0, config.height/2))

    bm.to_mesh(mesh)
    bm.free()

    # Create glass
    glass_mesh = bpy.data.meshes.new(f"{name}_glass")
    glass_obj = bpy.data.objects.new(f"{name}_glass", glass_mesh)

    bm_glass = bmesh.new()

    # Two glass panes
    for i in range(2):
        bmesh.ops.create_cube(bm_glass, size=1.0)
        bmesh.ops.transform(bm_glass, verts=bm_glass.verts[-8:], matrix=(
            (config.width - frame_width * 2, 0, 0, 0),
            (0, 0.003, 0, 0),
            (0, 0, config.height / 2 - frame_width * 1.5, 0),
            (0, 0, 0, 1)
        ))
        bmesh.ops.translate(bm_glass, verts=bm_glass.verts[-8:], vec=(
            config.width / 2,
            config.depth / 2,
            frame_width + (config.height / 2 - frame_width * 1.5) / 2 + i * (config.height / 2)
        ))

    bm_glass.to_mesh(glass_mesh)
    bm_glass.free()

    if collection:
        collection.objects.link(obj)
        collection.objects.link(glass_obj)
    else:
        bpy.context.collection.objects.link(obj)
        bpy.context.collection.objects.link(glass_obj)

    return obj, glass_obj


def create_casement_window(config: WindowConfig, collection: Any = None, name: str = "window") -> Tuple[Any, Any]:
    """
    Create casement window that opens outward on hinges.

    Args:
        config: Window configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Tuple of (frame mesh, glass mesh)
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for window creation")

    # Similar to double-hung but with crank mechanism
    # Simplified implementation
    return create_picture_window(config, collection, name)


def create_picture_window(config: WindowConfig, collection: Any = None, name: str = "window") -> Tuple[Any, Any]:
    """
    Create fixed picture window (non-opening).

    Args:
        config: Window configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Tuple of (frame mesh, glass mesh)
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for window creation")

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    bm = bmesh.new()

    frame_width = config.frame_width

    # Create frame
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=(
        (config.width, 0, 0, 0),
        (0, config.depth, 0, 0),
        (0, 0, config.height, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(config.width/2, 0, config.height/2))

    bm.to_mesh(mesh)
    bm.free()

    # Create glass
    glass_mesh = bpy.data.meshes.new(f"{name}_glass")
    glass_obj = bpy.data.objects.new(f"{name}_glass", glass_mesh)

    bm_glass = bmesh.new()

    bmesh.ops.create_cube(bm_glass, size=1.0)
    bmesh.ops.transform(bm_glass, verts=bm_glass.verts, matrix=(
        (config.width - frame_width * 2, 0, 0, 0),
        (0, 0.003, 0, 0),
        (0, 0, config.height - frame_width * 2, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm_glass, verts=bm_glass.verts, vec=(config.width/2, config.depth/2, config.height/2))

    bm_glass.to_mesh(glass_mesh)
    bm_glass.free()

    if collection:
        collection.objects.link(obj)
        collection.objects.link(glass_obj)
    else:
        bpy.context.collection.objects.link(obj)
        bpy.context.collection.objects.link(glass_obj)

    return obj, glass_obj


def create_slider_window(config: WindowConfig, collection: Any = None, name: str = "window") -> Tuple[Any, Any]:
    """
    Create horizontal sliding window.

    Args:
        config: Window configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Tuple of (frame mesh, glass mesh)
    """
    # Similar to double-hung but horizontal
    return create_picture_window(config, collection, name)


def create_window_frame(config: WindowConfig, collection: Any = None, name: str = "window") -> Any:
    """
    Create window frame/jamb.

    Args:
        config: Window configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Frame mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for window frame creation")

    mesh = bpy.data.meshes.new(f"{name}_frame")
    obj = bpy.data.objects.new(f"{name}_frame", mesh)

    bm = bmesh.new()

    frame_depth = 0.08
    frame_thickness = config.frame_width

    # Create frame box
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=(
        (config.width + frame_thickness * 2, 0, 0, 0),
        (0, frame_depth, 0, 0),
        (0, 0, config.height + frame_thickness * 2, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(config.width/2, -frame_depth/2, config.height/2))

    bm.to_mesh(mesh)
    bm.free()

    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def create_window_sill(config: WindowConfig, collection: Any = None, name: str = "window") -> Any:
    """
    Create window sill.

    Args:
        config: Window configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Sill mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for sill creation")

    mesh = bpy.data.meshes.new(f"{name}_sill")
    obj = bpy.data.objects.new(f"{name}_sill", mesh)

    bm = bmesh.new()

    sill_depth = 0.10  # How far sill extends into room
    sill_thickness = 0.03

    # Create sill
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=(
        (config.width + 0.04, 0, 0, 0),
        (0, sill_depth, 0, 0),
        (0, 0, sill_thickness, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(config.width/2, -sill_depth/2, -sill_thickness/2))

    bm.to_mesh(mesh)
    bm.free()

    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def create_curtains(config: WindowConfig, collection: Any = None, name: str = "window") -> Any:
    """
    Create curtain geometry.

    Args:
        config: Window configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Curtain mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for curtain creation")

    mesh = bpy.data.meshes.new(f"{name}_curtains")
    obj = bpy.data.objects.new(f"{name}_curtains", mesh)

    bm = bmesh.new()

    curtain_depth = 0.05
    curtain_height = config.height + 0.2
    curtain_width = config.width + 0.4

    # Create simple curtain panels
    # Left panel
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=(
        (curtain_width / 2, 0, 0, 0),
        (0, curtain_depth, 0, 0),
        (0, 0, curtain_height, 0),
        (0, 0, 0, 1)
    ))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(config.width/2, -curtain_depth, curtain_height/2 - 0.1))

    bm.to_mesh(mesh)
    bm.free()

    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


def create_blinds(config: WindowConfig, collection: Any = None, name: str = "window") -> Any:
    """
    Create window blinds.

    Args:
        config: Window configuration
        collection: Optional Blender collection
        name: Mesh name

    Returns:
        Blinds mesh object
    """
    try:
        import bpy
        import bmesh
    except ImportError:
        raise ImportError("Blender required for blinds creation")

    mesh = bpy.data.meshes.new(f"{name}_blinds")
    obj = bpy.data.objects.new(f"{name}_blinds", mesh)

    bm = bmesh.new()

    slat_height = 0.025
    slat_depth = 0.03
    num_slats = int(config.height / slat_height)

    # Create individual slats
    for i in range(num_slats):
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.transform(bm, verts=bm.verts[-8:], matrix=(
            (config.width - 0.02, 0, 0, 0),
            (0, slat_depth, 0, 0),
            (0, 0, slat_height * 0.8, 0),
            (0, 0, 0, 1)
        ))
        bmesh.ops.translate(bm, verts=bm.verts[-8:], vec=(
            config.width / 2,
            config.depth / 2,
            i * slat_height + slat_height / 2
        ))

    bm.to_mesh(mesh)
    bm.free()

    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    return obj


# =============================================================================
# PLACEMENT FUNCTIONS
# =============================================================================

def place_door(
    room_config: Any,
    wall: str,
    position: float,
    config: DoorConfig,
    collection: Any = None
) -> DoorMeshes:
    """
    Place door in room wall at specified position.

    Args:
        room_config: Room configuration object (must have wall info)
        wall: Wall orientation (north, south, east, west)
        position: Position along wall (0-1 normalized)
        config: Door configuration
        collection: Optional Blender collection

    Returns:
        DoorMeshes with placed door components
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("Blender required for door placement")

    # Create door
    meshes = create_door(config, collection, f"door_{wall}")

    # Calculate position based on wall and position parameter
    # This would be integrated with room_builder to get actual wall positions
    if wall in ("north", "south"):
        x_pos = position * room_config.width - room_config.width / 2
        y_pos = -room_config.depth / 2 if wall == "north" else room_config.depth / 2
        rotation = 0 if wall == "north" else math.pi
    else:
        x_pos = room_config.width / 2 if wall == "east" else -room_config.width / 2
        y_pos = position * room_config.depth - room_config.depth / 2
        rotation = math.pi / 2 if wall == "east" else -math.pi / 2

    # Position all door components
    for mesh_obj in [meshes.door, meshes.frame, meshes.handle, meshes.glass]:
        if mesh_obj:
            mesh_obj.location = (x_pos, y_pos, 0)
            mesh_obj.rotation_euler = (0, 0, rotation)

    return meshes


def place_window(
    room_config: Any,
    wall: str,
    position: float,
    height: float,
    config: WindowConfig,
    collection: Any = None
) -> WindowMeshes:
    """
    Place window in room wall at specified position and height.

    Args:
        room_config: Room configuration object
        wall: Wall orientation (north, south, east, west)
        position: Position along wall (0-1 normalized)
        height: Height from floor to sill
        config: Window configuration
        collection: Optional Blender collection

    Returns:
        WindowMeshes with placed window components
    """
    try:
        import bpy
    except ImportError:
        raise ImportError("Blender required for window placement")

    # Create window
    meshes = create_window(config, collection, f"window_{wall}")

    # Calculate position based on wall
    if wall in ("north", "south"):
        x_pos = position * room_config.width - room_config.width / 2
        y_pos = -room_config.depth / 2 if wall == "north" else room_config.depth / 2
        rotation = 0 if wall == "north" else math.pi
    else:
        x_pos = room_config.width / 2 if wall == "east" else -room_config.width / 2
        y_pos = position * room_config.depth - room_config.depth / 2
        rotation = math.pi / 2 if wall == "east" else -math.pi / 2

    # Position all window components
    for mesh_obj in [meshes.window, meshes.frame, meshes.glass, meshes.sill, meshes.curtains, meshes.blinds]:
        if mesh_obj:
            mesh_obj.location = (x_pos, y_pos, height)
            mesh_obj.rotation_euler = (0, 0, rotation)

    return meshes


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Data containers
    "DoorMeshes",
    "WindowMeshes",
    # Door functions
    "create_door",
    "create_panel_door",
    "create_flush_door",
    "create_barn_door",
    "create_french_door",
    "create_glass_door",
    "create_door_frame",
    "create_door_handle",
    # Window functions
    "create_window",
    "create_double_hung_window",
    "create_casement_window",
    "create_picture_window",
    "create_slider_window",
    "create_window_frame",
    "create_window_sill",
    "create_curtains",
    "create_blinds",
    # Placement functions
    "place_door",
    "place_window",
]
