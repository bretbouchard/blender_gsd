"""
Neve Knob Geometry Nodes Generator

Creates procedural Neve-style audio knobs using pure Geometry Nodes.
This replaces the previous shader-only approach with actual mesh geometry.

SKIRT STYLES:
- INTEGRATED (0): Flat bottom, seamless transition (clear/solid look)
- SEPARATE (1): Independent rotating ring with visible gap (indecent style)

FEATURES:
- Cap cylinder (configurable height/diameter)
- Skirt cylinder (can be wider than cap for grip)
- REAL ridge geometry via Set Position displacement (not shader bump)
- Pointer line as raised cube geometry
- Material with position-based pointer color mask

PARAMETERS:
    cap_height: Height of the cap section (meters)
    cap_diameter: Diameter of the cap (meters)
    skirt_height: Height of the skirt section (meters)
    skirt_diameter: Diameter of the skirt (meters)
    skirt_style: 0=integrated (seamless), 1=separate (with gap)
    ridge_count: Number of ridges (0 = smooth)
    ridge_depth: Depth of ridges (meters)

    KNURLING ZONE CONTROLS:
    knurl_z_start: Z position where knurling begins (0.0 = bottom of skirt)
    knurl_z_end: Z position where knurling ends (1.0 = top of cap)
    knurl_fade: Smooth transition distance at zone edges (0 = hard edge)

    KNURLING PROFILE CONTROL:
    knurl_profile: Shape of each ridge (0.0 = flat/trapezoid, 0.5 = round, 1.0 = sharp V)

    pointer_length: Length of pointer line (meters)
    pointer_width: Angular width of pointer (radians)
    segments: Mesh resolution around circumference
    base_color: RGB color of the knob body
    pointer_color: RGB color of the pointer line
    metallic: Metallic value (0-1)
    roughness: Roughness value (0-1)
    clearcoat: Clearcoat weight (0-1)
"""

import bpy
import sys
import pathlib
import math

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit


