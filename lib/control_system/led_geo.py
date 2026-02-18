"""
LED/Indicator Geometry Builders

Geometry Nodes builders for procedural LED and indicator generation.

Builders:
- build_single_led(): Individual LED with optional bezel
- build_led_bar(): Multi-segment level meter
- build_vu_meter(): Analog-style needle meter (placeholder)
- build_seven_segment(): Numeric display (placeholder)
"""

from __future__ import annotations
from typing import Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from lib.nodekit import NodeKit

from .leds import (
    LEDConfig,
    LEDBarConfig,
    VUMeterConfig,
    SevenSegmentConfig,
    BezelConfig,
    ColorZone,
    LEDShape,
    LEDLens,
    BezelStyle,
    BarDirection,
    LEDType,
)


def build_bezel(
    nk: "NodeKit",
    bezel_config: BezelConfig,
    led_diameter: float,
    x: float = 0,
    y: float = 0
) -> Any:
    """
    Build LED bezel geometry.

    Args:
        nk: NodeKit instance
        bezel_config: Bezel configuration
        led_diameter: Diameter of LED (for inner cutout)
        x, y: Node positions

    Returns:
        Geometry output socket or None if bezel style is NONE
    """
    if bezel_config.style == BezelStyle.NONE:
        return None

    # Create outer cylinder for bezel
    outer = nk.n("GeometryNodeMeshCylinder", "BezelOuter", x, y)
    outer.inputs["Vertices"].default_value = 32
    outer.inputs["Radius"].default_value = bezel_config.diameter / 2
    outer.inputs["Depth"].default_value = bezel_config.height

    # Create inner cylinder for LED opening
    inner = nk.n("GeometryNodeMeshCylinder", "BezelInner", x + 100, y)
    inner.inputs["Vertices"].default_value = 32
    inner.inputs["Radius"].default_value = led_diameter / 2 + 0.0005  # Slight gap
    inner.inputs["Depth"].default_value = bezel_config.height + 0.001

    # Boolean difference
    bool_diff = nk.n("GeometryNodeMeshBoolean", "BezelBool", x + 200, y)
    bool_diff.operation = 'DIFFERENCE'
    nk.link(outer.outputs["Mesh"], bool_diff.inputs[0])
    nk.link(inner.outputs["Mesh"], bool_diff.inputs[1])

    # Position
    transform = nk.n("GeometryNodeTransform", "BezelTransform", x + 400, y)
    nk.link(bool_diff.outputs[0], transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (0, 0, bezel_config.height / 2)

    return transform.outputs["Geometry"]


def build_single_led(
    nk: "NodeKit",
    config: LEDConfig,
    x: float = 0,
    y: float = 0
) -> Any:
    """
    Build single LED indicator geometry.

    Args:
        nk: NodeKit instance
        config: LED configuration
        x, y: Node positions

    Returns:
        Geometry output socket
    """
    geometries = []
    led_diameter = config.get_diameter()
    led_height = config.get_height()

    # 1. Build bezel if enabled
    if config.bezel.style != BezelStyle.NONE:
        bezel_geo = build_bezel(nk, config.bezel, led_diameter, x, y)
        if bezel_geo:
            geometries.append(bezel_geo)

    # 2. Build LED body
    if config.shape == LEDShape.ROUND:
        # Round LED - cylinder
        led = nk.n("GeometryNodeMeshCylinder", "LEDBody", x + 600, y)
        led.inputs["Vertices"].default_value = 32
        led.inputs["Radius"].default_value = led_diameter / 2
        led.inputs["Depth"].default_value = led_height

        led_transform = nk.n("GeometryNodeTransform", "LEDTransform", x + 800, y)
        nk.link(led.outputs["Mesh"], led_transform.inputs["Geometry"])

        # Position on top of bezel or at base
        z_offset = led_height / 2
        if config.bezel.style != BezelStyle.NONE:
            z_offset += config.bezel.height
        led_transform.inputs["Translation"].default_value = (0, 0, z_offset)

        led_geo = led_transform.outputs["Geometry"]

    elif config.shape == LEDShape.SQUARE:
        # Square LED - cube
        led = nk.n("GeometryNodeMeshCube", "LEDBody", x + 600, y)
        led.inputs["Size"].default_value = (led_diameter, led_diameter, led_height)
        led.inputs["Vertices X"].default_value = 2
        led.inputs["Vertices Y"].default_value = 2
        led.inputs["Vertices Z"].default_value = 2

        led_transform = nk.n("GeometryNodeTransform", "LEDTransform", x + 800, y)
        nk.link(led.outputs["Mesh"], led_transform.inputs["Geometry"])

        z_offset = led_height / 2
        if config.bezel.style != BezelStyle.NONE:
            z_offset += config.bezel.height
        led_transform.inputs["Translation"].default_value = (0, 0, z_offset)

        led_geo = led_transform.outputs["Geometry"]

    elif config.shape == LEDShape.RECTANGULAR:
        # Rectangular LED
        led = nk.n("GeometryNodeMeshCube", "LEDBody", x + 600, y)
        led.inputs["Size"].default_value = (config.diameter or led_diameter * 2,
                                            led_diameter * 0.5, led_height)
        led.inputs["Vertices X"].default_value = 2
        led.inputs["Vertices Y"].default_value = 2
        led.inputs["Vertices Z"].default_value = 2

        led_transform = nk.n("GeometryNodeTransform", "LEDTransform", x + 800, y)
        nk.link(led.outputs["Mesh"], led_transform.inputs["Geometry"])

        z_offset = led_height / 2
        if config.bezel.style != BezelStyle.NONE:
            z_offset += config.bezel.height
        led_transform.inputs["Translation"].default_value = (0, 0, z_offset)

        led_geo = led_transform.outputs["Geometry"]

    else:
        # Default to round
        led = nk.n("GeometryNodeMeshCylinder", "LEDBody", x + 600, y)
        led.inputs["Vertices"].default_value = 32
        led.inputs["Radius"].default_value = led_diameter / 2
        led.inputs["Depth"].default_value = led_height

        led_transform = nk.n("GeometryNodeTransform", "LEDTransform", x + 800, y)
        nk.link(led.outputs["Mesh"], led_transform.inputs["Geometry"])
        led_transform.inputs["Translation"].default_value = (0, 0, led_height / 2)

        led_geo = led_transform.outputs["Geometry"]

    geometries.append(led_geo)

    # 3. Add lens dome if diffused
    if config.lens == LEDLens.DIFFUSED:
        led_geo = _build_diffused_lens(nk, led_geo, config, x + 1000, y)
        geometries[-1] = led_geo

    # 4. Join all geometries
    if len(geometries) == 1:
        return geometries[0]

    join = nk.n("GeometryNodeJoinGeometry", "JoinLED", x + 1200, y)
    for i, geo in enumerate(geometries):
        nk.link(geo, join.inputs["Geometry"])

    return join.outputs["Geometry"]


def _build_diffused_lens(
    nk: "NodeKit",
    led_geo: Any,
    config: LEDConfig,
    x: float,
    y: float
) -> Any:
    """Add diffused lens effect to LED (slight dome on top)."""
    # Create a small sphere for lens effect
    lens_diameter = config.get_diameter() * 0.8
    lens = nk.n("GeometryNodeMeshIcoSphere", "LensSphere", x, y + 100)
    lens.inputs["Radius"].default_value = lens_diameter / 2
    lens.inputs["Subdivisions"].default_value = 2

    # Scale to flatten slightly
    scale = nk.n("GeometryNodeTransform", "LensScale", x + 100, y + 100)
    nk.link(lens.outputs["Mesh"], scale.inputs["Geometry"])
    scale.inputs["Scale"].default_value = (1.0, 1.0, 0.3)

    # Position on top of LED
    z_offset = config.get_height()
    if config.bezel.style != BezelStyle.NONE:
        z_offset += config.bezel.height

    lens_transform = nk.n("GeometryNodeTransform", "LensTransform", x + 200, y + 100)
    nk.link(scale.outputs["Geometry"], lens_transform.inputs["Geometry"])
    lens_transform.inputs["Translation"].default_value = (0, 0, z_offset)

    # Join with LED body
    join = nk.n("GeometryNodeJoinGeometry", "JoinLens", x + 400, y)
    nk.link(led_geo, join.inputs["Geometry"])
    nk.link(lens_transform.outputs["Geometry"], join.inputs["Geometry"])

    return join.outputs["Geometry"]


def build_led_bar(
    nk: "NodeKit",
    config: LEDBarConfig,
    x: float = 0,
    y: float = 0
) -> Any:
    """
    Build LED bar/level meter geometry.

    Args:
        nk: NodeKit instance
        config: LED bar configuration
        x, y: Node positions

    Returns:
        Geometry output socket
    """
    segments = []

    # Calculate total bar length
    segment_size = config.segment_height if config.direction == BarDirection.VERTICAL else config.segment_width
    total_length = (config.segments * segment_size) + ((config.segments - 1) * config.segment_spacing)

    # Build each segment
    for i in range(config.segments):
        segment_x = x + i * 150  # Spread nodes horizontally
        segment_y = y

        # Create segment cube
        seg = nk.n("GeometryNodeMeshCube", f"Seg_{i}", segment_x, segment_y)
        seg.inputs["Size"].default_value = (
            config.segment_width,
            config.segment_depth,
            config.segment_height
        )
        seg.inputs["Vertices X"].default_value = 2
        seg.inputs["Vertices Y"].default_value = 2
        seg.inputs["Vertices Z"].default_value = 2

        # Position segment
        if config.direction == BarDirection.VERTICAL:
            # Stack segments vertically
            pos_z = i * (config.segment_height + config.segment_spacing)
            translation = (0, 0, pos_z)
        else:
            # Arrange horizontally
            pos_x = i * (config.segment_width + config.segment_spacing)
            translation = (pos_x, 0, 0)

        transform = nk.n("GeometryNodeTransform", f"SegTransform_{i}", segment_x + 100, segment_y)
        nk.link(seg.outputs["Mesh"], transform.inputs["Geometry"])
        transform.inputs["Translation"].default_value = translation

        segments.append(transform.outputs["Geometry"])

    # Join all segments
    current_geo = segments[0]
    for i, seg_geo in enumerate(segments[1:], 1):
        join = nk.n("GeometryNodeJoinGeometry", f"JoinSeg_{i}", x + i * 100 + 500, y)
        nk.link(current_geo, join.inputs["Geometry"])
        nk.link(seg_geo, join.inputs["Geometry"])
        current_geo = join.outputs["Geometry"]

    # Add frame if enabled
    if config.frame_enabled:
        frame_geo = _build_ledbar_frame(nk, config, x + 800, y - 200)
        if frame_geo:
            join_frame = nk.n("GeometryNodeJoinGeometry", "JoinFrame", x + 1000, y)
            nk.link(current_geo, join_frame.inputs["Geometry"])
            nk.link(frame_geo, join_frame.inputs["Geometry"])
            current_geo = join_frame.outputs["Geometry"]

    return current_geo


def _build_ledbar_frame(
    nk: "NodeKit",
    config: LEDBarConfig,
    x: float,
    y: float
) -> Any:
    """Build frame around LED bar."""
    # Calculate frame dimensions
    if config.direction == BarDirection.VERTICAL:
        frame_width = config.segment_width * 1.5
        frame_height = (config.segments * config.segment_height) + \
                       ((config.segments - 1) * config.segment_spacing) + 0.004
    else:
        frame_width = (config.segments * config.segment_width) + \
                      ((config.segments - 1) * config.segment_spacing) + 0.004
        frame_height = config.segment_height * 1.5

    # Create frame as thin cube
    frame = nk.n("GeometryNodeMeshCube", "Frame", x, y)
    frame.inputs["Size"].default_value = (frame_width, 0.002, frame_height)
    frame.inputs["Vertices X"].default_value = 2
    frame.inputs["Vertices Y"].default_value = 2
    frame.inputs["Vertices Z"].default_value = 2

    # Position frame behind LEDs
    transform = nk.n("GeometryNodeTransform", "FrameTransform", x + 100, y)
    nk.link(frame.outputs["Mesh"], transform.inputs["Geometry"])

    if config.direction == BarDirection.VERTICAL:
        center_z = ((config.segments * config.segment_height) +
                    ((config.segments - 1) * config.segment_spacing)) / 2
        transform.inputs["Translation"].default_value = (0, -0.003, center_z - config.segment_height / 2)
    else:
        center_x = ((config.segments * config.segment_width) +
                    ((config.segments - 1) * config.segment_spacing)) / 2
        transform.inputs["Translation"].default_value = (center_x - config.segment_width / 2, -0.003, 0)

    return transform.outputs["Geometry"]


def build_vu_meter(
    nk: "NodeKit",
    config: VUMeterConfig,
    x: float = 0,
    y: float = 0
) -> Any:
    """
    Build VU meter geometry (simplified placeholder).

    Creates a rectangular meter housing with needle representation.
    Full needle animation would require armature/bones.

    Args:
        nk: NodeKit instance
        config: VU meter configuration
        x, y: Node positions

    Returns:
        Geometry output socket
    """
    geometries = []

    # 1. Build meter housing (back case)
    housing = nk.n("GeometryNodeMeshCube", "VUHousing", x, y)
    housing.inputs["Size"].default_value = (config.width, config.depth, config.height)
    housing.inputs["Vertices X"].default_value = 2
    housing.inputs["Vertices Y"].default_value = 2
    housing.inputs["Vertices Z"].default_value = 2

    housing_transform = nk.n("GeometryNodeTransform", "HousingTransform", x + 100, y)
    nk.link(housing.outputs["Mesh"], housing_transform.inputs["Geometry"])
    housing_transform.inputs["Translation"].default_value = (0, 0, config.height / 2)

    geometries.append(housing_transform.outputs["Geometry"])

    # 2. Build needle (simplified as thin cylinder)
    needle = nk.n("GeometryNodeMeshCube", "Needle", x, y + 100)
    needle.inputs["Size"].default_value = (config.needle_width, 0.0005, config.needle_length)
    needle.inputs["Vertices X"].default_value = 1
    needle.inputs["Vertices Y"].default_value = 1
    needle.inputs["Vertices Z"].default_value = 1

    # Calculate needle angle based on value (-20 to +3 dB maps to -45 to +45 degrees)
    # Simplified: assume value 0-1 maps to angle range
    import math
    angle = math.radians(-45 + (config.value * 90))  # -45 to +45 degrees

    needle_transform = nk.n("GeometryNodeTransform", "NeedleTransform", x + 100, y + 100)
    nk.link(needle.outputs["Mesh"], needle_transform.inputs["Geometry"])

    # Position needle at bottom center, rotated
    needle_pivot_z = 0.003  # Pivot point near bottom
    needle_transform.inputs["Translation"].default_value = (
        config.needle_length / 2 * math.sin(angle),
        -config.depth / 2 + 0.001,
        needle_pivot_z + config.needle_length / 2 * math.cos(angle)
    )
    needle_transform.inputs["Rotation"].default_value = (0, -angle, 0)

    geometries.append(needle_transform.outputs["Geometry"])

    # 3. Build frame if enabled
    if config.frame_enabled:
        frame = nk.n("GeometryNodeMeshCube", "Frame", x, y - 100)
        frame.inputs["Size"].default_value = (config.width + 0.004, 0.002, config.height + 0.004)
        frame.inputs["Vertices X"].default_value = 2
        frame.inputs["Vertices Y"].default_value = 2
        frame.inputs["Vertices Z"].default_value = 2

        frame_transform = nk.n("GeometryNodeTransform", "FrameTransform", x + 100, y - 100)
        nk.link(frame.outputs["Mesh"], frame_transform.inputs["Geometry"])
        frame_transform.inputs["Translation"].default_value = (0, 0.003, config.height / 2)

        geometries.append(frame_transform.outputs["Geometry"])

    # Join all parts
    join = nk.n("GeometryNodeJoinGeometry", "JoinVU", x + 300, y)
    for geo in geometries:
        nk.link(geo, join.inputs["Geometry"])

    return join.outputs["Geometry"]


def build_seven_segment(
    nk: "NodeKit",
    config: SevenSegmentConfig,
    x: float = 0,
    y: float = 0
) -> Any:
    """
    Build 7-segment display geometry (simplified placeholder).

    Creates a basic representation of 7-segment display.
    Full implementation would have individual segment control.

    Args:
        nk: NodeKit instance
        config: 7-segment configuration
        x, y: Node positions

    Returns:
        Geometry output socket
    """
    # Simplified: create a rectangular display area
    total_width = config.digits * (config.segment_width * 1.5) + \
                  (config.digits - 1) * config.digit_spacing
    total_height = config.segment_height * 1.5

    # Create display background
    bg = nk.n("GeometryNodeMeshCube", "SegmentBG", x, y)
    bg.inputs["Size"].default_value = (total_width, 0.002, total_height)
    bg.inputs["Vertices X"].default_value = 2
    bg.inputs["Vertices Y"].default_value = 2
    bg.inputs["Vertices Z"].default_value = 2

    bg_transform = nk.n("GeometryNodeTransform", "BGTransform", x + 100, y)
    nk.link(bg.outputs["Mesh"], bg_transform.inputs["Geometry"])
    bg_transform.inputs["Translation"].default_value = (total_width / 2, 0, total_height / 2)

    # Build simplified segments for each digit
    segments = []
    for digit_idx in range(config.digits):
        digit_x = x + digit_idx * 200
        digit_offset_x = digit_idx * (config.segment_width * 1.5 + config.digit_spacing)

        # Create 7 segments for this digit (simplified as single cube)
        seg = nk.n("GeometryNodeMeshCube", f"Digit_{digit_idx}", digit_x, y + 100)
        seg.inputs["Size"].default_value = (config.segment_width, 0.003, config.segment_height)
        seg.inputs["Vertices X"].default_value = 2
        seg.inputs["Vertices Y"].default_value = 2
        seg.inputs["Vertices Z"].default_value = 2

        seg_transform = nk.n("GeometryNodeTransform", f"SegTransform_{digit_idx}", digit_x + 100, y + 100)
        nk.link(seg.outputs["Mesh"], seg_transform.inputs["Geometry"])
        seg_transform.inputs["Translation"].default_value = (
            digit_offset_x + config.segment_width / 2,
            0.001,
            total_height / 2
        )

        segments.append(seg_transform.outputs["Geometry"])

    # Join all
    join = nk.n("GeometryNodeJoinGeometry", "JoinSegments", x + 400, y)
    nk.link(bg_transform.outputs["Geometry"], join.inputs["Geometry"])
    for seg in segments:
        nk.link(seg, join.inputs["Geometry"])

    return join.outputs["Geometry"]


def create_led_material(
    config: LEDConfig,
    color_override: tuple = None
) -> dict:
    """
    Create material parameters for LED.

    Args:
        config: LED configuration
        color_override: Optional color override

    Returns:
        Material parameter dictionary
    """
    color = color_override if color_override else (config.color if config.active else config.color_off)

    return {
        "base_color": list(color),
        "metallic": 0.0,
        "roughness": 0.3 if config.lens == LEDLens.DIFFUSED else 0.1,
        "emission_color": list(config.color) if config.active else [0.0, 0.0, 0.0],
        "emission_strength": config.brightness * config.value if config.active else 0.0,
    }
