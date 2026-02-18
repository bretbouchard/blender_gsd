"""
Surface Features Geometry Nodes Builder

Builds procedural surface features using Blender Geometry Nodes:
- Knurling (vertical ridges)
- Ribbing (horizontal rings)
- Grooves (channels)
- Indicators (position markers)
- Collet/Cap geometry
- Backlight geometry

This module provides low-level node building functions that can be
composed together to create complex surface features.
"""

from __future__ import annotations
import math
from typing import Optional, Any

import bpy

# Import NodeKit from parent lib
import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit
from lib.control_system.surface_features import (
    KnurlingConfig, RibbingConfig, GrooveConfig,
    IndicatorConfig, ColletConfig, CapConfig, BacklightConfig,
    KnurlPattern, IndicatorType, GroovePattern
)


# =============================================================================
# KNURLING BUILDER
# =============================================================================

def build_knurling(
    nk: NodeKit,
    geo_in: Any,
    config: KnurlingConfig,
    total_height: float,
    base_diameter: float,
    x: float,
    y: float
) -> Any:
    """
    Build knurling surface feature using Geometry Nodes.

    Creates vertical ridges using Set Position displacement based on
    angular sawtooth pattern with zone masking.

    Args:
        nk: NodeKit instance
        geo_in: Input geometry socket
        config: KnurlingConfig with parameters
        total_height: Total knob height for zone normalization
        base_diameter: Base diameter for calculations
        x, y: Node position offset

    Returns:
        Geometry socket with knurling applied
    """
    if not config.enabled or config.count <= 0:
        return geo_in

    X = x
    Y = y
    STEP = 100

    # === POSITION AND ZONE ===
    pos = nk.n("GeometryNodeInputPosition", "GetPosition", X, Y + 400)
    sep = nk.n("ShaderNodeSeparateXYZ", "SepPosition", X + STEP, Y + 400)
    nk.link(pos.outputs["Position"], sep.inputs["Vector"])

    # Normalize Z to [0, 1]
    z_norm = nk.n("ShaderNodeMath", "NormalizeZ", X + 2*STEP, Y + 400)
    z_norm.operation = "DIVIDE"
    nk.link(sep.outputs["Z"], z_norm.inputs[0])
    z_norm.inputs[1].default_value = total_height

    # === ZONE MASK ===
    zone_mask = _build_zone_mask(
        nk, z_norm.outputs["Value"],
        config.z_start, config.z_end, config.fade,
        X + 3*STEP, Y + 400
    )

    # === ANGULAR PATTERN ===
    # Calculate angle: atan2(x, y)
    angle = nk.n("ShaderNodeMath", "Angle", X + 2*STEP, Y + 600)
    angle.operation = "ARCTAN2"
    nk.link(sep.outputs["X"], angle.inputs[0])
    nk.link(sep.outputs["Y"], angle.inputs[1])

    # Normalize to [0, 1]
    add_pi = nk.n("ShaderNodeMath", "AddPi", X + 3*STEP, Y + 600)
    add_pi.operation = "ADD"
    nk.link(angle.outputs["Value"], add_pi.inputs[0])
    add_pi.inputs[1].default_value = math.pi

    div_2pi = nk.n("ShaderNodeMath", "Div2Pi", X + 4*STEP, Y + 600)
    div_2pi.operation = "DIVIDE"
    nk.link(add_pi.outputs["Value"], div_2pi.inputs[0])
    div_2pi.inputs[1].default_value = 2 * math.pi

    # Apply pattern type
    if config.pattern == KnurlPattern.DIAMOND:
        # Diamond pattern: add helical component
        helix_offset = nk.n("ShaderNodeMath", "HelixOffset", X + 5*STEP, Y + 550)
        helix_offset.operation = "MULTIPLY"
        nk.link(z_norm.outputs["Value"], helix_offset.inputs[0])
        helix_offset.inputs[1].default_value = config.cross_angle / (2 * math.pi)

        combined = nk.n("ShaderNodeMath", "Combined", X + 6*STEP, Y + 575)
        combined.operation = "ADD"
        nk.link(div_2pi.outputs["Value"], combined.inputs[0])
        nk.link(helix_offset.outputs["Value"], combined.inputs[1])

        freq = nk.n("ShaderNodeMath", "Frequency", X + 7*STEP, Y + 600)
        freq.operation = "MULTIPLY"
        nk.link(combined.outputs["Value"], freq.inputs[0])
        freq.inputs[1].default_value = float(config.count)
    elif config.pattern == KnurlPattern.HELICAL:
        # Helical pattern: continuous spiral
        helix = nk.n("ShaderNodeMath", "HelixPattern", X + 5*STEP, Y + 600)
        helix.operation = "MULTIPLY"
        nk.link(z_norm.outputs["Value"], helix.inputs[0])
        helix.inputs[1].default_value = config.helix_pitch / total_height if config.helix_pitch > 0 else 1.0

        combined = nk.n("ShaderNodeMath", "CombinedHelix", X + 6*STEP, Y + 600)
        combined.operation = "ADD"
        nk.link(div_2pi.outputs["Value"], combined.inputs[0])
        nk.link(helix.outputs["Value"], combined.inputs[1])

        freq = nk.n("ShaderNodeMath", "Frequency", X + 7*STEP, Y + 600)
        freq.operation = "MULTIPLY"
        nk.link(combined.outputs["Value"], freq.inputs[0])
        freq.inputs[1].default_value = float(config.count)
    else:
        # STRAIGHT pattern (default)
        freq = nk.n("ShaderNodeMath", "Frequency", X + 5*STEP, Y + 600)
        freq.operation = "MULTIPLY"
        nk.link(div_2pi.outputs["Value"], freq.inputs[0])
        freq.inputs[1].default_value = float(config.count)

    # Sawtooth
    sawtooth = nk.n("ShaderNodeMath", "Sawtooth", X + 8*STEP, Y + 600)
    sawtooth.operation = "FRACT"
    nk.link(freq.outputs["Value"], sawtooth.inputs[0])

    # === PROFILE SHAPING ===
    profile_disp = _build_profile_shape(
        nk, sawtooth.outputs["Value"],
        config.profile,
        X + 9*STEP, Y + 600
    )

    # === APPLY ZONE MASK ===
    masked_disp = nk.n("ShaderNodeMath", "MaskedDisp", X + 15*STEP, Y + 500)
    masked_disp.operation = "MULTIPLY"
    nk.link(profile_disp, masked_disp.inputs[0])
    nk.link(zone_mask, masked_disp.inputs[1])

    # Scale by depth
    depth = nk.n("ShaderNodeMath", "RidgeDepth", X + 16*STEP, Y + 500)
    depth.operation = "MULTIPLY"
    nk.link(masked_disp.outputs["Value"], depth.inputs[0])
    depth.inputs[1].default_value = config.depth

    # Get normal for displacement direction
    normal = nk.n("GeometryNodeInputNormal", "GetNormal", X + 16*STEP, Y + 350)

    # Scale normal by displacement
    scale_disp = nk.n("ShaderNodeVectorMath", "ScaleDisplacement", X + 17*STEP, Y + 400)
    scale_disp.operation = "SCALE"
    nk.link(normal.outputs["Normal"], scale_disp.inputs["Vector"])
    nk.link(depth.outputs["Value"], scale_disp.inputs["Scale"])

    # Set position with offset
    set_pos = nk.n("GeometryNodeSetPosition", "SetKnurlPosition", X + 18*STEP, Y)
    nk.link(geo_in, set_pos.inputs["Geometry"])
    nk.link(scale_disp.outputs["Vector"], set_pos.inputs["Offset"])

    return set_pos.outputs["Geometry"]