def build_artifact(task: dict, collection: bpy.types.Collection):
    """
    Build a Neve-style knob from task parameters.

    Args:
        task: Task dict with 'parameters' key containing geometry/material settings
        collection: Blender collection to place the object in

    Returns:
        Dict with 'root_objects' list containing the created object
    """
    params = task["parameters"]
    debug = task.get("debug", {})

    # Extract parameters with sensible defaults
    cap_height = params.get("cap_height", 0.020)
    cap_diameter = params.get("cap_diameter", 0.018)
    skirt_height = params.get("skirt_height", 0.008)
    skirt_diameter = params.get("skirt_diameter", 0.020)
    skirt_style = params.get("skirt_style", 0)
    ridge_count = params.get("ridge_count", 0)
    ridge_depth = params.get("ridge_depth", 0.001)

    # Knurling zone controls (normalized 0-1 where 0=bottom of skirt, 1=top of cap)
    knurl_z_start = params.get("knurl_z_start", 0.0)  # Start at bottom
    knurl_z_end = params.get("knurl_z_end", 1.0)      # End at top
    knurl_fade = params.get("knurl_fade", 0.0)        # No fade by default

    # Knurling profile control (0=flat, 0.5=round, 1=sharp)
    knurl_profile = params.get("knurl_profile", 0.5)

    pointer_length = params.get("pointer_length", 0.012)
    pointer_width_rad = params.get("pointer_width", 0.08)
    segments = params.get("segments", 64)

    # Calculate total height for zone normalization
    total_height = skirt_height + cap_height

    # Create empty mesh object
    mesh = bpy.data.meshes.new("NeveKnobMesh")
    obj = bpy.data.objects.new("NeveKnob", mesh)
    collection.objects.link(obj)

    # Geometry Nodes modifier
    mod = obj.modifiers.new("KnobGeometry", "NODES")
    tree = bpy.data.node_groups.new("NeveKnobGeoTree", "GeometryNodeTree")
    mod.node_group = tree

    nk = NodeKit(tree).clear()

    # Create interface
    tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    gi = nk.group_input(0, 0)
    go = nk.group_output(1800, 0)

    # === BUILD GEOMETRY ===

    # 1. CAP CYLINDER
    cap_cyl = nk.n("GeometryNodeMeshCylinder", "CapCylinder", 200, 300)
    cap_cyl.inputs["Vertices"].default_value = segments
    cap_cyl.inputs["Radius"].default_value = cap_diameter / 2
    cap_cyl.inputs["Depth"].default_value = cap_height

    cap_transform = nk.n("GeometryNodeTransform", "CapTransform", 400, 300)
    nk.link(cap_cyl.outputs["Mesh"], cap_transform.inputs["Geometry"])
    # Position cap on top of skirt
    cap_transform.inputs["Translation"].default_value = (0, 0, skirt_height + cap_height / 2)

    # 2. SKIRT CYLINDER
    skirt_cyl = nk.n("GeometryNodeMeshCylinder", "SkirtCylinder", 200, -100)
    skirt_cyl.inputs["Vertices"].default_value = segments
    skirt_cyl.inputs["Radius"].default_value = skirt_diameter / 2
    skirt_cyl.inputs["Depth"].default_value = skirt_height

    # For SEPARATE style, add a small gap between cap and skirt
    gap_z = 0.002 if skirt_style == 1 else 0.0

    skirt_transform = nk.n("GeometryNodeTransform", "SkirtTransform", 400, -100)
    nk.link(skirt_cyl.outputs["Mesh"], skirt_transform.inputs["Geometry"])
    skirt_transform.inputs["Translation"].default_value = (0, 0, skirt_height / 2 + gap_z)

    # 3. JOIN CAP + SKIRT
    join1 = nk.n("GeometryNodeJoinGeometry", "JoinCapSkirt", 600, 100)
    nk.link(cap_transform.outputs["Geometry"], join1.inputs["Geometry"])
    nk.link(skirt_transform.outputs["Geometry"], join1.inputs["Geometry"])

    # 4. ADD RIDGES (real mesh displacement) - NO subdivision, keep sharp edges
    ridge_geo = _build_ridges(
        nk, join1.outputs["Geometry"],
        ridge_count, ridge_depth,
        knurl_z_start, knurl_z_end, knurl_fade,
        knurl_profile,
        total_height,
        800, 100
    )

    # 5. NO SMOOTH SHADING - keep sharp faceted look for proper knob edges
    # Smooth shading was causing the "melted balloon" effect

    # 6. POINTER LINE (raised cube geometry)
    pointer_geo = _build_pointer(nk, cap_diameter, skirt_height, cap_height, pointer_length, pointer_width_rad, 200, 500)

    # 7. JOIN ALL PARTS
    join_all = nk.n("GeometryNodeJoinGeometry", "JoinAllParts", 1200, 100)
    nk.link(ridge_geo, join_all.inputs["Geometry"])
    nk.link(pointer_geo, join_all.inputs["Geometry"])

    # 8. MERGE NEARBY VERTICES
    merge = nk.n("GeometryNodeMergeByDistance", "MergeVertices", 1400, 100)
    nk.link(join_all.outputs["Geometry"], merge.inputs["Geometry"])

    # 9. SET MATERIAL
    mat = _create_material(params)
    set_mat = nk.n("GeometryNodeSetMaterial", "SetMaterial", 1600, 100)
    set_mat.inputs["Material"].default_value = mat
    nk.link(merge.outputs["Geometry"], set_mat.inputs["Geometry"])

    # OUTPUT
    nk.link(set_mat.outputs["Geometry"], go.inputs["Geometry"])

    return {"root_objects": [obj]}


