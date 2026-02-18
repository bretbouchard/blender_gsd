"""
Fader Geometry Builder

Builds procedural fader/slider geometry using Blender Geometry Nodes:
- Fader knob/handle (square, rounded, angled, tapered)
- Track/guide system
- Scale markings
- LED meter segments

All components are generated procedurally for easy customization.
"""

from __future__ import annotations
import math
from typing import Any, Optional

import bpy
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit
from lib.control_system.faders import (
    FaderConfig, FaderKnobConfig, TrackConfig, ScaleConfig, LEDMeterConfig,
    FaderKnobStyle, TrackStyle, ScalePosition
)


# =============================================================================
# FADER KNOB BUILDER
# =============================================================================

def build_fader_knob(
    nk: NodeKit,
    config: FaderKnobConfig,
    travel_length: float,
    position: float,
    x: float,
    y: float
) -> Any:
    """
    Build fader knob/handle geometry.

    Args:
        nk: NodeKit instance
        config: FaderKnobConfig with parameters
        travel_length: Total travel length of fader
        position: Current position (0-1 normalized)
        x, y: Node position offset

    Returns:
        Geometry socket with knob geometry
    """
    X = x
    Y = y

    # Calculate Y position based on travel
    y_pos = position * travel_length

    if config.style == FaderKnobStyle.ROUNDED:
        geo = _build_rounded_knob(nk, config, X, Y)
    elif config.style == FaderKnobStyle.ANGLED:
        geo = _build_angled_knob(nk, config, X, Y)
    elif config.style == FaderKnobStyle.TAPERED:
        geo = _build_tapered_knob(nk, config, X, Y)
    else:
        # Default: SQUARE
        geo = _build_square_knob(nk, config, X, Y)

    # Position the knob at the current fader position
    transform = nk.n("GeometryNodeTransform", "KnobPosition", X + 400, Y)
    nk.link(geo, transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (0, 0, y_pos)

    return transform.outputs["Geometry"]


def _build_square_knob(nk: NodeKit, config: FaderKnobConfig, x: float, y: float) -> Any:
    """Build square fader knob."""
    # Create main cube
    cube = nk.n("GeometryNodeMeshCube", "KnobCube", x, y)
    cube.inputs["Size"].default_value = (config.width, config.depth, config.height)
    cube.inputs["Vertices X"].default_value = 2
    cube.inputs["Vertices Y"].default_value = 2
    cube.inputs["Vertices Z"].default_value = 2

    # Subdivide for corner rounding
    if config.corner_radius > 0:
        subdivide = nk.n("GeometryNodeSubdivisionSurface", "SubdivideKnob", x + 200, y)
        subdivide.inputs["Level"].default_value = 2
        nk.link(cube.outputs["Mesh"], subdivide.inputs["Mesh"])

        # Apply corner radius via shrink/fatten
        # Note: For simplicity, we'll skip complex beveling
        return subdivide.outputs["Mesh"]

    return cube.outputs["Mesh"]


def _build_rounded_knob(nk: NodeKit, config: FaderKnobConfig, x: float, y: float) -> Any:
    """Build rounded fader knob with curved top."""
    # Create base cube
    cube = nk.n("GeometryNodeMeshCube", "RoundedKnob", x, y)
    cube.inputs["Size"].default_value = (config.width, config.depth, config.height)
    cube.inputs["Vertices X"].default_value = 4
    cube.inputs["Vertices Y"].default_value = 4
    cube.inputs["Vertices Z"].default_value = 2

    # Subdivide for smoothing
    subdivide = nk.n("GeometryNodeSubdivisionSurface", "SmoothKnob", x + 200, y)
    subdivide.inputs["Level"].default_value = 3
    nk.link(cube.outputs["Mesh"], subdivide.inputs["Mesh"])

    return subdivide.outputs["Mesh"]


def _build_angled_knob(nk: NodeKit, config: FaderKnobConfig, x: float, y: float) -> Any:
    """Build angled fader knob (API style)."""
    # Create base with angle cut
    # For simplicity, use a cube with transform for angle illusion
    cube = nk.n("GeometryNodeMeshCube", "AngledKnob", x, y)
    cube.inputs["Size"].default_value = (config.width, config.depth, config.height)
    cube.inputs["Vertices X"].default_value = 2
    cube.inputs["Vertices Y"].default_value = 4  # Extra vertices for tapering
    cube.inputs["Vertices Z"].default_value = 2

    # Subdivide
    subdivide = nk.n("GeometryNodeSubdivisionSurface", "SubdivideAngled", x + 200, y)
    subdivide.inputs["Level"].default_value = 1
    nk.link(cube.outputs["Mesh"], subdivide.inputs["Mesh"])

    return subdivide.outputs["Mesh"]


def _build_tapered_knob(nk: NodeKit, config: FaderKnobConfig, x: float, y: float) -> Any:
    """Build tapered fader knob."""
    # Create tapered shape using cube with modified dimensions
    top_width = config.width * config.taper_ratio
    avg_width = (config.width + top_width) / 2

    cube = nk.n("GeometryNodeMeshCube", "TaperedKnob", x, y)
    cube.inputs["Size"].default_value = (avg_width, config.depth, config.height)
    cube.inputs["Vertices X"].default_value = 4
    cube.inputs["Vertices Y"].default_value = 2
    cube.inputs["Vertices Z"].default_value = 2

    subdivide = nk.n("GeometryNodeSubdivisionSurface", "SubdivideTapered", x + 200, y)
    subdivide.inputs["Level"].default_value = 2
    nk.link(cube.outputs["Mesh"], subdivide.inputs["Mesh"])

    return subdivide.outputs["Mesh"]


# =============================================================================
# TRACK BUILDER
# =============================================================================

def build_fader_track(
    nk: NodeKit,
    config: TrackConfig,
    travel_length: float,
    x: float,
    y: float
) -> Any:
    """
    Build fader track/guide geometry.

    Args:
        nk: NodeKit instance
        config: TrackConfig with parameters
        travel_length: Total travel length
        x, y: Node position offset

    Returns:
        Geometry socket with track geometry
    """
    X = x
    Y = y

    if config.style == TrackStyle.LED_SLOT:
        geo = _build_led_slot_track(nk, config, travel_length, X, Y)
    elif config.style == TrackStyle.COVERED_SLOT:
        geo = _build_covered_slot_track(nk, config, travel_length, X, Y)
    else:
        # Default: EXPOSED
        geo = _build_exposed_track(nk, config, travel_length, X, Y)

    # Add end caps if enabled
    if config.end_caps_enabled:
        geo = _add_end_caps(nk, geo, config, travel_length, X + 400, Y)

    return geo


def _build_exposed_track(nk: NodeKit, config: TrackConfig, travel_length: float, x: float, y: float) -> Any:
    """Build exposed metal rail track."""
    # Main rail
    rail = nk.n("GeometryNodeMeshCube", "Rail", x, y)
    rail.inputs["Size"].default_value = (config.width, config.depth, travel_length)
    rail.inputs["Vertices X"].default_value = 2
    rail.inputs["Vertices Y"].default_value = 2
    rail.inputs["Vertices Z"].default_value = 2

    # Position centered at travel midpoint
    transform = nk.n("GeometryNodeTransform", "RailTransform", x + 200, y)
    nk.link(rail.outputs["Mesh"], transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (0, 0, travel_length / 2)

    return transform.outputs["Geometry"]


def _build_covered_slot_track(nk: NodeKit, config: TrackConfig, travel_length: float, x: float, y: float) -> Any:
    """Build covered slot channel track."""
    # Inner slot (gap)
    slot_width = config.width * 0.6
    slot = nk.n("GeometryNodeMeshCube", "Slot", x, y)
    slot.inputs["Size"].default_value = (slot_width, config.depth * 0.5, travel_length)

    slot_transform = nk.n("GeometryNodeTransform", "SlotTransform", x + 100, y + 100)
    nk.link(slot.outputs["Mesh"], slot_transform.inputs["Geometry"])
    slot_transform.inputs["Translation"].default_value = (0, 0, travel_length / 2)

    # Outer rail (left side)
    left_rail = nk.n("GeometryNodeMeshCube", "LeftRail", x, y - 100)
    left_rail.inputs["Size"].default_value = ((config.width - slot_width) / 2, config.depth, travel_length)

    left_transform = nk.n("GeometryNodeTransform", "LeftTransform", x + 100, y - 100)
    nk.link(left_rail.outputs["Mesh"], left_transform.inputs["Geometry"])
    left_transform.inputs["Translation"].default_value = (-(config.width + slot_width) / 4, 0, travel_length / 2)

    # Outer rail (right side)
    right_rail = nk.n("GeometryNodeMeshCube", "RightRail", x, y + 100)
    right_rail.inputs["Size"].default_value = ((config.width - slot_width) / 2, config.depth, travel_length)

    right_transform = nk.n("GeometryNodeTransform", "RightTransform", x + 100, y + 100)
    nk.link(right_rail.outputs["Mesh"], right_transform.inputs["Geometry"])
    right_transform.inputs["Translation"].default_value = ((config.width + slot_width) / 4, 0, travel_length / 2)

    # Join rails
    join_rails = nk.n("GeometryNodeJoinGeometry", "JoinRails", x + 200, y)
    nk.link(left_transform.outputs["Geometry"], join_rails.inputs["Geometry"])
    nk.link(right_transform.outputs["Geometry"], join_rails.inputs["Geometry"])

    return join_rails.outputs["Geometry"]


def _build_led_slot_track(nk: NodeKit, config: TrackConfig, travel_length: float, x: float, y: float) -> Any:
    """Build LED slot track (slot with space for LED strip)."""
    # Similar to covered slot but with extra width for LEDs
    return _build_covered_slot_track(nk, config, travel_length, x, y)


def _add_end_caps(nk: NodeKit, geo_in: Any, config: TrackConfig, travel_length: float, x: float, y: float) -> Any:
    """Add end caps to track."""
    # Bottom cap
    bottom_cap = nk.n("GeometryNodeMeshCube", "BottomCap", x, y - 150)
    bottom_cap.inputs["Size"].default_value = (config.width * 1.2, config.depth * 1.2, config.end_cap_height)

    bottom_transform = nk.n("GeometryNodeTransform", "BottomCapTransform", x + 100, y - 150)
    nk.link(bottom_cap.outputs["Mesh"], bottom_transform.inputs["Geometry"])
    bottom_transform.inputs["Translation"].default_value = (0, 0, -config.end_cap_height / 2)

    # Top cap
    top_cap = nk.n("GeometryNodeMeshCube", "TopCap", x, y + 150)
    top_cap.inputs["Size"].default_value = (config.width * 1.2, config.depth * 1.2, config.end_cap_height)

    top_transform = nk.n("GeometryNodeTransform", "TopCapTransform", x + 100, y + 150)
    nk.link(top_cap.outputs["Mesh"], top_transform.inputs["Geometry"])
    top_transform.inputs["Translation"].default_value = (0, 0, travel_length + config.end_cap_height / 2)

    # Join all
    join = nk.n("GeometryNodeJoinGeometry", "JoinWithCaps", x + 200, y)
    nk.link(geo_in, join.inputs["Geometry"])
    nk.link(bottom_transform.outputs["Geometry"], join.inputs["Geometry"])
    nk.link(top_transform.outputs["Geometry"], join.inputs["Geometry"])

    return join.outputs["Geometry"]


# =============================================================================
# SCALE BUILDER
# =============================================================================

def build_scale(
    nk: NodeKit,
    config: ScaleConfig,
    travel_length: float,
    track_width: float,
    x: float,
    y: float
) -> Any:
    """
    Build scale marking geometry.

    Args:
        nk: NodeKit instance
        config: ScaleConfig with parameters
        travel_length: Total travel length
        track_width: Width of track for positioning
        x, y: Node position offset

    Returns:
        Geometry socket with scale geometry (or None if disabled)
    """
    if not config.enabled:
        return None

    X = x
    Y = y

    # Calculate number of ticks based on travel and spacing
    num_ticks = int(travel_length / config.tick_spacing) + 1

    # X offset based on position
    if config.position == ScalePosition.LEFT:
        x_offset = -(track_width + 0.005)
    elif config.position == ScalePosition.RIGHT:
        x_offset = track_width + 0.005
    else:
        x_offset = 0  # BOTH - handled differently

    # Build tick marks using grid of small cubes
    # For simplicity, we'll create a single representative tick
    # (full implementation would instance along the travel)

    # Major ticks at key positions
    major_tick_positions = [0.0, 0.5, 1.0]  # Bottom, middle, top

    geometries = []
    current_x = X

    # Create tick marks
    for i, pos in enumerate(major_tick_positions):
        z_pos = pos * travel_length

        is_major = i in [0, len(major_tick_positions) - 1] or pos == 0.5
        tick_height = config.major_tick_height if is_major else config.tick_height

        tick = nk.n("GeometryNodeMeshCube", f"Tick_{i}", current_x, Y + i * 100)
        tick.inputs["Size"].default_value = (config.tick_width, 0.001, tick_height)

        tick_transform = nk.n("GeometryNodeTransform", f"TickTransform_{i}", current_x + 100, Y + i * 100)
        nk.link(tick.outputs["Mesh"], tick_transform.inputs["Geometry"])
        tick_transform.inputs["Translation"].default_value = (x_offset, 0, z_pos)

        geometries.append(tick_transform.outputs["Geometry"])

    # Join all ticks
    if len(geometries) > 1:
        join = nk.n("GeometryNodeJoinGeometry", "JoinTicks", current_x + 200, Y)
        for geo in geometries:
            nk.link(geo, join.inputs["Geometry"])
        return join.outputs["Geometry"]
    elif len(geometries) == 1:
        return geometries[0]

    return None


# =============================================================================
# LED METER BUILDER
# =============================================================================

def build_led_meter(
    nk: NodeKit,
    config: LEDMeterConfig,
    travel_length: float,
    track_width: float,
    x: float,
    y: float
) -> Any:
    """
    Build LED meter geometry.

    Args:
        nk: NodeKit instance
        config: LEDMeterConfig with parameters
        travel_length: Total travel length
        track_width: Width of track for positioning
        x, y: Node position offset

    Returns:
        Geometry socket with LED meter geometry (or None if disabled)
    """
    if not config.enabled:
        return None

    X = x
    Y = y

    # X offset based on position
    if config.position == "beside_track":
        x_offset = track_width + 0.006
    else:
        x_offset = 0  # in_track

    # Calculate total meter height
    total_height = config.segment_count * (config.segment_height + config.segment_spacing)

    # Create segments
    segments = []
    for i in range(config.segment_count):
        # Z position from bottom to top
        z_pos = (i / (config.segment_count - 1)) * total_height if config.segment_count > 1 else 0

        segment = nk.n("GeometryNodeMeshCube", f"LED_{i}", X, Y + i * 80)
        segment.inputs["Size"].default_value = (
            config.segment_width,
            0.002,  # Thin depth
            config.segment_height - config.segment_spacing
        )

        segment_transform = nk.n("GeometryNodeTransform", f"LEDTransform_{i}", X + 100, Y + i * 80)
        nk.link(segment.outputs["Mesh"], segment_transform.inputs["Geometry"])
        segment_transform.inputs["Translation"].default_value = (x_offset, 0, z_pos)

        segments.append(segment_transform.outputs["Geometry"])

    # Join all segments
    join = nk.n("GeometryNodeJoinGeometry", "JoinLEDs", X + 200, Y)
    for seg in segments:
        nk.link(seg, join.inputs["Geometry"])

    return join.outputs["Geometry"]


# =============================================================================
# COMPLETE FADER BUILDER
# =============================================================================

def build_fader(
    nk: NodeKit,
    config: FaderConfig,
    x: float,
    y: float
) -> Any:
    """
    Build complete fader assembly.

    Args:
        nk: NodeKit instance
        config: FaderConfig with all parameters
        x, y: Node position offset

    Returns:
        Geometry socket with complete fader geometry
    """
    X = x
    Y = y

    geometries = []

    # 1. Build track
    track_geo = build_fader_track(nk, config.track, config.travel_length, X, Y - 200)
    if track_geo:
        geometries.append(track_geo)

    # 2. Build scale
    scale_geo = build_scale(nk, config.scale, config.travel_length, config.track.width, X, Y)
    if scale_geo:
        geometries.append(scale_geo)

    # 3. Build LED meter
    led_geo = build_led_meter(nk, config.led_meter, config.travel_length, config.track.width, X + 300, Y)
    if led_geo:
        geometries.append(led_geo)

    # 4. Build knob (on top of everything)
    knob_geo = build_fader_knob(nk, config.knob, config.travel_length, config.position, X, Y + 200)
    if knob_geo:
        geometries.append(knob_geo)

    # 5. Join all components
    if len(geometries) > 1:
        join = nk.n("GeometryNodeJoinGeometry", "JoinFader", X + 600, Y)
        for geo in geometries:
            nk.link(geo, join.inputs["Geometry"])
        return join.outputs["Geometry"]
    elif len(geometries) == 1:
        return geometries[0]

    return None


# =============================================================================
# MATERIAL CREATION
# =============================================================================

def create_fader_material(config: FaderConfig) -> bpy.types.Material:
    """
    Create materials for fader components.

    Returns a single material that can be used for the entire fader.
    For production, you'd want separate materials per component.
    """
    mat = bpy.data.materials.new("FaderMaterial")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*config.knob.color, 1.0)
    bsdf.inputs["Metallic"].default_value = config.knob.metallic
    bsdf.inputs["Roughness"].default_value = config.knob.roughness

    # Output
    output = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    return mat