def _build_zone_mask(
    nk: NodeKit,
    z_value: Any,
    z_start: float,
    z_end: float,
    fade: float,
    x: float,
    y: float
) -> Any:
    """Build smooth zone mask with optional fade."""
    STEP = 100

    if fade > 0:
        # Smooth transition using smoothstep
        # Lower bound
        lower_t = nk.n("ShaderNodeMath", "LowerT", x, y + 100)
        lower_t.operation = "SUBTRACT"
        nk.link(z_value, lower_t.inputs[0])
        lower_t.inputs[1].default_value = z_start

        lower_t_div = nk.n("ShaderNodeMath", "LowerTDiv", x + STEP, y + 100)
        lower_t_div.operation = "DIVIDE"
        nk.link(lower_t.outputs["Value"], lower_t_div.inputs[0])
        lower_t_div.inputs[1].default_value = fade

        lower_clamp = _build_clamp_01(nk, lower_t_div.outputs["Value"], x + 2*STEP, y + 100)
        lower_smooth = _build_smoothstep(nk, lower_clamp, x + 5*STEP, y + 100)

        # Upper bound (inverted)
        upper_t = nk.n("ShaderNodeMath", "UpperT", x, y - 100)
        upper_t.operation = "SUBTRACT"
        nk.link(z_value, upper_t.inputs[0])
        upper_t.inputs[1].default_value = z_end - fade

        upper_t_div = nk.n("ShaderNodeMath", "UpperTDiv", x + STEP, y - 100)
        upper_t_div.operation = "DIVIDE"
        nk.link(upper_t.outputs["Value"], upper_t_div.inputs[0])
        upper_t_div.inputs[1].default_value = fade

        upper_clamp = _build_clamp_01(nk, upper_t_div.outputs["Value"], x + 2*STEP, y - 100)
        upper_smooth = _build_smoothstep(nk, upper_clamp, x + 5*STEP, y - 100)

        # Combine
        zone_mask = nk.n("ShaderNodeMath", "ZoneMask", x + 6*STEP, y)
        zone_mask.operation = "MULTIPLY"
        nk.link(lower_smooth, zone_mask.inputs[0])
        nk.link(upper_smooth, zone_mask.inputs[1])

        return zone_mask.outputs["Value"]
    else:
        # Hard edge zone mask
        lower_cmp = nk.n("ShaderNodeMath", "LowerCmp", x, y + 50)
        lower_cmp.operation = "GREATER_THAN"
        nk.link(z_value, lower_cmp.inputs[0])
        lower_cmp.inputs[1].default_value = z_start

        upper_cmp = nk.n("ShaderNodeMath", "UpperCmp", x, y - 50)
        upper_cmp.operation = "LESS_THAN"
        nk.link(z_value, upper_cmp.inputs[0])
        upper_cmp.inputs[1].default_value = z_end

        zone_mask = nk.n("ShaderNodeMath", "ZoneMask", x + STEP, y)
        zone_mask.operation = "MULTIPLY"
        nk.link(lower_cmp.outputs["Value"], zone_mask.inputs[0])
        nk.link(upper_cmp.outputs["Value"], zone_mask.inputs[1])

        return zone_mask.outputs["Value"]