def _build_ridges(nk: NodeKit, geo_in, ridge_count: int, ridge_depth: float,
                   knurl_z_start: float, knurl_z_end: float, knurl_fade: float,
                   knurl_profile: float, total_height: float,
                   x: float, y: float):
    """
    Add ridged grip pattern using real mesh displacement.

    Uses Set Position with normal-scaled offset based on angular sawtooth pattern.

    Args:
        nk: NodeKit instance
        geo_in: Input geometry socket
        ridge_count: Number of ridges around circumference
        ridge_depth: Depth of ridges in meters
        knurl_z_start: Normalized Z start position (0=bottom, 1=top)
        knurl_z_end: Normalized Z end position (0=bottom, 1=top)
        knurl_fade: Fade distance at zone edges (normalized)
        knurl_profile: Ridge shape (0=flat, 0.5=round, 1=sharp)
        total_height: Total knob height for normalization
        x, y: Node position offset

    Returns:
        Geometry socket with ridges applied
    """
    if ridge_count <= 0:
        return geo_in

    X = x
    Y = y
    STEP = 100

    # === ZONE MASK ===
    # Get position for both angle and zone calculations
    pos = nk.n("GeometryNodeInputPosition", "GetPosition", X, Y + 400)
    sep = nk.n("ShaderNodeSeparateXYZ", "SepPosition", X + STEP, Y + 400)
    nk.link(pos.outputs["Position"], sep.inputs["Vector"])

    # Normalize Z position to [0, 1] based on total height
    z_norm = nk.n("ShaderNodeMath", "NormalizeZ", X + 2*STEP, Y + 400)
    z_norm.operation = "DIVIDE"
    nk.link(sep.outputs["Z"], z_norm.inputs[0])
    z_norm.inputs[1].default_value = total_height

    # === ZONE MASK with optional fade ===
    # Create smooth zone mask using smoothstep-like function
    # mask = smoothstep(start, start+fade, z) * smoothstep(end, end-fade, z)

    # Build smoothstep manually: 3t² - 2t³ where t = clamp((x-edge0)/(edge1-edge0))
    # For lower edge:
    lower_t = nk.n("ShaderNodeMath", "LowerT", X + 3*STEP, Y + 400)
    lower_t.operation = "SUBTRACT"
    nk.link(z_norm.outputs["Value"], lower_t.inputs[0])
    lower_t.inputs[1].default_value = knurl_z_start

    if knurl_fade > 0:
        lower_t_div = nk.n("ShaderNodeMath", "LowerTDiv", X + 4*STEP, Y + 500)
        lower_t_div.operation = "DIVIDE"
        nk.link(lower_t.outputs["Value"], lower_t_div.inputs[0])
        lower_t_div.inputs[1].default_value = knurl_fade

        # Clamp to [0, 1] using MINIMUM and MAXIMUM
        lower_t_max = nk.n("ShaderNodeMath", "LowerTMax", X + 5*STEP, Y + 500)
        lower_t_max.operation = "MAXIMUM"
        nk.link(lower_t_div.outputs["Value"], lower_t_max.inputs[0])
        lower_t_max.inputs[1].default_value = 0.0

        lower_t_clamp = nk.n("ShaderNodeMath", "LowerTClamp", X + 6*STEP, Y + 500)
        lower_t_clamp.operation = "MINIMUM"
        nk.link(lower_t_max.outputs["Value"], lower_t_clamp.inputs[0])
        lower_t_clamp.inputs[1].default_value = 1.0

        # smoothstep: 3t² - 2t³
        lower_t2 = nk.n("ShaderNodeMath", "LowerT2", X + 7*STEP, Y + 500)
        lower_t2.operation = "MULTIPLY"
        nk.link(lower_t_clamp.outputs["Value"], lower_t2.inputs[0])
        nk.link(lower_t_clamp.outputs["Value"], lower_t2.inputs[1])

        lower_t3 = nk.n("ShaderNodeMath", "LowerT3", X + 8*STEP, Y + 500)
        lower_t3.operation = "MULTIPLY"
        nk.link(lower_t2.outputs["Value"], lower_t3.inputs[0])
        nk.link(lower_t_clamp.outputs["Value"], lower_t3.inputs[1])

        lower_3t2 = nk.n("ShaderNodeMath", "Lower3T2", X + 9*STEP, Y + 500)
        lower_3t2.operation = "MULTIPLY"
        lower_3t2.inputs[1].default_value = 3.0
        nk.link(lower_t2.outputs["Value"], lower_3t2.inputs[0])

        lower_2t3 = nk.n("ShaderNodeMath", "Lower2T3", X + 10*STEP, Y + 500)
        lower_2t3.operation = "MULTIPLY"
        lower_2t3.inputs[1].default_value = 2.0
        nk.link(lower_t3.outputs["Value"], lower_2t3.inputs[0])

        lower_smooth_result = nk.n("ShaderNodeMath", "LowerSmoothResult", X + 11*STEP, Y + 500)
        lower_smooth_result.operation = "SUBTRACT"
        nk.link(lower_3t2.outputs["Value"], lower_smooth_result.inputs[0])
        nk.link(lower_2t3.outputs["Value"], lower_smooth_result.inputs[1])

        # Upper bound (inverted): smoothstep(knurl_z_end, knurl_z_end - knurl_fade, z_norm)
        # This is equivalent to 1 - smoothstep(knurl_z_end - knurl_fade, knurl_z_end, z_norm)
        upper_t = nk.n("ShaderNodeMath", "UpperT", X + 3*STEP, Y + 300)
        upper_t.operation = "SUBTRACT"
        nk.link(z_norm.outputs["Value"], upper_t.inputs[0])
        upper_t.inputs[1].default_value = knurl_z_end - knurl_fade

        upper_t_div = nk.n("ShaderNodeMath", "UpperTDiv", X + 4*STEP, Y + 300)
        upper_t_div.operation = "DIVIDE"
        nk.link(upper_t.outputs["Value"], upper_t_div.inputs[0])
        upper_t_div.inputs[1].default_value = knurl_fade

        # Clamp to [0, 1]
        upper_t_max = nk.n("ShaderNodeMath", "UpperTMax", X + 5*STEP, Y + 300)
        upper_t_max.operation = "MAXIMUM"
        nk.link(upper_t_div.outputs["Value"], upper_t_max.inputs[0])
        upper_t_max.inputs[1].default_value = 0.0

        upper_t_clamp = nk.n("ShaderNodeMath", "UpperTClamp", X + 6*STEP, Y + 300)
        upper_t_clamp.operation = "MINIMUM"
        nk.link(upper_t_max.outputs["Value"], upper_t_clamp.inputs[0])
        upper_t_clamp.inputs[1].default_value = 1.0

        upper_t2 = nk.n("ShaderNodeMath", "UpperT2", X + 7*STEP, Y + 300)
        upper_t2.operation = "MULTIPLY"
        nk.link(upper_t_clamp.outputs["Value"], upper_t2.inputs[0])
        nk.link(upper_t_clamp.outputs["Value"], upper_t2.inputs[1])

        upper_t3 = nk.n("ShaderNodeMath", "UpperT3", X + 8*STEP, Y + 300)
        upper_t3.operation = "MULTIPLY"
        nk.link(upper_t2.outputs["Value"], upper_t3.inputs[0])
        nk.link(upper_t_clamp.outputs["Value"], upper_t3.inputs[1])

        upper_3t2 = nk.n("ShaderNodeMath", "Upper3T2", X + 9*STEP, Y + 300)
        upper_3t2.operation = "MULTIPLY"
        upper_3t2.inputs[1].default_value = 3.0
        nk.link(upper_t2.outputs["Value"], upper_3t2.inputs[0])

        upper_2t3 = nk.n("ShaderNodeMath", "Upper2T3", X + 10*STEP, Y + 300)
        upper_2t3.operation = "MULTIPLY"
        upper_2t3.inputs[1].default_value = 2.0
        nk.link(upper_t3.outputs["Value"], upper_2t3.inputs[0])

        upper_smooth_result = nk.n("ShaderNodeMath", "UpperSmoothResult", X + 11*STEP, Y + 300)
        upper_smooth_result.operation = "SUBTRACT"
        nk.link(upper_3t2.outputs["Value"], upper_smooth_result.inputs[0])
        nk.link(upper_2t3.outputs["Value"], upper_smooth_result.inputs[1])

        # Combine lower and upper masks
        zone_mask = nk.n("ShaderNodeMath", "ZoneMask", X + 12*STEP, Y + 400)
        zone_mask.operation = "MULTIPLY"
        nk.link(lower_smooth_result.outputs["Value"], zone_mask.inputs[0])
        nk.link(upper_smooth_result.outputs["Value"], zone_mask.inputs[1])
    else:
        # No fade - simple hard edge zone mask
        # mask = (z >= start) AND (z <= end)
        lower_cmp = nk.n("ShaderNodeMath", "LowerCmp", X + 4*STEP, Y + 400)
        lower_cmp.operation = "GREATER_THAN"
        nk.link(z_norm.outputs["Value"], lower_cmp.inputs[0])
        lower_cmp.inputs[1].default_value = knurl_z_start

        upper_cmp = nk.n("ShaderNodeMath", "UpperCmp", X + 4*STEP, Y + 300)
        upper_cmp.operation = "LESS_THAN"
        nk.link(z_norm.outputs["Value"], upper_cmp.inputs[0])
        upper_cmp.inputs[1].default_value = knurl_z_end

        zone_mask = nk.n("ShaderNodeMath", "ZoneMask", X + 5*STEP, Y + 350)
        zone_mask.operation = "MULTIPLY"
        nk.link(lower_cmp.outputs["Value"], zone_mask.inputs[0])
        nk.link(upper_cmp.outputs["Value"], zone_mask.inputs[1])

    # === ANGULAR PATTERN ===
    # Calculate angle: atan2(x, y)
    angle = nk.n("ShaderNodeMath", "Angle", X + 2*STEP, Y + 600)
    angle.operation = "ARCTAN2"
    nk.link(sep.outputs["X"], angle.inputs[0])
    nk.link(sep.outputs["Y"], angle.inputs[1])

    # Normalize to [0, 1]: (angle + pi) / (2*pi)
    add_pi = nk.n("ShaderNodeMath", "AddPi", X + 3*STEP, Y + 600)
    add_pi.operation = "ADD"
    nk.link(angle.outputs["Value"], add_pi.inputs[0])
    add_pi.inputs[1].default_value = math.pi

    div_2pi = nk.n("ShaderNodeMath", "Div2Pi", X + 4*STEP, Y + 600)
    div_2pi.operation = "DIVIDE"
    nk.link(add_pi.outputs["Value"], div_2pi.inputs[0])
    div_2pi.inputs[1].default_value = 2 * math.pi

    # Multiply by ridge count for frequency
    freq = nk.n("ShaderNodeMath", "Frequency", X + 5*STEP, Y + 600)
    freq.operation = "MULTIPLY"
    nk.link(div_2pi.outputs["Value"], freq.inputs[0])
    freq.inputs[1].default_value = float(ridge_count)

    # Sawtooth: fract()
    sawtooth = nk.n("ShaderNodeMath", "Sawtooth", X + 6*STEP, Y + 600)
    sawtooth.operation = "FRACT"
    nk.link(freq.outputs["Value"], sawtooth.inputs[0])

    # === PROFILE SHAPING ===
    # knurl_profile: 0=flat (trapezoid), 0.5=round (sinusoidal), 1=sharp (triangular)
    #
    # We interpolate between three profile types:
    # - Flat: abs(sawtooth - 0.5) * 2 (creates flat top/bottom)
    # - Round: sin(sawtooth * 2pi) (sinusoidal)
    # - Sharp: abs(sawtooth - 0.5) * 2 then sharpen

    # For simplicity, we'll use a mix approach:
    # profile 0.0 = flat trapezoid (threshold sawtooth)
    # profile 0.5 = sinusoidal (sin pattern)
    # profile 1.0 = sharp triangular (abs pattern)

    # Shift sawtooth to center: t = sawtooth - 0.5 (range -0.5 to 0.5)
    center_saw = nk.n("ShaderNodeMath", "CenterSaw", X + 7*STEP, Y + 600)
    center_saw.operation = "SUBTRACT"
    nk.link(sawtooth.outputs["Value"], center_saw.inputs[0])
    center_saw.inputs[1].default_value = 0.5

    # Absolute value for symmetric patterns
    abs_saw = nk.n("ShaderNodeMath", "AbsSaw", X + 8*STEP, Y + 600)
    abs_saw.operation = "ABSOLUTE"
    nk.link(center_saw.outputs["Value"], abs_saw.inputs[0])

    # Scale to [-1, 1] range: abs_saw * 2
    scaled_abs = nk.n("ShaderNodeMath", "ScaledAbs", X + 9*STEP, Y + 600)
    scaled_abs.operation = "MULTIPLY"
    nk.link(abs_saw.outputs["Value"], scaled_abs.inputs[0])
    scaled_abs.inputs[1].default_value = 2.0

    # === PROFILE INTERPOLATION ===
    # We'll create three profiles and mix based on knurl_profile value

    # FLAT PROFILE (knurl_profile = 0.0)
    # Flat-bottom trapezoid: use step function
    # If we're in the middle portion, stay flat
    flat_threshold = 0.3  # Controls flat portion width
    flat_step = nk.n("ShaderNodeMath", "FlatStep", X + 10*STEP, Y + 700)
    flat_step.operation = "LESS_THAN"
    nk.link(abs_saw.outputs["Value"], flat_step.inputs[0])
    flat_step.inputs[1].default_value = flat_threshold

    # Convert step to displacement: 0 = no displacement (flat), 1 = full displacement
    flat_disp = nk.n("ShaderNodeMath", "FlatDisp", X + 11*STEP, Y + 700)
    flat_disp.operation = "SUBTRACT"
    flat_disp.inputs[0].default_value = 1.0
    nk.link(flat_step.outputs["Value"], flat_disp.inputs[1])

    # Scale flat displacement
    flat_scaled = nk.n("ShaderNodeMath", "FlatScaled", X + 12*STEP, Y + 700)
    flat_scaled.operation = "MULTIPLY"
    nk.link(flat_disp.outputs["Value"], flat_scaled.inputs[0])
    nk.link(scaled_abs.outputs["Value"], flat_scaled.inputs[1])

    # ROUND PROFILE (knurl_profile = 0.5) - this is our base sinusoidal
    # sin(sawtooth * 2pi) gives smooth sinusoidal
    sin_input = nk.n("ShaderNodeMath", "SinInput", X + 10*STEP, Y + 600)
    sin_input.operation = "MULTIPLY"
    nk.link(sawtooth.outputs["Value"], sin_input.inputs[0])
    sin_input.inputs[1].default_value = 2 * math.pi

    round_disp = nk.n("ShaderNodeMath", "RoundDisp", X + 11*STEP, Y + 600)
    round_disp.operation = "SINE"
    nk.link(sin_input.outputs["Value"], round_disp.inputs[0])

    # SHARP PROFILE (knurl_profile = 1.0)
    # Sharp V shape - just use the scaled absolute value directly
    sharp_disp = scaled_abs

    # === MIX PROFILES ===
    # First mix flat (0) and round (0.5)
    # When knurl_profile <= 0.5: mix(flat, round, knurl_profile * 2)
    # When knurl_profile > 0.5: mix(round, sharp, (knurl_profile - 0.5) * 2)

    # We'll simplify: use a single mix based on profile value
    # 0.0 -> flat, 0.5 -> round, 1.0 -> sharp

    # Mix factor for flat->round (0 to 0.5 maps to 0 to 1)
    mix_fr_factor = nk.n("ShaderNodeMath", "MixFRFactor", X + 13*STEP, Y + 650)
    mix_fr_factor.operation = "MULTIPLY"
    mix_fr_factor.inputs[0].default_value = knurl_profile
    mix_fr_factor.inputs[1].default_value = 2.0  # Scale 0-0.5 to 0-1

    mix_fr_clamped = nk.n("ShaderNodeMath", "MixFRClamped", X + 14*STEP, Y + 650)
    mix_fr_clamped.operation = "MINIMUM"
    nk.link(mix_fr_factor.outputs["Value"], mix_fr_clamped.inputs[0])
    mix_fr_clamped.inputs[1].default_value = 1.0

    # Mix flat and round
    mix_flat_round = nk.n("ShaderNodeMix", "MixFlatRound", X + 15*STEP, Y + 650)
    mix_flat_round.data_type = "FLOAT"
    nk.link(mix_fr_clamped.outputs["Value"], mix_flat_round.inputs["Factor"])
    nk.link(flat_scaled.outputs["Value"], mix_flat_round.inputs[4])  # A = flat
    nk.link(round_disp.outputs["Value"], mix_flat_round.inputs[5])   # B = round

    # Mix factor for round->sharp (0.5 to 1 maps to 0 to 1)
    mix_rs_factor = nk.n("ShaderNodeMath", "MixRSFactor", X + 13*STEP, Y + 550)
    mix_rs_factor.operation = "SUBTRACT"
    mix_rs_factor.inputs[0].default_value = knurl_profile
    mix_rs_factor.inputs[1].default_value = 0.5

    mix_rs_scaled = nk.n("ShaderNodeMath", "MixRSScaled", X + 14*STEP, Y + 550)
    mix_rs_scaled.operation = "MULTIPLY"
    nk.link(mix_rs_factor.outputs["Value"], mix_rs_scaled.inputs[0])
    mix_rs_scaled.inputs[1].default_value = 2.0

    mix_rs_clamped = nk.n("ShaderNodeMath", "MixRSClamped", X + 15*STEP, Y + 550)
    mix_rs_clamped.operation = "MAXIMUM"
    nk.link(mix_rs_scaled.outputs["Value"], mix_rs_clamped.inputs[0])
    mix_rs_clamped.inputs[1].default_value = 0.0

    mix_rs_clamp_max = nk.n("ShaderNodeMath", "MixRSClampMax", X + 16*STEP, Y + 550)
    mix_rs_clamp_max.operation = "MINIMUM"
    nk.link(mix_rs_clamped.outputs["Value"], mix_rs_clamp_max.inputs[0])
    mix_rs_clamp_max.inputs[1].default_value = 1.0

    # Mix round and sharp (use mix_flat_round result as base when profile <= 0.5)
    mix_round_sharp = nk.n("ShaderNodeMix", "MixRoundSharp", X + 17*STEP, Y + 600)
    mix_round_sharp.data_type = "FLOAT"
    nk.link(mix_rs_clamp_max.outputs["Value"], mix_round_sharp.inputs["Factor"])
    nk.link(mix_flat_round.outputs[2], mix_round_sharp.inputs[4])  # A = flat/round mix
    nk.link(sharp_disp.outputs["Value"], mix_round_sharp.inputs[5])  # B = sharp

    profile_disp = mix_round_sharp.outputs[2]

    # === APPLY ZONE MASK ===
    # Multiply displacement by zone mask
    masked_disp = nk.n("ShaderNodeMath", "MaskedDisp", X + 18*STEP, Y + 500)
    masked_disp.operation = "MULTIPLY"
    nk.link(profile_disp, masked_disp.inputs[0])
    nk.link(zone_mask.outputs["Value"], masked_disp.inputs[1])

    # Scale by ridge depth
    depth = nk.n("ShaderNodeMath", "RidgeDepth", X + 19*STEP, Y + 500)
    depth.operation = "MULTIPLY"
    nk.link(masked_disp.outputs["Value"], depth.inputs[0])
    depth.inputs[1].default_value = ridge_depth

    # Get normal for displacement direction
    normal = nk.n("GeometryNodeInputNormal", "GetNormal", X + 19*STEP, Y + 350)

    # Scale normal by displacement value
    scale_disp = nk.n("ShaderNodeVectorMath", "ScaleDisplacement", X + 20*STEP, Y + 400)
    scale_disp.operation = "SCALE"
    nk.link(normal.outputs["Normal"], scale_disp.inputs["Vector"])
    nk.link(depth.outputs["Value"], scale_disp.inputs["Scale"])

    # Set position with offset
    set_pos = nk.n("GeometryNodeSetPosition", "SetRidgePosition", X + 21*STEP, Y)
    nk.link(geo_in, set_pos.inputs["Geometry"])
    nk.link(scale_disp.outputs["Vector"], set_pos.inputs["Offset"])

    return set_pos.outputs["Geometry"]


