"""
Road UV Utilities for Charlotte Digital Twin

Handles UV unwrapping and texture coordinate generation for road meshes.

Usage:
    from lib.charlotte_digital_twin.geometry import RoadUVGenerator

    uv_gen = RoadUVGenerator()

    # Calculate UV for road segment
    uvs = uv_gen.calculate_road_uv(segment)

    # Apply UV to mesh
    uv_gen.apply_uv_to_mesh(mesh, uvs)
"""

import math
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from .types import RoadSegment, WorldCoordinate


@dataclass
class UVConfig:
    """Configuration for UV generation."""
    scale_u: float = 1.0  # Scale along road length
    scale_v: float = 1.0  # Scale across road width
    offset_u: float = 0.0
    offset_v: float = 0.0
    tile_u: bool = True   # Tile along length
    tile_v: bool = False  # Tile across width (usually single texture across)
    rotation: float = 0.0  # UV rotation in radians


class RoadUVGenerator:
    """
    Generates UV coordinates for road meshes.

    Features:
    - Length-based U coordinate (tiles along road)
    - Width-based V coordinate (0-1 across road)
    - Support for different UV scaling modes
    - Intersection UV handling
    """

    def __init__(self, config: Optional[UVConfig] = None):
        """Initialize UV generator."""
        self.config = config or UVConfig()

    def calculate_road_uv(
        self,
        segment: RoadSegment,
        texture_width: float = 4.0,
    ) -> List[Tuple[float, float]]:
        """
        Calculate UV coordinates for a road segment.

        Args:
            segment: RoadSegment to calculate UVs for
            texture_width: Width of texture in meters (for tiling)

        Returns:
            List of (u, v) coordinate tuples
        """
        if len(segment.coordinates) < 2:
            return []

        uvs = []
        cumulative_length = 0.0

        # Calculate cumulative lengths for U coordinate
        for i, coord in enumerate(segment.coordinates):
            if i > 0:
                prev = segment.coordinates[i - 1]
                dx = coord.x - prev.x
                dy = coord.y - prev.y
                cumulative_length += math.sqrt(dx * dx + dy * dy)

            # U coordinate based on cumulative length
            u = cumulative_length / texture_width * self.config.scale_u
            if self.config.tile_u:
                u = u % 1.0  # Tile to 0-1 range

            # V coordinates for left and right edge of road
            v_left = 0.0 * self.config.scale_v
            v_right = 1.0 * self.config.scale_v

            if self.config.tile_v:
                v_left = v_left % 1.0
                v_right = v_right % 1.0

            # Add both left and right UV for this vertex pair
            uvs.append((u + self.config.offset_u, v_left + self.config.offset_v))
            uvs.append((u + self.config.offset_u, v_right + self.config.offset_v))

        return uvs

    def calculate_road_uv_detailed(
        self,
        segment: RoadSegment,
        texture_width: float = 4.0,
        include_lane_markings: bool = True,
    ) -> dict:
        """
        Calculate detailed UV coordinates with lane marking channels.

        Args:
            segment: RoadSegment to calculate UVs for
            texture_width: Width of texture in meters
            include_lane_markings: Whether to include lane marking UVs

        Returns:
            Dictionary with 'base' and optionally 'lane_markings' UV sets
        """
        base_uvs = self.calculate_road_uv(segment, texture_width)

        result = {"base": base_uvs}

        if include_lane_markings and segment.lanes > 1:
            # Calculate center line UVs
            center_uvs = self._calculate_center_line_uv(segment, texture_width)
            result["center_line"] = center_uvs

            # Calculate lane divider UVs
            if segment.lanes > 2:
                lane_uvs = self._calculate_lane_divider_uv(segment, texture_width)
                result["lane_dividers"] = lane_uvs

        return result

    def _calculate_center_line_uv(
        self,
        segment: RoadSegment,
        texture_width: float,
    ) -> List[Tuple[float, float]]:
        """Calculate UVs for center line marking."""
        uvs = []
        cumulative_length = 0.0

        for i, coord in enumerate(segment.coordinates):
            if i > 0:
                prev = segment.coordinates[i - 1]
                dx = coord.x - prev.x
                dy = coord.y - prev.y
                cumulative_length += math.sqrt(dx * dx + dy * dy)

            u = cumulative_length / texture_width
            u = u % 1.0

            # Center line is at V = 0.5 with small width
            v_center = 0.5
            v_half_width = 0.02  # 2% of texture width

            uvs.append((u, v_center - v_half_width))
            uvs.append((u, v_center + v_half_width))

        return uvs

    def _calculate_lane_divider_uv(
        self,
        segment: RoadSegment,
        texture_width: float,
    ) -> List[List[Tuple[float, float]]]:
        """Calculate UVs for lane divider markings."""
        all_dividers = []
        cumulative_length = 0.0

        # Calculate V positions for each lane divider
        # For N lanes, we have N-1 dividers
        num_dividers = segment.lanes - 1

        for divider_idx in range(num_dividers):
            divider_uvs = []
            v_pos = (divider_idx + 1) / segment.lanes

            cumulative_length = 0.0
            for i, coord in enumerate(segment.coordinates):
                if i > 0:
                    prev = segment.coordinates[i - 1]
                    dx = coord.x - prev.x
                    dy = coord.y - prev.y
                    cumulative_length += math.sqrt(dx * dx + dy * dy)

                u = cumulative_length / texture_width
                u = u % 1.0

                v_half_width = 0.01
                divider_uvs.append((u, v_pos - v_half_width))
                divider_uvs.append((u, v_pos + v_half_width))

            all_dividers.append(divider_uvs)

        return all_dividers

    def apply_uv_to_mesh(
        self,
        mesh: Any,
        uvs: List[Tuple[float, float]],
        uv_layer_name: str = "UVMap",
    ) -> bool:
        """
        Apply UV coordinates to a Blender mesh.

        Args:
            mesh: Blender mesh object
            uvs: List of UV coordinates
            uv_layer_name: Name for UV layer

        Returns:
            True if successful
        """
        try:
            import bpy
        except ImportError:
            return False

        # Get or create UV layer
        if uv_layer_name in mesh.uv_layers:
            uv_layer = mesh.uv_layers[uv_layer_name]
        else:
            uv_layer = mesh.uv_layers.new(name=uv_layer_name)

        # Apply UVs to loops
        for i, loop in enumerate(mesh.loops):
            if i < len(uvs):
                uv_layer.data[loop.index].uv = uvs[i]

        return True

    def create_uv2_for_ao(
        self,
        segment: RoadSegment,
        unwrap_method: str = "smart",
    ) -> List[Tuple[float, float]]:
        """
        Create secondary UV channel for ambient occlusion.

        This creates non-overlapping UVs for lightmap baking.

        Args:
            segment: RoadSegment
            unwrap_method: "smart" or "lightmap"

        Returns:
            List of UV coordinates
        """
        # For AO, we want non-overlapping UVs
        # Use a simple approach: pack each segment into a grid
        uvs = []

        if unwrap_method == "lightmap":
            # Lightmap-style packing with margins
            margin = 0.02
            for i, coord in enumerate(segment.coordinates):
                # Simple linear packing
                u = (i / max(1, len(segment.coordinates) - 1)) * (1.0 - 2 * margin) + margin
                v = 0.5  # Center of lightmap
                uvs.append((u, v - 0.1))
                uvs.append((u, v + 0.1))
        else:
            # Smart unwrap - follow road shape
            uvs = self.calculate_road_uv(segment, texture_width=100.0)

        return uvs

    def calculate_intersection_uv(
        self,
        position: WorldCoordinate,
        radius: float,
        segments: int = 16,
    ) -> List[Tuple[float, float]]:
        """
        Calculate UV coordinates for intersection marker.

        Args:
            position: Center of intersection
            radius: Radius of marker
            segments: Number of segments in circle

        Returns:
            List of UV coordinates
        """
        uvs = []

        # Create radial UV mapping
        for i in range(segments):
            angle = 2 * math.pi * i / segments

            # UV based on angle and radius
            u = 0.5 + 0.5 * math.cos(angle)
            v = 0.5 + 0.5 * math.sin(angle)

            uvs.append((u, v))

        # Center UV
        uvs.append((0.5, 0.5))

        return uvs

    def get_recommended_texture_size(
        self,
        segment: RoadSegment,
        pixels_per_meter: int = 128,
    ) -> Tuple[int, int]:
        """
        Get recommended texture size for a road segment.

        Args:
            segment: RoadSegment
            pixels_per_meter: Resolution

        Returns:
            (width, height) in pixels
        """
        length = segment.get_length()
        width = segment.width

        # Calculate pixel dimensions
        tex_width = int(length * pixels_per_meter)
        tex_height = int(width * pixels_per_meter)

        # Round to power of 2
        tex_width = 2 ** int(math.ceil(math.log2(max(1, tex_width))))
        tex_height = 2 ** int(math.ceil(math.log2(max(1, tex_height))))

        # Clamp to reasonable limits
        tex_width = min(tex_width, 4096)
        tex_height = min(tex_height, 4096)

        return (tex_width, tex_height)


__all__ = [
    "RoadUVGenerator",
    "UVConfig",
]