def _build_clamp_01(nk: NodeKit, value: Any, x: float, y: float) -> Any:
    """Clamp value to [0, 1]."""
    max_node = nk.n("ShaderNodeMath", "ClampMax", x, y)
    max_node.operation = "MAXIMUM"
    nk.link(value, max_node.inputs[0])
    max_node.inputs[1].default_value = 0.0

    min_node = nk.n("ShaderNodeMath", "ClampMin", x + 100, y)
    min_node.operation = "MINIMUM"
    nk.link(max_node.outputs["Value"], min_node.inputs[0])
    min_node.inputs[1].default_value = 1.0

    return min_node.outputs["Value"]


def _build_smoothstep(nk: NodeKit, t_value: Any, x: float, y: float) -> Any:
    """Build smoothstep: 3t² - 2t³"""
    t2 = nk.n("ShaderNodeMath", "T2", x, y)
    t2.operation = "MULTIPLY"
    nk.link(t_value, t2.inputs[0])
    nk.link(t_value, t2.inputs[1])

    t3 = nk.n("ShaderNodeMath", "T3", x + 100, y)
    t3.operation = "MULTIPLY"
    nk.link(t2.outputs["Value"], t3.inputs[0])
    nk.link(t_value, t3.inputs[1])

    three_t2 = nk.n("ShaderNodeMath", "3T2", x + 200, y + 50)
    three_t2.operation = "MULTIPLY"
    three_t2.inputs[1].default_value = 3.0
    nk.link(t2.outputs["Value"], three_t2.inputs[0])

    two_t3 = nk.n("ShaderNodeMath", "2T3", x + 200, y - 50)
    two_t3.operation = "MULTIPLY"
    two_t3.inputs[1].default_value = 2.0
    nk.link(t3.outputs["Value"], two_t3.inputs[0])

    result = nk.n("ShaderNodeMath", "SmoothResult", x + 300, y)
    result.operation = "SUBTRACT"
    nk.link(three_t2.outputs["Value"], result.inputs[0])
    nk.link(two_t3.outputs["Value"], result.inputs[1])

    return result.outputs["Value"]