def _build_pointer(nk: NodeKit, cap_diameter: float, skirt_height: float, cap_height: float,
                   pointer_length: float, pointer_width_rad: float, x: float, y: float):
    """
    Build the pointer line as raised cube geometry.

    Creates a thin rectangular prism on top of the cap, pointing at 12 o'clock.
    """
    # Calculate width from angular width
    pointer_width = (cap_diameter / 2) * pointer_width_rad
    pointer_thickness = 0.0005  # 0.5mm fixed

    # Create cube
    cube = nk.n("GeometryNodeMeshCube", "PointerCube", x, y)
    cube.inputs["Size"].default_value = (pointer_width, pointer_length, pointer_thickness)
    cube.inputs["Vertices X"].default_value = 1
    cube.inputs["Vertices Y"].default_value = 1
    cube.inputs["Vertices Z"].default_value = 1

    # Position: on top of cap, pointing at 12 o'clock (-Y direction)
    pointer_z = skirt_height + cap_height + pointer_thickness / 2
    pointer_y = -pointer_length / 2  # Offset so pointer tip is at center

    transform = nk.n("GeometryNodeTransform", "PointerTransform", x + 200, y)
    nk.link(cube.outputs["Mesh"], transform.inputs["Geometry"])
    transform.inputs["Translation"].default_value = (0, pointer_y, pointer_z)

    return transform.outputs["Geometry"]


