"""
Zone Geometry Builder

Builds zone-based geometry using Blender Geometry Nodes.
Creates reusable node groups that can be linked from other files.

Zone Structure:
┌─────────────────────────────────────────┐  ← Top of Zone A
│           ZONE A - TOP CAP              │
├─────────────────────────────────────────┤
│           ZONE A - MIDDLE               │  (with optional knurling)
├─────────────────────────────────────────┤
│           ZONE A - BOTTOM CAP           │
├─────────────────────────────────────────┤  ← Zone boundary
│           ZONE B - TOP CAP              │
├─────────────────────────────────────────┤
│           ZONE B - MIDDLE               │  (with optional knurling)
├─────────────────────────────────────────┤
│           ZONE B - BOTTOM CAP           │
└─────────────────────────────────────────┘  ← Bottom (Z=0)
"""

from __future__ import annotations
import bpy
import math
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib.nodekit import NodeKit
from lib.inputs.input_types import (
    ZoneConfig, CapConfig, KnurlConfig, InputConfig,
    CapStyle, KnurlProfile, BaseShape, mm
)


@dataclass
class ZoneGeometry:
    """
    Result of building a zone's geometry.

    Contains the geometry socket and the Z position after the zone.
    """
    geometry: Any  # Geometry socket
    z_end: float   # Z position after this zone


class ZoneBuilder:
    """
    Builds zone-based geometry using Geometry Nodes.

    This builder creates the actual mesh geometry for input controls
    based on zone configurations.
    """

    def __init__(self, node_tree: bpy.types.NodeTree):
        """
        Initialize builder with a Geometry Node tree.

        Args:
            node_tree: Blender GeometryNodeTree to build in
        """
        self.nk = NodeKit(node_tree)
        self.tree = node_tree

    def build_input(self, config: InputConfig, x: float = 0, y: float = 0) -> Any:
        """
        Build complete input geometry from configuration.

        Args:
            config: Complete input configuration
            x, y: Starting node position

        Returns:
            Geometry socket with complete input geometry
        """
        X = x
        Y = y
        STEP = 200

        # Start at Z=0 (bottom of input)
        z_current = 0.0

        # Collect all geometry parts
        geo_parts = []

        # === BUILD ZONE B (BOTTOM) ===
        if config.zone_b.height_mm > 0:
            zone_b_geo, z_current = self.build_zone(
                config.zone_b,
                config.base_shape,
                config.segments,
                config.cap_segments,
                z_current,
                "B",
                X, Y - STEP * 3
            )
            if zone_b_geo:
                geo_parts.append(zone_b_geo)

        # === BUILD ZONE A (TOP) ===
        if config.zone_a.height_mm > 0:
            zone_a_geo, z_current = self.build_zone(
                config.zone_a,
                config.base_shape,
                config.segments,
                config.cap_segments,
                z_current,
                "A",
                X, Y
            )
            if zone_a_geo:
                geo_parts.append(zone_a_geo)

        # === JOIN ALL PARTS ===
        if not geo_parts:
            return None

        if len(geo_parts) == 1:
            return geo_parts[0]

        join_all = self.nk.n("GeometryNodeJoinGeometry", "JoinAllZones", X + STEP, Y)
        for geo in geo_parts:
            self.nk.link(geo, join_all.inputs["Geometry"])

        return join_all.outputs["Geometry"]

    def build_zone(
        self,
        zone: ZoneConfig,
        base_shape: BaseShape,
        segments: int,
        cap_segments: int,
        z_start: float,
        zone_name: str,
        x: float,
        y: float
    ) -> Tuple[Optional[Any], float]:
        """
        Build a single zone with caps and middle section.

        Args:
            zone: Zone configuration
            base_shape: Overall shape type
            segments: Circumference segments
            cap_segments: Radial segments for rounded caps
            z_start: Starting Z position
            zone_name: Zone identifier (for node naming)
            x, y: Node position

        Returns:
            (geometry_socket, z_end) tuple
        """
        X = x
        Y = y
        STEP = 100

        geo_parts = []
        z_current = z_start

        # Calculate middle height (total minus caps)
        middle_height_m = zone.height_m - zone.top_cap.height_m - zone.bottom_cap.height_m

        # === BOTTOM CAP ===
        if zone.bottom_cap.height_m > 0:
            cap_geo, z_current = self.build_cap(
                zone.bottom_cap,
                zone.width_bottom_m / 2,  # Radius at bottom
                segments,
                cap_segments,
                z_current,
                "down",
                f"Zone{zone_name}_BottomCap",
                X, Y - STEP * 2
            )
            if cap_geo:
                geo_parts.append(cap_geo)

        # === MIDDLE SECTION ===
        if middle_height_m > 0:
            mid_geo, z_current = self.build_middle(
                zone.width_bottom_m / 2,
                zone.width_top_m / 2,
                middle_height_m,
                segments,
                z_current,
                f"Zone{zone_name}_Middle",
                X, Y - STEP
            )
            if mid_geo:
                geo_parts.append(mid_geo)

            # Apply knurling to middle section
            if zone.middle_knurl.enabled and zone.middle_knurl.count > 0:
                mid_geo = self.apply_knurling(
                    mid_geo,
                    zone.width_top_m / 2,  # Approximate radius
                    middle_height_m,
                    z_current - middle_height_m,
                    zone.middle_knurl,
                    segments,
                    f"Zone{zone_name}_Knurl",
                    X + STEP, Y - STEP
                )

        # === TOP CAP ===
        if zone.top_cap.height_m > 0:
            cap_geo, z_current = self.build_cap(
                zone.top_cap,
                zone.width_top_m / 2,  # Radius at top
                segments,
                cap_segments,
                z_current,
                "up",
                f"Zone{zone_name}_TopCap",
                X, Y
            )
            if cap_geo:
                geo_parts.append(cap_geo)

        # Join zone parts
        if not geo_parts:
            return None, z_start

        if len(geo_parts) == 1:
            return geo_parts[0], z_current

        join_zone = self.nk.n(
            "GeometryNodeJoinGeometry",
            f"JoinZone{zone_name}",
            X + STEP * 3, Y
        )
        for geo in geo_parts:
            self.nk.link(geo, join_zone.inputs["Geometry"])

        return join_zone.outputs["Geometry"], z_current

    def build_cap(
        self,
        cap: CapConfig,
        radius: float,
        segments: int,
        cap_segments: int,
        z_start: float,
        direction: str,
        name: str,
        x: float,
        y: float
    ) -> Tuple[Optional[Any], float]:
        """
        Build a cap section.

        Args:
            cap: Cap configuration
            radius: Cap radius in meters
            segments: Circumference segments
            cap_segments: Radial segments for rounded caps
            z_start: Starting Z position
            direction: "up" or "down"
            name: Node name prefix
            x, y: Node position

        Returns:
            (geometry_socket, z_end) tuple
        """
        if cap.height_m <= 0:
            return None, z_start

        X = x
        Y = y
        height = cap.height_m

        if cap.style == CapStyle.FLAT:
            # Simple flat cylinder
            cyl = self.nk.n("GeometryNodeMeshCylinder", f"{name}_Cyl", X, Y)
            cyl.inputs["Vertices"].default_value = segments
            cyl.inputs["Radius"].default_value = radius
            cyl.inputs["Depth"].default_value = height

            transform = self.nk.n("GeometryNodeTransform", f"{name}_Transform", X + 150, Y)
            self.nk.link(cyl.outputs["Mesh"], transform.inputs["Geometry"])

            if direction == "up":
                z_center = z_start + height / 2
                z_end = z_start + height
            else:
                z_center = z_start - height / 2
                z_end = z_start - height

            transform.inputs["Translation"].default_value = (0, 0, z_center)

            return transform.outputs["Geometry"], z_end

        elif cap.style == CapStyle.BEVEL:
            # Beveled cap using cone (slightly tapered)
            # Bevel is essentially a small tapered section
            bevel_height = min(height * 0.3, radius * 0.5)  # Bevel portion
            main_height = height - bevel_height

            # Main cylinder
            cyl = self.nk.n("GeometryNodeMeshCylinder", f"{name}_MainCyl", X, Y)
            cyl.inputs["Vertices"].default_value = segments
            cyl.inputs["Radius"].default_value = radius
            cyl.inputs["Depth"].default_value = main_height

            # Bevel cone
            cone = self.nk.n("GeometryNodeMeshCone", f"{name}_BevelCone", X, Y - 100)
            cone.inputs["Vertices"].default_value = segments
            cone.inputs["Radius Top"].default_value = radius * 0.9  # Slight taper
            cone.inputs["Radius Bottom"].default_value = radius
            cone.inputs["Depth"].default_value = bevel_height

            # Join and transform
            join = self.nk.n("GeometryNodeJoinGeometry", f"{name}_Join", X + 150, Y - 50)
            self.nk.link(cyl.outputs["Mesh"], join.inputs["Geometry"])
            self.nk.link(cone.outputs["Mesh"], join.inputs["Geometry"])

            transform = self.nk.n("GeometryNodeTransform", f"{name}_Transform", X + 300, Y - 50)
            self.nk.link(join.outputs["Geometry"], transform.inputs["Geometry"])

            if direction == "up":
                z_center = z_start + height / 2
                z_end = z_start + height
            else:
                z_center = z_start - height / 2
                z_end = z_start - height
                transform.inputs["Rotation"].default_value = (math.pi, 0, 0)

            transform.inputs["Translation"].default_value = (0, 0, z_center)

            return transform.outputs["Geometry"], z_end

        elif cap.style == CapStyle.ROUNDED:
            # Rounded cap using sphere portion
            # Use a hemisphere
            sphere = self.nk.n("GeometryNodeMeshUVSphere", f"{name}_Sphere", X, Y)
            sphere.inputs["Segments"].default_value = segments
            sphere.inputs["Rings"].default_value = cap_segments
            sphere.inputs["Radius"].default_value = radius

            transform = self.nk.n("GeometryNodeTransform", f"{name}_Transform", X + 150, Y)
            self.nk.link(sphere.outputs["Mesh"], transform.inputs["Geometry"])

            if direction == "up":
                z_end = z_start + radius  # Hemisphere adds radius to height
                transform.inputs["Translation"].default_value = (0, 0, z_start + radius)
            else:
                z_end = z_start - radius
                transform.inputs["Translation"].default_value = (0, 0, z_start - radius)
                transform.inputs["Rotation"].default_value = (math.pi, 0, 0)

            return transform.outputs["Geometry"], z_end

        return None, z_start

    def build_middle(
        self,
        radius_bottom: float,
        radius_top: float,
        height: float,
        segments: int,
        z_start: float,
        name: str,
        x: float,
        y: float
    ) -> Tuple[Optional[Any], float]:
        """
        Build the middle (main) section of a zone.

        Can be tapered if top and bottom radii differ.

        Args:
            radius_bottom: Radius at bottom in meters
            radius_top: Radius at top in meters
            height: Section height in meters
            segments: Circumference segments
            z_start: Starting Z position
            name: Node name prefix
            x, y: Node position

        Returns:
            (geometry_socket, z_end) tuple
        """
        if height <= 0:
            return None, z_start

        X = x
        Y = y

        # Use cone for tapered sections, cylinder for straight
        if abs(radius_bottom - radius_top) < 0.0001:
            # Straight cylinder
            cyl = self.nk.n("GeometryNodeMeshCylinder", f"{name}_Cyl", X, Y)
            cyl.inputs["Vertices"].default_value = segments
            cyl.inputs["Radius"].default_value = radius_bottom
            cyl.inputs["Depth"].default_value = height
            mesh_out = cyl.outputs["Mesh"]
        else:
            # Tapered cone
            cone = self.nk.n("GeometryNodeMeshCone", f"{name}_Cone", X, Y)
            cone.inputs["Vertices"].default_value = segments
            cone.inputs["Radius Bottom"].default_value = radius_bottom
            cone.inputs["Radius Top"].default_value = radius_top
            cone.inputs["Depth"].default_value = height
            mesh_out = cone.outputs["Mesh"]

        # Transform to position
        transform = self.nk.n("GeometryNodeTransform", f"{name}_Transform", X + 150, Y)
        self.nk.link(mesh_out, transform.inputs["Geometry"])

        z_center = z_start + height / 2
        z_end = z_start + height

        transform.inputs["Translation"].default_value = (0, 0, z_center)

        return transform.outputs["Geometry"], z_end

    def apply_knurling(
        self,
        geo_in,
        radius: float,
        section_height: float,
        z_base: float,
        knurl: KnurlConfig,
        segments: int,
        name: str,
        x: float,
        y: float
    ) -> Any:
        """
        Apply knurling (grip grooves) to geometry.

        Uses Set Position to displace vertices inward.

        Args:
            geo_in: Input geometry socket
            radius: Approximate radius
            section_height: Height of section being knurled
            z_base: Z position of section bottom
            knurl: Knurl configuration
            segments: Mesh segments
            name: Node name prefix
            x, y: Node position

        Returns:
            Geometry socket with knurling applied
        """
        if not knurl.enabled or knurl.count <= 0:
            return geo_in

        X = x
        Y = y
        STEP = 80

        # Get position and normal
        pos = self.nk.n("GeometryNodeInputPosition", f"{name}_Pos", X, Y + 300)
        sep = self.nk.n("ShaderNodeSeparateXYZ", f"{name}_SepPos", X + STEP, Y + 300)
        self.nk.link(pos.outputs["Position"], sep.inputs["Vector"])

        normal = self.nk.n("GeometryNodeInputNormal", f"{name}_Normal", X, Y + 200)

        # === ZONE MASK ===
        # Only apply knurling within this section's height
        lower_cmp = self.nk.n("ShaderNodeMath", f"{name}_LowerCmp", X + 2*STEP, Y + 300)
        lower_cmp.operation = "GREATER_THAN"
        self.nk.link(sep.outputs["Z"], lower_cmp.inputs[0])
        lower_cmp.inputs[1].default_value = z_base

        upper_cmp = self.nk.n("ShaderNodeMath", f"{name}_UpperCmp", X + 2*STEP, Y + 200)
        upper_cmp.operation = "LESS_THAN"
        self.nk.link(sep.outputs["Z"], upper_cmp.inputs[0])
        upper_cmp.inputs[1].default_value = z_base + section_height

        zone_mask = self.nk.n("ShaderNodeMath", f"{name}_ZoneMask", X + 3*STEP, Y + 250)
        zone_mask.operation = "MULTIPLY"
        self.nk.link(lower_cmp.outputs["Value"], zone_mask.inputs[0])
        self.nk.link(upper_cmp.outputs["Value"], zone_mask.inputs[1])

        # === ANGULAR PATTERN ===
        angle = self.nk.n("ShaderNodeMath", f"{name}_Angle", X + 2*STEP, Y + 400)
        angle.operation = "ARCTAN2"
        self.nk.link(sep.outputs["X"], angle.inputs[0])
        self.nk.link(sep.outputs["Y"], angle.inputs[1])

        # Normalize to [0, 1]
        add_pi = self.nk.n("ShaderNodeMath", f"{name}_AddPi", X + 3*STEP, Y + 400)
        add_pi.operation = "ADD"
        self.nk.link(angle.outputs["Value"], add_pi.inputs[0])
        add_pi.inputs[1].default_value = math.pi

        div_2pi = self.nk.n("ShaderNodeMath", f"{name}_Div2Pi", X + 4*STEP, Y + 400)
        div_2pi.operation = "DIVIDE"
        self.nk.link(add_pi.outputs["Value"], div_2pi.inputs[0])
        div_2pi.inputs[1].default_value = 2 * math.pi

        # Multiply by count for frequency
        freq = self.nk.n("ShaderNodeMath", f"{name}_Freq", X + 5*STEP, Y + 400)
        freq.operation = "MULTIPLY"
        self.nk.link(div_2pi.outputs["Value"], freq.inputs[0])
        freq.inputs[1].default_value = float(knurl.count)

        # Sawtooth: fract()
        sawtooth = self.nk.n("ShaderNodeMath", f"{name}_Sawtooth", X + 6*STEP, Y + 400)
        sawtooth.operation = "FRACT"
        self.nk.link(freq.outputs["Value"], sawtooth.inputs[0])

        # === PROFILE SHAPING ===
        if knurl.profile == KnurlProfile.V_SHAPED:
            profile_disp = self._build_v_profile(sawtooth, knurl.width_fraction, X, Y + 400, STEP, name)
        elif knurl.profile == KnurlProfile.U_SHAPED:
            profile_disp = self._build_u_profile(sawtooth, X, Y + 400, STEP, name)
        else:  # FLAT
            profile_disp = self._build_flat_profile(sawtooth, knurl.width_fraction, X, Y + 400, STEP, name)

        # === APPLY ZONE MASK AND DEPTH ===
        masked_disp = self.nk.n("ShaderNodeMath", f"{name}_MaskedDisp", X + 14*STEP, Y + 300)
        masked_disp.operation = "MULTIPLY"
        self.nk.link(profile_disp.outputs["Value"], masked_disp.inputs[0])
        self.nk.link(zone_mask.outputs["Value"], masked_disp.inputs[1])

        scaled_depth = self.nk.n("ShaderNodeMath", f"{name}_ScaledDepth", X + 15*STEP, Y + 300)
        scaled_depth.operation = "MULTIPLY"
        self.nk.link(masked_disp.outputs["Value"], scaled_depth.inputs[0])
        scaled_depth.inputs[1].default_value = knurl.depth_m

        # NEGATE for inward displacement
        neg_depth = self.nk.n("ShaderNodeMath", f"{name}_NegDepth", X + 16*STEP, Y + 300)
        neg_depth.operation = "MULTIPLY"
        self.nk.link(scaled_depth.outputs["Value"], neg_depth.inputs[0])
        neg_depth.inputs[1].default_value = -1.0

        # Scale normal by displacement
        scale_disp = self.nk.n("ShaderNodeVectorMath", f"{name}_ScaleDisp", X + 17*STEP, Y + 250)
        scale_disp.operation = "SCALE"
        self.nk.link(normal.outputs["Normal"], scale_disp.inputs["Vector"])
        self.nk.link(neg_depth.outputs["Value"], scale_disp.inputs["Scale"])

        # Set position
        set_pos = self.nk.n("GeometryNodeSetPosition", f"{name}_SetPos", X + 18*STEP, Y)
        self.nk.link(geo_in, set_pos.inputs["Geometry"])
        self.nk.link(scale_disp.outputs["Vector"], set_pos.inputs["Offset"])

        return set_pos.outputs["Geometry"]

    def _build_v_profile(self, sawtooth_node, width: float, x: float, y: float, step: float, name: str):
        """Build V-shaped groove profile."""
        X = x
        Y = y
        STEP = step

        # Center the groove: (sawtooth - 0.5) * 2
        centered = self.nk.n("ShaderNodeMath", f"{name}_Center", X + 7*STEP, Y)
        centered.operation = "SUBTRACT"
        self.nk.link(sawtooth_node.outputs["Value"], centered.inputs[0])
        centered.inputs[1].default_value = 0.5

        scaled = self.nk.n("ShaderNodeMath", f"{name}_ScaleSaw", X + 8*STEP, Y)
        scaled.operation = "MULTIPLY"
        self.nk.link(centered.outputs["Value"], scaled.inputs[0])
        scaled.inputs[1].default_value = 2.0

        # Absolute value
        abs_val = self.nk.n("ShaderNodeMath", f"{name}_Abs", X + 9*STEP, Y)
        abs_val.operation = "ABSOLUTE"
        self.nk.link(scaled.outputs["Value"], abs_val.inputs[0])

        # Width mask
        width_mask = self.nk.n("ShaderNodeMath", f"{name}_WidthMask", X + 10*STEP, Y)
        width_mask.operation = "LESS_THAN"
        self.nk.link(abs_val.outputs["Value"], width_mask.inputs[0])
        width_mask.inputs[1].default_value = width

        # V-shape: 1 - |value|/width
        ratio = self.nk.n("ShaderNodeMath", f"{name}_Ratio", X + 11*STEP, Y)
        ratio.operation = "DIVIDE"
        self.nk.link(abs_val.outputs["Value"], ratio.inputs[0])
        ratio.inputs[1].default_value = width

        one_minus = self.nk.n("ShaderNodeMath", f"{name}_OneMinus", X + 12*STEP, Y)
        one_minus.operation = "SUBTRACT"
        one_minus.inputs[0].default_value = 1.0
        self.nk.link(ratio.outputs["Value"], one_minus.inputs[1])

        # Apply width mask
        profile_disp = self.nk.n("ShaderNodeMath", f"{name}_VProfile", X + 13*STEP, Y)
        profile_disp.operation = "MULTIPLY"
        self.nk.link(one_minus.outputs["Value"], profile_disp.inputs[0])
        self.nk.link(width_mask.outputs["Value"], profile_disp.inputs[1])

        return profile_disp

    def _build_u_profile(self, sawtooth_node, x: float, y: float, step: float, name: str):
        """Build U-shaped (rounded) groove profile."""
        X = x
        Y = y
        STEP = step

        # sin(sawtooth * pi) creates smooth U shapes
        sin_input = self.nk.n("ShaderNodeMath", f"{name}_SinIn", X + 7*STEP, Y)
        sin_input.operation = "MULTIPLY"
        self.nk.link(sawtooth_node.outputs["Value"], sin_input.inputs[0])
        sin_input.inputs[1].default_value = math.pi

        sin_val = self.nk.n("ShaderNodeMath", f"{name}_SinVal", X + 8*STEP, Y)
        sin_val.operation = "SINE"
        self.nk.link(sin_input.outputs["Value"], sin_val.inputs[0])

        # For grooves: 1 - abs(sin)
        abs_sin = self.nk.n("ShaderNodeMath", f"{name}_AbsSin", X + 9*STEP, Y)
        abs_sin.operation = "ABSOLUTE"
        self.nk.link(sin_val.outputs["Value"], abs_sin.inputs[0])

        profile_disp = self.nk.n("ShaderNodeMath", f"{name}_UProfile", X + 10*STEP, Y)
        profile_disp.operation = "SUBTRACT"
        profile_disp.inputs[0].default_value = 1.0
        self.nk.link(abs_sin.outputs["Value"], profile_disp.inputs[1])

        return profile_disp

    def _build_flat_profile(self, sawtooth_node, width: float, x: float, y: float, step: float, name: str):
        """Build flat-bottom groove profile."""
        X = x
        Y = y
        STEP = step

        # Center and absolute
        centered = self.nk.n("ShaderNodeMath", f"{name}_Center", X + 7*STEP, Y)
        centered.operation = "SUBTRACT"
        self.nk.link(sawtooth_node.outputs["Value"], centered.inputs[0])
        centered.inputs[1].default_value = 0.5

        scaled = self.nk.n("ShaderNodeMath", f"{name}_ScaleSaw", X + 8*STEP, Y)
        scaled.operation = "MULTIPLY"
        self.nk.link(centered.outputs["Value"], scaled.inputs[0])
        scaled.inputs[1].default_value = 2.0

        abs_val = self.nk.n("ShaderNodeMath", f"{name}_Abs", X + 9*STEP, Y)
        abs_val.operation = "ABSOLUTE"
        self.nk.link(scaled.outputs["Value"], abs_val.inputs[0])

        # Flat groove: constant depth where |value| < width
        profile_disp = self.nk.n("ShaderNodeMath", f"{name}_FlatProfile", X + 10*STEP, Y)
        profile_disp.operation = "LESS_THAN"
        self.nk.link(abs_val.outputs["Value"], profile_disp.inputs[0])
        profile_disp.inputs[1].default_value = width

        return profile_disp