def _build_profile_shape(
    nk: NodeKit,
    sawtooth: Any,
    profile: float,
    x: float,
    y: float
) -> Any:
    """
    Build profile shape from sawtooth pattern.

    Profile values:
    - 0.0 = flat/trapezoid
    - 0.5 = round/sinusoidal
    - 1.0 = sharp/triangular
    """
    STEP = 80

    # Center sawtooth: t - 0.5 (range -0.5 to 0.5)
    center = nk.n("ShaderNodeMath", "CenterSaw", x, y)
    center.operation = "SUBTRACT"
    nk.link(sawtooth, center.inputs[0])
    center.inputs[1].default_value = 0.5

    # Absolute value for symmetric patterns
    abs_val = nk.n("ShaderNodeMath", "AbsSaw", x + STEP, y)
    abs_val.operation = "ABSOLUTE"
    nk.link(center.outputs["Value"], abs_val.inputs[0])

    # Scale to [-1, 1]: abs_saw * 2
    scaled = nk.n("ShaderNodeMath", "ScaledAbs", x + 2*STEP, y)
    scaled.operation = "MULTIPLY"
    nk.link(abs_val.outputs["Value"], scaled.inputs[0])
    scaled.inputs[1].default_value = 2.0

    # FLAT PROFILE (profile = 0.0)
    flat_threshold = 0.3
    flat_step = nk.n("ShaderNodeMath", "FlatStep", x + 3*STEP, y + 100)
    flat_step.operation = "LESS_THAN"
    nk.link(abs_val.outputs["Value"], flat_step.inputs[0])
    flat_step.inputs[1].default_value = flat_threshold

    flat_disp = nk.n("ShaderNodeMath", "FlatDisp", x + 4*STEP, y + 100)
    flat_disp.operation = "SUBTRACT"
    flat_disp.inputs[0].default_value = 1.0
    nk.link(flat_step.outputs["Value"], flat_disp.inputs[1])

    flat_scaled = nk.n("ShaderNodeMath", "FlatScaled", x + 5*STEP, y + 100)
    flat_scaled.operation = "MULTIPLY"
    nk.link(flat_disp.outputs["Value"], flat_scaled.inputs[0])
    nk.link(scaled.outputs["Value"], flat_scaled.inputs[1])

    # ROUND PROFILE (profile = 0.5)
    sin_input = nk.n("ShaderNodeMath", "SinInput", x + 3*STEP, y)
    sin_input.operation = "MULTIPLY"
    nk.link(sawtooth, sin_input.inputs[0])
    sin_input.inputs[1].default_value = 2 * math.pi

    round_disp = nk.n("ShaderNodeMath", "RoundDisp", x + 4*STEP, y)
    round_disp.operation = "SINE"
    nk.link(sin_input.outputs["Value"], round_disp.inputs[0])

    # SHARP PROFILE (profile = 1.0) - just use scaled absolute
    sharp_disp = scaled

    # MIX PROFILES
    # Mix flat (0) and round (0.5)
    mix_fr_factor = nk.n("ShaderNodeMath", "MixFRFactor", x + 6*STEP, y + 50)
    mix_fr_factor.operation = "MULTIPLY"
    mix_fr_factor.inputs[0].default_value = profile
    mix_fr_factor.inputs[1].default_value = 2.0

    mix_fr_clamped = nk.n("ShaderNodeMath", "MixFRClamped", x + 7*STEP, y + 50)
    mix_fr_clamped.operation = "MINIMUM"
    nk.link(mix_fr_factor.outputs["Value"], mix_fr_clamped.inputs[0])
    mix_fr_clamped.inputs[1].default_value = 1.0

    mix_flat_round = nk.n("ShaderNodeMix", "MixFlatRound", x + 8*STEP, y + 50)
    mix_flat_round.data_type = "FLOAT"
    nk.link(mix_fr_clamped.outputs["Value"], mix_flat_round.inputs["Factor"])
    nk.link(flat_scaled.outputs["Value"], mix_flat_round.inputs[4])
    nk.link(round_disp.outputs["Value"], mix_flat_round.inputs[5])

    # Mix round/flat with sharp
    mix_rs_factor = nk.n("ShaderNodeMath", "MixRSFactor", x + 6*STEP, y - 50)
    mix_rs_factor.operation = "SUBTRACT"
    mix_rs_factor.inputs[0].default_value = profile
    mix_rs_factor.inputs[1].default_value = 0.5

    mix_rs_scaled = nk.n("ShaderNodeMath", "MixRSScaled", x + 7*STEP, y - 50)
    mix_rs_scaled.operation = "MULTIPLY"
    nk.link(mix_rs_factor.outputs["Value"], mix_rs_scaled.inputs[0])
    mix_rs_scaled.inputs[1].default_value = 2.0

    mix_rs_clamped = nk.n("ShaderNodeMath", "MixRSClamped", x + 8*STEP, y - 50)
    mix_rs_clamped.operation = "MAXIMUM"
    nk.link(mix_rs_scaled.outputs["Value"], mix_rs_clamped.inputs[0])
    mix_rs_clamped.inputs[1].default_value = 0.0

    mix_rs_max = nk.n("ShaderNodeMath", "MixRSClampMax", x + 9*STEP, y - 50)
    mix_rs_max.operation = "MINIMUM"
    nk.link(mix_rs_clamped.outputs["Value"], mix_rs_max.inputs[0])
    mix_rs_max.inputs[1].default_value = 1.0

    mix_round_sharp = nk.n("ShaderNodeMix", "MixRoundSharp", x + 10*STEP, y)
    mix_round_sharp.data_type = "FLOAT"
    nk.link(mix_rs_max.outputs["Value"], mix_round_sharp.inputs["Factor"])
    nk.link(mix_flat_round.outputs[2], mix_round_sharp.inputs[4])
    nk.link(sharp_disp.outputs["Value"], mix_round_sharp.inputs[5])

    return mix_round_sharp.outputs[2]


# =============================================================================
# RIBBING BUILDER
# =============================================================================

def build_ribbing(
    nk: NodeKit,
    geo_in: Any,
    config: RibbingConfig,
    total_height: float,
    base_diameter: float,
    x: float,
    y: float
) -> Any:
    """
    Build horizontal ribbing using Geometry Nodes.

    Creates ring-like ridges around the knob circumference.

    Args:
        nk: NodeKit instance
        geo_in: Input geometry socket
        config: RibbingConfig with parameters
        total_height: Total knob height
        base_diameter: Base diameter
        x, y: Node position offset

    Returns:
        Geometry socket with ribbing applied
    """
    if not config.enabled or config.count <= 0:
        return geo_in

    X = x
    Y = y
    STEP = 100

    # Get position
    pos = nk.n("GeometryNodeInputPosition", "GetPosition", X, Y + 300)
    sep = nk.n("ShaderNodeSeparateXYZ", "SepPosition", X + STEP, Y + 300)
    nk.link(pos.outputs["Position"], sep.inputs["Vector"])

    # Normalize Z
    z_norm = nk.n("ShaderNodeMath", "NormalizeZ", X + 2*STEP, Y + 300)
    z_norm.operation = "DIVIDE"
    nk.link(sep.outputs["Z"], z_norm.inputs[0])
    z_norm.inputs[1].default_value = total_height

    # === ZONE MASK ===
    zone_mask = _build_zone_mask(
        nk, z_norm.outputs["Value"],
        config.z_start, config.z_end, 0.05,
        X + 3*STEP, Y + 300
    )

    # === RIB PATTERN ===
    # Calculate rib frequency based on count and zone
    zone_height = config.z_end - config.z_start
    rib_freq = config.count / zone_height if zone_height > 0 else 1

    # Multiply z by frequency
    freq = nk.n("ShaderNodeMath", "RibFreq", X + 5*STEP, Y + 300)
    freq.operation = "MULTIPLY"
    nk.link(z_norm.outputs["Value"], freq.inputs[0])
    freq.inputs[1].default_value = rib_freq

    # Sawtooth for ribs
    sawtooth = nk.n("ShaderNodeMath", "RibSawtooth", X + 6*STEP, Y + 300)
    sawtooth.operation = "FRACT"
    nk.link(freq.outputs["Value"], sawtooth.inputs[0])

    # Profile shape
    profile_disp = _build_profile_shape(
        nk, sawtooth.outputs["Value"],
        config.profile,
        X + 7*STEP, Y + 300
    )

    # Apply zone mask
    masked = nk.n("ShaderNodeMath", "MaskedRib", X + 13*STEP, Y + 300)
    masked.operation = "MULTIPLY"
    nk.link(profile_disp, masked.inputs[0])
    nk.link(zone_mask, masked.inputs[1])

    # Scale by depth
    depth = nk.n("ShaderNodeMath", "RibDepth", X + 14*STEP, Y + 300)
    depth.operation = "MULTIPLY"
    nk.link(masked.outputs["Value"], depth.inputs[0])
    depth.inputs[1].default_value = config.depth

    # Get normal and apply displacement
    normal = nk.n("GeometryNodeInputNormal", "GetNormal", X + 14*STEP, Y + 150)
    scale_disp = nk.n("ShaderNodeVectorMath", "ScaleRibDisp", X + 15*STEP, Y + 200)
    scale_disp.operation = "SCALE"
    nk.link(normal.outputs["Normal"], scale_disp.inputs["Vector"])
    nk.link(depth.outputs["Value"], scale_disp.inputs["Scale"])

    set_pos = nk.n("GeometryNodeSetPosition", "SetRibPosition", X + 16*STEP, Y)
    nk.link(geo_in, set_pos.inputs["Geometry"])
    nk.link(scale_disp.outputs["Vector"], set_pos.inputs["Offset"])

    return set_pos.outputs["Geometry"]


# =============================================================================
# GROOVE BUILDER
# =============================================================================

def build_grooves(
    nk: NodeKit,
    geo_in: Any,
    config: GrooveConfig,
    total_height: float,
    base_diameter: float,
    x: float,
    y: float
) -> Any:
    """
    Build grooves (channels) in surface using Geometry Nodes.

    Grooves are cut into the surface rather than raised.

    Args:
        nk: NodeKit instance
        geo_in: Input geometry socket
        config: GrooveConfig with parameters
        total_height: Total knob height
        base_diameter: Base diameter
        x, y: Node position offset

    Returns:
        Geometry socket with grooves applied
    """
    if not config.enabled:
        return geo_in

    X = x
    Y = y
    STEP = 100

    # Get position
    pos = nk.n("GeometryNodeInputPosition", "GetPosition", X, Y + 300)
    sep = nk.n("ShaderNodeSeparateXYZ", "SepPosition", X + STEP, Y + 300)
    nk.link(pos.outputs["Position"], sep.inputs["Vector"])

    # Normalize Z
    z_norm = nk.n("ShaderNodeMath", "NormalizeZ", X + 2*STEP, Y + 300)
    z_norm.operation = "DIVIDE"
    nk.link(sep.outputs["Z"], z_norm.inputs[0])
    z_norm.inputs[1].default_value = total_height

    # Build groove pattern based on type
    if config.pattern == GroovePattern.MULTI:
        # Multiple parallel grooves
        groove_pattern = _build_multi_groove_pattern(
            nk, z_norm.outputs["Value"],
            config.count, config.spacing / total_height,
            X + 3*STEP, Y + 300
        )
    elif config.pattern == GroovePattern.SPIRAL:
        # Spiral groove
        groove_pattern = _build_spiral_groove_pattern(
            nk, sep.outputs["X"], sep.outputs["Y"], z_norm.outputs["Value"],
            config.spiral_turns, config.width,
            X + 3*STEP, Y + 300
        )
    else:
        # Single groove
        groove_pattern = _build_single_groove_pattern(
            nk, z_norm.outputs["Value"],
            config.z_position, config.width / total_height,
            X + 3*STEP, Y + 300
        )

    # Profile shape (inverted for groove)
    profile_disp = _build_profile_shape(
        nk, groove_pattern,
        config.profile,
        X + 7*STEP, Y + 300
    )

    # Invert for groove (cut into surface)
    invert = nk.n("ShaderNodeMath", "InvertGroove", X + 13*STEP, Y + 300)
    invert.operation = "MULTIPLY"
    nk.link(profile_disp, invert.inputs[0])
    invert.inputs[1].default_value = -1.0

    # Scale by depth
    depth = nk.n("ShaderNodeMath", "GrooveDepth", X + 14*STEP, Y + 300)
    depth.operation = "MULTIPLY"
    nk.link(invert.outputs["Value"], depth.inputs[0])
    depth.inputs[1].default_value = config.depth

    # Apply displacement
    normal = nk.n("GeometryNodeInputNormal", "GetNormal", X + 14*STEP, Y + 150)
    scale_disp = nk.n("ShaderNodeVectorMath", "ScaleGrooveDisp", X + 15*STEP, Y + 200)
    scale_disp.operation = "SCALE"
    nk.link(normal.outputs["Normal"], scale_disp.inputs["Vector"])
    nk.link(depth.outputs["Value"], scale_disp.inputs["Scale"])

    set_pos = nk.n("GeometryNodeSetPosition", "SetGroovePosition", X + 16*STEP, Y)
    nk.link(geo_in, set_pos.inputs["Geometry"])
    nk.link(scale_disp.outputs["Vector"], set_pos.inputs["Offset"])

    return set_pos.outputs["Geometry"]


def _build_single_groove_pattern(
    nk: NodeKit,
    z_norm: Any,
    z_position: float,
    width: float,
    x: float,
    y: float
) -> Any:
    """Build single groove pattern at z_position."""
    STEP = 100

    # Distance from groove center
    dist = nk.n("ShaderNodeMath", "GrooveDist", x, y)
    dist.operation = "SUBTRACT"
    nk.link(z_norm, dist.inputs[0])
    dist.inputs[1].default_value = z_position

    abs_dist = nk.n("ShaderNodeMath", "AbsDist", x + STEP, y)
    abs_dist.operation = "ABSOLUTE"
    nk.link(dist.outputs["Value"], abs_dist.inputs[0])

    # Groove mask (within width)
    mask = nk.n("ShaderNodeMath", "GrooveMask", x + 2*STEP, y)
    mask.operation = "LESS_THAN"
    nk.link(abs_dist.outputs["Value"], mask.inputs[0])
    mask.inputs[1].default_value = width / 2

    # Invert mask for groove pattern (1 inside groove, 0 outside)
    invert = nk.n("ShaderNodeMath", "InvertMask", x + 3*STEP, y)
    invert.operation = "SUBTRACT"
    invert.inputs[0].default_value = 1.0
    nk.link(mask.outputs["Value"], invert.inputs[1])

    # Scale by distance from center for profile
    scale = nk.n("ShaderNodeMath", "ScaleDist", x + 4*STEP, y)
    scale.operation = "MULTIPLY"
    nk.link(abs_dist.outputs["Value"], scale.inputs[0])
    scale.inputs[1].default_value = 2.0 / width

    combined = nk.n("ShaderNodeMath", "CombinedGroove", x + 5*STEP, y)
    combined.operation = "MULTIPLY"
    nk.link(invert.outputs["Value"], combined.inputs[0])
    nk.link(scale.outputs["Value"], combined.inputs[1])

    return combined.outputs["Value"]


def _build_multi_groove_pattern(
    nk: NodeKit,
    z_norm: Any,
    count: int,
    spacing: float,
    x: float,
    y: float
) -> Any:
    """Build multiple parallel grooves."""
    # Similar to ribbing but inverted
    freq = nk.n("ShaderNodeMath", "GrooveFreq", x, y)
    freq.operation = "MULTIPLY"
    nk.link(z_norm, freq.inputs[0])
    freq.inputs[1].default_value = 1.0 / spacing if spacing > 0 else 1.0

    sawtooth = nk.n("ShaderNodeMath", "GrooveSaw", x + 100, y)
    sawtooth.operation = "FRACT"
    nk.link(freq.outputs["Value"], sawtooth.inputs[0])

    return sawtooth.outputs["Value"]


def _build_spiral_groove_pattern(
    nk: NodeKit,
    x_val: Any,
    y_val: Any,
    z_norm: Any,
    turns: float,
    width: float,
    x: float,
    y: float
) -> Any:
    """Build spiral groove pattern."""
    STEP = 100

    # Calculate angle
    angle = nk.n("ShaderNodeMath", "SpiralAngle", x, y)
    angle.operation = "ARCTAN2"
    nk.link(x_val, angle.inputs[0])
    nk.link(y_val, angle.inputs[1])

    # Normalize angle to [0, 1]
    norm_angle = nk.n("ShaderNodeMath", "NormAngle", x + STEP, y)
    norm_angle.operation = "ADD"
    nk.link(angle.outputs["Value"], norm_angle.inputs[0])
    norm_angle.inputs[1].default_value = math.pi

    div = nk.n("ShaderNodeMath", "DivAngle", x + 2*STEP, y)
    div.operation = "DIVIDE"
    nk.link(norm_angle.outputs["Value"], div.inputs[0])
    div.inputs[1].default_value = 2 * math.pi

    # Combine with Z for spiral
    spiral = nk.n("ShaderNodeMath", "Spiral", x + 3*STEP, y)
    spiral.operation = "ADD"
    nk.link(div.outputs["Value"], spiral.inputs[0])
    # Scale z by turns
    z_scaled = nk.n("ShaderNodeMath", "ZScaled", x + 3*STEP, y + 100)
    z_scaled.operation = "MULTIPLY"
    nk.link(z_norm, z_scaled.inputs[0])
    z_scaled.inputs[1].default_value = turns
    nk.link(z_scaled.outputs["Value"], spiral.inputs[1])

    # Sawtooth for spiral groove
    sawtooth = nk.n("ShaderNodeMath", "SpiralSaw", x + 4*STEP, y)
    sawtooth.operation = "FRACT"
    nk.link(spiral.outputs["Value"], sawtooth.inputs[0])

    return sawtooth.outputs["Value"]


# =============================================================================
# INDICATOR BUILDER
# =============================================================================

def build_indicator(
    nk: NodeKit,
    cap_diameter: float,
    skirt_height: float,
    cap_height: float,
    config: IndicatorConfig,
    x: float,
    y: float
) -> Any:
    """
    Build indicator geometry using Geometry Nodes.

    Creates various indicator types: line, dot, pointer.

    Args:
        nk: NodeKit instance
        cap_diameter: Diameter of cap
        skirt_height: Height of skirt section
        cap_height: Height of cap section
        config: IndicatorConfig with parameters
        x, y: Node position offset

    Returns:
        Geometry socket with indicator geometry
    """
    if not config.enabled:
        return None

    X = x
    Y = y

    # Calculate Z position
    pointer_z = skirt_height + cap_height + config.height / 2 + config.z_offset

    if config.indicator_type == IndicatorType.DOT:
        # Create dot indicator
        return _build_dot_indicator(nk, cap_diameter, pointer_z, config, X, Y)
    elif config.indicator_type == IndicatorType.POINTER:
        # Create pointer (chicken head style)
        return _build_pointer_indicator(nk, cap_diameter, skirt_height, cap_height, config, X, Y)
    else:
        # Default: line indicator
        return _build_line_indicator(nk, cap_diameter, pointer_z, config, X, Y)


def _build_line_indicator(
    nk: NodeKit,
    cap_diameter: float,
    pointer_z: float,
    config: IndicatorConfig,
    x: float,
    y: float
) -> Any:
    """Build line indicator as thin cube."""
    pointer_width = (cap_diameter / 2) * config.width

    cube = nk.n("GeometryNodeMeshCube", "PointerCube", x, y)
    cube.inputs["Size"].default_value = (pointer_width, config.length, config.height)
    cube.inputs["Vertices X"].default_value = 1
    cube.inputs["Vertices Y"].default_value = 1
    cube.inputs["Vertices Z"].default_value = 1

    pointer_y = -config.length / 2  # Offset so tip is at center

    transform = nk.n("GeometryNodeTransform", "PointerTransform", x + 200, y)
    nk.link(cube.outputs["Mesh"], transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (0, pointer_y, pointer_z)

    return transform.outputs["Geometry"]


def _build_dot_indicator(
    nk: NodeKit,
    cap_diameter: float,
    pointer_z: float,
    config: IndicatorConfig,
    x: float,
    y: float
) -> Any:
    """Build dot indicator as cylinder/sphere."""
    # Use UV sphere for dot
    sphere = nk.n("GeometryNodeMeshUVSphere", "DotSphere", x, y)
    sphere.inputs["Radius"].default_value = config.dot_diameter / 2
    sphere.inputs["Segments"].default_value = 16
    sphere.inputs["Rings"].default_value = 8

    # Position at top center of cap
    transform = nk.n("GeometryNodeTransform", "DotTransform", x + 200, y)
    nk.link(sphere.outputs["Mesh"], transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (0, 0, pointer_z)

    return transform.outputs["Geometry"]


def _build_pointer_indicator(
    nk: NodeKit,
    cap_diameter: float,
    skirt_height: float,
    cap_height: float,
    config: IndicatorConfig,
    x: float,
    y: float
) -> Any:
    """Build extended pointer indicator (chicken head style)."""
    # Pointer extends from edge toward center
    pointer_width = (cap_diameter / 2) * config.width

    # Create tapered pointer using cone or custom mesh
    # For simplicity, use elongated cube with taper
    cube = nk.n("GeometryNodeMeshCube", "PointerCube", x, y)
    cube.inputs["Size"].default_value = (pointer_width, config.length, config.height * 1.5)
    cube.inputs["Vertices X"].default_value = 1
    cube.inputs["Vertices Y"].default_value = 2  # Extra vertex for taper
    cube.inputs["Vertices Z"].default_value = 1

    pointer_z = skirt_height + cap_height + config.height * 0.75
    pointer_y = -config.length / 2

    transform = nk.n("GeometryNodeTransform", "PointerTransform", x + 200, y)
    nk.link(cube.outputs["Mesh"], transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (0, pointer_y, pointer_z)

    return transform.outputs["Geometry"]


# =============================================================================
# COLLET BUILDER
# =============================================================================

def build_collet(
    nk: NodeKit,
    config: ColletConfig,
    x: float,
    y: float
) -> Any:
    """
    Build collet (metal ring) geometry.

    Args:
        nk: NodeKit instance
        config: ColletConfig with parameters
        x, y: Node position offset

    Returns:
        Geometry socket with collet geometry
    """
    if not config.enabled:
        return None

    X = x
    Y = y

    # Create outer cylinder
    outer = nk.n("GeometryNodeMeshCylinder", "ColletOuter", X, Y)
    outer.inputs["Vertices"].default_value = 64
    outer.inputs["Radius"].default_value = config.diameter / 2
    outer.inputs["Depth"].default_value = config.height

    # Create inner cylinder for subtraction
    inner_radius = (config.diameter / 2) - config.thickness
    inner = nk.n("GeometryNodeMeshCylinder", "ColletInner", X + 200, Y)
    inner.inputs["Vertices"].default_value = 64
    inner.inputs["Radius"].default_value = inner_radius
    inner.inputs["Depth"].default_value = config.height + 0.001  # Slightly taller

    # Subtract inner from outer using difference boolean
    # Note: Geometry Nodes uses Mesh Boolean node
    bool_diff = nk.n("GeometryNodeMeshBoolean", "ColletBool", X + 400, Y)
    bool_diff.operation = "DIFFERENCE"
    nk.link(outer.outputs["Mesh"], bool_diff.inputs["Mesh A"])
    nk.link(inner.outputs["Mesh"], bool_diff.inputs["Mesh B"])

    # Position
    transform = nk.n("GeometryNodeTransform", "ColletTransform", X + 600, Y)
    nk.link(bool_diff.outputs["Mesh"], transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (
        0, 0,
        config.z_position + config.height / 2 + config.gap
    )

    return transform.outputs["Geometry"]


# =============================================================================
# CAP BUILDER
# =============================================================================

def build_cap(
    nk: NodeKit,
    skirt_height: float,
    cap_height: float,
    base_diameter: float,
    config: CapConfig,
    x: float,
    y: float
) -> Any:
    """
    Build cap/insert geometry.

    Args:
        nk: NodeKit instance
        skirt_height: Height of skirt
        cap_height: Height of main cap
        base_diameter: Base diameter
        config: CapConfig with parameters
        x, y: Node position offset

    Returns:
        Geometry socket with cap geometry
    """
    if not config.enabled:
        return None

    X = x
    Y = y

    if config.domed:
        # Domed cap
        cap_geo = nk.n("GeometryNodeMeshUVSphere", "CapSphere", X, Y)
        cap_geo.inputs["Radius"].default_value = config.diameter / 2
        cap_geo.inputs["Segments"].default_value = 32
        cap_geo.inputs["Rings"].default_value = 16
    else:
        # Flat cap
        cap_geo = nk.n("GeometryNodeMeshCylinder", "CapCylinder", X, Y)
        cap_geo.inputs["Vertices"].default_value = 32
        cap_geo.inputs["Radius"].default_value = config.diameter / 2
        cap_geo.inputs["Depth"].default_value = config.height

    # Position at top of main cap
    top_z = skirt_height + cap_height - config.inset
    if config.domed:
        top_z += config.dome_radius
    else:
        top_z += config.height / 2

    transform = nk.n("GeometryNodeTransform", "CapTransform", X + 200, Y)
    nk.link(cap_geo.outputs["Mesh"] if not config.domed else cap_geo.outputs["Mesh"],
            transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (0, 0, top_z)

    return transform.outputs["Geometry"]