def _create_material(params: dict) -> bpy.types.Material:
    """
    Create material with position-based pointer color mask.

    The pointer is rendered as a wedge-shaped color overlay based on angular position.
    """
    mat = bpy.data.materials.new("NeveKnobMaterial")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    nk = NodeKit(nt)

    base_color = params.get("base_color", [0.5, 0.5, 0.5])
    pointer_color = params.get("pointer_color", [1.0, 1.0, 1.0])
    pointer_width = params.get("pointer_width", 0.08)
    metallic = params.get("metallic", 0.0)
    roughness = params.get("roughness", 0.3)
    clearcoat = params.get("clearcoat", 0.0)

    X = -1000
    STEP = 100

    # Get position
    geo = nk.n("ShaderNodeNewGeometry", "Geometry", X, 0)
    sep = nk.n("ShaderNodeSeparateXYZ", "SepPosition", X + STEP, 0)
    nk.link(geo.outputs["Position"], sep.inputs["Vector"])

    # Negate Y for 12 o'clock direction
    neg_y = nk.n("ShaderNodeMath", "NegateY", X + 2*STEP, 0)
    neg_y.operation = "MULTIPLY"
    nk.link(sep.outputs["Y"], neg_y.inputs[0])
    neg_y.inputs[1].default_value = -1.0

    # Calculate angle: atan2(x, -y)
    angle = nk.n("ShaderNodeMath", "Angle", X + 3*STEP, 0)
    angle.operation = "ARCTAN2"
    nk.link(sep.outputs["X"], angle.inputs[0])
    nk.link(neg_y.outputs["Value"], angle.inputs[1])

    # Absolute value
    abs_angle = nk.n("ShaderNodeMath", "AbsAngle", X + 4*STEP, 0)
    abs_angle.operation = "ABSOLUTE"
    nk.link(angle.outputs["Value"], abs_angle.inputs[0])

    # Wedge mask: |angle| < pointer_width
    wedge = nk.n("ShaderNodeMath", "WedgeMask", X + 5*STEP, 0)
    wedge.operation = "LESS_THAN"
    nk.link(abs_angle.outputs["Value"], wedge.inputs[0])
    wedge.inputs[1].default_value = pointer_width

    # Mix colors based on mask
    mix = nk.n("ShaderNodeMix", "ColorMix", X + 6*STEP, 0)
    mix.data_type = "RGBA"
    nk.link(wedge.outputs["Value"], mix.inputs["Factor"])
    mix.inputs[6].default_value = (*base_color, 1.0)     # A = base color
    mix.inputs[7].default_value = (*pointer_color, 1.0)  # B = pointer color

    # Principled BSDF
    bsdf = nk.n("ShaderNodeBsdfPrincipled", "BSDF", X + 8*STEP, 0)
    nk.link(mix.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness

    if clearcoat > 0:
        bsdf.inputs["Coat Weight"].default_value = clearcoat
        bsdf.inputs["Coat Roughness"].default_value = 0.05

    # Output
    out = nk.n("ShaderNodeOutputMaterial", "Output", X + 10*STEP, 0)
    nk.link(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat
